---
name: image-overlay
description: >
  Applies the StorySelling text overlay (eyebrow, headline, subheadline, badge, selos,
  CTA, technical dimensions) on top of an already-generated 1200x1200 product photo.
  Deterministic Python/Pillow renderer -- no browser, no HTML. Three layout archetypes
  (faixa clara, scrim, plate) chosen by photo slot. Also hosts the companion product-photo
  tooling used by the ml-anuncios pipeline: BiRefNet cutout, product lock/composition,
  framing gate and stainless-color gate.
description_pt-BR: >
  Aplica o overlay de texto StorySelling (eyebrow, headline, subheadline, badge, selos,
  CTA, cotas tecnicas) sobre uma foto de produto ja gerada em 1200x1200. Render
  deterministico em Python/Pillow -- sem navegador, sem HTML. Tres arquetipos de layout
  (faixa clara, scrim, plate) escolhidos por slot da foto. Tambem abriga as ferramentas
  vizinhas de foto de produto usadas no pipeline ml-anuncios: recorte BiRefNet, trava e
  composicao do produto, gate de enquadramento e gate de cor do inox.
type: script
version: "2.0.0"
script:
  path: scripts/render_faixa.py
  runtime: python3
  invoke: "python3 {skill_path}/scripts/render_faixa.py --config \"{config}\""
categories: [design, automation, marketplace]
---

# Image Overlay — Texto sobreposto em fotos de anúncio ML

## When to use

Use quando precisar aplicar texto (eyebrow, headline, subheadline, badge, selos, CTA, cotas de medida) sobre uma imagem JÁ GERADA do produto, no pipeline de fotos da squad `ml-anuncios`.

Não é para gerar imagem do zero (isso é `image-ai-generator`). **A ambientalizada (capa da cor) nunca leva overlay** — ela é onde o comprador compara cor, e texto atrapalha a comparação.

## O motor

`scripts/render_faixa.py` — render **determinístico em Python/Pillow**, fonte Montserrat variável (`assets/fonts/Montserrat.ttf`), saída **1200×1200 exata**.

**Não use navegador para overlay.** O render por browser (chrome-devtools/Playwright) foi abandonado em 06/2026: no Windows o `dpr` fica 0,5 e a janela varia, cortando a imagem. Pillow dá o mesmo resultado toda vez. A skill `image-creator` (HTML→PNG via Playwright) continua existindo para outros usos, mas **não participa mais do overlay** — não monte HTML, não suba `http.server`, não tire screenshot.

## Como chamar

```
python skills/image-overlay/scripts/render_faixa.py --config caminho/overlay-NN.json
```

Um único argumento: `--config`, apontando para um JSON. O script imprime `OK <output> (1200, 1200)` no sucesso. O config de cada foto fica versionado em `output/fotos/{pai_sku}/prompts/overlay-{NN}.json` (auditoria).

## Os 3 arquétipos (chave `layout`)

| `layout` | O que é | Slots |
|---|---|---|
| *ausente* (default) | **Faixa clara** — painel sólido de texto no rodapé, legibilidade máxima | 3, 6, 9 e os slim |
| `"scrim"` | Sombra suave em degradê sobre a foto, texto respirando | 5, 7, 8, 10 |
| `"plate"` | Texto em **espaço negativo limpo** da própria cena — sem faixa e sem sombra | quando a cena já tem área vazia boa |

O slot 6 (Clareza) precisa declarar a limitação de forma inequívoca — **painel vence sombra** nisso, por isso faixa. O slot 5 é respiro emocional e pede pouco texto, por isso scrim.

**Foto técnica** não é um `layout`: é a chave `dim_altura` presente no config (só no arquétipo faixa). Ela liga as setas de cota + selo de litragem por cima do produto.

## Contrato do config

Chaves lidas de fato pelo `render_faixa.py` (extraídas do próprio script — não invente chave nova, ela é silenciosamente ignorada):

| Grupo | Chaves |
|---|---|
| **Obrigatórias** | `base` (foto de entrada), `output` (arquivo final) |
| Texto | `eyebrow`, `headline_ink`, `headline_accent`, `sub`, `selos[]`, `badge`, `cta`, `liters` |
| Layout / ajuste | `layout`, `band_h`, `scrim_h`, `scrim_alpha`, `halo`, `autofit`, `text_x`, `text_y`, `text_maxw`, `headline_size`, `sub_size` |
| Cores | `ink_color`, `accent_color`, `sub_color` |
| Foto técnica | `dim_altura` (liga o modo), `dim_largura`, `dim_profundidade` (opcional), `dim_style`, `dim_extension`, `dim_dashed`, `dim_label_box` |
| Marca — **gate desligado, ver abaixo** | `show_brand`, `brand`, `brand_logo`, `brand_logo_h`, `logo`, `logo_align`, `slogan` |
| Escape | `no_qa` (pula o gate de enquadramento) |

