# PesquisaFácil — desenho da solução

Autor da entrega: Yuri Henrique Morilla Lima.

O enunciado delega a escolha do problema e da interface. A solução escolhida atende
estudantes que precisam localizar referências verificáveis para iniciar uma pesquisa.
O objetivo é reunir artigos e livros em uma conversa, preservando tema e restrições.

## Abordagens consideradas

1. Pesquisa bibliográfica com Crossref e Open Library: escolhida porque oferece duas
   ferramentas externas sem credenciais e permite verificar DOI e links.
2. Planejamento de atividades pelo clima: descartado porque a avaliação dependeria
   de previsões e datas voláteis sem contribuir para a pesquisa acadêmica.
3. Agente com busca web genérica: maior cobertura, mas com dependência adicional de
   uma chave de busca e menor uniformidade dos metadados.

As escolhas de domínio, Gemini e CLI são decisões de implementação, feitas com base
na liberdade concedida pelo enunciado; não foram apresentadas como preferências do autor.

## Arquitetura e limites

- Python 3.12+, LangChain `create_agent`, LangGraph `InMemorySaver`, Gemini configurável.
- CLI com pergunta única ou conversa; `/novo` limpa o contexto e `/sair` encerra.
- `buscar_artigos(tema, limite=3, ano_minimo=None)` consulta Crossref via HTTP.
- `buscar_livros(tema, limite=3)` consulta Open Library via HTTP.
- As ferramentas devolvem JSON normalizado e erros controlados, nunca credenciais.
- ReAct: modelo escolhe ferramenta; a observação retorna ao modelo; ele decide
  consultar outra fonte ou responder. A interface exibe ações e observações.
- Memória por `thread_id`, isolada entre conversas e mantida apenas no processo.
- Até 24 passos por invocação; entrada e resultados limitados para conter custos.
- Sem promessa de acesso ao texto integral ou validação de qualidade científica.
- Metadados externos são dados não confiáveis, não instruções ao agente.
- Demonstração separada com modelo roteirizado e transporte HTTP de fixtures,
  identificada como simulação; nunca apresentada como execução de Gemini.

## Validação

Testar normalização de metadados, filtro temporal, ausência de resultados, campos
incompletos, argumentos inválidos, timeout, HTTP 429 e JSON inesperado. Testar o
grafo real com modelo determinístico, duas ações em sequência, memória, isolamento
e limite de passos. Executar as duas APIs reais em script separado e preservar
resultados observados. A validação qualitativa com Gemini fica explicitamente
pendente se não houver chave de API.
