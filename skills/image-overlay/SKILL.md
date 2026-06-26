---
name: image-overlay
description: >
  Aplica overlay de texto (headline, subheadline, badge, selos, CTA) sobre
  uma imagem base via HTML/CSS renderizado por Playwright. Especializado em
  marketplaces (Mercado Livre): cada um dos 10 slots da hierarquia psicológica
  StorySelling tem um template de posicionamento próprio. Depende da skill
  image-creator para o motor de renderização HTML→PNG.
description_pt-BR: >
  Aplica overlay de texto (headline, subheadline, badge, selos, CTA) sobre
  uma imagem base via HTML/CSS renderizado por Playwright. Especializado em
  marketplaces (Mercado Livre): cada um dos 10 slots da hierarquia psicológica
  StorySelling tem um template de posicionamento próprio. Depende da skill
  image-creator para o motor de renderização HTML→PNG.
type: mcp
version: "1.0.0"
mcp:
  server_name: playwright
categories: [design, automation, marketplace]
depends_on: [image-creator]
---

# Image Overlay — Texto sobreposto em fotos de anúncio ML

## When to use

Use esta skill quando precisar adicionar texto (headline, subheadline, badge, selos visuais, CTA) sobre uma imagem JÁ GERADA do produto, no contexto do pipeline de fotos da squad `ml-anuncios`.

Não é para gerar imagens do zero (isso é `image-ai-generator`) nem para padronizar dimensão/recorte (isso é `image-creator`). É especificamente o overlay de texto seguindo o método StorySelling.

## Inputs

A skill recebe 1 arquivo JSON com os seguintes campos:

```json
{
  "background_image_path": "absolute/path/to/foto-base-gerada.jpg",
  "slot": "CAPA_PURPLE_COW",
  "headline": "Seu banheiro com aparência mais moderna em segundos",
  "subheadline": "Visual sofisticado por preço acessível",
  "badge": null,
  "cta": null,
  "selos_visuais": [
    { "texto": "✔ Corpo em aço inox", "objetivo": "reduzir medo de material ruim" }
  ],
  "brand_signature": "Terra Casa Decor — O seu melhor lugar é a sua casa",
  "output_path": "absolute/path/to/foto-01.jpg"
}
```

`slot` deve ser um destes 11 valores (correspondendo a `photo-templates.md`):
`CAPA_PURPLE_COW`, `ANTES_DEPOIS`, `BADGE_TAMANHO`, `ANTI_ANSIEDADE_MATERIAL`, `CLAREZA_ABSOLUTA`, `DETALHE_TECNICO_FUNCIONAMENTO`, `DETALHE_TECNICO_DURABILIDADE`, `LIFESTYLE_USO_REAL`, `SOBRECORRECAO_ANSIEDADE`, `MACRO_YES_CTA_FINAL`, `FICHA_TECNICA_DIMENSOES`.

## Output

Imagem JPG/PNG com dimensão **exata 1200×1200 px** com texto sobreposto, salva no `output_path` indicado.

A skill EXIGE input em 1200×1200 e PRODUZ saída em 1200×1200 — esse é o padrão fixo do projeto. Se o `background_image_path` apontado vier em dimensão diferente, a skill deve falhar com erro `dimensao_invalida` (não tentar redimensionar — quem redimensiona é o Felipe antes de chamar overlay).

## Posicionamento por slot (regras de layout)

Cada slot tem regras fixas de onde o texto entra para não cobrir o produto:

| Slot | Headline | Subheadline | Badge | Selos | CTA |
|------|----------|-------------|-------|-------|-----|
| CAPA_PURPLE_COW | topo, 64px, white shadow | abaixo, 28px | — | — | — |
| ANTES_DEPOIS | centro horizontal (na divisão), 48px | abaixo, 24px | — | — | — |
| BADGE_TAMANHO | topo, 44px | abaixo, 22px | canto inferior direito, pill verde | — | — |
| ANTI_ANSIEDADE_MATERIAL | direita vertical, 40px | abaixo, 20px | — | — | — |
| CLAREZA_ABSOLUTA | topo, 44px, fundo branco semi | abaixo, 22px | canto superior direito | — | — |
| DETALHE_TECNICO_FUNCIONAMENTO | topo, 38px | — | — | — | — |
| DETALHE_TECNICO_DURABILIDADE | topo, 38px | — | — | — | — |
| LIFESTYLE_USO_REAL | inferior, 34px, fundo gradient bottom | — | — | — | — |
| SOBRECORRECAO_ANSIEDADE | topo, 44px | abaixo, 22px | canto inferior, pill | 4-6 selos ao redor do produto, cada um pill branca | — |
| MACRO_YES_CTA_FINAL | topo, 56px | abaixo, 26px | canto superior direito, pill dourada | — | inferior centralizado, 32px, fundo escuro com sombra |
| FICHA_TECNICA_DIMENSOES | topo, 40px, white shadow | — | quadro medidas: painel branco semi canto inf. direito (DIM_ALTURA / DIM_LARGURA / DIM_PROFUNDIDADE) | — | — |

