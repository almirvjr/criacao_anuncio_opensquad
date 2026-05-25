# PROGRESSO

## Estado atual

Suporte a anúncios **simples E com variações de cor** implementado ponta a ponta (Fases 1-4 + v2 em 25/05 — ver HISTORICO). Spec/plano em `docs/superpowers/`. Workflow `ML Publicar` (`0rzNJ7RLqLzMbKnf`) montando `variations[]`, **INATIVO** de propósito até o teste.

1º lote real (**lixeiras Viel 5L/8L × 3 cores**) com dados ingeridos em `squads/ml-anuncios/output/anuncios-entrada.json`: marca Viel, ficha técnica (material, dimensões, capacidade — 8L já corrigido pra 8 litros), fotos no bucket `tcd-produtos`.

## Proximas tarefas

1. **Fase 5 — rodar a esteira (PRÓXIMA SESSÃO).** Pipeline nos 2 anúncios das lixeiras: Cibele (categoria + concorrentes) → Helena (scraping/enriquecimento) → **checkpoint de dados** → Renata (copy) → **checkpoint copy** → Felipe (fotos via Nano Banana 2, ~R$2-3, 1º uso real dos overlays + foto técnica) → Vinícius → **dry-run: parar antes do POST**. Depois publicar **5L e 8L em teste** com ok explícito.
2. Após cada publicação no ML, **vincular SKU→MLB manualmente** no painel Tiny (Integrações > ML PADRAO > Relacionar Anúncios).

## Notas

- 1º uso real dos templates de overlay na Fase 5 — validar render (fonte Inter no ambiente).
- Geração de imagem: OpenRouter + Nano Banana 2 (`google/gemini-3.1-flash-image-preview`); ver DECISOES.
- Info do produto vem da coluna "Descrição complementar" do Tiny; o que faltar, Helena enriquece dos concorrentes e o checkpoint `step-04b` chama o Almir.
