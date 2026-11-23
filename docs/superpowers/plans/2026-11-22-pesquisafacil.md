# PesquisaFácil Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** entregar projeto Python e ZIP com agente bibliográfico, duas tools e memória.

**Architecture:** clientes HTTP limitados e ferramentas LangChain ficam em `tools.py`.
O grafo e o prompt ficam em `agent.py`; a CLI em `cli.py`; a simulação em `demo.py`.

**Tech Stack:** Python 3.12, LangChain 1, LangGraph 1, Gemini, HTTPX, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-11-22-pesquisafacil-design.md`.

## Global Constraints

- Python 3.12+; duas ferramentas externas; interface CLI em português.
- Memória por `thread_id`, isolada entre conversas e mantida apenas no processo.
- Não declarar Gemini testado sem uma chamada real bem-sucedida.
- Não publicar chaves, ambientes virtuais ou histórico de usuário.

## Review Focus

- Metadados ausentes ou malformados: erro controlado ou indicação de ausência.
- HTTP 429/timeout: explicar falha sem inventar resultados.
- Conversa nova: não reutilizar tema da conversa anterior.
- Modelo que repete chamadas: parar com limite de passos.
- Chave ausente: orientar configuração com mensagem clara.

## Task 1: ferramentas bibliográficas

**Files:** `pesquisafacil/tools.py`, `tests/test_tools.py`.
**Interfaces:** `create_tools(client: httpx.Client) -> list[BaseTool]`.

- [x] Escrever testes de normalização, filtro, limites, erros e metadados incompletos.
- [x] Executar `python -m pytest tests/test_tools.py -q`; observar falha antes do código.
- [x] Implementar clientes e ferramentas; executar novamente e obter sucesso.

## Task 2: agente, memória e demonstração

**Files:** `pesquisafacil/agent.py`, `pesquisafacil/demo.py`, `tests/test_agent.py`.
**Interfaces:** `build_agent(model, tools)` e `ResearchSession.ask(text)`.

- [x] Testar duas ferramentas sequenciais com observações retornando ao modelo.
- [x] Testar preservação de histórico, nova conversa e limite de passos.
- [x] Observar falhas, implementar e executar toda a suíte.
- [x] Adicionar demonstração roteirizada explícita usando o mesmo grafo e tools.

## Task 3: CLI, evidências e entrega

**Files:** `app.py`, `pesquisafacil/cli.py`, `tests/test_cli.py`, README, `.env.example`,
`scripts/validar_servicos.py`, `.github/workflows/tests.yml`, `docs/evidencias/`.
**Interfaces:** `main(argv=None) -> int`, pergunta única, chat e `--demo`.

- [x] Testar entrada inválida, chave ausente e comandos `/novo` e `/sair`.
- [x] Implementar e executar `pytest`, `ruff check`, `ruff format --check`.
- [x] Rodar demonstração e APIs reais; documentar saídas e limitações.
- [ ] Revisar segurança, requisitos e execução a partir do ZIP extraído.
- [ ] Publicar repositório público e criar ZIP com nome informado pelo autor.
