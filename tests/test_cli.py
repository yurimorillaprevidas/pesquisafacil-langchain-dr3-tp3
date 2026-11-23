import pytest
from langchain_core.messages import AIMessage, HumanMessage

from pesquisafacil import cli
from tests.helpers import ScenarioModel


def test_demo_runs_without_credentials_and_identifies_simulation(capsys):
    assert cli.main(["--demo"]) == 0
    output = capsys.readouterr().out
    assert "SIMULADA" in output
    assert "buscar_artigos" in output
    assert "buscar_livros" in output
    assert "mesmo tema" in output
    assert "https://" in output


def test_missing_key_exits_with_configuration_guidance(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert cli.main(["--pergunta", "Busque livros sobre python"]) == 2
    assert "GOOGLE_API_KEY" in capsys.readouterr().err


def test_new_command_restarts_context(monkeypatch, tmp_path, capsys):
    def respond(messages):
        humans = [m for m in messages if isinstance(m, HumanMessage)]
        return AIMessage(
            content="Tema registrado." if "python" in humans[0].content else "Qual tema?"
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "create_gemini_model", lambda: ScenarioModel(responder=respond))
    answers = iter(["Meu tema é python", "/novo", "Qual era meu tema?", "/sair"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    assert "Nova conversa" in output
    assert "Qual tema?" in output


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError])
def test_provider_error_does_not_leak_details(monkeypatch, tmp_path, capsys, error_type):
    def respond(messages):
        raise error_type("secret=provider-key-never-print")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "create_gemini_model", lambda: ScenarioModel(responder=respond))
    assert cli.main(["--pergunta", "Busque artigos sobre python"]) == 1
    error = capsys.readouterr().err
    assert "Não foi possível" in error
    assert "provider-key" not in error


def test_provider_initialization_value_error_is_sanitized(monkeypatch, tmp_path, capsys):
    def initialize():
        raise ValueError("secret=provider-key-never-print")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "create_gemini_model", initialize)
    assert cli.main(["--pergunta", "Busque livros"]) == 2
    error = capsys.readouterr().err
    assert "Não foi possível" in error
    assert "provider-key" not in error
