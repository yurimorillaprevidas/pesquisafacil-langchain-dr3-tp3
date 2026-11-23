import json

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from pesquisafacil.agent import AgentError, ResearchSession, build_agent, create_gemini_model
from pesquisafacil.tools import create_tools
from tests.helpers import ScenarioModel


def test_react_observation_drives_second_action_and_final_answer():
    def handler(request):
        if request.url.host == "api.crossref.org":
            return httpx.Response(
                200,
                json={
                    "message": {
                        "items": [
                            {"title": ["Artigo encontrado"], "DOI": "10.1000/exemplo"},
                        ]
                    }
                },
            )
        return httpx.Response(200, json={"docs": [{"title": "Livro encontrado"}]})

    def respond(messages):
        observations = [m for m in messages if isinstance(m, ToolMessage)]
        if not observations:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "buscar_artigos",
                        "args": {"tema": "python"},
                        "id": "artigos-1",
                    }
                ],
            )
        if len(observations) == 1:
            assert "Artigo encontrado" in observations[-1].content
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "buscar_livros",
                        "args": {"tema": "python"},
                        "id": "livros-1",
                    }
                ],
            )
        assert "Livro encontrado" in observations[-1].content
        return AIMessage(content="Artigo encontrado e Livro encontrado. DOI: 10.1000/exemplo")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        session = ResearchSession(
            build_agent(ScenarioModel(responder=respond), create_tools(client))
        )
        turn = session.ask("Busque artigos e livros de python.")
    assert "10.1000/exemplo" in turn.answer
    assert [action["ferramenta"] for action in turn.actions] == ["buscar_artigos", "buscar_livros"]
    assert json.loads(turn.observations[1]["resultado"])["fonte"] == "Open Library"


def test_memory_carries_topic_and_new_conversation_is_isolated():
    def respond(messages):
        human = [m.content for m in messages if isinstance(m, HumanMessage)]
        if len(human) == 1:
            return AIMessage(content="Tema registrado." if "diabetes" in human[0] else "Qual tema?")
        assert human == ["Meu tema é diabetes.", "E livros sobre esse tema?"]
        return AIMessage(content="Livros sobre diabetes.")

    session = ResearchSession(build_agent(ScenarioModel(responder=respond), []))
    session.ask("Meu tema é diabetes.")
    turn = session.ask("E livros sobre esse tema?")
    assert turn.answer == "Livros sobre diabetes."
    old_id = session.thread_id
    session.new_conversation()
    assert session.thread_id != old_id
    assert session.ask("E livros sobre esse tema?").answer == "Qual tema?"


def test_empty_input_is_rejected_without_changing_history():
    model = ScenarioModel(responder=lambda messages: AIMessage(content="ok"))
    session = ResearchSession(build_agent(model, []))
    with pytest.raises(ValueError):
        session.ask("   ")
    with pytest.raises(ValueError):
        session.ask("x" * 4001)
    assert session.agent.get_state(session.config).values == {}


def test_repeated_actions_stop_at_limit_and_reset_session():
    def respond(messages):
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "buscar_livros",
                    "args": {"tema": "python"},
                    "id": str(len(messages)),
                }
            ],
        )

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"docs": []}))
    ) as client:
        session = ResearchSession(
            build_agent(ScenarioModel(responder=respond), create_tools(client)),
            max_steps=4,
        )
        old_id = session.thread_id
        with pytest.raises(AgentError, match="limite"):
            session.ask("Pesquise livros.")
        assert session.thread_id != old_id


def test_missing_key_has_clear_configuration_message(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        create_gemini_model()
