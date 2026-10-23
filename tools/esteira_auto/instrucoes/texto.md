Voce esta rodando SEM CONVERSA, chamado pelo maestro da esteira de anuncios. Ninguem vai responder pergunta: nao pergunte, decida pelo que esta escrito.

Faca SO a etapa abaixo e pare.

Etapa: squads/ml-anuncios/pipeline/steps/step-05-copywriting.md (leia o arquivo e siga, junto com o agente que ele indica em squads/ml-anuncios/agents/).
Pasta deste lote: {LOTE}
Onde o step disser `squads/ml-anuncios/output/`, use a pasta do lote no lugar. Nao leia nem escreva em outra pasta de saida.
Produtos deste lote: {PAIS}

Regras:
- DECISOES DO ALMIR (hub): o campo `decisoes_almir` de cada anuncio em {LOTE}/anuncios-entrada.json (campo + valor; `sku` vazio = vale para a familia toda) ja foi decidido por ele e vale sobre qualquer fonte (dossie, catalogo, concorrente, opiniao). Use o valor, nao registre como pendencia, divergencia ou pergunta. Fonte que discorda: ignore.
- Nao publique nada. Nao chame o webhook, nao rode disparar_publicacao.py nem completar_anuncio.py.
- Checkpoint humano (step-04b, step-06, step-09) NAO para a esteira: deixe pendencias e divergencias registradas no brief/dossie, a tela mostra ao Almir.
- So grave arquivos dentro da pasta do lote. Programa (.py) nao se cria nem se altera.
- Se o maestro mandou motivo de reprovacao abaixo, corrija exatamente isso.
- FICHA TECNICA (regra do Almir, 16/10/2026): a lista de campos que o comprador ve esta em {LOTE}/categorizacao/campos-<pai>.json. TODO campo dessa lista tem um destino em `attributes`: (a) o valor real (de preferencia um dos `values` da lista); (b) exatamente "não se aplica" quando o campo nao faz sentido para este produto (ex.: diametro em peca quadrada, comprimento/largura em peca redonda que ja tem diametro, nome do desenho em peca lisa); (c) deixar fora de `attributes` SO quando o campo faz sentido mas nenhuma fonte trouxe o dado — e entao listar o id em `campos_pendentes` (lista no anuncio-<pai>.yaml), para o Almir decidir na tela. Proibido valor de enchimento ("N/A", "-", "nenhum", "nao informado"). Sim/Nao e resposta valida para campo de sim ou nao (ex.: Com pe = Nao). Confira com: python squads/ml-anuncios/pipeline/validators/validar_ficha_nsa.py {LOTE}/copywriting/anuncio-<pai>.yaml {LOTE}/categorizacao/campos-<pai>.json
- As 3 conferencias do texto (validar_claims, validar_ficha_seo, validar_ficha_nsa) e a dos titulos longos o maestro roda logo depois desta etapa e devolve o motivo se reprovar. Se o comando for barrado aqui, siga sem escrever aviso disso no anuncio.
- Anuncio com `status_copy: devolvido` no {LOTE}/copywriting/anuncio-<pai>.yaml: leia `nota_almir`, reescreva atendendo a nota e grave `status_copy: pendente` (mantenha `nota_almir` e `devolvido_em`). Anuncio `aprovado` ou `tirado`: nao mexa.

Motivo da reprovacao anterior (vazio = primeira tentativa): {MOTIVO}

Saida esperada nesta etapa: {LOTE}/copywriting/anuncio-<pai>.yaml de cada produto e {LOTE}/copywriting/anuncios.yaml

Ao terminar, responda em uma linha: "pronto" ou "nao consegui: <motivo curto>".
