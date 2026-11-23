# Testes

Foram executados quatro casos práticos com **Gemini 3.5 Flash-Lite**, Crossref e
Open Library em **22/11/2026, às 23h46, horário de São Paulo**. As respostas foram
conferidas com os metadados e as chamadas registradas. Também foram executados
35 testes automatizados e a demonstração offline.

Ambiente: Python 3.12.15, LangChain 1.5.2, `langchain-google-genai` 4.5.2,
LangGraph 1.2.24 e HTTPX 0.28.1.

## Casos práticos com Gemini

### 1. Buscar artigos com filtro de ano

**Pedido:** “Busque 2 artigos sobre aprendizado de máquina em educação desde 2020.”

**Esperado:** utilizar o Crossref com filtro de ano e apresentar referências
fiéis aos dados recebidos.

**Observado:** o agente traduziu a consulta para `machine learning in education`
e chamou `buscar_artigos` com `limite=2` e `ano_minimo=2020`. Foram retornados
dois artigos, publicados em 2022 e 2025. Títulos, ano, autoria disponível e links
DOI foram conferidos. No registro sem autoria, a resposta informou a ausência
em vez de atribuir um nome. O agente também deixou claro que não havia lido
os textos integrais.

**Resultado:** aprovado.

### 2. Continuar a pesquisa e refinar a busca de livros

**Pedido:** “Agora encontre 2 livros sobre o mesmo tema.”

**Esperado:** recuperar o tema anterior, usar a ferramenta de livros e selecionar
referências relacionadas a aprendizado de máquina na educação.

**Observado:** o agente manteve o tema e consultou a Open Library. A primeira
busca, `machine learning education`, trouxe dois livros de ficção que não
correspondiam ao assunto. Ao observar esses resultados, o agente executou uma
segunda chamada com a expressão exata `"machine learning in education"` e
`limite=5`. O catálogo retornou dois registros pertinentes:

- *Analysis of a Machine Learning in Education System*, de Lata Menon,
  Pradip P. Chatterjjee e Prof. Mange Amar Vilasrao, de 2022.
- *Machine Learning in Educational Sciences*, de Myint Swe Khine, de 2024.

A resposta apresentou esses dois livros, com títulos, autores, anos e links
iguais aos retornados. Os livros de ficção não foram recomendados. As duas
chamadas estão registradas na evidência, mostrando o ciclo de ação, observação
e refinamento da consulta.

**Resultado:** aprovado.

### 3. Reunir somente as referências do histórico

**Pedido:** “Liste somente as referências que você encontrou, sem fazer novas buscas.”

**Esperado:** utilizar o histórico e não adicionar referências sem apoio nas
observações anteriores.

**Observado:** foram listados os dois artigos e os dois livros pertinentes dos
casos anteriores. Não houve nova chamada de ferramenta. Títulos, autoria,
datas e os quatro links foram conferidos com os registros anteriores; não
foram acrescentados outros links ou títulos.

**Resultado:** aprovado.

### 4. Iniciar uma conversa sem o contexto anterior

**Procedimento:** iniciar uma nova conversa, equivalente ao comando `/novo`,
e enviar “Quero livros sobre o mesmo tema.”

**Esperado:** pedir o tema, pois ele não foi informado nessa nova conversa.

**Observado:** o identificador da conversa mudou. Gemini respondeu:

> Para que eu possa buscar livros sobre o mesmo tema, por favor, informe qual é o tema ou assunto que você deseja pesquisar.

Não houve consulta a ferramentas nem recuperação das referências anteriores.

**Resultado:** aprovado.

## Evidências da execução real

- [Registro completo em JSON](evidencias/gemini_real.json): modelo, versões,
  horários, pedidos, ações, observações, respostas e avaliação de cada caso.
- [Registro em texto](evidencias/gemini_real.txt): a mesma execução em formato
  de leitura direta.
- [Consultas independentes às APIs](evidencias/apis_reais.json).

Os três primeiros pedidos utilizaram a mesma conversa. O quarto utilizou outra
conversa. Ao todo, foram realizadas três chamadas de ferramenta: uma ao Crossref
e duas à Open Library. As respostas vieram de Gemini; não foram usadas respostas
programadas ou cópias locais dos catálogos nesses quatro casos.

## Testes automatizados

Os **35 testes passaram**. Eles verificam:

- Integração entre o grafo, as ferramentas e as observações.
- Preservação do tema e isolamento entre conversas.
- Filtro temporal e normalização dos metadados.
- Entrada inválida, campos ausentes, listas vazias, timeout, HTTP 429/503 e JSON inválido.
- Limite de passos, configuração, comandos da interface e mensagens de erro.
- Registro dos quatro casos sem criar evidência real quando falta chave.

Esses testes usam respostas controladas para os serviços externos, mantendo o
grafo, as ferramentas e a memória da aplicação. São independentes da execução
com Gemini relatada acima. A análise com Ruff e a verificação de formatação
também passaram.

- [Testes e verificações locais](evidencias/verificacao.txt).
- [Demonstração offline](evidencias/demo.txt): usa respostas programadas e dados
  salvos em `data/`, identificados como simulação.

## Reprodução

Depois de instalar as dependências e configurar `GOOGLE_API_KEY` no `.env`:

```text
python -m scripts.validar_agente
```

O comando executa os quatro pedidos com Gemini e as APIs reais e grava
`docs/evidencias/gemini_real.json`. A marcação `executado` indica que houve
resposta; a aprovação exige conferir os critérios com as respostas. Repetir o
comando substitui o registro anterior. O modo manual é `python app.py --rastro`.

Para as demais verificações:

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python app.py --demo
python -m scripts.validar_servicos
```

Os testes automatizados e a demonstração não precisam de credenciais ou rede.
Os comandos de validação real dependem da disponibilidade do modelo e das APIs.

## Comparação com o processo manual

Sem o agente, o estudante precisaria pesquisar nos dois catálogos, reaplicar o
tema, identificar os resultados fora do assunto, reformular a busca e reunir
manualmente títulos, autores, datas e links. Nos casos executados, o agente
realizou essas operações a partir dos pedidos em linguagem natural e manteve
o contexto para organizar as quatro referências sem uma nova consulta.

O refinamento da busca de livros mostra uma contribuição além de copiar dados:
o agente utilizou a observação recebida para decidir outra ação antes da resposta.
A ausência de autoria em um artigo foi preservada, o que facilita identificar
quais informações ainda precisam ser conferidas pelo estudante.

## Limites da avaliação

Os quatro casos comprovam o funcionamento observado nesse recorte. Não medem
a precisão geral de Gemini, a qualidade científica das obras ou uma economia
de tempo com usuários. Resultados de catálogos podem ser incompletos ou pouco
relacionados ao assunto; a seleção crítica e a leitura dos textos continuam
necessárias. O agente não garante acesso gratuito ao texto integral.
