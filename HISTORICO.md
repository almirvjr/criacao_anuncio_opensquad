# HISTORICO

<!-- Tarefas concluidas (arquivo morto). Formato: data - resumo. -->

## 2026-08-06 a 10 - Auditoria e conserto da ficha tecnica dos 958 anuncios (frente nova)

Frente **fora do pipeline de criacao**: auditar e consertar a ficha dos anuncios JA no ar.
Ferramentas em `tools/auditoria_ficha/` (5 scripts PS 5.1, todos com backup + releitura de conferencia).

### O que foi medido
- **958 anuncios** (698 ativos + 260 pausados). Nao existe endpoint de qualidade (`/items/{id}/health`,
  `/health/actions`, `/performance`, `/moderations/*` = **404**): a medida sai de
  `GET /items?ids=...&include_attributes=all` contra `/categories/{id}/attributes` filtrando
  `tags.hidden` e `tags.read_only` (corta ~70 atributos para ~20 reais).
- **785 anuncios com campo vazio**; 173 com ficha completa. **Anuncio de catalogo nao tem nota** (`health`
  nulo): dos 310 ativos com nota, ZERO sao de catalogo → ficha de catalogo nao mexe na qualidade.
- **215 irregularidades** (valor errado, nao vazio) em 164 anuncios: peso irreal, medida irreal, diametro
  em produto nao-redondo, titulo x ficha divergente, codigo de barras invalido, caixa menor que o produto.

### O que foi corrigido (com backup e conferencia campo a campo)
- **Piloto MLB1254314177**: Cor principal nas 4 variacoes + Forma + Peso 1 g→1 kg + Diametro "nao se aplica".
- **8 erros de unidade**: 340 kg→340 g, 1 g→1 kg, 100 kg→350 g, 0,1 g→150 g, 23 m→23 cm, banqueta 0→29 cm.
- **36 de 36** anuncios ganharam "nao se aplica" no Diametro (produto retangular/quadrado).
- **Lote grande: 371 campos em 146 anuncios** (203 Cor principal, 51 Cor, 22 Diametro, 50 medidas...).
  Fonte: ficha do catalogo do ML achada pelo **codigo de barras** (957 dos 958 anuncios tem EAN).
- Em nenhuma das ~450 gravacoes preco/fotos/estoque/variacoes foram alterados (conferido contra backup).

### O que NAO deu (e por que)
- **5 anuncios travados**: sao de catalogo, o ML aceita o PUT com **200 e ignora**. So via "Sugerir correcoes".
- **41 campos de vela pulados de proposito**: cada variacao pedia uma cor e o campo e do anuncio inteiro.
- **Concorrente com mesmo EAN nao serve de fonte** (0 de 10 casos): quem divide catalogo divide a mesma ficha.
- Busca aberta por EAN (`/sites/MLB/search?q=EAN`) nao devolve nada — o caminho e pelo produto de catalogo.

## 2026-07-22 (tarde) - Sessao: motor de overlay defasado + as 4 decisoes de contrato + profundidade na foto tecnica

Continuacao da higiene. Fecha o que a sessao da manha deixou "para decisao do Almir". **118 testes verdes** ao final (eram 99). Nada commitado no codigo da squad — rollback por git.

### O manual da skill `image-overlay` ensinava o motor APOSENTADO (achado novo, nao estava no diagnostico)
- `SKILL.md` intocado desde **25/mai**: mandava montar HTML, subir `http.server` e tirar screenshot no Playwright, e trazia `brand_signature` como campo do contrato — a marca e PROIBIDA desde 19/06. O motor real e `render_faixa.py` (Pillow) desde 06/2026.
- O Felipe ja estava correto, **mas declara essa skill no `skills:`** e a carrega como instrucao. Mesmo padrao da Cibele com o host morto do step-03.
- Reescrito do zero contra o proprio script: `type: script`, os 3 arquetipos reais (faixa/`scrim`/`plate`) com mapa por slot, **contrato de config extraido do codigo (38 chaves)**, secao SEM MARCA (`show_brand` e gate desligado, nao opcao), gates (`framing_gate` exit 3 — e o registro honesto de que so roda no arquetipo faixa; `inox_cast` exit 2), scripts vizinhos, templates HTML marcados como legado. Snapshot `SKILL.md.snapshot-2026-07-22`.
- `image-creator` **saiu do loadout do Felipe** (3 pontos): e motor HTML->PNG e nada no processo dele monta HTML. Quem normaliza 1200x1200 e o proprio `render_faixa.py`.

### Outros consertos do mesmo lote
- **Angulo de camera** (`generate.py`): saiu o "you MAY place it at a different, more flattering camera angle" — o angulo vem do campo `angulo` do template.
- **Falso positivo do linter** (TDD): `\bmacro\b` acusava `CAMERA_INFLA` no **nome do slot** "Macro-Yes" (MECLABS). Excecao `_MACRO_YES_SLOT`, 4 testes (2 que falhavam + 2 garantindo que "macro" de lente segue avisando). Varredura nos 12 templates: o template 10 saiu de aviso -> limpo; sobram os 2 avisos legitimos (slots 4 e 7, que pedem close mesmo).
- **Ficha tecnica de dimensoes** (`photo-templates.md`): descrevia "quadro branco semi-transparente no canto inferior direito" e uma linha que sumia "via `:has(.dim-value:empty)`" — CSS de motor que nao existe mais. Realinhada as cotas reais; composicao e posicao do produto trocadas (a folga tem que ficar a esquerda/abaixo).
- **Hierarquia velha sobrevivia em +2 arquivos** (`research-brief.md`, `domain-framework.md`): "2-5 angulos / 6-8 detalhes". Trocada por ponteiro pra fonte unica (secao 6 do storyselling-framework) em vez de repetir a lista.
- **`_overlay_html/`** saiu do step-07 (pasta do motor morto).

