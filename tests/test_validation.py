import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from pesquisafacil.agent import ResearchSession, build_agent
from scripts import validar_agente
from tests.helpers import ScenarioModel


def test_practical_cases_preserve_three_turns_then_start_new_context():
    received_histories = []

    def respond(messages):
        received_histories.append([m.content for m in messages if isinstance(m, HumanMessage)])
        return AIMessage(content="Resposta registrada.")

    session = ResearchSession(build_agent(ScenarioModel(responder=respond), []))
    report = validar_agente.run_cases(session, "modelo-de-teste")
    assert len(report["casos"]) == 4
    assert [len(history) for history in received_histories] == [1, 2, 3, 1]
    assert report["casos"][0]["resposta"] == "Resposta registrada."
    assert report["casos"][0]["conversa"] == report["casos"][2]["conversa"]
    assert report["casos"][3]["conversa"] != report["casos"][0]["conversa"]
    assert all(case["status"] == "executado" for case in report["casos"])


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError])
def test_provider_failure_is_recorded_without_secret_and_stops_calls(error_type):
    def respond(messages):
        raise error_type("provider-key-never-record")

    session = ResearchSession(build_agent(ScenarioModel(responder=respond), []))
    report = validar_agente.run_cases(session, "modelo-de-teste")
    assert len(report["casos"]) == 1
    assert report["casos"][0]["status"] == "erro"
    assert "provider-key" not in json.dumps(report)


def test_missing_key_does_not_create_real_execution_evidence(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    output = tmp_path / "evidencia.json"
    assert validar_agente.main(["--saida", str(output)]) == 2
    assert not output.exists()
    assert "GOOGLE_API_KEY" in capsys.readouterr().err
