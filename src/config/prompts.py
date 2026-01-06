SELECTING_USEFUL_COLS_PROMPT = """
Seu papel é identificar quais colunas descrevem diretamente o item em si (modelo, marca ou características), e não informações administrativas ou operacionais.

Retorne apenas os nomes das colunas relevantes, separados por vírgula, sem qualquer texto adicional. Jamais invente ou adicione colunas que não estejam presentes na lista fornecida. Ignore colunas como código, preço, quantidade, estoque, unidade ou identificadores técnicos. Considere apenas colunas que descrevem o item de forma específica, como nome do produto, marca e descrição textual.

Colunas disponíveis: {cols}

Exemplo de item:
{item}

Responda imediatamente apenas com os nomes das colunas separados por vírgula.
"""

COMPARING_ITEMS_PROMPT = """
Seu papel é comparar dois itens e determinar se eles descrevem o mesmo produto (mesmo modelo), mesmo que com variações leves de escrita ou descrição.

Considere equivalentes apenas itens que tenham a mesma marca e o mesmo modelo, permitindo pequenas variações como abreviações, ordem das palavras ou descrições complementares. Diferenças relevantes de especificação (como capacidade, versão ou geração) indicam que os itens NÃO são equivalentes.

Responda exclusivamente com:
S — se forem equivalentes
N — se não forem equivalentes

Item 1: {item1}
Item 2: {item2}
"""