### As 4 decisoes de contrato — fechadas pelo Almir e aplicadas (detalhe em DECISOES)
- **Vinicius: 7 blocos COM nota**, tabela unica 15/20/15/20/15/10/5; Variacoes ML virou **portao sem pontos** (matou a tabela dupla 4x25 vs 5x20). **StorySelling entrou de verdade** — a palavra nao existia no prompt dele; agora ha passo auditando `dor_interna`, `linguagem_real_cliente`, `escada_e_dai` e `only_factor` contra o brief da Helena, que virou input obrigatorio. Gabaritos reescritos e **somas medidas por script** (93/100/50, todas batendo, nenhum bloco acima do teto).
- **Paula le a lista pronta do Felipe**; `pictures_compartilhadas` removido do contrato nos 6 pontos + nos 3 gabaritos de variacao (que ensinavam a conta velha e mostravam 5 fotos; agora 10, conferido por `json.loads` + contagem). **Bucket dos exemplos da Paula era `viel-produtos`, que nao existe** — so aparecia ali; o real e `tcd-produtos` (`BUCKET` no `rehost_fotos.py:25`).
- **`cor_value_map` continua lista**; `payload_builder.py` normaliza os dois formatos e agora **falha alto** (`ValueError` com o SKU) se faltar lista de fotos ou vier tamanho != 10. +6 testes.
- **`publico_alvo`/`ambientes_uso` ficam**; principio novo no Caio + os 2 campos nos 2 gabaritos dele (preenchido e vazio-com-warning).

### Profundidade na foto tecnica — IMPLEMENTADA (pedido "funcionalidade")
- `dim_profundidade` existia nos templates e no step-07 e **nunca era lido**. Agora o `render_faixa.py` desenha a 3a cota: diagonal de recuo (~29 graus) saindo da base a direita, nos 3 estilos, respeitando os flags. So desenha se a medida existir. Sem espaco: avisa e nao desenha. TDD, 9 testes + 3 subtestes.
- **Validado no olho** (nao so em teste): renderizado sobre a foto real da lixeira 5L nos estilos `modelo` e `finas`, com enquadramento de 62% como o template pede.
- **Bug PRE-EXISTENTE achado ao validar:** produto perto da borda faz as cotas de altura/largura serem desenhadas **fora do canvas — somem sem erro nenhum**. O renderer passou a **avisar** (`[dim] AVISO: so ha Npx de folga...`); nao repositionei nada, pra nao mexer em foto ja aprovada. 3 testes.

## 2026-07-20/22 - Sessao: higiene de prompts (fila ALTA zerada) + lote de consertos da onda MEDIA

Parte de uma rodada cross-projeto (28C reembolso, Perguntas ML, Pos-Venda, Petra, Mentor — registrada no hub `.claude-hub/plans/`). O que tocou ESTE projeto:

### Categoria REAL descoberta + preditor do ML trocado
- Os IDs `MLB263532` (usado em 13 pontos) e `MLB264586` eram categorias **RAIZ** (`Ferramentas`/`Saude`, `listing_allowed:false`) — nenhum anuncio publicaria. Categoria real = **`MLB33375`** (folha, verificada ao vivo em 3 checagens). Breadcrumb tambem estava errado (`Utilidades de Cozinha` -> `Armazenamento e Organizacao`) e o ID de "Cozinha" (`MLB1648` -> `MLB1618`).
- `category_predictor/predict` foi **descontinuado (404)**. Trocado por `domain_discovery/search` (sem token, retorna lista sem numero de confianca) em Cibele, step-03, quality-criteria, anti-patterns, domain-framework, research-brief, design.yaml. Host morto `api.mercadolivre.com.br` -> `api.mercadolibre.com`. Corrigido em 9 arquivos + fixture de teste. **99 testes passando.**
- **Descoberta:** a propria Cibele ja tinha detectado o endpoint morto numa run de 26/mai (`output/2026-05-26-.../categorias.yaml`: "resource not found - endpoint legado", `prediction_probability: null`). Quebra sangrava desde maio; so as instrucoes nao acompanharam.

### Lote de consertos da onda MEDIA (diagnostico em `.claude-hub/plans/2026-07-20-diagnostico-onda-media.md`)
Aplicados via 3 subagentes paralelos (propriedade exclusiva de arquivo) + eu nos de producao sensivel. Todos com snapshots `.snapshot-2026-07-22` e 99 testes verdes:
- **Vinicius:** `--lock` ligado no `qa_imagens.py` (prova de proveniencia do produto-travado, estava desligada); gabarito nao viola mais SEM MARCA; dimensao `>=` -> `== 1200x1200 exatas`.
- **storyselling-framework:** capa nao manda mais escrever headline (regra textless); hierarquia velha da secao 4 alinhada a tabela Equilibrado da secao 6.
- **generate.py + SKILL.md:** `--edit` realinhado ao CLAUDE.md (so fundo, nunca o produto); `SCENE_COHERENCE` agora anexado tambem no caminho sem referencia.
- **Felipe:** lia `dossie.specs.material` (inexistente) -> `dossie.dados_produto.material.valor`.
- **step-02:** `specs` descrito como escalar -> objeto `{valor,fonte}` (formato real do Caio).
- Reverti a remocao de `publico_alvo`/`ambientes_uso` do step-02 — um hook do projeto barrou (sao spec canonica; LLM le o dossie inteiro). Virou decisao do dono.

