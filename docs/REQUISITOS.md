# Conferência do enunciado

| Item | Implementação ou documentação | Situação |
| --- | --- | --- |
| 1. Definir o problema, o público, as funcionalidades e os casos de uso | README: problema e objetivo; `docs/TESTES.md`: casos práticos e automatizados | Atendido |
| 2. Configurar LangChain e escolher um LLM | `requirements.txt`, `.env.example` e `create_gemini_model` em `pesquisafacil/agent.py` | Atendido; Gemini utilizado em teste real |
| 3. Criar pelo menos duas ferramentas externas | `buscar_artigos` e `buscar_livros`, em `pesquisafacil/tools.py`, com nome, descrição, parâmetros e registro `@tool` | Atendido |
| 4. Utilizar ReAct | `build_agent`, em `pesquisafacil/agent.py`; ciclo entre modelo, ferramentas e observações | Atendido; seleção e refinamento de ferramentas observados com Gemini |
| 5. Adicionar memória conversacional | `InMemorySaver`, `thread_id` e `ResearchSession` | Atendido; memória mantida durante a execução |
| 6. Integrar a lógica do agente | `build_agent` e `ResearchSession.ask` integram modelo, ferramentas e histórico | Atendido; integração verificada em quatro casos reais |
| 7. Criar interface funcional | `app.py` e `pesquisafacil/cli.py`: chat, pergunta única, `/novo`, `/sair` e demonstração | Atendido |
| 8. Realizar testes práticos e explicar o benefício do agente | Quatro casos com Gemini, 35 testes automatizados, evidências e comparação com a pesquisa manual | Atendido; respostas e metadados conferidos |
| 9. Publicar o código e elaborar README | Repositório público; README com problema, solução, execução, casos testados e reflexão | Atendido |
| 10. Seguir boas práticas de codificação | Módulos separados, nomes descritivos, tipagem, comentários, tratamento de erros e verificação com Ruff | Atendido |

## Arquivo de entrega

`Yuri_Henrique_Morilla_Lima_DR3_TP3.ZIP`, com o código `.py`, README, dependências,
testes e evidências. A submissão no ambiente acadêmico deve ser feita pelo aluno.

## Validação prática

Os quatro casos foram executados com Gemini 3.5 Flash-Lite e as APIs reais em
22/11/2026. As respostas, ações e observações estão em `docs/evidencias/gemini_real.json`
e `docs/evidencias/gemini_real.txt`. A análise dos resultados está em `docs/TESTES.md`.
As execuções simuladas continuam identificadas separadamente.
