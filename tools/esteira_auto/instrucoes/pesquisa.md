Voce esta rodando SEM CONVERSA, chamado pelo maestro da esteira de anuncios. Ninguem vai responder pergunta: nao pergunte, decida pelo que esta escrito.

Faca SO a etapa abaixo e pare.

Etapa: squads/ml-anuncios/pipeline/steps/step-04-inteligencia-conversao.md (leia o arquivo e siga, junto com o agente que ele indica em squads/ml-anuncios/agents/).
Pasta deste lote: {LOTE}
Onde o step disser `squads/ml-anuncios/output/`, use a pasta do lote no lugar. Nao leia nem escreva em outra pasta de saida.
Produtos deste lote: {PAIS}

Regras:
- DECISOES DO ALMIR (hub): o campo `decisoes_almir` de cada anuncio em {LOTE}/anuncios-entrada.json (campo + valor; `sku` vazio = vale para a familia toda) ja foi decidido por ele e vale sobre qualquer fonte (dossie, catalogo, concorrente, opiniao). Use o valor, nao registre como pendencia, divergencia ou pergunta. Fonte que discorda: ignore.
- Nao publique nada. Nao chame o webhook, nao rode disparar_publicacao.py nem completar_anuncio.py.
- Checkpoint humano (step-04b, step-06, step-09) NAO para a esteira: deixe pendencias e divergencias registradas no brief/dossie, a tela mostra ao Almir.
- So grave arquivos dentro da pasta do lote. Programa (.py) nao se cria nem se altera.
- Se o maestro mandou motivo de reprovacao abaixo, corrija exatamente isso.

Motivo da reprovacao anterior (vazio = primeira tentativa): {MOTIVO}

Saida esperada nesta etapa: {LOTE}/inteligencia/brief-<pai>.yaml de cada produto e {LOTE}/inteligencia/briefs.yaml

Ao terminar, responda em uma linha: "pronto" ou "nao consegui: <motivo curto>".
