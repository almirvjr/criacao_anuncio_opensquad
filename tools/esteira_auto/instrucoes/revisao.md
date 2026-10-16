Voce esta rodando SEM CONVERSA, chamado pelo maestro da esteira de anuncios. Ninguem vai responder pergunta: nao pergunte, decida pelo que esta escrito.

Faca SO a etapa abaixo e pare.

Etapa: squads/ml-anuncios/pipeline/steps/step-08-revisao.md (leia o arquivo e siga, junto com o agente que ele indica em squads/ml-anuncios/agents/).
Pasta deste lote: {LOTE}
Onde o step disser `squads/ml-anuncios/output/`, use a pasta do lote no lugar. Nao leia nem escreva em outra pasta de saida.
Produtos deste lote: {PAIS}

Regras:
- Nao publique nada. Nao chame o webhook, nao rode disparar_publicacao.py nem completar_anuncio.py.
- Checkpoint humano (step-04b, step-06, step-09) NAO para a esteira: deixe pendencias e divergencias registradas no brief/dossie, a tela mostra ao Almir.
- So grave arquivos dentro da pasta do lote. Programa (.py) nao se cria nem se altera.
- Se o maestro mandou motivo de reprovacao abaixo, corrija exatamente isso.
- Em cada parecer-<pai>.yaml grave tambem `para_o_almir`: lista de ATE 4 frases curtas (no maximo 70 letras cada), em portugues simples, so com o que o Almir precisa FAZER na tela antes de publicar (ex.: "Trocar a frase do pe na descricao"). Nada a fazer = lista vazia. Nao repita preco nem titulo (a tela ja cobra).

Motivo da reprovacao anterior (vazio = primeira tentativa): {MOTIVO}

Saida esperada nesta etapa: {LOTE}/revisao/parecer-<pai>.yaml de cada produto e {LOTE}/revisao/pareceres.yaml

Ao terminar, responda em uma linha: "pronto" ou "nao consegui: <motivo curto>".
