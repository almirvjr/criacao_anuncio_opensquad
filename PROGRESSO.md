# PROGRESSO

> Atualizado 2026-10-07. **Frentes:** (1) **esteira de anúncio SEM fotos** — 1º teste com a Viel 5L e 8L (seção 0); (2) **ficha técnica dos anúncios no ar** (seção 5), parada esperando 4 decisões suas; (3) **Raio-X do anúncio** e (4) **entrar em catálogo sem oferta** — prontos e em uso. O trabalho de fotos do 8L foi encerrado aqui e vai para um projeto de fotos separado (HISTORICO 07/10).

## 0. Esteira sem fotos — 1º teste: Viel 5L (`VIE-1066-PAI`) e 8L (`VIE-1067-PAI`), 3 cores cada
**Feito (07/10, branch `esteira-sem-fotos`):** travas com modo sem fotos, `validar_ficha_seo.py` (Marca/Modelo), `capas.py` (busca no Cloudinary), tradutor lê `.xls` + cubagem + preço provisório, `montar_payload.py`, instruções dos agentes reescritas, material de foto em `squads/ml-anuncios/_arquivo-fotos/`. Desenho em `docs/superpowers/specs/2026-10-07-esteira-sem-fotos-design.md`, plano em `docs/superpowers/plans/2026-10-07-esteira-sem-fotos.md`.
**Entrada pronta:** `squads/ml-anuncios/output/anuncios-entrada.json` (planilha `produtos_2026-10-07-12-07-32.xls`, preço provisório R$ 100, peso/caixa da cubagem). 6 capas no Cloudinary com etiqueta (BR/CI/PT; branca e cinza feitas no ChatGPT, conferidas).
**Parou em 07/10 no step-06 (aprovação do texto), esperando o Almir:** steps 02–05 feitos (dossiês, categoria MLB33375 Lixeiras p/ os dois — 8L decidido pelo Almir; 5L diâmetro 18 cm confirmado; briefs OK; copy OK nas travas). Perguntas abertas: (1) título da 5L e (2) da 8L (recomendado = nº 3 de cada), (3) aprovar Marca/Modelo, (4) tirar da 5L a frase com avaliação de concorrente ("linda e tamanho ideal para banheiro"); falta garantia e peso sem embalagem no cadastro. Ao retomar: gravar `titulo_final` em `output/copywriting/anuncio-{pai}.yaml` e rodar as 2 travas de novo.
⚠️ Um agente imprimiu o token do ML (lido do `.mcp.json`) no registro da sessão de 07/10 — vence sozinho em ~6h; limpar o registro é do Almir.
**PRÓXIMO PASSO:** depois do step-06, seguir steps 07→09 até a tela final; publicar só com o "sim" do Almir; ligar o `ML Publicar` (`0rzNJ7RLqLzMbKnf`) só nessa hora; conferir no ML se aceitou Marca/Modelo como enviados; perguntar se pausa até ter o preço real; vínculo no Tiny é manual.

## 4. Pendências
- Código da squad commitado em 07/10 (branch `esteira-sem-fotos`, sem push). ⚠️ Repo PÚBLICO — conferir segredo antes de qualquer push.
- **`ML Publicar`** (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito até o 1º teste. O nó `Montar Payload` aceita `pictures_compartilhadas` vazio (não precisa mexer). O webhook no `.env` **já está preenchido**.

## 5. Ficha técnica dos anúncios NO AR — `tools/auditoria_ficha/`
371 campos preenchidos em 146 anúncios (06-10/08). Nada alterou preço/fotos/estoque/variações.
**Esperando decisão do Almir:** (1) 6 anúncios com litros divergentes entre título e ficha — corrijo qual? (2) 5 travados no catálogo, só via "Sugerir correções" um a um; (3) 41 campos de vela — 1 cor por anúncio ou vazio? (4) 112 suspeitas (63 de caixa menor que o produto, mexe em frete; 49 de "Kit N" com ficha dizendo 1).
⚠️ Antes de qualquer lote: filtrar `catalog_listing=false` (catálogo responde 200 e IGNORA), rodar `validar_sugestoes.ps1`, comparar título antes/depois.
