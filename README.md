# neofuturo-desafio-tecnico

## 📝 Descrição do problema

O [desafio](./desc.md) consiste na criação de um algoritmo de agrupamento eficiente e escalável para identificar e agrupar itens equivalentes a partir de suas descrições textuais. Essas descrições podem apresentar variações, como abreviações, diferenças na ordem das informações, uso de sinônimos e pequenas inconsistências textuais, o que torna o problema não trivial.

## 💻 Stack

- **Linguagem:** [Python](https://www.python.org/)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)

## 💡 Estratégia

### Similaridade entre strings

Para comparar duas descrições textuais (strings), foram testadas duas métricas de dissimilaridade: [Jaccard](https://en.wikipedia.org/wiki/Jaccard_index) (complexidade $O(N)$, onde $N$ é o tamanho da união) e a [distância de Levenshtein](https://pt.wikipedia.org/wiki/Dist%C3%A2ncia_Levenshtein) (complexidade $O(N \times M)$, onde $N$ e $M$ são os comprimentos das duas strings comparadas). Também foi avaliada uma ponderação entre essas métricas. Os testes, resultados e visualizações podem ser consultados no [notebook de testes](./tests.ipynb).

Os resultados mostraram-se bastante satisfatórios, especialmente quando se utiliza a combinação ponderada das duas métricas.

**Nota**: como forma de normalização, optou-se pelo uso de uma [ferramenta de stemming](https://www.nltk.org/_modules/nltk/stem/rslp.html) antes do cálculo das métricas.

**Nota**: os pesos utilizados na ponderação entre as métricas, assim como os *thresholds*, foram definidos empiricamente.

#### Quando a métrica não é suficiente

Existem situações em que as métricas de similaridade textual, por si só, não são suficientes para tomar uma decisão confiável de agrupamento. Isso pode ocorrer, por exemplo, quando diferentes itens compartilham termos semelhantes, mas representam conceitos distintos, ou quando descrições semanticamente equivalentes apresentam baixa similaridade.

Nesses casos, o sistema recorre a um modelo de linguagem para apoiar a decisão. Dado um item e um conjunto de itens candidatos (composto pelos mais similares), o modelo é utilizado para avaliar se o item deve ser associado a um grupo existente ou se a criação de um novo grupo é mais apropriada. Essa abordagem permite capturar relações semânticas mais sutis que não são plenamente refletidas pelas métricas de similaridade baseadas em string.

Dessa forma, o modelo de linguagem atua como uma etapa complementar ao algoritmo de agrupamento, sendo acionado apenas quando as métricas tradicionais não atingem um nível de confiança suficiente. Essa estratégia equilibra precisão e eficiência, reduzindo o número de chamadas ao modelo e mantendo o sistema escalável.

O [notebook de testes](./tests.ipynb) mostra que mesmo um modelo pequeno, barato e com *reasoning* minimizado foi extremamente preciso.

### Escolha e persistência de colunas relevantes

Considerando que a entrada do sistema é um arquivo estruturado (representando um catálogo de itens) contendo uma tabela, surge um segundo desafio: identificar quais colunas são relevantes para descrever os itens. Para abordar esse problema, optou-se pela utilização de um modelo de linguagem. Como a tarefa é relativamente simples, foi escolhido um modelo pequeno e rápido; além disso, o nível de *reasoning* foi minimizado, reduzindo latência e custo.

Conforme evidenciado no [notebook](./tests.ipynb), o modelo de linguagem apresentou (novamente) um ótimo desempenho.

Adicionalmente, para evitar chamadas redundantes ao modelo, foi criado um conjunto de *hashes* a partir das colunas, de modo que documentos com as mesmas colunas (mesmo que em ordens diferentes) não gerem múltiplas chamadas ao modelo.

### Feedback e alteração humana

Um endpoint dedicado foi projetado para permitir intervenção humana no processo de agrupamento, possibilitando a correção manual de decisões tomadas automaticamente pelo algoritmo. A principal motivação é reconhecer que, apesar da eficácia das métricas de similaridade e do uso pontual de modelos de linguagem, casos ambíguos ou específicos do domínio podem exigir validação humana.

Por meio do endpoint, é possível mover manualmente um item de um grupo para outro, ou ainda forçar a criação de um novo grupo. Opcionalmente, o usuário pode fornecer uma lista de *keywords* relevantes, que passam a caracterizar o grupo de destino. Essas palavras-chave são utilizadas como sinais adicionais em análises futuras, ajudando a reforçar a identidade semântica do grupo.

Após a realocação do item, o sistema executa uma etapa de verificação para identificar itens potencialmente mal posicionados. Essa verificação analisa os itens do grupo de origem em relação ao grupo de destino, buscando casos em que outros itens possam ter sido afetados pela correção manual e também devam ser reconsiderados. Os itens considerados suspeitos são retornados na resposta do endpoint.

Dessa forma, o endpoint não apenas permite a correção pontual de um erro, mas também promove um ciclo de feedback humano no processo de agrupamento, auxiliando na identificação de inconsistências e contribuindo para a melhoria contínua da qualidade dos grupos ao longo do tempo.

## 📂 Estrutura do projeto

- **Arquivos na raiz**
  - `README.md`: documentação principal do projeto, contendo a descrição do problema, abordagem adotada e instruções de uso.
  - `desc.md`: descrição detalhada do desafio proposto.
  - `pyproject.toml`, `.python-version` e `uv.lock`: arquivos de configuração do ambiente e dependências.
  - `tests.ipynb`: notebook contendo experimentos e resultados a partir dos quais decisões técnicas foram tomadas.
  - `dump/`: diretório utilizado para persistir o estado dos agrupamentos para inspeção após encerrar a API.
  - `exemplos/`: arquivos CSV de exemplo, representando catálogos de diferentes fornecedores.

- **src/**
  - `main.py`: ponto de entrada da aplicação e definição dos endpoints da API.
  - `state.py`: definição do estado global da aplicação, responsável por armazenar grupos, itens, caches e mecanismos de sincronização.
  - `config/`: configurações gerais da aplicação, incluindo *settings*, *logging* e *prompts* utilizados pelo modelo de linguagem.
  - `domain/`: definição das entidades centrais do domínio.
  - `llm/`: abstração e integração com o modelo de linguagem utilizado para decisões semânticas.
  - `service/`: serviços que encapsulam a lógica de aplicação, como criação de itens a partir de CSVs, agrupamento automático e identificação de itens suspeitos.

## 👨🏻‍💻 Como usar

1. Clone o repositório
```bash
git clone https://github.com/joaoloss/neofuturo-desafio-tecnico.git
cd neofuturo-desafio-tecnico
```

2. Crie um `.env`
```
OPENAI_API_KEY=<sua-chave-api>
LLM_MODEL_NAME=<gpt-5-nano-2025-08-07 ou outro modelo>
```

3. Inicialize o ambiente com [uv](https://docs.astral.sh/uv/)
```bash
uv sync
```

4. Execução do Programa
```bash
uv run fastapi run ./src/main.py
```

## 🧩 Melhorias e limitações reconhecidas

Como o algoritmo é apenas um protótipo, é importante pontuar limitações/melhorias reconhecidas:

1. Tratativa de erros.
2. Suporte para mais tipos de arquivo.
3. Armazenamento em memória: para simplificar o desenvolvimento e acelerar testes, optou-se por não utilizar um SGBD. Todo o estado da aplicação é mantido em memória e, portanto, é perdido após o encerramento do programa. Uma evolução natural seria a persistência dos dados em um banco de dados.
4. Atualmente, a criação de *keywords* associadas aos grupos ocorre apenas após intervenção manual humana. É possível evoluir esse mecanismo para uma abordagem mais dinâmica, em que as *keywords* sejam automaticamente inferidas a partir dos termos mais frequentes ou mais representativos dos itens de cada grupo.
5. Estratégias de encurtamento de descrições (removendo palavras irrelevantes ou pouco significativas) podem se mostrar essencias pensando em escalabilidade.
6. Os pesos das métricas de similaridade e os *thresholds* foram definidos empiricamente. Uma possível melhoria seria automatizar esse processo por meio de validação com dados rotulados, otimização de hiperparâmetros ou técnicas adaptativas que ajustem esses valores ao longo do tempo.