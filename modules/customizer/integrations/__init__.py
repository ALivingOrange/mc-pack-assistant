from collections.abc import Callable
from dataclasses import dataclass

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from ..config import MODEL_NAME, retry_config


@dataclass(frozen=True)
class Integration:
    """One mod-integration vertical: a modifier agent + the tools it owns.

    The shared `searcher_agent` runs first and feeds every modifier via the
    `search_result_summary` session key. Each integration supplies its own
    instruction text and tool list; `build_agent` wires them into an LlmAgent.
    """

    name: str
    instruction: str
    tools: list[Callable]

    def build_agent(self) -> LlmAgent:
        return LlmAgent(
            name=f"{self.name}_modifier_agent",
            model=Gemini(model=MODEL_NAME, retry_options=retry_config),
            instruction=self.instruction,
            tools=list(self.tools),
        )


from .recipes import recipes_integration  # noqa: E402

INTEGRATIONS: list[Integration] = [
    recipes_integration,
]

__all__ = ["INTEGRATIONS", "Integration"]
