"""Interface de linha de comando em português."""

import argparse
import json
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from pesquisafacil.agent import AgentError, ResearchSession, Turn, build_agent, create_gemini_model
from pesquisafacil.demo import DEMO_QUESTIONS, create_demo_session, demo_transport
from pesquisafacil.tools import create_tools


def print_turn(turn: Turn, full_trace: bool = False) -> None:
    for i, action in enumerate(turn.actions):
        arguments = json.dumps(action["argumentos"], ensure_ascii=False)
        print(f"Ação: {action['ferramenta']}({arguments})")
        if i < len(turn.observations):
            observation = turn.observations[i]
            raw = observation["resultado"]
            try:
                data = json.loads(raw)
                summary = (
                    data["erro"]["mensagem"]
                    if "erro" in data
                    else f"{data.get('fonte')}: {len(data.get('resultados', []))} registro(s)."
                )
            except (ValueError, TypeError, KeyError):
                summary = "Retorno de validação da ferramenta."
            print(f"Observação: {raw if full_trace else summary}")
    print(f"\nPesquisaFácil> {turn.answer}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PesquisaFácil — agente bibliográfico com memória")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pergunta", help="Faz uma pergunta única e encerra.")
    mode.add_argument(
        "--demo", action="store_true", help="Executa demonstração simulada sem chave/rede."
    )
    parser.add_argument(
        "--rastro", action="store_true", help="Mostra observações completas das tools."
    )
    args = parser.parse_args(argv)
    load_dotenv(Path.cwd() / ".env", override=False)

    if args.demo:
        print("DEMONSTRAÇÃO SIMULADA: modelo roteirizado + snapshots das APIs.")
        print("Não chama Gemini nem internet; demonstra o grafo ReAct e a memória.\n")
        with httpx.Client(transport=httpx.MockTransport(demo_transport)) as client:
            session = create_demo_session(client)
            for question in DEMO_QUESTIONS:
                print(f"Você> {question}")
                print_turn(session.ask(question), args.rastro)
        return 0

    try:
        model = create_gemini_model()
    except ValueError as error:
        print(f"Configuração: {error}", file=sys.stderr)
        return 2
    except Exception:
        print("Não foi possível configurar Gemini. Revise .env e dependências.", file=sys.stderr)
        return 2

    with httpx.Client(timeout=httpx.Timeout(20, connect=5)) as client:
        session = ResearchSession(build_agent(model, create_tools(client)))
        if args.pergunta is not None:
            return _ask_once(session, args.pergunta, args.rastro)
        print("PesquisaFácil | Gemini | memória temporária nesta execução")
        print("Digite seu tema. Comandos: /novo (outro contexto), /sair.\n")
        while True:
            try:
                question = input("Você> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nConversa encerrada.")
                break
            if question.lower() == "/sair":
                break
            if question.lower() == "/novo":
                session.new_conversation()
                print("Nova conversa iniciada. Informe o tema novamente.\n")
                continue
            if not question:
                continue
            result = _ask_once(session, question, args.rastro)
            if result == 1:
                session.new_conversation()
                print("Nova conversa iniciada após a falha. Informe o tema novamente.")
    return 0


def _ask_once(session: ResearchSession, question: str, full_trace: bool) -> int:
    try:
        print_turn(session.ask(question), full_trace)
        return 0
    except (ValueError, AgentError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except Exception:
        # Mensagens brutas de provedores podem conter detalhes de credenciais/requisições.
        print(
            "Não foi possível concluir a consulta. Verifique chave, modelo, cota e conexão.",
            file=sys.stderr,
        )
        return 1
