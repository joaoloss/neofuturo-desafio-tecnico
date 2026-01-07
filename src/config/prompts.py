SELECTING_USEFUL_COLS_PROMPT = """
Seu papel é identificar quais colunas descrevem diretamente o item em si (modelo, marca ou características), e não informações administrativas ou operacionais.

Retorne apenas os nomes das colunas relevantes, separados por vírgula, sem qualquer texto adicional. Jamais invente ou adicione colunas que não estejam presentes na lista fornecida. Ignore colunas como preço, quantidade, estoque, unidade etc. Considere apenas colunas que descrevem o item de forma específica, como nome do produto, marca e descrição textual.
Além disso, sempre acrescente no início da lista a coluna que representa o identificador único do item (ID, código, SKU etc.).

Colunas disponíveis: {cols}

Exemplo de item:
{item}

Responda imediatamente apenas com os nomes das colunas separados por vírgula.
"""

SELECTING_SIMILAR_ITEM_PROMPT = """
Seu papel é determinhar se um dado item é equivalente a algum outro item presente em um dado conjunto de itens. Dois itens são considerados equivalentes se descrevem o mesmo produto, mesmo que com palavras diferentes. Considere que os itens podem ter pequenas variações na descrição, mas ainda assim serem equivalentes.

Saiba que existem apenas duas possibilidades: nenhum item equivalente existe no dado conjunto, ou exatamente um item equivalente existe no dado conjunto.

Responda apenas com um número inteiro, que representa o número do item equivalente no dado conjunto. Se nenhum item equivalente existir, responda com -1. Não responda nada além do número inteiro solicitado.

Conjunto de itens:
{items}

Item a ser comparado: 
{item}

Responda imediatamente apenas com um número inteiro que deverá ser um dos seguintes: {possible_values}.
"""