### Ficou para decisao do Almir
Contrato de auditoria do Vinicius (4 vs 7 blocos); `pictures_compartilhadas` (Paula remonta vs le `picture_ids_por_variacao`; payload_builder e orfao); `cor_value_map` lista vs dict; cortar ou manter `publico_alvo`/`ambientes_uso`.

## 2026-07-19/20 - Sessao: higiene de prompts da squad (Helena, Felipe, Renata, photo-templates) + 2 bugs de producao

Rodada de `/common-kit:prompt-limpo` na squad ml-anuncios. **Metodo que revelou tudo: rodar a TRAVA de cada agente contra os GABARITOS do proprio prompt, antes de editar.** Nenhuma alteracao no trabalho do 8L; as mudancas sao nos prompts e validadores.

### Helena Estrategista — 480 → 270 linhas
- **O gabarito "alta confianca" do proprio prompt era REPROVADO pela trava** (`validar_brief.py`): 4 erros. O prompt ensinava a Helena a produzir brief que a trava rejeita.
- Lacunas fechadas (a trava exigia, o prompt nunca dizia): `nome_base`, `limitacoes_nota`, selos da foto 9 (4-6) e da 10 (min. 1), tokens MECLABS proibidos, condicao do slot 11, evidencia com min. 12 caracteres.
- Corrigido: "Foto 5 (Clareza)" → Foto 6 (resquicio de hierarquia velha); escala de confianca unificada; regra do "luxuoso" agora distingue `evidencias` (aceita a palavra do cliente) de `linguagem_real_cliente` (vocabulario da Renata).
- Cortados 18 de 25 itens de Never/Always Do que a trava ja confere sozinha. Eval: `BRIEF REJEITADO (4 erros)` → `BRIEF OK`.

### Felipe Fotos — 386 → 205 linhas
- **Brigava consigo mesmo:** principio 2b(e) dizia "prompt sempre PROSA, JSON so auditoria", mas os passos d/c mandavam "prompt: conteudo do JSON". Seguindo os passos, 12/12 templates eram bloqueados por `JSON_CRU`.
- Exemplo dizia `slot 5 = CLAREZA_ABSOLUTA` (canonico e 6); vocabulario dizia "1200x1200 = resolucao MINIMA" enquanto o principio 6 dizia "EXATAMENTE, nao minimo".
- 33 itens de Never/Always/Quality → tabela das 5 travas reais + 4 erros que trava nenhuma pega.

### Renata Redatora — 430 → 197 linhas
- **A regra SEM MARCA era enunciada 7 VEZES e os 3 gabaritos a violavam (3/3)**, com `- Marca: Terra Casa Decor` dentro do bloco de specs, que E a descricao. Demonstracao pratica de que o modelo copia o EXEMPLO, nao a prosa.
- Campo `BRAND` passou a receber a marca do FABRICANTE (aparece na caixa de Caracteristicas do anuncio, entao a loja ali furava a propria regra).

### photo-templates.md + `prompt_lint.py`
- **Template 1 (CAPA) brigava consigo mesmo:** `composicao` pedia "dominante, ~60% da area" e `direcao_de_arte` pedia "BEM pequena (~0,28)". 60% contra 28% no mesmo prompt — explica parte da briga de escala.
- Escala da capa estava como razao em texto ("ATE 1/3"), a forma que o linter bloqueia porque o modelo ignora. Trocada por framing de fotografo + marco fisico.
- **Bug no linter de producao:** `"vista 3/4"` (angulo de camera) era tratado como razao de escala e bloqueava quem seguia o proprio template. Corrigido com TDD (4 testes primeiro, 2 falharam; 1 garante que razao de tamanho real continua bloqueada). Templates bloqueados em prosa: 1 → **0 de 12**.

### `validar_claims.py` — guarda estendida para a copy
- A guarda anti-claim-falso varria **so o overlay das fotos**. Titulo e descricao — que o comprador le antes de olhar foto por foto — nao tinham trava nenhuma. Agora `--copy anuncio-{pai_sku}.yaml` poe a copy sob as mesmas checagens. TDD: 5 testes (4 falharam), 1 trava retrocompatibilidade.

**Suite de testes: 82 → 91, todas passando.** Todos os arquivos com `.snapshot-2026-07-19` ao lado (nada disso esta no git).

**Erros meus, registrados:** (1) cortei os exemplos de `metadata.yaml` do Felipe inteiros — e sao o unico lugar que documenta o formato que a Paula consome; devolvidos enxutos. (2) meu gabarito novo da Renata saiu com `length` errado por 1 char e `word_count: 213` num texto de 192 palavras — o mesmo defeito que eu estava corrigindo; so apareceu porque medi antes de aplicar.

## 2026-07-12 - Sessao: estudo loop engineering (Addy Osmani) + diagnóstico do pipeline + plano do Juiz Visual

Sessão de estudo/planejamento (nenhum código alterado). Lidos 4 artigos do Addy Osmani (loop engineering; code review; agência×orquestração; outer loop/accountability) e mapeados sobre os projetos do workspace.

