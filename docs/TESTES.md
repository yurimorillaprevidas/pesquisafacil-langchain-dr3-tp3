# Testes

O projeto foi verificado com Python 3.12.15, LangChain 1.5.2, LangGraph 1.2.24 e
HTTPX 0.28.1. Os testes automatizados utilizam respostas controladas para os
serviços externos; o grafo, as ferramentas e o armazenamento do histórico são
os utilizados pela aplicação.

## Casos de uso

### 1. Buscar artigos e livros

**Pedido:** “Encontre 2 artigos e 2 livros sobre machine learning.”

**Esperado:** consultar Crossref e Open Library, reunir os registros e indicar
a fonte de cada referência.

**Observado:** o teste de integração chamou `buscar_artigos`, recebeu o resultado
como `ToolMessage` e então chamou `buscar_livros`. A demonstração apresentou os
quatro registros dos dados salvos. Nas consultas reais, cada API também retornou
dois registros. Veja [apis_reais.json](evidencias/apis_reais.json).

### 2. Continuar uma pesquisa

**Pedido:** após o caso anterior, “Agora mostre só livros sobre o mesmo tema.”

**Esperado:** manter `machine learning` como tema e consultar apenas livros.

**Observado:** a segunda invocação recuperou o histórico e reutilizou o tema.
Outro teste conferiu o histórico com o assunto `diabetes`. Depois de iniciar uma
nova conversa, o modelo de teste deixou de receber o assunto anterior. A
demonstração também solicita o tema quando a continuação chega sem histórico.

### 3. Restringir o período dos artigos

**Entrada:** `buscar_artigos(tema="machine learning", limite=2, ano_minimo=2020)`.

**Esperado:** enviar o filtro temporal ao serviço antes de obter os resultados.

**Observado:** o teste conferiu o parâmetro
`filter=type:journal-article,from-pub-date:2020-01-01`. A consulta real filtrada
está no arquivo de evidências. A ferramenta de livros não aplica esse filtro;
seu ano corresponde à primeira publicação registrada no catálogo.

### 4. Tratar ausência de dados e falhas

**Entradas:** tema vazio, limites fora do intervalo, campos obrigatórios ausentes,
tipos inválidos, lista vazia, timeout, HTTP 429/503 e JSON inesperado.

**Esperado:** impedir requisições inválidas e distinguir falhas de consultas sem
resultados. Campos ausentes não devem ser preenchidos com informações inventadas.

**Observado:** os testes retornaram os códigos de erro previstos e listas vazias
quando apropriado. Autoria e data ausentes não interromperam a aplicação. Erros
de esquema retornaram JSON serializado pelo validador do LangChain.

### 5. Controlar a execução e reiniciar a conversa

**Esperado:** interromper chamadas repetidas, separar o contexto ao usar `/novo`
e orientar a configuração quando não houver chave.

**Observado:** o limite de passos interrompeu um modelo que repetia ações e
renovou a sessão. Os comandos `/novo` e `/sair` passaram pelo teste da interface.
Sem chave, a consulta encerrou com código 2 e instrução de configuração. Falhas
externas durante a consulta encerraram com código 1, sem imprimir detalhes
internos do provedor.

## Resultados e reprodução

Os **31 testes automatizados passaram**. A análise com Ruff e a verificação de
formatação também passaram. A demonstração executou duas perguntas e três
chamadas de ferramenta.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python app.py --demo
python -m scripts.validar_servicos
```

- [Execução da demonstração](evidencias/demo.txt).
- [Resultados das APIs reais](evidencias/apis_reais.json).
- [Testes e verificações locais](evidencias/verificacao.txt).

As cópias dos dados em `data/` tornam a demonstração reproduzível sem internet.
O script `validar_servicos` consulta as APIs reais; os resultados podem mudar
conforme o catálogo ou a disponibilidade dos serviços.

## Validação com Gemini

Esta etapa permanece pendente porque não havia uma chave de API configurada.
Os testes controlados verificam a integração e a memória, mas não avaliam a
qualidade das respostas de Gemini.

Após preencher `.env`, executar `python app.py --rastro` e realizar os pedidos:

| Pedido | Critério de aprovação |
| --- | --- |
| “Busque 2 artigos sobre aprendizado de máquina em educação desde 2020.” | Chamada de artigos com o filtro de ano; título, autoria e DOI iguais aos retornados |
| “Agora encontre 2 livros sobre o mesmo tema.” | Tema mantido e ferramenta de livros utilizada |
| “Liste somente as referências que você encontrou.” | Nenhum registro incluído sem apoio nos resultados anteriores |
| `/novo`, seguido de “Quero livros sobre o mesmo tema.” | Solicitação de esclarecimento por falta do assunto |

Registrar o modelo, a data, as chamadas realizadas e a resposta observada para
cada pedido. A conversa deve informar fontes e não alegar leitura dos textos
integrais. Esta etapa é necessária para concluir a validação prática com o LLM.

## Comparação com o processo manual

Na abordagem manual, cada serviço precisa ser consultado separadamente e os
metadados precisam ser reunidos pelo estudante. O agente centraliza as consultas
e mantém o contexto dos refinamentos. A conferência das referências e a análise
crítica dos textos continuam necessárias. Não foi medida uma economia de tempo.
