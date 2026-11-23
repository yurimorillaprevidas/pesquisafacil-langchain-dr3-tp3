import json

import httpx
import pytest

from pesquisafacil.tools import create_tools


def invoke(handler, name="buscar_artigos", **arguments):
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        tools = {tool.name: tool for tool in create_tools(client)}
        return tools[name].invoke(arguments)


def test_crossref_normalizes_and_sends_year_filter():
    def handler(request):
        assert request.url.host == "api.crossref.org"
        assert request.url.params["query.bibliographic"] == "machine learning"
        assert request.url.params["rows"] == "2"
        assert request.url.params["filter"] == "type:journal-article,from-pub-date:2020-01-01"
        return httpx.Response(
            200,
            json={
                "message": {
                    "total-results": 1,
                    "items": [
                        {
                            "title": ["Aprendizado de máquina"],
                            "DOI": "10.1234/teste",
                            "author": [{"given": "Ana", "family": "Silva"}],
                            "published": {"date-parts": [[2021, 4]]},
                            "container-title": ["Revista Exemplo"],
                        }
                    ],
                }
            },
        )

    result = invoke(handler, tema=" machine learning ", limite=2, ano_minimo=2020)
    assert result["resultados"] == [
        {
            "titulo": "Aprendizado de máquina",
            "autores": ["Ana Silva"],
            "ano": 2021,
            "doi": "10.1234/teste",
            "url": "https://doi.org/10.1234/teste",
            "publicacao": "Revista Exemplo",
        }
    ]


def test_openlibrary_normalizes_book_and_handles_missing_fields():
    def handler(request):
        assert request.url.host == "openlibrary.org"
        assert request.url.params["q"] == "python"
        return httpx.Response(
            200,
            json={
                "numFound": 2,
                "docs": [
                    {
                        "title": "Python",
                        "author_name": ["Ana"],
                        "first_publish_year": 2020,
                        "key": "/works/OL123W",
                    },
                    {"key": "javascript:bad"},
                ],
            },
        )

    result = invoke(handler, name="buscar_livros", tema="python", limite=2)
    assert result["resultados"][0] == {
        "titulo": "Python",
        "autores": ["Ana"],
        "ano": 2020,
        "url": "https://openlibrary.org/works/OL123W",
    }
    assert result["resultados"][1]["ano"] is None
    assert result["resultados"][1]["url"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        {"tema": "   "},
        {"tema": "x" * 301},
        {"tema": "x", "limite": 0},
        {"tema": "x", "limite": 6},
        {"tema": "x", "ano_minimo": 1499},
    ],
)
def test_invalid_input_does_not_reach_network(arguments):
    def handler(request):
        pytest.fail("Entrada inválida não pode chamar a API.")

    result = invoke(handler, **arguments)
    assert result["erro"]["codigo"] == "entrada_invalida"


@pytest.mark.parametrize(
    "name,payload",
    [
        ("buscar_artigos", {"message": {"items": [], "total-results": 0}}),
        ("buscar_livros", {"docs": [], "numFound": 0}),
    ],
)
def test_empty_search_is_not_network_error(name, payload):
    result = invoke(lambda request: httpx.Response(200, json=payload), name=name, tema="xyz")
    assert result["resultados"] == []
    assert "erro" not in result


@pytest.mark.parametrize("status,code", [(429, "limite_api"), (503, "servico_indisponivel")])
def test_http_errors_are_controlled(status, code):
    result = invoke(lambda request: httpx.Response(status), tema="python")
    assert result["erro"]["codigo"] == code
    assert result["resultados"] == []


def test_timeout_is_controlled():
    def handler(request):
        raise httpx.ReadTimeout("sensitive internal details", request=request)

    result = invoke(handler, tema="python")
    assert result["erro"]["codigo"] == "timeout"
    assert "sensitive" not in str(result)


@pytest.mark.parametrize("payload", [[], {"message": None}, {"message": {"items": "bad"}}])
def test_malformed_schema_is_controlled(payload):
    result = invoke(lambda request: httpx.Response(200, json=payload), tema="python")
    assert result["erro"]["codigo"] == "dados_invalidos"


def test_invalid_json_is_controlled():
    result = invoke(lambda request: httpx.Response(200, text="not json"), tema="python")
    assert result["erro"]["codigo"] == "dados_invalidos"


def test_null_article_metadata_does_not_crash():
    payload = {"message": {"items": [{"title": None, "author": None, "published": None}]}}
    result = invoke(lambda request: httpx.Response(200, json=payload), tema="python")
    assert result["resultados"][0]["titulo"] == "Título não informado"
    assert result["resultados"][0]["ano"] is None


@pytest.mark.parametrize("arguments", [{"tema": "python", "limite": []}, {}])
def test_schema_errors_are_json_without_network(arguments):
    def handler(request):
        pytest.fail("O validador não deve consultar a rede.")

    result = json.loads(invoke(handler, **arguments))
    assert result["erro"]["codigo"] == "entrada_invalida"
    assert result["resultados"] == []
