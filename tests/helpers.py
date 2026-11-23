from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScenarioModel(BaseChatModel):
    """Substitui apenas o serviço LLM; o grafo, as tools e a memória são reais."""

    responder: Callable

    @property
    def _llm_type(self) -> str:
        return "scenario-test-double"

    def bind_tools(self, tools, **kwargs: Any):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        answer: AIMessage = self.responder(messages)
        return ChatResult(generations=[ChatGeneration(message=answer)])