### Feito
- **Diagnóstico do Opensquad ml-anuncios:** já é ~85% um sistema de loop engineering. Tem maker≠checker (Felipe step-07 gera / Vinícius step-08 confere), veredito determinístico rodando (`pipeline/validators/qa_imagens.py`: dimensão, produto, eixo, inox dourado, procedência sha256), e loops de auto-correção no `_opensquad/core/runner.pipeline.md` (retry de output vazio, veto 2x, review loop `on_reject`).
- **Identificados os 2 vazamentos** que ainda puxam o Almir pra dentro do loop: (1) o veredito ESTÉTICO (escala 1/3, materiais, sem-marca, foto×slot) está entregue ao olho humano no step-08 passo (ii); (2) os checkpoints são obrigatórios por regra (runner + SKILL.md).
- **Decisão:** NÃO reiniciar/remover o Opensquad — o loop mora um andar acima do harness (artigo 1). Adicionar 3 peças em cima. Registrado em DECISOES 2026-07-12.
- **Plano criado:** `PLANO-LOOP-JUIZ-VISUAL.md` (Peça A = Juiz Visual, calibrar contra 5L; Peças B/C depois).

### Questão aberta p/ próxima sessão
- Onde estão as fotos APROVADAS do 5L p/ calibrar o juiz. Pista levantada: `output/.../fotos/VIE_1066-PAI/` (5L = VIE_1066, fechado em 24-26/06).

## 2026-06-26 - Sessao: inicio do 8L (VIE_1067) - herói preto, produto travado, capa v8 (1/3+realista)

Rodada em `output/2026-06-26-conforme-8L/`. Pipeline herdado do 5L. NÃO concluído — capa aguarda aprovação; 9 StorySelling pendentes.

### Feito
- **Cor-herói = PRETO** (Almir escolheu; quer definir herói por anúncio). Master branco (recolor fiel pro/faithful das fotos reais) gerado e guardado p/ futura capa Branco; mas o herói é preto.
- **Produto-travado preto** (`pipeline/data/produtos-travados/VIE_1067-PAI.{json,_aberto.png,_fechado.png}`) travado DIRETO das fotos reais pretas do fornecedor (WhatsApp 15/06) — fidelidade máxima, sem recolor. Descoberta: as fotos do WhatsApp são o 8L ALTO real (a `base-branco.jpg` é que é squat/proporção 5L; nota antiga da memória estava desatualizada).
- **Brief conformado** (`inteligencia/brief-VIE_1067-PAI.yaml`): hierarquia do 5L, SEM marca (removido slogan/loja da foto 10), COZINHA-líder, dims reais 18Ø×34cm, foto 6 = sem balde interno.
- **Capa v8** (`_redesign/capa-v8.jpg`): escala MEDIDA razão 0,32 (≤1/3) + realista. Aguarda OK do Almir.

### Como a capa chegou na v8 (7 iterações — a lição técnica está em DECISOES 26/06)
- v1/v2 (one-shot Pro): realista mas lixeira inflada (~0,5-0,66); Almir reprovou ">meia bancada".
- v4 (compose do PNG-travado de estúdio): escala 0,33 exata MAS adesivo (inox refletia estúdio, não a cozinha); Almir reprovou "figurinha colada".
- v6 (--edit encolher): distorceu (squat, perdeu silhueta alta).
- v7 (one-shot wide): melhor realista mas ainda ~0,46.
- **v8 (método novo):** render-in-scene (v7) → --edit remove lixeira (cena vazia) → recorta a lixeira realista da v7 → compose encolhida a 1/3 na mesma cena (reflexos já casam) + sombra reforçada. = escala 0,32 + realista.
- Erros de processo do assistente nesta sessão (Almir cobrou): apresentei v4 sem rodar o checklist de realismo; me enrolei justificando escala 0,43-0,64 como "ok". Corrigido.

## 2026-06-24/26 - Sessao: 5L (VIE_1066) FECHADO (10 fotos sem marca) + bake-ins de overlay/escala

### Anuncio 5L completo e aprovado (todos validados no Chrome dedicado)
- 10 fotos sem marca em `output/2026-06-21-conforme-5L/fotos/VIE_1066-PAI/`: capa 3 cores + foto-02..10. foto-08 agora LOCAL (era reuso).
- **Slot 6 (Clareza):** refeito SEM saco (saco NAO acompanha o produto) — base master ABERTO vazio, "Sem balde interno removivel".
- **Slot 7 (Pedal):** conceito MAOS OCUPADAS (algodao+frasco) + pe no pedal; mudou de COZINHA p/ BANHEIRO (a 5L e bin de banheiro); TAMPA BRANCA corrigida (saia inox); overlay `plate`. Escala ~0,38 aceita (foto de acao = foreground, perspectiva).
- **Slots 9/10:** infograficos studio (master fechado reenquadrado), overlays faixa-clara (9: 5 selos de transparencia) e CTA (10).
- **Slot 5:** mantido original (abertura escura = sombra, nao saco; foi over-flag meu; regen via compose-lifestyle nao cravou pouso).
- **Slot 8:** reusou `base-foto8-pro` + overlay `plate` neutro (removeu verde-marca); headline sem "cozinha".

### Construido (bake-ins, suite 71->82 verdes)
- `skills/image-overlay/scripts/framing_gate.py` + integracao no `render_faixa.py`: `autofit` (reescala p/ caber) + `check_clip` (gate inpulavel) -> produto invade fade/faixa = `_rejeitado/`+exit3. 11 testes (`test_framing_gate.py`).
- Layout `plate` no `render_faixa.py`: texto tinta escura+halo no espaco negativo da cena (sem faixa/scrim) — p/ lifestyle com parede/area clara.
- `prompt_lint` confirmado barrando ratio/half em texto de escala (usar framing de fotografo/marcos).
- Memoria da squad (`_memory/memories.md`) atualizada: inox-natural-lifestyle, proporcao ≤0,33 medida (+excecao acao), sem-saco-interno, plate, compor-com-espaco-negativo.

