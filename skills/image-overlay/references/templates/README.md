# Templates de overlay — squad ml-anuncios

10 templates HTML, um por slot da hierarquia StorySelling (ver `photo-templates.md`).
Gerados a partir da especificação em `../../SKILL.md` (tabela "Posicionamento por slot"
e seção "Identidade visual Terra Casa Decor"). Versionados em 2026-05-25 — antes disso
a skill os geraria sob demanda na primeira invocação.

## Como a skill usa estes arquivos

1. Seleciona `{SLOT}.html` pelo campo `slot` do JSON de input.
2. Substitui os placeholders por texto do input.
3. Salva o HTML composto em `_overlay_html/` ao lado do `output_path`.
4. Renderiza via `image-creator` (Playwright) em PNG 1200×1200.

## Placeholders

| Placeholder | Conteúdo | Slots que usam |
|---|---|---|
| `{{BACKGROUND_IMAGE}}` | caminho `file://` absoluto ou base64 da foto base | todos |
| `{{HEADLINE}}` | título principal | todos |
| `{{SUBHEADLINE}}` | subtítulo | todos menos os 2 DETALHE_TECNICO e LIFESTYLE |
| `{{BADGE}}` | texto da pill (verde/dourada) | BADGE_TAMANHO, CLAREZA_ABSOLUTA, SOBRECORRECAO_ANSIEDADE, MACRO_YES_CTA_FINAL |
| `{{CTA}}` | chamada para ação | MACRO_YES_CTA_FINAL |
| `{{SELOS_HTML}}` | sequência de `<div class="selo">…</div>` (4-6) | SOBRECORRECAO_ANSIEDADE |
| `{{BRAND_SIGNATURE}}` | assinatura "Terra Casa Decor — …" | todos (proeminente no Macro-Yes) |

## Robustez a campos vazios

Cada template tem `.classe:empty { display:none }` nos elementos opcionais. Se o caller
substituir um placeholder ausente por string vazia, o elemento simplesmente desaparece —
sem pill vazia, sem CTA fantasma. Campos `null` no input devem virar `""` na substituição.

## Padrão fixo

- Canvas **1200×1200 px exatos** (input e output). Dimensão diferente = falha `dimensao_invalida`.
- Fonte **Inter** via Google Fonts CDN (v1). Em v2, embedar base64 para render offline.
- Paleta e tamanhos mínimos conforme `SKILL.md` (headline ≥34px, sub ≥20px, selo 18px, CTA 28px, brand 16px).
- `padding: 48px` mínimo nas bordas em todos os slots.

## Pendência conhecida

Ainda não renderizados de ponta a ponta com o `image-creator` (validação prevista no
teste E2E da lixeira inox 12L). A nota da SKILL.md vale: **renderizar 1 imagem de teste
antes de batch** — a fonte Inter pode não estar instalada no ambiente de render.