Todas as configurações detalhadas estão em `references/templates/*.html` (gerar quando esta skill for usada pela primeira vez).

## Core Workflow

1. **Carregar input JSON** — ler o arquivo com background_image_path, slot, textos e output_path.

2. **Selecionar template HTML** baseado no `slot`. Os 10 templates ficam em `references/templates/{slot}.html` (gerar sob demanda na primeira execução; consultar regras de posicionamento acima).

3. **Compor HTML**:
   - Copiar template do slot.
   - Substituir placeholders: `{{BACKGROUND_IMAGE}}`, `{{HEADLINE}}`, `{{SUBHEADLINE}}`, `{{BADGE}}`, `{{CTA}}`, `{{SELOS_HTML}}`, `{{BRAND_SIGNATURE}}`.
   - `{{BACKGROUND_IMAGE}}` deve ser caminho absoluto file:// OU base64 inline.
   - Campos `null` no input viram strings vazias / sections ocultas via display:none.
   - `{{SELOS_HTML}}` é gerado iterando o array de selos, cada um virando `<div class="selo">{{texto}}</div>`.

4. **Salvar HTML** em `{output_dir}/_overlay_html/{filename}.html` (mesmo diretório do `output_path`, subpasta `_overlay_html`).

5. **Renderizar via image-creator** seguindo o workflow padrão:
   - Iniciar HTTP server local (Python `http.server`) na pasta do HTML.
   - Playwright `browser_navigate` para `http://localhost:PORT/{filename}.html`.
   - `browser_resize` para 1200×1200.
   - `browser_take_screenshot` para o `output_path`.
   - Parar HTTP server.

6. **Verificar resultado**: ler o arquivo final, conferir que dimensões batem 1200×1200 e que texto está legível.

## Identidade visual Terra Casa Decor

Todos os templates aplicam por padrão:

- **Fonte principal:** Inter, Bold para headlines e regular para body. Fallback: system-ui sans-serif.
- **Paleta:**
  - Texto sobre fundo claro: `#1a1a1a` (preto suave)
  - Texto sobre fundo escuro: `#ffffff`
  - Pill verde confirmação (selos OK): `#2d8a4a` background, `#ffffff` texto
  - Pill dourada incentivo (Macro-Yes): `#c79a3a` background, `#ffffff` texto
  - Sombra de texto para legibilidade: `text-shadow: 0 2px 8px rgba(0,0,0,0.35)` quando texto fica direto sobre foto
  - Fundo branco semi (Clareza, Sobrecorreção): `rgba(255,255,255,0.92)`, border-radius 12px, padding 16-24px

- **Tamanhos mínimos (anti-pattern de fonte pequena demais):**
  - Headline: nunca abaixo de 34px (mesmo em slots com headline pequena)
  - Subheadline: nunca abaixo de 20px
  - Selo: 18px
  - CTA: 28px
  - Brand signature: 16px

- **Margens:** todos os templates têm `padding: 48px` mínimo nas bordas para não cortar texto em thumbnails.

## Anti-patterns

### Nunca fazer
1. **Texto cobrindo o produto** — o produto é o herói; texto vai em áreas livres definidas no template.
2. **Fonte abaixo do mínimo declarado** — vira ilegível em thumbnail de busca ML.
3. **Selos sem ícone (✔, ✕, número)** — selo sem prefixo visual perde escaneabilidade.
4. **Mais de 6 selos no slot 9** — sobrecarrega; reduz a 4-6 mesmo que a Helena tenha proposto mais.
5. **Cor de pill verde em selo de limitação** — selo "✕ Não vem com balde" pede pill cinza neutra, não verde de confirmação.

### Sempre fazer
1. **Validar contraste** — texto sobre foto sem text-shadow é proibido a menos que haja fundo de pill por trás.
2. **Renderizar 1 imagem completa de teste antes de batch** — fonte pode falhar em sistemas sem Inter instalada.
3. **Preservar HTML em `_overlay_html/`** — auditoria futura precisa.

## Quality Criteria

- [ ] Output salvo no `output_path` declarado
- [ ] Dimensões 1200×1200 exatas
- [ ] Texto não corta nas bordas (padding mínimo respeitado)
- [ ] Fonte legível em thumbnail (verificável reduzindo para 300×300 mentalmente)
- [ ] Selos com ícone visual prefixado
- [ ] Brand signature presente onde o template prevê (Macro-Yes especialmente)
- [ ] HTML correspondente preservado em `_overlay_html/`

## Available operations

- **Apply overlay** — Adicionar texto sobre uma imagem usando o template do slot informado
- **Batch overlay** — Processar as 10 fotos de um SKU em sequência (reutilizando HTTP server)
- **Preview** — Gerar HTML sem renderizar PNG (para revisar antes de bater no servidor)

## Notes

- Esta skill é **dependente** da `image-creator` para o motor de renderização. Não duplique o setup do HTTP server — chame os passos da `image-creator`.
- Os templates HTML em `references/templates/` são criados lazy (na primeira invocação de cada slot). Versionar quando estabilizar.
- Para a v1, fonte Inter é carregada via Google Fonts CDN. Em v2, embedar a fonte como base64 para funcionar offline.
