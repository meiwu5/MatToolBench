"""
CodeAgent  —  code-generation agent for materials-science database / API tasks.

Supported task categories (maps to the required virtual environment):
  • oqmd       → oqmd venv   (qmpy_rester / requests)
  • mp         → pymatgen venv  (mp_api / pymatgen)
  • pymatgen   → pymatgen venv
  • optimade   → pymatgen venv  (optimade-client)
  • ms         → ms venv
  • dm         → dm venv

Workflow per predict() call:
  1. Build a prompt from the instruction (+ error feedback if retrying).
  2. Call the LLM (text-only, no screenshot needed).
  3. Parse the returned ```python … ``` block.
  4. Return an action that writes the code to a temp file and runs it
     using the correct venv's Python interpreter.

The number of attempts is controlled by the outer max_steps loop in
lib_run_single.py (same as GUIAgent), not by an internal retry counter.
On each subsequent call the previous code and stderr are fed back to the
LLM so it can self-correct.  When code executes successfully the agent
returns ["DONE"] to terminate the episode immediately.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from mm_agents.navi.llm.llm_planner import LLMPlanner
from mm_agents.navi.llm import planner_messages

logger = logging.getLogger("desktopenv.code_agent")

# ---------------------------------------------------------------------------
# Venv base directory inside the VM and per-category sub-directory names.
# Adjust VENV_BASE if the VM layout differs.
# ---------------------------------------------------------------------------
VENV_BASE = r"C:\Users\Docker"

CATEGORY_TO_VENV: dict = {
    "oqmd":      "oqmd",
    "mp":        "pymatgen",
    "pymatgen":  "pymatgen",
    "optimade":  "optimade"
}

# Temp script path written inside the VM for each execution attempt.
TEMP_SCRIPT = r"C:\Users\Docker\Desktop\setup\mat_temp_solution.py"
# Output capture file — cmd.exe redirects stdout/stderr here so we can read it back.
TEMP_OUTPUT = r"C:\Users\Docker\Desktop\setup\mat_temp_output.txt"


def _python_exe(venv_name: str) -> str:
    """Return the absolute path to the venv's Python interpreter."""
    return rf"{VENV_BASE}\{venv_name}\Scripts\python.exe"


def _make_run_action(code: str, venv_name: str) -> str:
    """
    Return a Python code string (executed inside the VM) that:
      1. Writes `code` to TEMP_SCRIPT via base64 (immune to any quote/backslash issues).
      2. Opens a visible cmd.exe window that activates the venv and runs the script,
         redirecting stdout+stderr to TEMP_OUTPUT (CREATE_NEW_CONSOLE is incompatible
         with PIPE on Windows, so we use file redirection to capture output).
      3. Reads TEMP_OUTPUT and prints it for the harness to parse.
    """
    import base64
    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    python_exe = _python_exe(venv_name)
    activate_bat = rf"{VENV_BASE}\{venv_name}\Scripts\activate.bat"

    lines = [
        "import subprocess, os, base64, time",
        f'_script = r"{TEMP_SCRIPT}"',
        f'_output = r"{TEMP_OUTPUT}"',
        f'_python_exe = r"{python_exe}"',
        f'_activate = r"{activate_bat}"',
        f'_code = base64.b64decode("{encoded}").decode("utf-8")',
        "os.makedirs(os.path.dirname(_script), exist_ok=True)",
        'with open(_script, "w", encoding="utf-8") as _f:',
        "    _f.write(_code)",
        "if not os.path.exists(_python_exe):",
        '    print("SCRIPT_STDOUT:")',
        '    print("SCRIPT_STDERR: Python executable not found:", _python_exe)',
        '    print("RETURNCODE:", 127)',
        "else:",
        "    try:",
        # Build cmd command: activate venv then run script, redirect output to file
        '        _cmd = f\'cmd /c ""{_activate}" && "{_python_exe}" "{_script}" > "{_output}" 2>&1"\'',
        "        _proc = subprocess.Popen(",
        "            _cmd,",
        "            shell=True,",
        "            creationflags=subprocess.CREATE_NEW_CONSOLE,",
        "        )",
        "        _proc.wait(timeout=300)",
        "        _rc = _proc.returncode",
        '        _out = open(_output, encoding="utf-8", errors="replace").read() if os.path.exists(_output) else ""',
        '        print("SCRIPT_STDOUT:", _out[:3000])',
        '        print("SCRIPT_STDERR:")',
        '        print("RETURNCODE:", _rc)',
        "    except Exception as _e:",
        '        print("SCRIPT_STDOUT:")',
        '        print("SCRIPT_STDERR:", str(_e))',
        '        print("RETURNCODE:", 1)',
    ]
    return "\n".join(lines) + "\n"


