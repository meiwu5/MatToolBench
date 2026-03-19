"""
OriginAgent  —  visual step-by-step agent for OriginLab plotting tasks.

Inherits NaviAgent's observation parsing and image handling, but uses
an Origin-specific system prompt that guides the model to write and run
Python (originpro) scripts through Origin's Code Builder (Alt+4).

Ablation flag
-------------
use_scripts : bool  (default True)
    True  → inject the domain-specific template script from origin_draw/ into
            the system prompt so the LLM adapts it rather than writing from scratch.
    False → no script provided; LLM must write the full script itself.
            Use this condition as the ablation baseline.
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
}

# Default directory that holds the template scripts (relative to this file's
# location one level up: client/origin_draw/).
_DEFAULT_SCRIPTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "origin_draw")
)


def _load_script(task_category: str, scripts_dir: str) -> Optional[str]:
    """Return the content of the template script for *task_category*, or None."""
    key = task_category.lower().strip()
    filename = _CATEGORY_TO_SCRIPT.get(key)
    if filename is None:
        logger.warning(
            "OriginAgent: no template script mapped for category '%s'. "
            "Known categories: %s",
            task_category,
            list(_CATEGORY_TO_SCRIPT.keys()),
        )
        return None

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
        LLM to write everything from scratch (baseline condition).
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
        # --- script-injection params ---
        task_category: Optional[str] = None,
        use_scripts: bool = True,
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
        )
        self.related_apps = related_apps or ["Origin"]
        self.task_category = task_category
        self.use_scripts = use_scripts
        self.scripts_dir = scripts_dir or _DEFAULT_SCRIPTS_DIR

        # Load template script (may be None if disabled or not found)
        script_content = None
        if use_scripts and task_category:
            script_content = _load_script(task_category, self.scripts_dir)

        self.gpt4v_planner.system_prompt = planner_messages.build_origin_system_message(
            self.related_apps, script_content=script_content
        )
        logger.info(
            "OriginAgent initialised (model=%s, apps=%s, category=%s, use_scripts=%s, script=%s)",
            model,
            self.related_apps,
            task_category,
            use_scripts,
            "injected" if script_content else "none",
        )

    def update_related_apps(self, related_apps: List[str]) -> None:
        """Update related apps list and refresh the system prompt."""
        self.related_apps = related_apps
        script_content = None
        if self.use_scripts and self.task_category:
            script_content = _load_script(self.task_category, self.scripts_dir)
        self.gpt4v_planner.system_prompt = planner_messages.build_origin_system_message(
            self.related_apps, script_content=script_content
        )

    def update_task_category(self, task_category: str) -> None:
        """Switch to a different task category and reload the template script.

        Call this before each new example when the category changes (e.g. when
        the benchmark loop moves from an XRD task to an XPS task).
        """
        if task_category == self.task_category:
            return  # nothing to do
        self.task_category = task_category
        script_content = None
        if self.use_scripts and task_category:
            script_content = _load_script(task_category, self.scripts_dir)
        self.gpt4v_planner.system_prompt = planner_messages.build_origin_system_message(
            self.related_apps, script_content=script_content
        )
        logger.info(
            "OriginAgent: updated task_category=%s, script=%s",
            task_category,
            "injected" if script_content else "none",
        )

    def predict(self, instruction: str, obs: Dict):
        return super().predict(instruction, obs)


# Backward-compatible alias for code that still imports OriginCodeAgent.
OriginCodeAgent = OriginAgent
