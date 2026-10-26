Voce esta rodando SEM CONVERSA, chamado pelo maestro da esteira de anuncios. Ninguem vai responder pergunta: nao pergunte, decida pelo que esta escrito.

Faca SO a etapa abaixo e pare.

Etapa: squads/ml-anuncios/pipeline/steps/step-07-capas.md (leia o arquivo e siga, junto com o agente que ele indica em squads/ml-anuncios/agents/).
Pasta deste lote: {LOTE}
Onde o step disser `squads/ml-anuncios/output/`, use a pasta do lote no lugar. Nao leia nem escreva em outra pasta de saida.
Produtos deste lote: {PAIS}

Regras:
- Nao publique nada. Nao chame o webhook, nao rode disparar_publicacao.py nem completar_anuncio.py.
- Checkpoint humano (step-04b, step-06, step-09) NAO para a esteira: deixe pendencias e divergencias registradas no brief/dossie, a tela mostra ao Almir.
- So grave arquivos dentro da pasta do lote. Programa (.py) nao se cria nem se altera.
- Se o maestro mandou motivo de reprovacao abaixo, corrija exatamente isso.
- NESTA etapa faca SO a busca das fotos: para os SKUs das cores dos produtos do lote (estao em {LOTE}/anuncios-entrada.json, campo variacoes[].sku), rode mcp__cloudinary__search-assets com a expressao `tags="<sku1>" OR tags="<sku2>" ...` (todas as cores, com e sem a etiqueta capa-anuncio), max_results 500, with_field ["tags"], e grave a resposta INTEIRA (o JSON com a lista resources) em {LOTE}/capas/_busca.json. Nao rode capas.py (o maestro roda) e nao escolha fotos. Busca sem nenhuma foto tambem e "pronto": grave a resposta assim mesmo (foto faltando nao para a esteira).

Motivo da reprovacao anterior (vazio = primeira tentativa): {MOTIVO}

Saida esperada nesta etapa: {LOTE}/capas/_busca.json

Ao terminar, responda em uma linha: "pronto" ou "nao consegui: <motivo curto>".