## 2026-06-23 - Sessao: ARQUITETURA PRODUTO-TRAVADO (mata edit-drift) + slots 6 e 7 do ciclo 5L

### Council + decisao (ver DECISOES.md 2026-06-23)
- Diagnostico: `--edit` do Nano Banana re-renderiza a cena toda → corrigir 1 detalhe REGRIDE outros (slot 6 = 9 iteracoes/~US$1,80). Disciplina dependia da atencao do assistente, nao de codigo.
- Council (llm-council, 5 conselheiros + revisao) + teste ao vivo decidiram: **produto NAO e re-renderizado, e COMPOSICAO**. Plano `~/.claude/plans/bubbly-sleeping-ember.md`.

### Construido e testado (71 testes verdes; pytest em pipeline/validators/tests/)
- `skills/image-overlay/scripts/lock_product.py` — trava hero→PNG recortado (BiRefNet)+manifesto sha256 em `pipeline/data/produtos-travados/{pai_sku}.json`. VIE_1066-PAI travado (aberto+fechado).
- `skills/image-overlay/scripts/compose.py` — cola PNG travado sobre studio(codigo, custo IA 0)/cena IA + sombra + `--harmonize warm`; grava sidecar `.lock.json` (proveniencia).
- `skills/image-ai-generator/scripts/fidelity.py` — `verify_provenance` (composicao, garantia forte por hash) + `disaster_check` (one-shot, so produto ausente).
- Gate embutido no `generate.py` (`--lock`): roda disaster_check apos gravar, produto ausente → `_rejeitado/`+exit 3, override `--no-qa`. Inpulavel (igual prompt_lint).
- `qa_imagens.py` ganhou `check_produto_fiel` (`--lock`) → `PRODUTO_INFIEL` se sha do sidecar fora do manifesto. Trava `produto_travado` no `pipeline.yaml`. Testes novos: `test_fidelity.py` + casos em `test_qa_imagens.py`.
- Docs atualizados: `step-07-fotos.md` (passo 4d composicao-primeiro + 7b `--lock`), `felipe-fotos.agent.md` (principio 2b).

### Ciclo conforme 5L (VIE_1066) — slots 6 e 7 aprovados
- **Slot 6 (Clareza)** `foto-06-clareza.jpg`: studio, saco PRETO por dentro sob o aro branco, externa limpa, inox espelhado sem faixa preta, fundo limpo. 9 edits no metodo antigo (~US$1,80).
- **Slot 7 (Pedal)** `foto-07-pedal.jpg`: primeiro slot pelo PIPELINE NOVO (one-shot com pe + `--lock`, gate passou, US$0,14). Aro encaixa sobre o corpo, interior vazio, sem artefato cor-de-pele. Faixa preta vertical do inox aceita como reflexo real.
- Working versions em `output/2026-06-21-conforme-5L/fotos/VIE_1066-PAI/_historico/`.
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

## 2026-06-15 - Sessao: redesenho completo das 6 capas (lixeiras Viel 5L/8L)

### Capas finalizadas (6/6) — aprovadas pelo Almir
- Retomada da Fase 5 (fotos), pausada em 26/05. Redesenhadas as 6 capas ambientalizadas (5L e 8L x Branco/Preto/Cinza), salvas em `fotos/VIE_1066-PAI/_final/capa-5L-*.jpg` e `fotos/VIE_1067-PAI/_final/capa-8L-*.jpg` (1200x1200).
- ~25 iteracoes ate a formula final. Cada cor gerada da foto-base REAL (baixadas do bucket `tcd-produtos/<SKU_VARIACAO>/foto-01.jpg`, listadas no dossie) — nao "fingida" a partir da branca.

### Correcoes tecnicas aplicadas
- `skills/image-ai-generator/scripts/generate.py`: wrapper do prompt corrigido — antes embrulhava a referencia como "logo/mascote" (ruim p/ fidelidade); agora "the reference IS the exact product... you MAY place it at a different flattering angle". Liberou angulo 3/4 mantendo fidelidade.
- Dimensoes REAIS do produto corrigidas (dossie tinha 5L 25x19 / 8L 35x22 errado): **5L = 18cm diam x 25cm alt**; **8L = 18cm diam x 34cm alt** (mesma largura da 5L, so mais alta). Anotado na memoria da squad.

### Regras novas do agente Felipe (codificadas em `squads/ml-anuncios/_memory/memories.md`)
1. Capa = ambientalizada SEM texto (texto migra para as 9 StorySelling).
2. Fidelidade e de PRODUTO, nao de angulo; corrigir tonalidade adulterada (branco vinha azulado).
3. Ancorar proporcao em medidas-padrao do ambiente (bancada ~90cm); a IA nao acerta escala "no olho".
4. **Formula do "gabinete cortado"**: quando destaque do produto e escala 1/3 brigam, cortar a bancada fora do topo do quadro — o gabinete some pra cima e a lixeira fica no terco de baixo, lendo pequena mesmo grande no frame. Evidencia vem de luz/foco/composicao, nao de tamanho.
5. Coerencia/harmonia dos props (toalha no toalheiro, vaso pequeno na bancada; no chao so tapete/planta de piso).

