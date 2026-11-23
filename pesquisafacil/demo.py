"""Demonstração determinística: não usa Gemini nem conexão com a internet."""

import json
from pathlib import Path
from typing import Any

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from pesquisafacil.agent import ResearchSession, build_agent
from pesquisafacil.tools import create_tools

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEMO_QUESTIONS = [
    "Encontre 2 artigos e 2 livros sobre machine learning.",
    "Agora mostre só livros sobre o mesmo tema.",
]


class DemoModel(BaseChatModel):
    """Modelo roteirizado para os dois pedidos de DEMO_QUESTIONS, sem inteligência LLM."""

    @property
    def _llm_type(self) -> str:
        return "demo-roteirizada-sem-llm"

    def bind_tools(self, tools, **kwargs: Any):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        start = max(i for i, item in enumerate(messages) if isinstance(item, HumanMessage))
        books_only = "só livros" in messages[start].content
        observations = [m for m in messages[start + 1 :] if isinstance(m, ToolMessage)]
        # A segunda pergunta recupera o tema dos argumentos preservados na memória.
        previous_calls = [
            call
            for message in messages[:start]
            if isinstance(message, AIMessage)
            for call in message.tool_calls
        ]
        if books_only and not previous_calls:
            result = AIMessage(content="Informe o tema para esta nova conversa.")
            return ChatResult(generations=[ChatGeneration(message=result)])
        theme = (
            previous_calls[-1]["args"]["tema"]
            if books_only and previous_calls
            else "machine learning"
        )
        next_tool = None
        if not observations:
            next_tool = "buscar_livros" if books_only else "buscar_artigos"
        elif len(observations) == 1 and not books_only:
            next_tool = "buscar_livros"
        if next_tool:
            result = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": next_tool,
                        "args": {"tema": theme, "limite": 2},
                        "id": f"demo-{len(messages)}",
                    }
                ],
            )
        else:
            lines = [f"[Resposta roteirizada de demonstração] Tema: {theme}."]
            for observation in observations:
                data = json.loads(observation.content)
                lines.append(f"\nFonte: {data['fonte']}")
                for record in data["resultados"]:
                    authors = ", ".join(record["autores"]) or "Autoria não informada"
                    lines.append(
                        f"- {record['titulo']} — {authors} ({record['ano'] or 'ano ausente'}). "
                        f"{record['url'] or 'Link não informado'}"
                    )
            lines.append("\nSão metadados de um snapshot; o texto integral não foi consultado.")
            result = AIMessage(content="\n".join(lines))
        return ChatResult(generations=[ChatGeneration(message=result)])


def demo_transport(request: httpx.Request) -> httpx.Response:
    files = {"api.crossref.org": "demo_crossref.json", "openlibrary.org": "demo_openlibrary.json"}
    filename = files.get(request.url.host)
    if filename is None:
        return httpx.Response(404)
    return httpx.Response(200, json=json.loads((DATA_DIR / filename).read_text(encoding="utf-8")))


def create_demo_session(client: httpx.Client) -> ResearchSession:
    return ResearchSession(build_agent(DemoModel(), create_tools(client)))
