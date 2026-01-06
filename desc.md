# Contexto do problema

Temos catálogos de produtos provenientes de múltiplas fontes, com estruturas diferentes e dados inconsistentes.

O objetivo é identificar e agrupar produtos que são **funcionalmente equivalentes**, mesmo quando há variações na forma como são descritos.

Isso inclui, por exemplo:

- Diferenças de nomenclatura e escrita  
- Abreviações ou variações de marca  
- Informações distribuídas em campos diferentes ou ausentes  
- Descrições textuais pouco padronizadas  

Arquivos de exemplo serão fornecidos.


# Escopo da solução esperada

## Tecnologia base

- **Linguagem:** Python  
- **Framework:** FastAPI  

## Ingestão de dados

- Upload de arquivos via API  
- Suporte a arquivos **CSV** e **PDF**  
- Parse e normalização dos dados extraídos  


## Processamento

- Execução **assíncrona** do processamento  
- Persistência dos dados e resultados em banco de dados  
  - SQLite ou armazenamento em memória  
  - Não há necessidade de alta complexidade nesta etapa  
- API para consulta dos resultados  


## Principal desafio: agrupamento de produtos

- Identificar e agrupar produtos equivalentes a partir de:
  - Dados textuais
  - Dados estruturados  
- Gerar grupos de similaridade de forma **consistente** e **escalável**  
- A abordagem técnica fica totalmente a critério do candidato  


## Revisão humana e aprendizado

- Deve existir uma etapa de **revisão humana** dos agrupamentos  
- Ajustes feitos por humanos devem ser **registrados**  
- A solução deve considerar como **aprender com essas revisões** para melhorar os agrupamentos futuros  


# Avaliação

O foco da avaliação está em:

- Clareza das decisões técnicas  
- Robustez da solução  
- Forma como o sistema evolui a partir do feedback humano  

O candidato tem liberdade para definir:

- Arquitetura  
- Modelos  
- Fluxos  
- Justificativas técnicas consideradas mais adequadas ao problema  


# Entrega

O teste pode ser compartilhado por meio de um **repositório no GitHub**, contendo:

- Código-fonte  
- Instruções de execução  
- Documentação adicional que julgar relevante