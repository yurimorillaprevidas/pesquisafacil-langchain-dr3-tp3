# Testes e evidências — DR3 TP3

Autor: Yuri Henrique Morilla Lima. Data local: 22/11/2026 (America/Sao_Paulo).

## O que foi executado

- Python 3.12.15; LangChain 1.5.2; LangGraph 1.2.24; HTTPX 0.28.1.
- 26 testes automatizados sem rede ou credenciais.
- `ruff check .` e `ruff format --check .` para código e formatação.
- Demonstração CLI com duas perguntas e memória no mesmo processo.
- Consultas reais no Crossref e na Open Library, sem usar um LLM.

As falhas iniciais dos testes foram observadas antes de implementar os módulos
de tools, agente e CLI; depois as suítes passaram. A ausência de chave Gemini
impediu a validação de respostas geradas por um LLM real. Nenhuma execução
simulada deste relatório deve ser interpretada como teste de qualidade do Gemini.

## Casos práticos

### UC1 — levantamento inicial em duas fontes

Pedido da demo: “Encontre 2 artigos e 2 livros sobre machine learning.”
Esperado: usar ambas as ferramentas, devolver referências e indicar as fontes.
Observado: o grafo enviou a primeira ação a `buscar_artigos`, recebeu um
`ToolMessage`, enviou a segunda a `buscar_livros` e apresentou os quatro registros
dos snapshots. O teste `test_react_observation_drives_second_action_and_final_answer`
confirma que a observação chega ao modelo antes da próxima ação.

Nas consultas reais, os dois serviços retornaram dois registros cada. Entre os
livros observados está *Hands-On Machine Learning with Scikit-Learn, Keras, and
TensorFlow*, de Aurélien Géron, com primeira publicação registrada como 2019.
Esses dados descrevem o catálogo e não uma leitura do livro. A consulta ampla
também retornou artigos antigos, o que mostra a importância de informar o recorte
temporal quando isso for necessário. Evidência: [apis_reais.json](evidencias/apis_reais.json).

### UC2 — continuação com memória

Segundo pedido da demo: “Agora mostre só livros sobre o mesmo tema.”
Esperado: recuperar `machine learning` sem exigir a repetição do assunto.
Observado: a segunda invocação recebeu o histórico pelo checkpointer, recuperou
os argumentos anteriores e chamou apenas `buscar_livros` para o mesmo tema.
Trata-se de uma decisão roteirizada que comprova o transporte de contexto.
Não é uma evidência de compreensão linguística por Gemini.

O teste de memória usa outro tema (`diabetes`) e verifica o histórico completo.
Após `new_conversation()`, o modelo de teste recebe apenas a nova pergunta e
responde que precisa do tema. O teste da CLI também percorre `/novo` e `/sair`.

### UC3 — filtro temporal

Entrada: `buscar_artigos(tema="machine learning", limite=2, ano_minimo=2020)`.
Esperado: enviar filtro de data ao serviço, sem filtrar somente depois da busca.
Observado: o teste verifica a URL e os parâmetros; o script de APIs reais também
registra a resposta filtrada. O filtro se aplica aos artigos. A tool de livros
retorna o ano da primeira publicação e não oferece filtro de ano.

### UC4 — resultados ausentes e falhas

Entradas controladas: lista vazia, timeout, HTTP 429, HTTP 503, JSON inválido,
estrutura inesperada, autoria e data ausentes, limite zero/seis e tema vazio.
Esperado: preservar a distinção entre ausência de resultados e falha, impedir
requisição inválida e não inventar referências.
Observado: ferramentas retornaram listas vazias e/ou códigos de erro apropriados;
metadados opcionais foram tratados sem quebrar a aplicação. URLs de catálogo
fora do formato permitido não foram transformadas em links.

### UC5 — limite e configuração

Esperado: interromper ações repetidas e orientar o uso sem credenciais.
Observado: um modelo que sempre chama a mesma ferramenta foi interrompido pelo
limite do grafo e a sessão foi renovada. Sem chave, a CLI explica como configurar
`GOOGLE_API_KEY` e termina com código 2. Erros inesperados de provedor terminam
com código 1 na consulta única e não expõem a mensagem bruta nem seus segredos.

## Arquivos e reprodução

- [Demonstração CLI](evidencias/demo.txt): saída de `python app.py --demo`.
- [APIs reais](evidencias/apis_reais.json): instante UTC, versões e metadados.
- [Verificação local](evidencias/verificacao.txt): testes, análise estática e formatação.
- Snapshots em `data/`: dados mínimos capturados nas duas APIs; a demo é offline.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python app.py --demo
python -m scripts.validar_servicos
```

Os testes automáticos substituem apenas os serviços externos lentos/cobrados.
O grafo LangChain, as tools, a normalização e o checkpointer são os reais.
Já o script de serviços chama as APIs públicas; seus resultados podem variar.

## Validação com Gemini — pendente

Após preencher `.env`, executar no chat real:

| Pedido | Verificar |
| --- | --- |
| “Busque 2 artigos sobre aprendizado de máquina em educação desde 2020.” | Tool de artigos com `ano_minimo=2020`, títulos e DOIs iguais aos retornados |
| “Agora 2 livros sobre o mesmo tema.” | Tema mantido e tool de livros chamada |
| “Liste apenas as referências que você encontrou.” | Nenhuma referência adicionada sem observação que a sustente |
| `/novo`, seguido de “Quero livros sobre o mesmo tema.” | Solicitação de esclarecimento por falta do assunto |

Critérios: fonte correta, fidelidade a título/autoria/data/link, coerência da
continuação, tratamento de falhas e ausência de alegações de leitura integral.
Registrar nome do modelo, data e resultado de cada pedido ao concluir essa etapa.
Não há resultados inventados ou marcação de aprovação para esta validação.

## Comparação com a execução manual

Sem o agente, o estudante precisa formular a consulta em cada serviço, recolher
os metadados, reunir a lista e repetir o processo a cada refinamento. O agente
centraliza essas operações e carrega o contexto entre pedidos. A seleção crítica
das referências e a leitura dos textos permanecem responsabilidade do estudante.
O ganho de tempo é uma hipótese fundamentada no fluxo, não uma medida coletada.
