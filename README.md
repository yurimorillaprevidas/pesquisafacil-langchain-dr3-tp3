# PesquisaFácil

**Yuri Henrique Morilla Lima**

Desenvolvimento de Data-Driven Apps com Python [26E4_3] — DR3 TP3

[Repositório no GitHub](https://github.com/yurimorillaprevidas/pesquisafacil-langchain-dr3-tp3)

## Problema e objetivo

O levantamento bibliográfico exige pesquisar em diferentes catálogos, reunir
títulos, autores e links e repetir as consultas quando o tema é refinado. O
PesquisaFácil reúne esse trabalho em uma conversa: busca artigos no Crossref e
livros na Open Library, organiza os metadados e mantém o assunto dos pedidos
anteriores.

A aplicação é voltada a estudantes de graduação e pesquisadores iniciantes.
Seu objetivo é ajudar na seleção inicial de referências, com indicação da fonte
de cada registro. A leitura dos textos e a avaliação da qualidade das publicações
continuam sendo feitas pelo estudante.

As funcionalidades são:

- Busca de artigos por tema, com filtro opcional de ano inicial.
- Busca de livros por tema.
- Apresentação de título, autoria, ano e link.
- Continuação da pesquisa sem precisar repetir o assunto.
- Reinício da conversa e exibição das ferramentas utilizadas.

## Instalação e execução

O projeto foi testado com **Python 3.12**. Execute os comandos dentro da pasta
extraída do ZIP ou clonada do repositório.

### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` e preencha `GOOGLE_API_KEY` com uma chave obtida no
[Google AI Studio](https://aistudio.google.com/apikey). Depois, inicie a aplicação:

```powershell
.\.venv\Scripts\python.exe app.py
```

### Linux e macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# Preencha GOOGLE_API_KEY em .env.
.venv/bin/python app.py
```

O arquivo de configuração contém:

```dotenv
GOOGLE_API_KEY=sua_chave
GEMINI_MODEL=gemini-3.5-flash-lite
```

O modelo é integrado pelo pacote `langchain-google-genai` e pode ser alterado
pela variável `GEMINI_MODEL`. A escolha considera o suporte a chamadas de
ferramentas e o uso em consultas curtas. São usados os parâmetros de amostragem
padrão do modelo, timeout de 30 segundos e uma tentativa por chamada ao provedor.
O uso depende da disponibilidade e da cota da conta Google. O arquivo `.env` é
ignorado pelo Git e não deve ser publicado.

### Como utilizar

```text
Você> Busque 2 artigos sobre aprendizado de máquina em educação desde 2020.
Você> Agora encontre 2 livros sobre o mesmo tema.
Você> Organize as referências que já encontrou em uma lista de leitura.
Você> /novo
Você> /sair
```

`/novo` inicia uma conversa sem o contexto anterior. `/sair` encerra o programa.
Também é possível enviar uma pergunta única ou consultar o retorno das ferramentas:

```powershell
.\.venv\Scripts\python.exe app.py --pergunta "Encontre 2 livros sobre Python"
.\.venv\Scripts\python.exe app.py --rastro
.\.venv\Scripts\python.exe app.py --help
```

Para conhecer a interface sem configurar uma chave:

```powershell
.\.venv\Scripts\python.exe app.py --demo
```

Essa demonstração executa dois exemplos fixos com respostas programadas e cópias
de dados das APIs. Ela utiliza o grafo e a memória do projeto, mas não chama Gemini
nem faz novas consultas à internet. O aviso de simulação aparece ao iniciar.

## Ferramentas externas

As duas funções de pesquisa são registradas no LangChain com `@tool`, nome,
descrição e parâmetros tipados. A comunicação HTTP é feita com HTTPX.

| Ferramenta | Função | Parâmetros | Dados retornados |
| --- | --- | --- | --- |
| `buscar_artigos` | Consultar artigos no Crossref | `tema`, `limite` e `ano_minimo` opcional | Título, autores, ano, periódico, DOI e link |
| `buscar_livros` | Consultar livros na Open Library | `tema` e `limite` | Título, autores, ano da primeira publicação e link do catálogo |

`tema` aceita de 1 a 300 caracteres e `limite` aceita de 1 a 5 resultados por
consulta. Para artigos, `ano_minimo` deve estar entre 1500 e 2100. Esse filtro é
enviado ao Crossref; a ferramenta de livros não oferece filtro temporal.

As APIs não exigem chave nas consultas implementadas. Erros de entrada, timeout,
limite de requisições e respostas inválidas são tratados separadamente. Campos
ausentes são identificados como não informados. As ferramentas retornam JSON
com os registros encontrados ou uma descrição do erro.

## ReAct e funcionamento do agente

O agente é criado em `pesquisafacil/agent.py` com `langchain.agents.create_agent`,
usando Gemini como modelo e as duas ferramentas de pesquisa. O ciclo segue o
padrão ReAct:

1. O modelo recebe o pedido, as instruções e o histórico da conversa.
2. Decide se precisa consultar uma ferramenta e escolhe seus argumentos.
3. O LangChain executa a chamada e devolve o resultado como uma observação.
4. O modelo considera o resultado e pode realizar outra consulta.
5. Quando possui informação suficiente, apresenta a resposta ao usuário.

Por exemplo, um pedido de artigos e livros pode começar com uma busca no
Crossref. Após receber os artigos, o agente consulta a Open Library e reúne as
duas fontes na resposta. No modo com Gemini, a seleção das ferramentas depende
do pedido e das observações, em vez de seguir uma sequência fixa.

A interface mostra as ações e um resumo dos resultados. `--rastro` exibe as
observações completas. O processamento é limitado a 24 passos por pergunta para
interromper chamadas repetidas. O prompt orienta o agente a citar somente os
dados recebidos e a informar falhas ou ausência de resultados.

## Memória conversacional

O histórico é mantido por `InMemorySaver`, do LangGraph. Cada conversa possui um
`thread_id`; as perguntas seguintes usam o mesmo identificador para recuperar
pedidos, respostas e resultados das ferramentas.

Isso permite continuar com “agora apenas livros sobre o mesmo tema”. O comando
`/novo` muda o identificador, separando o contexto da conversa anterior. O histórico
fica somente na memória do processo e é perdido ao fechar o programa. No modo
com Gemini, esse histórico é enviado ao provedor para compor o contexto.

## Casos de uso e testes

| Caso | Validação | Resultado observado |
| --- | --- | --- |
| Pesquisar artigos e livros | Consultar ambas as fontes e reunir referências | As APIs retornaram dois registros cada; o teste de integração percorreu as duas ferramentas |
| Continuar a pesquisa | Recuperar o tema da pergunta anterior | O histórico chegou à segunda invocação e o tema foi mantido nos testes |
| Filtrar artigos por ano | Enviar o filtro temporal ao Crossref | O parâmetro foi conferido no teste e a consulta filtrada foi executada na API |
| Iniciar outra conversa | Separar o contexto anterior | Os testes de sessão e do comando `/novo` passaram |
| Tratar falhas | Informar problemas sem inventar registros | Foram testados timeout, HTTP 429/503, listas vazias, JSON inválido e campos ausentes |
| Interromper repetições | Aplicar o limite de passos | O teste interrompeu o ciclo e iniciou outra sessão |

Foram executados **31 testes automatizados**, a demonstração em linha de comando
e consultas reais às duas APIs. Os testes do agente usam respostas controladas
para conferir ferramentas e memória. **A validação da conversa com Gemini permanece
pendente, pois não havia chave configurada no ambiente de teste.** O roteiro e as
evidências estão em [docs/TESTES.md](docs/TESTES.md).

Comandos de verificação:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m scripts.validar_servicos
```

O último comando consulta as APIs reais e salva o resultado em
`docs/evidencias/apis_reais.json`. Os demais testes não precisam de internet ou
credenciais. O workflow do GitHub executa testes, análise estática, formatação e
demonstração a cada atualização do repositório.

## Organização do código

```text
app.py                       Entrada do programa
pesquisafacil/agent.py        Modelo, instruções, ciclo ReAct e memória
pesquisafacil/tools.py        Consultas, validação e normalização de metadados
pesquisafacil/cli.py          Interface de linha de comando
pesquisafacil/demo.py         Demonstração offline
tests/                       Testes das ferramentas, do agente e da interface
scripts/validar_servicos.py   Verificação das APIs reais
data/                        Dados utilizados pela demonstração
docs/TESTES.md               Casos de uso e resultados
docs/REQUISITOS.md           Conferência dos itens do enunciado
docs/evidencias/             Registros de execução
requirements.txt             Versões das dependências
.env.example                 Exemplo de configuração
```

Os módulos separam a interface, o agente e o acesso aos serviços externos. O
código usa nomes descritivos, parâmetros tipados e comentários sobre decisões
de implementação. As mensagens brutas de erro do provedor não são exibidas.

## Comparação com a pesquisa manual

Sem o agente, o estudante precisa abrir cada catálogo, definir as consultas,
copiar os metadados e reunir as referências. Ao mudar o recorte, precisa repetir
parte desse processo. A aplicação centraliza as consultas e reaproveita o contexto
da conversa para os próximos pedidos.

O benefício esperado é reduzir a repetição e a organização manual das buscas.
As ferramentas fornecem dados dos catálogos, e o modelo decide como utilizá-las
e apresentar os resultados. O agente não substitui a conferência das referências
nem a leitura dos textos. Não foi realizado um estudo de tempo ou de precisão
com usuários para medir esse benefício.

## Entrega

O arquivo `Yuri_Henrique_Morilla_Lima_DR3_TP3.ZIP` contém os arquivos `.py`, o
README, as dependências, os testes e as evidências. Não contém chaves nem ambiente
virtual. O repositório é público e está indicado no início deste documento.

## Referências técnicas

- [Agentes no LangChain](https://docs.langchain.com/oss/python/langchain/agents)
- [Memória de curto prazo](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Integração com Gemini](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai)
- [Modelo Gemini configurado](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite)
- [ReAct](https://github.com/ysymyth/ReAct)
- [API do Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- [API da Open Library](https://openlibrary.org/dev/docs/api/search)
