"""
OriginAgent  —  visual step-by-step agent for OriginLab plotting tasks.

Inherits NaviAgent's observation parsing and image handling, but uses
an Origin-specific system prompt that guides the model to write and run
Python (originpro) scripts through Origin's Code Builder (Alt+4).

Ablation flags
--------------
use_scripts : bool  (default True)
    True  → inject the domain-specific template script from origin_draw/ into
            the system prompt so the LLM adapts it rather than writing from scratch.
    False → no script provided; LLM must write the full script itself.
use_hint : bool  (default True)
    True  → include the full Origin workflow instructions (steps 1-7, key
            shortcuts, data-access rules) in the system prompt.
    False → no workflow hint at all; LLM receives only generic agent guidelines.
            Use this as the strongest ablation baseline (no_hint mode).
"""

import logging
import os
from typing import Dict, List, Optional

from mm_agents.navi.agent import NaviAgent
from mm_agents.navi.llm import planner_messages

logger = logging.getLogger("desktopenv.origin_agent")

# ---------------------------------------------------------------------------
# Mapping: task category keyword → template script filename in origin_draw/
# Add new entries here when new script types are added.
# ---------------------------------------------------------------------------
_CATEGORY_TO_SCRIPT: Dict[str, str] = {
    "bs":              "BS.py",
    "band_structure":  "BS.py",
    "xrd":             "XRD_match.py",
    "xrd_match":       "XRD_match.py",
    "xps":             "XPS.py",
    "ftir":            "FTIR.py",
    "raman":           "roman.py",
    "roman":           "roman.py",
    "cycle":           "cycle.py",
    "ce":              "CE.py",
    "coulombic":       "CE.py",
    "step":            "step.py",
    "free_energy":     "step.py",
    # Generic fallback — used for unknown/uncategorised tasks
    "base":            "base.py",
}

# Default directory that holds the template scripts (relative to this file's
# location one level up: client/origin_draw/).
_DEFAULT_SCRIPTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "origin_draw")
)


_STEP_EXTRA_NOTE = """\
**IMPORTANT – step/free-energy diagram data:** `REACTION_STEPS` and `GIBBS_ENERGY` \
in the template are placeholder example values. Before running the script you MUST:
1. Read the actual step labels and Gibbs energy values from the task instruction or \
the loaded worksheet (open the file with Ctrl+O if not yet loaded, then inspect the sheet).
2. Update `REACTION_STEPS` and `GIBBS_ENERGY` in the script to match the real values.
3. If no data is available in the task description or worksheet, open the sheet with \
Ctrl+O and copy the values from there into the script before running.
"""

_STEP_CATEGORIES = {"step", "free_energy"}


def _load_script(task_category: str, scripts_dir: str) -> Optional[str]:
    """Return the content of the template script for *task_category*.

    Falls back to ``base.py`` when the category is not in *_CATEGORY_TO_SCRIPT*.
    Returns None only if base.py itself is also missing.
    """
    key = task_category.lower().strip()
    filename = _CATEGORY_TO_SCRIPT.get(key)
    if filename is None:
        logger.warning(
            "OriginAgent: no template script mapped for category '%s'. "
            "Falling back to base.py.  Known categories: %s",
            task_category,
            list(_CATEGORY_TO_SCRIPT.keys()),
        )
        filename = "base.py"

    path = os.path.join(scripts_dir, filename)
    if not os.path.isfile(path):
        logger.warning("OriginAgent: script file not found: %s", path)
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info("OriginAgent: loaded template script '%s' (%d chars)", filename, len(content))
    return content


