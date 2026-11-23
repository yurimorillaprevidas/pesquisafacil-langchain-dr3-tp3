"""Executa quatro casos com Gemini e salva perguntas, ações, observações e respostas."""

import argparse
import json
import platform
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import httpx
from dotenv import load_dotenv

from pesquisafacil.agent import (
    ConfigurationError,
    ResearchSession,
    build_agent,
    create_gemini_model,
)
from pesquisafacil.tools import create_tools

CASES = [
    {
        "id": "artigos",
        "pedido": "Busque 2 artigos sobre aprendizado de máquina em educação desde 2020.",
        "criterios": [
            "Utilizar buscar_artigos com ano_minimo=2020.",
            "Apresentar título, autoria, ano e link de dois artigos encontrados.",
            "Manter os metadados recebidos da ferramenta.",
        ],
    },
    {
        "id": "livros_com_memoria",
        "pedido": "Agora encontre 2 livros sobre o mesmo tema.",
        "criterios": [
            "Preservar o tema de aprendizado de máquina em educação.",
            "Utilizar buscar_livros e apresentar dois registros da fonte.",
        ],
    },
    {
        "id": "referencias_do_historico",
        "pedido": "Liste somente as referências que você encontrou, sem fazer novas buscas.",
        "criterios": [
            "Utilizar somente os registros anteriores.",
            "Não fazer novas chamadas de ferramenta.",
            "Não acrescentar títulos, autores ou links sem apoio nas observações.",
        ],
    },
    {
        "id": "nova_conversa",
        "pedido": "Quero livros sobre o mesmo tema.",
        "criterios": [
            "Pedir o tema, que não foi informado na nova conversa.",
            "Não reutilizar o contexto da sessão anterior nem consultar ferramentas.",
        ],
    },
]


def run_cases(session: ResearchSession, model_name: str) -> dict:
    """Registra a execução; a aprovação exige conferir os critérios e as respostas."""
    report = {
        "inicio_utc": datetime.now(UTC).isoformat(),
        "modelo": model_name,
        "python": platform.python_version(),
        "versoes": {
            name: version(name)
            for name in ("langchain", "langchain-google-genai", "langgraph", "httpx")
        },
        "casos": [],
    }
    for definition in CASES:
        print(f"Executando {definition['id']}...", flush=True)
        if definition["id"] == "nova_conversa":
            session.new_conversation()
        case = {**definition, "conversa": session.thread_id}
        try:
            turn = session.ask(definition["pedido"])
        except Exception:
            case.update(
                status="erro",
                erro="Não foi possível executar o caso. Verifique chave, modelo, cota e conexão.",
            )
            report["casos"].append(case)
            break
        case.update(
            status="executado",
            resposta=turn.answer,
            acoes=turn.actions,
            observacoes=turn.observations,
        )
        report["casos"].append(case)
    report["fim_utc"] = datetime.now(UTC).isoformat()
    report["status_execucao"] = (
        "concluida"
        if len(report["casos"]) == 4 and case["status"] == "executado"
        else "interrompida"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="docs/evidencias/gemini_real.json")
    args = parser.parse_args(argv)
    load_dotenv(Path.cwd() / ".env", override=False)
    try:
        model = create_gemini_model()
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    except Exception:
        print("Não foi possível configurar Gemini. Revise chave e modelo.", file=sys.stderr)
        return 2

    with httpx.Client(timeout=httpx.Timeout(20, connect=5)) as client:
        session = ResearchSession(build_agent(model, create_tools(client)))
        report = run_cases(session, model.model)
    report["modo"] = "Gemini e APIs reais; sem respostas programadas"
    output = Path(args.saida)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    for case in report["casos"]:
        print(f"{case['id']}: {case['status']}")
    print(f"Registro salvo em {output}. Confira os critérios e as respostas antes de aprovar.")
    return int(report["status_execucao"] != "concluida")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
