# PROGRESSO

## Estado atual — Fase 5 (fotos): CAPAS FECHADAS, faltam as StorySelling

**Run ID:** `2026-05-26-091553` — `squads/ml-anuncios/output/2026-05-26-091553/`
**Lote:** lixeiras Viel 5L (VIE_1066-PAI, R$150) e 8L (VIE_1067-PAI, R$200), 3 cores cada (Branco/Preto/Cinza), modo `variacoes`.

### Steps concluídos
| Step | Agente | Status |
|---|---|---|
| 02 Curadoria (Caio) | `curadoria/dossies.json` | ✅ (dims do dossiê estavam erradas — corrigidas: 5L 18×25, 8L 18×34) |
| 03 Categorização (Cibele) | MLB33375; COLOR defines_picture; cores casadas | ✅ |
| 04 Inteligência (Helena) | `inteligencia/briefs.yaml` | ✅ confiança media |
| 04b/06 Checkpoints | dados + copy | ✅ aprovados |
| 05 Copy (Renata) | `copywriting/anuncios.yaml` | ✅ aprovada |
| 07 Fotos — CAPAS (Felipe) | 6 capas em `_final/` | ✅ **aprovadas 15/06** |

### Títulos finais (Checkpoint A)
- **5L:** `Lixeira Inox 5L Pedal Tampa Banheiro Cozinha Escritório`
- **8L:** `Lixeira Inox 8L Pedal Tampa Cozinha Banheiro Sofisticada`

### Capas (6/6 finais) — `fotos/VIE_1066-PAI/_final/capa-5L-*.jpg` e `VIE_1067-PAI/_final/capa-8L-*.jpg`
Receita completa codificada em `_memory/memories.md` (ambientalizada sem texto, ângulo 3/4, cores quentes, fórmula do gabinete cortado, props coerentes, dims reais, fidelidade). Bases reais por cor em `tcd-produtos`. Ver DECISOES 2026-06-15 e HISTORICO.

## Próximas tarefas (retomar daqui)
1. **Redesenhar o overlay das 9 fotos StorySelling** (observação 5 do Almir: tipografia/cor/distribuição). Texto vive SÓ aqui (capa é limpa); neutro de cor. Ler templates `skills/image-overlay/references/templates/` + `pipeline/data/storyselling-framework.md` e propor layout ANTES de gerar.
2. Gerar as 9 StorySelling + foto técnica. Montar `picture_ids` por variação = 1 capa + 9 StorySelling = 10. Subir capas ao bucket `tcd-produtos` (precisa SERVICE_ROLE).
3. Step-08 Vinícius (revisão) → Step-09 Checkpoint B (dry-run, parar antes do POST) → Step-10 publicar 5L e 8L com OK explícito.
4. Após publicar: vincular SKU→MLB manualmente no Tiny (Integrações > ML PADRAO > Relacionar Anúncios).

## Pendências (do Almir)
- **SUPABASE_SERVICE_ROLE** (`sb_secret_...`): não persistida em disco. Re-fornecer ao retomar: `! $env:SUPABASE_SERVICE_ROLE='<chave>'`.
- **Publicação (step-10):** `N8N_WEBHOOK_ML_PUBLICAR` ausente do `.env` e workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito. Resolver antes do POST.

## Notas técnicas de geração de fotos
- `generate.py` devolve 1024×1024 (às vezes JPEG com ext .png) → **normalizar pra 1200×1200** pós-geração (PIL LANCZOS). Wrapper já corrigido (referência = produto exato).
- Overlay renderiza via MCP **chrome-devtools** (não playwright); screenshot 1200×1200 só com `emulate viewport 1200x1200x1`. Fonte Inter (Google Fonts CDN) ok.