class OriginAgent(NaviAgent):
    """Visual step-by-step agent for OriginLab plotting and analysis tasks.

    Parameters
    ----------
    task_category : str or None
        The analysis type for this run (e.g. "xrd", "xps", "ftir", "raman",
        "cycle", "bs", "step", "ce").  Used to look up the matching template
        script in *scripts_dir*.  If None, no script is injected.
    use_scripts : bool
        Ablation flag.  Set to False to disable script injection and force the
        LLM to write everything from scratch.
    use_hint : bool
        Ablation flag.  Set to False to omit the entire Origin workflow hint
        (steps 1-7, key shortcuts, data-access rules) from the system prompt.
        Implies use_scripts=False (no script section either).
    scripts_dir : str or None
        Directory that contains the template scripts.  Defaults to
        ``client/origin_draw/`` relative to this file.
    """

    def __init__(
        self,
        server: str = "oai",
        model: str = "gpt-4o",
        som_config: Optional[dict] = None,
        som_origin: str = "oss",
        obs_view: str = "screen",
        auto_window_maximize: bool = False,
        use_last_screen: bool = True,
        related_apps: Optional[List[str]] = None,
        temperature: float = 0.5,
        max_tokens: int = 8000,
        # --- script-injection / hint params ---
        task_category: Optional[str] = None,
        use_scripts: bool = True,
        use_hint: bool = True,
        scripts_dir: Optional[str] = None,
    ):
        super().__init__(
            server=server,
            model=model,
            som_config=som_config,
            som_origin=som_origin,
            obs_view=obs_view,
            auto_window_maximize=auto_window_maximize,
            use_last_screen=use_last_screen,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.related_apps = related_apps or ["Origin"]
        self.task_category = task_category
        self.use_scripts = use_scripts
        self.use_hint = use_hint
        self.scripts_dir = scripts_dir or _DEFAULT_SCRIPTS_DIR

        # no_hint implies no script either
        effective_use_scripts = use_scripts and use_hint

        # Load template script — falls back to base.py when category is None or unknown
        script_content = None
        if effective_use_scripts:
            script_content = _load_script(task_category or "base", self.scripts_dir)

        # Choose system prompt based on observation mode:
        # no_omni = raw screenshots only, no element IDs → use raw variant
        self.gpt4v_planner.system_prompt = self._build_system_prompt(script_content)
        logger.info(
            "OriginAgent initialised (model=%s, apps=%s, category=%s, use_scripts=%s, use_hint=%s, script=%s, som_origin=%s)",
            model,
            self.related_apps,
            task_category,
            use_scripts,
            use_hint,
            "injected" if script_content else "none",
            som_origin,
        )

    def _build_system_prompt(self, script_content):
        """Select the correct system prompt variant based on observation mode."""
        extra_note = (
            _STEP_EXTRA_NOTE
            if self.task_category and self.task_category.lower().strip() in _STEP_CATEGORIES
            else None
        )
        if self.som_origin == "no_omni":
            return planner_messages.build_origin_raw_system_message(
                self.related_apps, script_content=script_content, extra_note=extra_note,
                use_hint=self.use_hint,
            )
        return planner_messages.build_origin_system_message(
            self.related_apps, script_content=script_content, extra_note=extra_note,
            use_hint=self.use_hint,
        )

    def update_related_apps(self, related_apps: List[str]) -> None:
        """Update related apps list and refresh the system prompt."""
        self.related_apps = related_apps
        script_content = None
        if self.use_scripts and self.use_hint:
            script_content = _load_script(self.task_category or "base", self.scripts_dir)
        self.gpt4v_planner.system_prompt = self._build_system_prompt(script_content)

    def update_task_category(self, task_category: str) -> None:
        """Switch to a different task category and reload the template script.

        Call this before each new example when the category changes (e.g. when
        the benchmark loop moves from an XRD task to an XPS task).
        """
        if task_category == self.task_category:
            return  # nothing to do
        self.task_category = task_category
        script_content = None
        if self.use_scripts and self.use_hint and task_category:
            script_content = _load_script(task_category, self.scripts_dir)
        self.gpt4v_planner.system_prompt = self._build_system_prompt(script_content)
        logger.info(
            "OriginAgent: updated task_category=%s, script=%s, som_origin=%s",
            task_category,
            "injected" if script_content else "none",
            self.som_origin,
        )

    def predict(self, instruction: str, obs: Dict):
        return super().predict(instruction, obs)


# Backward-compatible alias for code that still imports OriginCodeAgent.
OriginCodeAgent = OriginAgent
