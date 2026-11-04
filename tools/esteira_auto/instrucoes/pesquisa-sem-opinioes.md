MODO SEM OPINIOES para: {SEM}
A esteira tentou 3 vezes e nao conseguiu ler as opinioes dos concorrentes no ML. Para esses produtos o Almir decidiu seguir sem elas (concorrente e opcional):
- NAO tente o caminho antigo das opinioes (2b do step) e NAO invente opiniao, citacao, linguagem do comprador nem persona tirada de opiniao.
- Se {LOTE}/inteligencia/_coleta/coleta-<pai>.json trouxe concorrentes (atributos, descricao, perguntas), use-os como o step manda. Se nao trouxe nem concorrente, apoie-se so nas fontes proprias (Olist/entrada, dossie, fotos do lote) e marque `sem_concorrente: true`. Concorrente nunca vira fato fisico do nosso produto.
- No brief: `confianca: baixa`. Dor interna, ansiedades e `linguagem_real_cliente` podem ficar vazias ou sem evidencia; evidencia ou frase do comprador so entra se o trecho existir de verdade em {LOTE}/inteligencia/_raw/ (pergunta ou descricao de concorrente, 12 letras ou mais). `only_factor`, `escada_e_dai` e `limitacoes` continuam obrigatorios (saem do produto).
- Declare a falta no brief, num campo proprio (NAO em `limitacoes`, que e ponto fraco do produto e vai para a descricao):
  `limitacoes_pesquisa: ["sem opiniões de concorrentes: o texto sai sem a linguagem real do comprador"]`
- A trava desses produtos roda com a opcao extra: `python squads/ml-anuncios/pipeline/validators/validar_brief.py {LOTE}/inteligencia/brief-<pai>.yaml --sem-fotos --sem-opinioes`