### Pendente (proximo passo)
- Redesenho do overlay das 9 fotos StorySelling (tipografia/cor/distribuicao profissionais — observacao 5 do Almir).

## 2026-06-16/17 - Sessao: identidade da marca + redesenho do overlay + BLOCO 1 das StorySelling (5L)

### Identidade da marca Terra Casa Decor (raspada)
- Raspado site (terracasadecor.com.br) + Instagram (@terracasadecor, via espelho publico) com chrome-devtools. Doc completo em `squads/ml-anuncios/_memory/brand-identity.md`, evidencias em `_memory/brand-recon/`.
- Fonte = **Montserrat** (nao Inter). Cores: **marrom #541D03** (primaria), **terracota #EBB28A** (assinatura), **verde #228D40** (CTA), amarelo #FED65E, preto #0F0F0F, creme. Logo = arvore line-art + "Terra" serifa; versao sem fundo pessego em `terra-logo-clean.png` (extraida por luminancia).

### Overlay redesenhado (resolve "observacao 5" — tipografia/cor/distribuicao amadoras)
- Arquetipo "faixa clara" on-brand: painel creme na base, filete terracota, eyebrow + destaque marrom, selos chip verde, **logo real a direita + slogan**, Montserrat, **sem abreviacoes**. Mix por slot.
- **Render migrado pro Python/Pillow** (chrome-devtools no Windows fica dpr 0.5 / janela 1366x577 e corta — inviavel). Ferramentas novas em `skills/image-overlay/scripts/`: `render_faixa.py` (overlay, dim_style finas/modelo/cotas, badge/selos/faixa configuravel, modo tecnico), `fit_scale.py` (encolhe/sobe produto sobre creme reconstruido), `compose_two.py` (compoe lixeira+caixa sem recorte). Fonte `assets/fonts/Montserrat.ttf` (variavel).

### Receita da base validada (v9) + correcoes do Almir
- Base via Nano Banana 2 (image-to-image): **esbelta** (corpo ~1,4-1,5x, nunca squat — a branca tinha "never tall/slim" no prompt, removido), **reflexo do inox = estilo CAPA** (espelhado vidrado refletindo ambiente quente, nao fosco/nao faixa escura), **inox prata neutro** (creme puxa dourado), tampa/pedal branco puro.

### BLOCO 1 (faixa-clara) do 5L — feito/aprovado em `VIE_1066-PAI/_final/`
- `foto-09-sobrecorrecao.jpg` (5 selos), `foto-05-clareza.jpg` (lixeira esbelta + caixa kraft em pe proporcional, composta), `foto-03-tamanho.jpg` (**FOTO TECNICA** = cota de engenharia com linhas de chamada + seta dupla + largura diagonal; ref. base sem sombra; etiqueta "5 Litros"). Capa branca esbelta em `_redesign/capa-branco-slim.jpg` (pendente substituir).
- Muitas iteracoes na foto tecnica ate igualar o modelo do Almir; aprendido: detectar a base com limiar alto pra ignorar a sombra.

## 2026-06-17 - Sessao: stack de imagem (council) + cutout BiRefNet + gate de cor do inox

### Sincronizacao do agent file do Felipe com a realidade da Fase 5
- `felipe-fotos.agent.md` estava desatualizado (descrevia render por browser/HTML e "Gemini 2.5"). Atualizado: render = Pillow (`render_faixa.py`), modelo = Nano Banana 2 (`google/gemini-3.1-flash-image-preview`), arquetipos faixa-clara/scrim, fonte Montserrat. Tambem refletido o cutout e o gate de cor (abaixo).

### Council: avaliacao de comprar ferramentas novas de imagem (FLUX.1 Kontext / Nano Banana Pro / BiRefNet)
- Rodado o llm-council sobre o stack sugerido em outra sessao. Veredito: NAO comprar FLUX nem Nano Banana Pro (texto por IA e irrelevante — overlay e Pillow; trocar modelo joga fora a receita v9). Unico upgrade defensavel: cutout real (BiRefNet), de graca.

### Bake-off cutout: BiRefNet vs heuristica do pixel-de-canto (VALIDADO)
- Teste em `tests/cutout-bakeoff/` (`heuristic_mask.py` vs `alpha_cutout.py`) com 5 fotos reais de inox. Heuristica falhava feio: inox espelhado em fundo branco apagava ~78% do produto; fundo cinza degrade estourava o bbox pra imagem inteira (0,0,1300,1300). BiRefNet: mascara solida + bbox justo em todas (cobertura ~85%). Custo R$0, offline.
- **Integrado:** novo `skills/image-overlay/scripts/cutout.py` (BiRefNet via rembg, cache de sessao, fallback automatico pra heuristica antiga se rembg faltar ou `CUTOUT_DISABLE=1`). Plugado em `render_faixa.py` (foto tecnica: bbox/colunas/base), `fit_scale.py` (`product_bottom`) e `compose_two.py` (`bbox_of`). Verificado: base-cinza saiu de (0,0,1300,1300) pra (367,244,972,1126). Deps `rembg`+`onnxruntime` instaladas (Python 3.14).

