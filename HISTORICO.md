# HISTORICO

<!-- Tarefas concluidas (arquivo morto). Formato: data - resumo. -->

## 2026-05-16 - Sessao: setup infra + revisao spec do workflow ML Publicar

### Infraestrutura criada
- Schema `ml_tools` + tabela `ml_tools.publicacoes` no Supabase (log de publicacoes ML; sem RLS, decisao consciente em DECISOES.md).
- Bucket publico `tcd-produtos` no Supabase Storage (Felipe Fotos vai salvar fotos aqui; ML baixa via URL).
- Workflow n8n "ML Publicar" criado (ID `0rzNJ7RLqLzMbKnf`), 13 nos, validado sem erros, inativo no n8n.
- Variavel `N8N_WEBHOOK_ML_PUBLICAR` adicionada ao `.env`.
- Variavel `OPENROUTER_API_KEY` adicionada ao `.env` (chave correta `sk-or-v1-...`).
- Credencial `openrouter_cloudfy` do n8n corrigida (antes estava com chave Supabase por engano).

### Skills verificadas
- `image-fetcher` (hybrid, MCP playwright): OK.
- `image-creator` (mcp, playwright): OK.
- `image-ai-generator` (script Python, env `OPENROUTER_API_KEY`): OK (chave configurada).

