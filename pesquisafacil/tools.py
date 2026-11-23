"""Tools de leitura para duas APIs bibliográficas públicas."""

import re
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import BaseTool, tool

USER_AGENT = "PesquisaFacil-DR3-TP3/1.0 (educational bibliography search)"


def _error(source: str, code: str, message: str) -> dict[str, Any]:
    return {"fonte": source, "resultados": [], "erro": {"codigo": code, "mensagem": message}}


def _validate(theme: str, limit: int, year: int | None = None) -> bool:
    return (
        1 <= len(theme.strip()) <= 300
        and 1 <= limit <= 5
        and (year is None or 1500 <= year <= 2100)
    )


def _get_json(client: httpx.Client, url: str, params: dict) -> Any:
    response = client.get(url, params=params, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


def _network_error(source: str, error: Exception) -> dict:
    if isinstance(error, httpx.TimeoutException):
        return _error(source, "timeout", "A consulta demorou demais. Tente novamente mais tarde.")
    if isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 429:
        return _error(
            source, "limite_api", "Limite da API atingido. Aguarde antes de tentar de novo."
        )
    if isinstance(error, (ValueError, TypeError, KeyError, IndexError)):
        return _error(source, "dados_invalidos", "A API retornou dados em formato inesperado.")
    return _error(source, "servico_indisponivel", "Não foi possível consultar esta fonte agora.")


def _first_text(value: Any, fallback: str = "Título não informado") -> str:
    if isinstance(value, list):
        return next((item[:500] for item in value if isinstance(item, str) and item), fallback)
    return fallback


def _article_year(item: dict) -> int | None:
    for field in ("published", "published-print", "published-online", "issued"):
        date = item.get(field)
        parts = date.get("date-parts") if isinstance(date, dict) else None
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            year = parts[0][0]
            if isinstance(year, int):
                return year
    return None


def create_tools(client: httpx.Client) -> list[BaseTool]:
    """Constrói tools com cliente injetado; o chamador controla seu ciclo de vida."""

    @tool
    def buscar_artigos(tema: str, limite: int = 3, ano_minimo: int | None = None) -> dict:
        """Busca artigos científicos no Crossref por tema, com DOI e metadados.

        Use para localizar artigos verificáveis, sem alegar leitura do texto integral.
        tema: termos da pesquisa (1 a 300 caracteres; inglês pode melhorar cobertura).
        limite: quantidade de registros, de 1 a 5.
        ano_minimo: primeiro ano aceito, entre 1500 e 2100, ou None para não filtrar.
        """
        if not _validate(tema, limite, ano_minimo):
            return _error("Crossref", "entrada_invalida", "Revise tema, limite (1–5) e ano mínimo.")
        params = {
            "query.bibliographic": tema.strip(),
            "rows": limite,
            "filter": "type:journal-article",
        }
        if ano_minimo is not None:
            params["filter"] += f",from-pub-date:{ano_minimo}-01-01"
        try:
            data = _get_json(client, "https://api.crossref.org/works", params)
            if not isinstance(data, dict) or not isinstance(data.get("message"), dict):
                raise ValueError("Invalid message")
            message = data["message"]
            if not isinstance(message.get("items"), list):
                raise ValueError("Invalid items")
            records = []
            for item in message["items"][:limite]:
                if not isinstance(item, dict):
                    raise ValueError("Invalid article")
                authors = item.get("author") or []
                if not isinstance(authors, list):
                    raise ValueError("Invalid authors")
                names = []
                for author in authors[:8]:
                    if isinstance(author, dict):
                        name = " ".join(str(author.get(key) or "") for key in ("given", "family"))
                        if name.strip():
                            names.append(name.strip()[:200])
                doi = item.get("DOI")
                doi = doi if isinstance(doi, str) and doi.startswith("10.") else None
                records.append(
                    {
                        "titulo": _first_text(item.get("title")),
                        "autores": names,
                        "ano": _article_year(item),
                        "doi": doi,
                        "url": f"https://doi.org/{quote(doi, safe='/')}" if doi else None,
                        "publicacao": _first_text(item.get("container-title"), "Não informada"),
                    }
                )
            return {
                "fonte": "Crossref",
                "consulta": tema.strip(),
                "total_encontrado": message.get("total-results"),
                "resultados": records,
            }
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as error:
            return _network_error("Crossref", error)

    @tool
    def buscar_livros(tema: str, limite: int = 3) -> dict:
        """Busca livros por tema no catálogo público Open Library.

        Retorna título, autores, ano da primeira publicação e link do catálogo.
        tema: termos de busca (1 a 300 caracteres); limite: de 1 a 5.
        Um registro no catálogo não garante texto integral ou empréstimo disponível.
        """
        if not _validate(tema, limite):
            return _error("Open Library", "entrada_invalida", "Informe tema e limite entre 1 e 5.")
        try:
            data = _get_json(
                client,
                "https://openlibrary.org/search.json",
                {
                    "q": tema.strip(),
                    "limit": limite,
                    "fields": "key,title,author_name,first_publish_year",
                },
            )
            if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
                raise ValueError("Invalid books")
            records = []
            for item in data["docs"][:limite]:
                if not isinstance(item, dict):
                    raise ValueError("Invalid book")
                key = item.get("key")
                valid_key = isinstance(key, str) and re.fullmatch(r"/works/OL\d+W", key)
                title = item.get("title")
                authors = item.get("author_name")
                year = item.get("first_publish_year")
                records.append(
                    {
                        "titulo": title[:500] if isinstance(title, str) else "Título não informado",
                        "autores": [name[:200] for name in authors[:8] if isinstance(name, str)]
                        if isinstance(authors, list)
                        else [],
                        "ano": year if isinstance(year, int) else None,
                        "url": f"https://openlibrary.org{key}" if valid_key else None,
                    }
                )
            return {
                "fonte": "Open Library",
                "consulta": tema.strip(),
                "total_encontrado": data.get("numFound"),
                "resultados": records,
            }
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as error:
            return _network_error("Open Library", error)

    tools = [buscar_artigos, buscar_livros]
    for item in tools:
        item.handle_validation_error = "Argumentos inválidos. Use os tipos indicados na ferramenta."
    return tools
