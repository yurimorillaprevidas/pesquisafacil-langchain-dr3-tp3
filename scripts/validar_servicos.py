"""Verifica as duas APIs reais, sem LLM; salva evidências sem credenciais."""

import argparse
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import httpx

from pesquisafacil.tools import create_tools


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="docs/evidencias/apis_reais.json")
    args = parser.parse_args()
    with httpx.Client(timeout=httpx.Timeout(25, connect=5)) as client:
        tools = {tool.name: tool for tool in create_tools(client)}
        results = [
            tools["buscar_artigos"].invoke({"tema": "machine learning", "limite": 2}),
            tools["buscar_livros"].invoke({"tema": "machine learning", "limite": 2}),
            tools["buscar_artigos"].invoke(
                {"tema": "machine learning", "limite": 2, "ano_minimo": 2020}
            ),
        ]
    report = {
        "instante_utc": datetime.now(UTC).isoformat(),
        "tipo": "APIs reais, sem execução do modelo Gemini",
        "python": platform.python_version(),
        "versoes": {name: version(name) for name in ("langchain", "langgraph", "httpx")},
        "consultas": results,
    }
    output = Path(args.saida)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        state = result.get("erro", {}).get("codigo", "ok")
        print(f"{result['fonte']}: {state}; {len(result['resultados'])} registro(s).")
    print(f"Evidência: {output}")
    return int(any("erro" in result for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