### Gate de cor do inox (lacuna #1 dourado) — detector, NAO correcao (VALIDADO)
- Novo `skills/image-overlay/scripts/inox_cast.py`: mede calor normalizado RGB `100*(R-B)/(R+G+B)` no corpo metalico (mask do cutout). Limiar `w_med>=14` ou `warm_frac>=0.5` = `dourado` (exit 2 -> pedir retry). LAB do Pillow neste build NAO centra a/b em 128 (deu lixo) -> usar RGB.
- Calibrado/validado 100% contra ground-truth visual (VIE_1066): fotos reais ~0; v3 neutro 3.9; bons 9-12; v5/v2/cinza dourados 15.7-19.1. Correcao em pos descartada (achataria reflexos quentes desejados) — caminho e regenerar. Gate entrou no step-07 do Felipe (item 6e).

## 2026-06-18/19 - Sessao: BLOCO 2 das StorySelling (5L) + virada Gemini Pro + regra "sem marca"

### Conjunto 5L fechado (exceto foto 10) em `VIE_1066-PAI/_final/` — todas SEM marca
- **Capas** (3 cores) redesenhadas: lixeira ABERTA hero + "gabinete cortado" (bancada cortada no topo) p/ destaque + escala correta. Preto/cinza = recolor `faithful` da branca (cena/escala idênticas).
- **Foto 2** antes/depois (DOR×DESEJO): esquerda bagunçada/fria + lixeira plástica barata; direita limpa/quente com a inox; headline no topo. 1 geração Gemini Pro.
- **Foto 4** macro do corpo de inox (reflexo limpo do ambiente, recorte real + faithful).
- **Foto 6** pedal (pé acionando, tampa aberta, scrim) — fechada 18/06.
- **Foto 7** redesenhada = MACRO da dobradiça/mecanismo (recorte da foto real `16.48.40` + faithful recolor preto→branco); faixa-clara.
- **Foto 8** lifestyle = banheiro aspiracional via Pro (escala ~1/3, coerência dos props OK).
- Fotos 3/5/9 (faixa-clara) re-renderizadas sem marca.

### Motor de imagem evoluído (`skills/image-overlay` + `image-ai-generator`)
- `render_faixa.py`: novo `layout:"scrim"` (full-bleed + degradê numpy + texto branco, word-wrap, helpers `_wrap_segments`/`_draw_segment_lines`/`render_scrim`); cotas `dim_dashed`/`dim_label_box`/`dim_extension`; selo+CTA no scrim; logo centralizado no slogan; **gate `show_brand` (off) → não desenha marca**.
- `generate.py`: modo **`faithful`** (recolor idêntico) + modo **`pro`** (`google/gemini-3-pro-image`) + constante **`SCENE_COHERENCE`** anexada auto a toda cena.
- Novos: `compose_scale.py` (composição determinística de escala — usado só p/ "tamanho em contexto"), `zoom_out.py` (DEPRECADO — borra lateral), heros `branco-studio-fiel.jpg` (aberto) e `branco-studio-fiel-fechada.jpg` (fechado), logo branco `terra-logo-white.png`.
- Histórico de imagens versionado em `_redesign-overlay/_historico/` (Almir exigiu).

### Concorrência / Firecrawl
- Raspagem dos 3 campeões: `firecrawl_scrape` FUNCIONA no ML; `firecrawl_extract` ALUCINA (URLs/reviews falsos) → usar scrape + grep das URLs reais `http2.mlstatic.com/D_...`. Galerias deles = genéricas (estúdio + lifestyle + fotos de cliente). Helena hoje usa Playwright (não hidrata JS do ML).

### Pendente
- Foto 10 (CTA) com Pro. Replicar 8L. Validar briefing Helena vs agente-referência (Almir envia respostas aos poucos).

## 2026-06-19 - Sessao: regra SEM MARCA ampliada (foto+titulo+descricao) + neutralizacao do hook que interrompia

### Imagem 4 (spec + data badge) aprovada
- Revisada contra o briefing: inox PRATA (passou no gate de cor, o ponto critico), 4 callouts legiveis, badge presente. Aprovada. O 4,6★ foi desconsiderado a pedido do Almir.

### Regra SEM MARCA ampliada para TODO o anuncio
- Antes (19/06 manha): SEM MARCA so nas FOTOS. Agora (19/06): a marca — nome "Terra Casa Decor" + slogan "O seu melhor lugar e a sua casa" — NAO entra em foto, titulo NEM descricao (nao prender o anuncio a um rebrand). So o tom/voz acolhedor permanece.
- Propagado em 18 arquivos: `CLAUDE.md`, `felipe-fotos.agent.md`, `renata-redatora.agent.md` (tirada a assinatura obrigatoria; PMME so usa marca de fabricante real, nunca a loja; exemplos e checklist), `vinicius-validador.agent.md` (agora VETA se a marca aparecer), `step-05-copywriting.md`, `step-07-fotos.md`, `step-08-revisao.md`, `quality-criteria.md`, `anti-patterns.md`, `photo-templates.md`, `storyselling-framework.md`, `research-brief.md`, `output-examples.md`, `design.yaml`, `brand-identity.md`, `memories.md`, `PROGRESSO.md`, `DECISOES.md`. A assinatura na DESCRICAO foi REVOGADA (fecha com frase acolhedora generica).

### Interrupcoes a cada Edit — diagnosticadas e neutralizadas
- Causa: hook PostToolUse (matcher Edit|Write|MultiEdit) do plugin `security-guidance` v2.0.6 (`security_reminder_hook.py`), feature de pattern-rules por-edicao.
- Fix cirurgico: `ENABLE_PATTERN_RULES=0` no bloco `env` do `~/.claude/settings.json` (aplicado pelo Almir). Desliga SO o aviso por-edicao; mantem o review LLM no Stop (`ENABLE_CODE_SECURITY_REVIEW`) e em commit/push (`ENABLE_COMMIT_REVIEW`). Sobrevive a updates do plugin. Requer reload (`/hooks`) ou restart.