A headline é dividida em duas partes de cor: `headline_ink` (tinta normal) + `headline_accent` (destaque). `dim_style` aceita `"modelo"` (default), `"cotas"` e `"finas"`.

**Cotas (modo técnico):** altura sai à esquerda do produto, largura na base e **profundidade como diagonal de recuo à direita** (só desenha se `dim_profundidade` vier preenchida — produto redondo manda vazio e ela some). O produto precisa de folga: ~80px à esquerda e ~110px abaixo. Sem essa folga a cota é desenhada fora do quadro e some — o renderer **avisa no log** (`[dim] AVISO: ...`) em vez de falhar calado, mas quem reenquadra é quem gerou a base.

## SEM MARCA — regra definitiva do projeto

**Nenhuma foto leva logo, slogan ou assinatura** (Almir, 19/06, DEFINITIVA): a marca não aparece em foto, título nem descrição, para não prender o anúncio a um eventual rebrand. Também não se apoiar nas cores da marca.

Na prática: o `show_brand` nasce **desligado** e **não se passa** `logo`, `slogan`, `logo_align`, `brand` nem `brand_signature` no config. As chaves continuam no script como gate, não como opção de uso.

O **tom** acolhedor ("casa", "lar", "dia a dia") permanece — isso é estilo de escrita, não citação de marca.

## Gates embutidos

- **`framing_gate`** (só no arquétipo faixa — é a faixa que corta o produto): se o produto invade o degradê da faixa, a imagem vai para `_rejeitado/` ao lado do output e o script sai com **código 3**. Pular só com `no_qa`. Nos arquétipos `scrim` e `plate` não há esse gate.
- **`autofit`**: quando ligado, reenquadra antes de checar e informa o motivo no log.
- **`cutout` (BiRefNet)**: a máscara/bbox do produto vem de `rembg` + `onnxruntime`, offline e sem custo. Sem essas bibliotecas, cai para a heurística antiga do pixel-de-canto (qualidade menor, mas funciona). `CUTOUT_DISABLE=1` força o fallback.
- **`inox_cast`** (chamado antes do overlay, pelo Felipe): reprova foto de inox que puxou dourado — **código 2**. Não corrigir em pós; regenerar.

## Scripts vizinhos (mesma pasta)

`cutout.py` (máscara/bbox) · `lock_product.py` (PNG travado + sha256 da arquitetura produto-travado) · `compose.py`, `compose_two.py`, `compose_scale.py` (colagem do produto travado sobre a cena) · `fit_product.py`, `fit_scale.py` (escala/encaixe) · `framing_gate.py` · `inox_cast.py`.

## Anti-patterns

1. **Texto cobrindo o produto** — o produto é o herói; é para isso que existem os 3 arquétipos.
2. **Selo sem ícone** (✔, ✕, número) — perde escaneabilidade na miniatura.
3. **Mais de 6 selos no slot 9** — sobrecarrega; ficar em 4-6 mesmo que a Helena tenha proposto mais.
4. **Pill verde em selo de limitação** — "✕ Não vem com balde" pede neutro, não o verde de confirmação.
5. **Marca em qualquer forma** — ver a seção SEM MARCA.
6. **Montar HTML / abrir navegador para overlay** — motor aposentado.

## Quality Criteria

- [ ] Saída no `output` declarado, **1200×1200 exatos** (nem maior nem menor — os dois são veto)
- [ ] `framing_gate` retornou OK (e não foi pulado com `no_qa`)
- [ ] Texto não corta nas bordas
- [ ] Legível na miniatura (reduzir mentalmente a 300×300)
- [ ] Selos com ícone prefixado
- [ ] **Zero marca**: sem logo, slogan ou assinatura
- [ ] Config salvo em `prompts/overlay-{NN}.json`

## Legado

`references/templates/*.html` e o `README.md` de lá são do motor por navegador (até 05/2026). **Não são lidos pelo `render_faixa.py`.** Ficam como registro do posicionamento por slot da época; a versão anterior deste manual está em `SKILL.md.snapshot-2026-07-22`.
