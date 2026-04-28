"""
GUIAgent  —  visual step-by-step agent for materials-science GUI software.

Supported applications (non-exhaustive):
  • Jade  (XRD analysis)
  • Avantage  (XPS analysis)
  • VESTA  (crystal structure visualisation)
  • DM
  • Material Studio

This is a thin subclass of NaviAgent that swaps in a domain-specific
system prompt.  All observation handling, screen parsing, and LLM
plumbing are inherited unchanged.
"""

import logging
from typing import Dict, List, Optional

from mm_agents.navi.agent import NaviAgent
from mm_agents.navi.llm import planner_messages

logger = logging.getLogger("desktopenv.gui_agent")


class GUIAgent(NaviAgent):
    """Step-by-step GUI agent for materials-science desktop applications."""

    def __init__(
        self,
        server: str = "oai",
        model: str = "gpt-4o",
        som_config: Optional[dict] = None,
        som_origin: str = "oss",
        obs_view: str = "screen",
        auto_window_maximize: bool = False,
        use_last_screen: bool = True,
        temperature: float = 0.5,
        max_tokens: int = 2048,
        use_software_hints: bool = True,
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
        # Replace the generic planner prompt with the GUI-specific one.
        raw = som_origin == "no_omni"
        self.gpt4v_planner.system_prompt = planner_messages.build_gui_system_message(
            use_software_hints=use_software_hints, raw=raw
        )
        logger.info(
            "GUIAgent initialised (model=%s, server=%s, use_software_hints=%s)",
            model, server, use_software_hints,
        )
