"""LLMPlanner — model-agnostic multi-modal planner."""
from mm_agents.navi.gpt.gpt4v_planner import GPT4V_Planner


class LLMPlanner(GPT4V_Planner):
    """
    Model-agnostic planner.  Identical to GPT4V_Planner but without the
    GPT-specific name.  Supports any OpenAI-compatible backend (Qwen, Claude,
    GPT-4o, etc.) by passing the appropriate `server` and `model` arguments.
    """
    pass