### Revisao da spec - ponto 1 (description plain_text)
- Confirmado via doc ML: `description.plain_text` e estrito - sem HTML, sem emojis, sem `<` `>`, quebra so com `\n`.
- Workflow n8n nó "Montar Payload" agora sanitiza defensivamente (regex remove HTML/markdown/emojis/`< >`, normaliza `\r\n` -> `\n`).
- Agente Renata atualizado: novo principio (#4), 4 novos anti-patterns, 2 novos quality criteria.
- `quality-criteria.md` e `anti-patterns.md` da squad atualizados com regras plain text.

### Revisao da spec - ponto 2 (shipping ME2 + fluxo Tiny)
- Verificado via API ML: conta TERRACASADECOR e Platinum 5_green (34k+ vendas), usa ME2 com `logistic_type: "fulfillment"`. Workflow estava com config correta.
- Esclarecido fluxo Tiny: integracao ML-Tiny NAO importa anuncios sozinha; Almir varre manualmente o painel Tiny hoje. O no "POST Tiny" do workflow SUBSTITUI essa varredura manual.
- Decisao: `available_quantity: 1` fixo no payload ML (Tiny corrige depois com estoque real do ERP).
- Workflow nó "POST Tiny" atualizado: `conta: "ML PADRAO"` (era "Mercado Livre" - errado).
- Agente Paula atualizado: payload sem `available_quantity`, fotos via URLs Supabase Storage (nao mais paths locais), novos anti-patterns, timeout 60s.

### Outros
- Tabela `ml_tools.publicacoes` criada sem RLS - decisao consciente (uso interno, service_role only).

## 2026-05-17 - Sessao: validacao do MCP Tiny + dry-run do workflow ML Publicar

### MCP olist-docs adicionado
- Novo MCP `olist-docs` (HTTP, https://api-docs.erp.olist.com/mcp) adicionado ao `.mcp.json`. E **MCP de documentacao** (Mintlify), nao executor. Expoe 2 tools: `search_olist_erp_api_v3` e `query_docs_filesystem_olist_erp_api_v3` (shell read-only com rg/grep/cat/jq no filesystem virtual da doc). Carrega apos reiniciar Claude Code.

### Mapeamento da API v3 Tiny
- Baixado swagger.json (~1MB) de `erp.tiny.com.br/public-api/v3/swagger/swagger.json`.
- Total: 177 endpoints em 26 areas. Distribuicao: GET 72, POST 50, PUT 37, DELETE 18.
- **Achado critico:** API v3 NAO tem endpoint para mapear anuncio Tiny↔MLB. Busca por "anuncio/marketplace/mlb/mercado/mapeamento" retorna ZERO em paths, summaries e schemas. API v2 documentada tambem nao tem endpoint publico para isso (`incluir-mapeamento-anuncio.php` e folclore de forum, sem doc oficial).
- Confirmado via doc oficial e fontes terceiras (Arcos Scale, Marketfacil, suporte Olist): integracao nativa Tiny↔ML **nao cria anuncios novos** nem detecta MLBs criados via API externa. So gerencia anuncios ja existentes.
- Memoria criada: `reference_olist_tiny_api_v3.md` com mapa completo (evita re-baixar swagger em sessoes futuras).

### Workflow ML Publicar ajustado
- **No `POST Tiny` removido.** Revoga decisao anterior (DECISOES.md 2026-05-16) - endpoint que ela assumia nao existe.
- `Publicacao OK?` (branch true) agora liga direto em `Log Sucesso`.
- `Log Sucesso` simplificado: status='success' fixo (so roda no branch ML 201).
- `Respond Sucesso` agora retorna `tiny_sync: { status: "manual_pending", instrucao: "vincular SKU ao MLB no painel Tiny: Integracoes > ML PADRAO > Relacionar Anuncios" }`.
- Workflow agora tem 12 nos (era 13), validacao OK 0 erros.

### Montar Payload reforcado (pontos 4 e 5 da spec)
- Ponto 5: injeta `{ id: 'SELLER_SKU', value_name: sku }` em `attributes` se nao vier (padrao ML moderno, complementa `seller_custom_field` legado).
- Ponto 4: `listing_type_id` validado contra `['gold_special','gold_pro']` com fallback `gold_special` (antes era `||` cego que aceitaria qualquer string).

### Bug estrutural corrigido em Buscar Publicacao Existente
- Query antiga `SELECT mlb_id ... LIMIT 1` retornava 0 linhas quando SKU era novo. n8n descarta downstream nesses casos -> toda primeira publicacao morria silenciosamente.
- Trocado por `SELECT COALESCE((subquery), '') AS mlb_id` que sempre retorna 1 linha (string vazia se SKU novo, MLB-id se existente). IF `notEmpty` continua roteando certo.

### Dry-run parcial executado com sucesso
- 6 nos pos-`Montar Payload` desabilitados temporariamente para zero-risco (evita criar anuncio real no ML).
- Webhook-test acionado via curl com payload dummy (SKU `TEST-DRY-RUN-001`).
- Execution 118607: webhook -> Buscar Publicacao -> Ja Publicado? (false, mlb_id='') -> Buscar Token -> Montar Payload. Payload final validado: SELLER_SKU injetado, listing_type validado, description sanitizada, pictures shape correto, shipping ME2 default.
- 6 nos reabilitados ao final; workflow no mesmo estado funcional de antes (mais correto).

### Memoria
- `reference_olist_tiny_api_v3.md` criada (mapa API v3 + status do MCP olist-docs).
- Plugin `github@claude-plugins-official` desabilitado (conta GitHub gratuita do Almir nao tem Copilot ativo; plugin nao essencial para o projeto).

## 2026-05-17 - Sessao: producao de fotos - integracao do metodo StorySelling (GPT Himmel) na squad

### Conceito absorvido
- Estudado em detalhe a execucao completa do GPT externo "Cientific Selling: O anuncio bionico da Himmel" sobre lixeira inox 12L.
- Metodo destilado: transforma reviews+FAQ de concorrentes ML em diagnostico psicologico (dor interna, only factor, ansiedades) e gera prompts JSON cinematograficos onde cada foto quebra uma objecao especifica. Usa codigos MECLABS (-a-f, +i+v) e image-to-image preservando produto real.
- Outro GPT publico ("Gerador de Titulos ML") absorvido em parte: 3-5 titulos com scoring + inputs estruturados canonicos.

### Frameworks de referencia criados (pipeline/data/)
- `storyselling-framework.md` — equacao MECLABS (C = 4m + 3v + 2(i-f) - 2a), codigos psicologicos (`+m`, `-a-f`, etc), escada "E Dai?", StoryBrand adaptado, ONLY FACTOR, hierarquia das 10 fotos.
- `objection-patterns.md` — catalogo de 10 familias de objecao tipicas de casa/decoracao (F1-F10) com gatilhos nos reviews/FAQ, slot de foto recomendado e template de headline.
- `photo-templates.md` — 10 templates JSON parametrizados (CAPA_PURPLE_COW -> MACRO_YES_CTA_FINAL) com placeholders `{{...}}` que Felipe substitui.

### Novo agente Helena Estrategista
- `agents/helena-estrategista.agent.md` criado (icone 🎯).
- `pipeline/steps/step-04-inteligencia-conversao.md` criado: faz scraping via Playwright dos 3 permalinks de concorrentes_top que Cibele coleta, gera diagnostico + briefing das 10 fotos por SKU.
- Inserida em `squad.yaml` e `squad-party.csv`.

### Skill nova: image-overlay
- `skills/image-overlay/SKILL.md` criada. Aplica overlay de texto (headline, subheadline, badge, selos, CTA) sobre imagem gerada pela IA, via HTML/CSS renderizado por Playwright (depende de `image-creator`). 10 templates de posicionamento (1 por slot da hierarquia).

### Felipe Fotos refatorado
- `agents/felipe-fotos.agent.md` reescrito: vira EXECUTOR (nao decide mais o que cada foto mostra — consome brief da Helena). Usa Gemini 2.5 Flash Image (Nano Banana) em image-to-image preservando `foto_base_url`, depois aplica overlay.
- Antigo `step-06-fotos.md` deletado, criado `step-07-fotos.md` (renumerado pelo step novo da Helena).

### Renata atualizada (3-5 titulos com scoring + brief)
- `agents/renata-redatora.agent.md` reescrito: gera 3-5 titulos por SKU, cada um com `score_busca` (0-10), `score_conversao` (0-10), `justificativa` e `recomendado`. Bloco 1 da descricao ancora na `dor_interna` do brief; bloco 3 segue `escada_e_dai` do brief.
- Antigo `step-04-copywriting.md` deletado, criado `step-05-copywriting.md`.

### Caio Curador ajustado (D8 - campos canonicos)
- Adicionados `publico_genero` e `compatibilidade` ao schema do dossie (opcionais, `null` na maior parte do catalogo Terra Casa Decor).
- Quality criteria e exemplos atualizados em `caio-curador.agent.md` e `step-02-curadoria-produtos.md`.

### Checkpoint de copy reformulado
- `step-06-checkpoint-copy.md` apresenta as 3-5 alternativas de titulo com scores e recomendacao. Modo `batch` default usa recomendacao da Renata; usuario pode selecionar outra ou editar livremente.

### Pipeline renumerado de 10 para 11 steps
- `pipeline.yaml` atualizado: novo step-04 (Helena) entre Cibele e Renata. Steps 5-11 sao os antigos 4-10 renumerados.
- 7 arquivos antigos deletados; 4 novos criados; 4 renumerados (step-08-revisao, step-09-checkpoint-publicacao, step-10-publicacao, step-11-relatorio-final).
- Checkpoints renumerados: `step-06-checkpoint-copy` e `step-09-checkpoint-publicacao`.

### Quality criteria e anti-patterns atualizados
- `quality-criteria.md`: novo bloco "Inteligência de Conversão" (Helena) + reforma do bloco "Mídia Visual StorySelling" (Felipe) + bloco "Títulos" multi-opção (Renata) + regra global de tamanho 1200x1200 destacada no inicio.
- `anti-patterns.md`: novos anti-patterns para Helena (nao inventar dor interna sem evidencia), Felipe (nao embutir texto na imagem AI; nao salvar dimensao diferente de 1200x1200) e Renata (nao entregar 1 titulo so; nao marcar 2 recomendados).

### Regra global 1200x1200 formalizada
- Tamanho de foto agora e PADRAO FIXO (era "minimo"). Maior ou menor e veto automatico. Aplicado em 6 arquivos: quality-criteria, photo-templates (campo `dimensao` em todos os JSONs), felipe-fotos (principio + processo + checklist + anti-pattern), step-07-fotos, anti-patterns, image-overlay SKILL.

### Plan file
- Plano completo escrito em `~/.claude/plans/eu-tenho-um-gpt-delightful-thacker.md` e aprovado pelo Almir antes da execucao.

## 2026-05-25 - Sessao: suporte a anuncios com variacoes (Fases 1-4 + v2) + base do 1o lote real (lixeiras Viel)

### Base do 1o lote (lixeiras Viel)
- Planilha padrao Tiny processada: 2 anuncios x 3 cores (Lixeira 5L R$150 / 8L R$200 Inox Tampa Pedal, Branco/Preto/Cinza).
- `tools/tiny_to_esteira.py` (tradutor Tiny->esteira: agrupa pai/filho por "Codigo do pai", extrai cor de "Variacoes") + `tools/esteira/normalizer.py` -> emite `squads/ml-anuncios/output/anuncios-entrada.json`.
- 17 fotos re-hospedadas do Google Drive no bucket `tcd-produtos` via `tools/rehost_fotos.py` (0 falhas, URLs publicas confirmadas; service_role obtida via API de gerencia so em memoria).
- Dados ingeridos com ficha tecnica (marca Viel, material, dimensoes, capacidade). Typo do 8L ("Capacidade: 5 litros") corrigido pra 8 litros no dado de teste.

### Suporte a variacoes - implementado (Fases 1-4)
- Spec `docs/superpowers/specs/2026-05-25-suporte-variacoes-anuncio-design.md` + plano `docs/superpowers/plans/2026-05-25-suporte-variacoes-anuncio.md`. Abordagem A (unidade = anuncio; simples = N=1).
- Fase 1: `tools/esteira/normalizer.py` (deteccao modo) + `payload_builder.py` (contrato ML pros 2 modos + `validate_anuncio`). 8 testes pytest verdes em `tools/esteira/tests/`.
- Fase 2: step-01 detecta modo e usa o normalizer.
- Fase 3: 6 agentes ajustados pra raciocinar por anuncio (Caio, Cibele resolve COLOR/value_id/cor_value_map, Renata titulo sem cravar cor, Felipe StorySelling compartilhada + ambientalizada por cor, Vinicius regras ML, Paula payload). Convencao canonica de artefatos (caminhos planos sob `output/`, chaveados por `pai_sku`).
- Fase 4: migracao `ml_tools.publicacoes.modo`; workflow `ML Publicar` (0rzNJ7RLqLzMbKnf) monta `variations[]` (idempotencia por pai_sku/sku, picture_ids por cor, preco uniforme, available_quantity:1, SELLER_SKU/EAN por variacao). Validado 0 erros, INATIVO. `ml-api-reference.md` ganhou secao de variacoes.
- 10 templates HTML do image-overlay versionados (`skills/image-overlay/references/templates/`).

### v2: fonte de dados + checkpoint + foto tecnica
- Modelo da "2a planilha de atributos" DESCARTADO. Info do produto vem da coluna "Descricao complementar" do Tiny (`descricao_complementar`, lido pelo tradutor).
- Caio parseia a descricao complementar; Helena enriquece os campos pendentes a partir dos concorrentes top do ML + detecta divergencias + define `cor_heroi`.
- Novo checkpoint humano `step-04b-checkpoint-dados` (entre Helena e copy): notifica Almir em lacuna/divergencia/sem-concorrente; gate duro das dimensoes do produto. Fonte unica do dado = `curadoria/dossies.json`.
- Foto tecnica nova `FICHA_TECNICA_DIMENSOES` (dimensoes do produto). Profundidade OPCIONAL (produtos redondos = Altura x Diametro); gate exige so altura+largura.

### Memoria
- `criacao_anuncio_tiny_format_e_variacoes.md` criada (formato planilha Tiny pai/filho + suporte a variacoes + v2).
