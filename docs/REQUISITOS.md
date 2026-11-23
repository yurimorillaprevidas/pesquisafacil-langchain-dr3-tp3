# Conferência do enunciado

| Item | Implementação ou documentação | Situação |
| --- | --- | --- |
| 1. Definir o problema, o público, as funcionalidades e os casos de uso | README: problema e objetivo; `docs/TESTES.md`: cinco casos de uso | Atendido |
| 2. Configurar LangChain e escolher um LLM | `requirements.txt`, `.env.example` e `create_gemini_model` em `pesquisafacil/agent.py` | Implementado; uso com Gemini requer chave |
| 3. Criar pelo menos duas ferramentas externas | `buscar_artigos` e `buscar_livros`, em `pesquisafacil/tools.py`, com nome, descrição, parâmetros e registro `@tool` | Atendido |
| 4. Utilizar ReAct | `build_agent`, em `pesquisafacil/agent.py`; ciclo entre modelo, ferramentas e observações | Implementado e verificado com modelo controlado |
| 5. Adicionar memória conversacional | `InMemorySaver`, `thread_id` e `ResearchSession` | Atendido; memória mantida durante a execução |
| 6. Integrar a lógica do agente | `build_agent` e `ResearchSession.ask` integram modelo, ferramentas e histórico | Implementado e verificado com modelo controlado |
| 7. Criar interface funcional | `app.py` e `pesquisafacil/cli.py`: chat, pergunta única, `/novo`, `/sair` e demonstração | Atendido |
| 8. Realizar testes práticos e explicar o benefício do agente | 31 testes, demonstração, consultas reais às APIs e comparação com a pesquisa manual | Parcial: falta executar os casos com Gemini e registrar as respostas |
| 9. Publicar o código e elaborar README | Repositório público; README com problema, solução, execução, casos testados e reflexão | Atendido |
| 10. Seguir boas práticas de codificação | Módulos separados, nomes descritivos, tipagem, comentários, tratamento de erros e verificação com Ruff | Atendido |

## Arquivo de entrega

`Yuri_Henrique_Morilla_Lima_DR3_TP3.ZIP`, com o código `.py`, README, dependências,
testes e evidências. A submissão no ambiente acadêmico deve ser feita pelo aluno.

## Pendência

Para concluir o item 8, configurar `GOOGLE_API_KEY` no `.env` e executar o roteiro
de `docs/TESTES.md` no modo com Gemini. A demonstração offline não substitui esse
teste. As simulações e as consultas reais estão identificadas separadamente.