### Pendente
- **Commitar os 18 arquivos da squad** (renata/vinicius/steps/data) — o `/save` so commita os 5 docs raiz; a propagacao SEM MARCA nos arquivos da squad segue NAO commitada.

## 2026-09-09 - Sessao: Raio-X do anuncio ML (userscript novo) - do EAN13 ate o painel enxuto

### Origem: achar o codigo universal (EAN13) de um anuncio
- Pergunta do Almir: 2 anuncios do mesmo Organizador Coza New Retro 1L 1x4 Cristal. Achado: **EAN13 = 7900161004868** (ref. de fabrica 102573009). Irmao 2x2 = ref 102583009 / EAN 7900161020875.
- Confirmado por DOIS caminhos independentes: site da propria Coza (dataLayer `"EAN"`) e conexao oficial do ML. Bate.
- **O GTIN NAO existe no codigo da pagina do anuncio** — varrido o HTML dos formatos `/p/` e `/up/` procurando "GTIN", "EAN", "Codigo universal" e o proprio numero: zero ocorrencias.

### A ferramenta: `userscripts/raio-x-anuncio.user.js` (v2.0.1) + `README-raio-x.md`
- Userscript Tampermonkey. Cola a URL de qualquer anuncio (inclusive de concorrente) e devolve o que NAO esta na tela. Instalado e configurado no Chrome do Almir; chave via GM storage (funcao `get-ml-token`, mesma da reposicao).
- Instalacao/atualizacao pelo metodo ja conhecido: `python -m http.server` na pasta + abrir `http://127.0.0.1:8899/<script>.user.js` no Chrome dele (Tampermonkey intercepta e mostra a tela de instalar/atualizar).

### Reconhecimento de API feito ao vivo (o que responde sobre anuncio de TERCEIRO)
- ✅ `/products/search?q={id_da_ficha}` → **GTIN** (unica porta). `/products/{id}` NAO traz.
- ✅ `/products/{ficha}/items` → quem disputa a ficha (item_id, seller_id, price). Serve de PROVA de vinculo.
- ✅ `/items/{id}/visits/time_window?last=30&unit=day` → visitas do concorrente.
- ✅ `/users/{id}` → nickname, nivel, power seller, total historico de transacoes.
- ✅ `/sites/MLB/listing_prices?price=` → comissao. Sem `category_id` vem generica; categoria sai de `/sites/MLB/domain_discovery/search?q=<titulo>`.
- ✅ `/reviews/item/{id}`, `/highlights/MLB/category/{cat}` (ranking de mais vendidos).
- ❌ 403: `/items/{id}` de terceiro, `/items/{id}/price_to_win`, `/sites/MLB/search` (busca), `/sites/MLB/search?seller_id=`.

### Bugs pegos nos testes ao vivo (nenhum foi achado por leitura de codigo)
- **Falso positivo por buscar na pagina inteira:** "loja oficial" e o icone do Full aparecem no carrossel de OUTROS vendedores embaixo do anuncio. Deu "Terra e loja oficial" (falso) e "esta no Full" (falso). Fix: procurar so na area certa — Full em `.ui-pdp-container__row--stock-and-full`, entrega em `.xprod-lib-shipping-promises`, loja oficial subindo 6 niveis do titulo do vendedor.
- **Pagina `/up/MLBU...` nao tem o numero do anuncio no endereco** — esta no HTML em `"item_id"`. Sem pescar dali o script confundia o numero do anuncio com o da ficha (o ML escreve os dois como `/p/MLB...`).
- **Detector de catalogo so pelo redirecionamento ERRA em loja oficial** (o ML manda loja oficial pra pagina `/up/` dela, nunca pra ficha). Fix: provar por `/products/{ficha}/items`.
- **Vendedor errado na ficha:** a pagina de catalogo mostra quem GANHA a caixa de compra, nao o dono do anuncio colado. Passou a mostrar as duas linhas.

### Enxugamento (decisao do Almir, apos conselho)
- Veredito dele sobre a v1: "mais do mesmo, nao soma" — preco, vendas, estoque, frete, vendedor, categoria, ficha, fotos, descricao e avaliacoes ja estao na tela. Tudo cortado.
- v2 = 5 blocos: codigo universal, catalogo vs lista, marca+modelo, visitas 30d, quanto sobra pro vendedor, quem disputa a ficha.
- Conselho (llm-council, 5 conselheiros + 3 revisoes) rodado antes de decidir. Os 3 revisores escolheram o mesmo conselheiro (First Principles). Dois argumentos do conselho foram DERRUBADOS por fato: (a) risco de ban — sao portas oficiais com a chave do proprio Almir; (b) "radar nao da porque o ML bloqueia de fora" — o bloqueio e so nas PAGINAS, a API responde de qualquer lugar.

### Posicao na busca — investigado, viavel, ficou fora
- Busca pela API = 403. A pagina de resultados vem do servidor SEM os anuncios (so renderizam no navegador), entao `fetch` + parse nao ve nada.
- Lendo a pagina JA ABERTA funciona: 60 cards por pagina em `li.ui-search-layout__item`. Medido ao vivo: anuncio MLB1968951521 na **posicao 34 de 937 resultados** para "lixeira pedal 12 litros". Fora do escopo da v2 porque exige abrir a busca, nao colar URL.