class CodeAgent:
    """
    LLM-driven code-generation agent for materials database / API tasks.

    Parameters
    ----------
    task_category : str
        One of the keys in CATEGORY_TO_VENV (e.g. "oqmd", "mp").
    server : str
        LLM backend – "oai" (OpenAI-compatible) or "azure".
    model : str
        Model identifier forwarded to GPT4V_Planner.
    temperature : float
        Sampling temperature for the LLM.
    """

    def __init__(
        self,
        task_category: str,
        server: str = "oai",
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        use_api_hints: bool = True,
    ):
        self.action_space = "code_block"   # required by DesktopEnv / lib_run_single
        self.task_category = task_category.lower()
        self.venv_name = CATEGORY_TO_VENV.get(self.task_category, self.task_category)

        # Text-only planner (images are not needed for code tasks).
        self.planner = LLMPlanner(server=server, model=model, temperature=temperature)
        mp_api_key = os.getenv("MP_API_KEY") or os.getenv("MAPI_KEY") or ""
        print(f"MP_API_KEY: {mp_api_key[:10]}..." if mp_api_key else "MP_API_KEY: NOT SET")
        self.planner.system_prompt = planner_messages.build_code_system_message(
            mp_api_key, use_api_hints=use_api_hints
        )

        self.max_tokens = max_tokens

        # Per-episode state
        self._prev_code: Optional[str] = None
        self._prev_error: Optional[str] = None
        self._succeeded: bool = False

        logger.info(
            "CodeAgent initialised (category=%s, venv=%s, model=%s, use_api_hints=%s)",
            self.task_category, self.venv_name, model, use_api_hints,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, instruction: str, obs: Dict) -> Tuple[str, List[str], Dict, Dict]:
        """
        Generate (or revise) a Python solution script and return an action
        that runs it inside the VM.

        Returns
        -------
        response          : str   – empty (not used by harness)
        actions           : list  – single action string or ["DONE"] / ["FAIL"]
        logs              : dict  – diagnostic information
        computer_update_args : dict – minimal stub (no GUI rects needed)
        """
        logs: Dict = {}

        # --- Terminal condition: previous run succeeded ------------------
        if self._succeeded:
            logger.info("CodeAgent: previous execution succeeded — DONE")
            return "", ["DONE"], logs, self._stub_computer_args()

        # --- Build user prompt -------------------------------------------
        user_msg = planner_messages.build_code_user_msg(
            instruction=instruction,
            prev_code=self._prev_code,
            error_msg=self._prev_error,
        )
        logs["user_msg"] = user_msg

        # --- Call LLM (text only, no images) -----------------------------
        logger.info("CodeAgent: calling LLM…")
        llm_response = self.planner.plan(images=[], user_query=user_msg, max_tokens=self.max_tokens)
        logs["llm_response"] = llm_response

        # --- Parse code block --------------------------------------------
        match = re.search(r"```python\n(.*?)```", llm_response, re.DOTALL)
        if not match:
            logger.error("CodeAgent: no python block found in LLM response")
            self._prev_error = "No ```python``` block was returned by the model."
            return "", ["# code block not found"], logs, self._stub_computer_args()

        solution_code = match.group(1).strip()
        self._prev_code = solution_code
        logs["solution_code"] = solution_code

        # --- Build run action --------------------------------------------
        action = _make_run_action(solution_code, self.venv_name)
        logs["run_action"] = action

        return "", [action], logs, self._stub_computer_args()

    def handle_action_result(self, stdout: str, stderr: str, returncode: int) -> None:
        """
        Feed back execution results so the next predict() call can self-correct.
        Call this after the harness has executed the returned action.

        Parameters
        ----------
        stdout, stderr  : output captured from the subprocess run.
        returncode      : 0 means success.
        """
        if returncode == 0:
            self._prev_error = None
            self._succeeded = True
            logger.info("CodeAgent: execution succeeded")
        else:
            self._prev_error = f"returncode={returncode}\nSTDERR:\n{stderr[:2000]}"
            logger.warning("CodeAgent: execution failed (rc=%d)", returncode)

    def reset(self) -> None:
        """Reset per-episode state."""
        self._prev_code = None
        self._prev_error = None
        self._succeeded = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stub_computer_args() -> Dict:
        """Return empty dict — CodeAgent has no GUI state to push.
        lib_run_single checks `if computer_update_args:` before calling
        update_computer(), so returning {} safely skips that call and avoids
        a crash from update_computer trying to base64-encode a None screenshot.
        """
        return {}
