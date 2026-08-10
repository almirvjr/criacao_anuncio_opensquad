# DECISOES

<!-- Decisoes tecnicas importantes. Formato: data - contexto - decisao - motivo. -->

## 2026-08-06 a 10 — auditoria da ficha tecnica dos anuncios no ar

### Medida de produto NAO vem do Tiny; peso VEM (e mora dentro de `dimensoes`)
**Contexto:** propus preencher medidas puxando do Tiny. O Almir corrigiu: **o que o Tiny guarda e a medida
da CAIXA de expedicao**, nao do produto.
**Decisao:** medida de produto sai da **ficha do catalogo do ML do mesmo item, achada pelo codigo de barras**
(`/products/search?q={EAN}` → `/products/{id}`); a tabela de conhecimento (`public.knowledge_base`,
`content_type='produto'`, 70 itens) e **segunda opiniao**, nunca fonte primaria — ela tem erro dentro
(peso "1 g" copiado do proprio anuncio). **Peso** e a excecao: o Tiny tem, em `dimensoes.pesoLiquido`
(em KG). Nao existe `pesoLiquido` na raiz do JSON — ler a raiz devolve vazio e parece cadastro em branco.
**Motivo:** medida de caixa no lugar de medida de produto engana o comprador e nao e o que o filtro de busca usa.

### Toda gravacao em lote passa por peneira de valor ANTES de sair
**Contexto:** o catalogo do ML sugeriu Forma="Cilindrica" para uma lixeira; a categoria MLB33375 so aceita
Retangular/Quadrada/Circular/Oval. Sem conferir, a gravacao seria recusada ou entraria torta.
**Decisao:** `validar_sugestoes.ps1` roda 4 peneiras antes de qualquer PUT — (1) anuncio no ar e nao-catalogo,
(2) campo ainda vazio, (3) valor existe em `values[]` da categoria, (4) unidade dentro de `allowed_units`.
Das 441 sugestoes, **410 passaram e 31 cairam**. Sinonimo obvio (Cilindrica/Redonda → Circular) e resgate
manual aprovado pelo Almir, nao automatico.
**Motivo:** valor que veio de outra ficha nao e valor valido aqui — categoria diferente, lista diferente.

### O ML mexeu no titulo sozinho e o Almir decidiu MANTER
**Contexto:** gravar `COLOR` em anuncio **sem variacao** faz o ML anexar a cor ao fim do titulo
("...Limpeza Carro" → "...Limpeza Carro Branco"). 3 casos em 146, nao pedidos.
**Decisao (Almir, 10/08):** **deixar como ficou**. Mas todo lote passa a comparar titulo antes/depois e
reportar — mudanca de titulo mexe com busca e nao pode passar despercebida.
**Motivo:** a informacao no titulo nao atrapalha; o que nao pode e a mudanca acontecer sem ninguem ver.

### Campo do anuncio com valores divergentes por variacao: NAO grava
**Contexto:** em velas (MLB31547), `COLOR` e campo do anuncio, mas cada fragrancia tinha uma cor diferente
na sugestao. Gravar uma so faria o anuncio afirmar que todas as velas sao daquela cor.
**Decisao:** quando um campo nao-de-variacao recebe valores diferentes vindos de variacoes diferentes,
**pular e registrar**. Foram 41 campos em 9 anuncios.
**Motivo:** meia-verdade na ficha e pior que campo vazio — o vazio o comprador perdoa, a informacao errada gera reclamacao.

### Detector nao pode contar o mesmo problema uma vez por variacao
**Contexto:** a primeira varredura acusou "Diametro faltando" em 79 lugares, mas eram 36 anuncios — o
detector cobrava o campo em cada cor. `DIAMETER` nao e atributo de variacao em nenhuma categoria vista.
**Decisao:** so cobra na variacao se a variacao **tiver** aquele campo; senao cobra so no anuncio.
**Motivo:** numero inflado vira prioridade errada — "256 anuncios sem diametro" na verdade era bem menos.

## 2026-07-22 (tarde) — as 4 decisoes de contrato + funcionalidade

### Auditoria do Vinicius = 7 blocos COM nota (contrato unico com o step-08)
**Contexto:** o agente auditava 4 blocos com score; o `step-08-revisao.md` mandava 7 blocos sem score. Um dos 3 que faltavam era **StorySelling** — a palavra nao aparecia nenhuma vez no prompt do Vinicius, ou seja, ninguem conferia se a descricao ancorava na dor do cliente que a Helena mapeou.
**Decisao (Almir):** os **7 blocos** (Titulo, Descricao, Ficha Tecnica, Midia Visual, StorySelling, Compliance ML, Tom Marca) **com nota**, tabela fixa **15/20/15/20/15/10/5 = 100**, igual nos dois modos. O brief da Helena virou input obrigatorio do Vinicius. Veto novo: bloco 1 da descricao sem ancora na `dor_interna` (fora do caso `diagnostico_neutro`) reprova.
**Motivo:** o step-08 ja falava em "score >= 80" sem definir score — cada lado tinha metade do contrato.

### Bloco que e PORTAO nao pontua (Variacoes ML)
**Contexto:** o bloco Variacoes ML valia 20 pontos E qualquer falha nele ja era veto duro. Por causa desses 20 pontos existiam DUAS tabelas de score (4x25 no modo simples, 5x20 no variacoes).
**Decisao:** o bloco saiu da nota e virou portao puro; a tabela de pontos passou a ser uma so nos dois modos.
**Motivo:** peso que nunca decidiu nada custava manutencao dupla. **Padrao geral:** criterio que e "veto automatico" E tem peso na nota ao mesmo tempo — o peso e decorativo, tirar.

### Fotos: a Paula LE a lista pronta do Felipe; `pictures_compartilhadas` deixou de existir
**Contexto:** a Paula remontava `picture_ids` por formula (`fotos_cor` + `pictures_compartilhadas`), que dava 11 = **o bug das duas capas** que o DECISOES ja declarara resolvido. O Felipe ja entrega `picture_ids_por_variacao[].picture_ids` pronto, com 10 e a capa na 1a posicao.
**Decisao:** a Paula **copia** essa lista, sem somar/recalcular/reordenar. O campo `pictures_compartilhadas` foi **removido** do contrato (Paula, step-10, `payload_builder.py`). Lista ausente ou com tamanho != 10 = parar o anuncio e reportar, nunca completar por conta propria.
**Motivo:** duas fontes pra mesma verdade; a formula ja tinha quebrado uma vez. O n8n **desligado** `ML Publicar` tolera a ausencia do campo (ele tambem une todos os `picture_ids`), mas a linha deve sair quando o workflow for ligado.

### `cor_value_map` continua LISTA — o codigo passou a aceita-la
**Contexto:** Cibele e step-03 definem lista de objetos; `payload_builder.py` consumia como dict plano (`AttributeError` no pipeline real; o teste passava porque o fixture usava dict).
**Decisao:** o formato canonico e a **lista**; o `payload_builder` normaliza (dict legado segue funcionando).
**Motivo:** a lista carrega `value_name_livre` ("esta cor nao tem codigo no ML"), aviso que o dict plano nao consegue expressar — e descobrir isso na hora de publicar sai caro.

### `publico_alvo` / `ambientes_uso` FICAM, e o Caio aprendeu a preencher
**Contexto:** o step-02 exigia os dois; o prompt do Caio nunca os mencionava. O grep nao achava consumidor — mas Helena e Renata leem o dossie INTEIRO como LLM.
**Decisao:** manter os campos + principio novo no Caio ensinando a preencher a partir do que o anuncio sustenta. Sem base: grava vazio (`null` / `[]`) e registra warning apontando a Helena. Nunca inventa.
**Motivo:** "grep nao acha consumidor" != "campo morto" quando quem le e um modelo, nao um parser.

### Foto tecnica: profundidade IMPLEMENTADA (3a cota)
**Contexto:** `dim_profundidade` existia nos templates e no step-07 desde sempre e **nada lia** — o step mandava "deixar vazio", e a doc descrevia um painel de medidas no canto que era do overlay por navegador, aposentado.
**Decisao (Almir, "funcionalidade"):** o `render_faixa.py` desenha a profundidade como **diagonal de recuo (~29 graus) saindo da base a direita**, nos 3 estilos (`modelo`/`cotas`/`finas`), respeitando `dim_dashed`/`dim_label_box`/`dim_extension`. So desenha se a medida vier preenchida (produto redondo manda vazio). Sem espaco a direita: avisa no log e nao desenha.
**Motivo:** o eixo real de perspectiva nao e legivel de uma silhueta 2D, entao o recuo e uma diagonal fixa — a convencao de catalogo em vista 3/4. Validado no olho sobre a foto real da 5L, nao so em teste.

### Cota que nao cabe no quadro AVISA (nao reposiciona)
**Contexto:** achado ao validar a profundidade — se o produto chega perto da borda, as cotas de altura/largura sao desenhadas **fora do canvas e somem sem erro nenhum**. Aconteceu num render real (produto terminando em y=1155 de 1200; cota de largura em y=1189).
**Decisao:** o renderer **avisa** (`[dim] AVISO: so ha Npx de folga...`), dizendo quanto falta e que e caso de reenquadrar a base. **Nao reposiciona nada** — mover as cotas mudaria o resultado de fotos ja aprovadas.
**Motivo:** falha silenciosa e pior que falha barulhenta; mas conserto que mexe em saida aprovada precisa ser decisao do dono, nao efeito colateral de um aviso.

### Skill `image-overlay`: o manual descrevia o motor aposentado
**Contexto:** o `SKILL.md` (intocado desde 25/mai) ensinava montar HTML, subir `http.server` e tirar screenshot no Playwright, e pedia `brand_signature` — a marca e PROIBIDA desde 19/06. O motor real e `render_faixa.py` (Pillow) desde 06/2026. O Felipe estava certo, **mas carrega essa skill como instrucao**.
**Decisao:** SKILL.md reescrito contra o proprio script (`type: script`, 3 arquetipos, contrato de config extraido do codigo, secao SEM MARCA, gates). `image-creator` **saiu do loadout do Felipe** — e motor HTML->PNG por navegador e nada no processo dele monta HTML.
**Motivo:** **ao higienizar um agente, abrir tambem tudo que ele carrega** (`skills:`, steps, `data/`) — o prompt do agente e so a camada de cima. Mesmo padrao da Cibele usando o host certo e carregando o step-03 com o host morto.

### Angulo de camera vem do template, nunca do gosto do modelo
**Contexto:** o `generate.py` autorizava "you MAY place it at a different, more flattering camera angle", enquanto o `photo-templates.md` fixa o `angulo` por slot e o CLAUDE.md exige escala medida.
**Decisao:** a permissao saiu. O enquadramento e o angulo vem da descricao do prompt; o modelo e proibido de escolher angulo "lisonjeiro" ou inclinar a camera pra cima.
**Motivo:** "lisonjeiro" e sinonimo de heroico/contra-plongee — exatamente o que INCHA o produto e quebra a escala real (o mesmo que o `prompt_lint` ja avisa como `CAMERA_INFLA`).

## 2026-07-22

### Categoria ML real = `MLB33375` (os IDs anteriores eram falsos)
**Contexto:** o projeto usava `MLB263532` ("Lixeiras") em 13 pontos e `MLB264586` em outros. Verificacao ao vivo: ambos sao categorias RAIZ (`Ferramentas` e `Saude`), `listing_allowed:false`, nenhum publica.
**Decisao:** categoria = **`MLB33375`** (folha, `Casa, Moveis e Decoracao > Cozinha > Armazenamento e Organizacao > Lixeiras`). Corrigido tambem o ID de "Cozinha" (`MLB1648` -> `MLB1618`, real).
**Motivo:** ID copiado entre docs nunca tinha sido verificado contra a API. Regra nova: sempre confirmar categoria = folha + `settings.listing_allowed==true` via `GET /categories/{id}` antes de aceitar.

### Preditor de categoria: `domain_discovery` substitui `category_predictor` + veto por AMBIGUIDADE (nao por confianca)
**Contexto:** `GET /sites/MLB/category_predictor/predict` foi descontinuado (responde 404). O substituto `domain_discovery/search` funciona sem token mas **nao devolve numero de confianca** — a regra antiga da Cibele "confianca < 70% = veto" ficou inexequivel (estava em 8 pontos).
**Decisao (Almir):** o gatilho de veto/revisao humana passa a ser a **ambiguidade**: (a) predictor devolve 2+ candidatos plausiveis E os 3 concorrentes top se dividem entre eles; ou (b) menos de 2 dos 3 concorrentes na categoria #1; ou (c) categoria nao e folha que aceita anuncio. As "2 alternativas" agora saem prontas na propria lista do predictor (antes a Cibele reinventava rodando o predict de novo). A validacao cruzada com concorrentes virou a ancora principal.
**Motivo:** o numero morreu; ambiguidade + validacao cruzada cobrem a mesma intencao (nao chutar categoria incerta) com dado que existe. Ver `.claude-hub/memory/ml_preditor_categoria_domain_discovery.md`.

### Gate/veto deve falhar FECHADO (guardiao.sh do Mentor)
**Contexto:** o `guardiao.sh` (veto de saude mental do Mentor) imprimia `OK` quando nao conseguia consultar o Guardiao, e o Foco tratava `OK` como "segue livre" — falha-aberta num veto.
**Decisao:** fallback passou a emitir veredito distinto `INDISPONIVEL` (nao `OK`); o AGENTS.md do Foco trata `INDISPONIVEL` com cautela. Padrao geral: a falha segura de um veto e negar/pausar, nunca liberar.

### `--lock` do `qa_imagens.py` LIGADO no Vinicius e step-08
**Contexto:** a arquitetura produto-travado (2026-06-23, DEFINITIVA) confere o sha256 da camada do produto via `--lock`, mas os comandos do Vinicius e do step-08 nunca passavam a flag — a prova de proveniencia estava desligada.
**Decisao:** comandos passam `--lock pipeline/data/produtos-travados/{pai_sku}.json`. Nao e redecisao — e ligar uma trava ja decidida que estava inerte.

### `specs` do dossie e OBJETO `{valor, fonte}`, nao escalar
**Contexto:** o Caio grava `specs.capacidade_l = {valor, fonte}`; o step-02 descrevia como escalar `<num|null>` (Felipe/quem le pegava formato errado).
**Decisao:** step-02 (Output Format + 2 exemplos) alinhado ao objeto. `specs` guarda capacidade/peso/voltagem; **material NAO fica em specs** — fica em `dados_produto.material` (o Felipe foi corrigido pra ler `dados_produto.material.valor`).

### [SUPERADA 2026-07-22 -> ver bloco "2026-07-22 (tarde)" no topo] Aberto (decisao do Almir, NAO decidido nesta sessao)
Contrato de auditoria do Vinicius (4 blocos vs os 7 do step-08, que inclui StorySelling); `pictures_compartilhadas` (Paula remonta por formula que pode gerar 2 capas vs ler `picture_ids_por_variacao` ja pronto do Felipe — `payload_builder.py` que queria a chave e ORFAO, nao roda); `cor_value_map` lista vs dict (so quebra o payload_builder orfao; a Paula le como LLM); cortar ou manter `publico_alvo`/`ambientes_uso`.
**As 4 foram decididas no mesmo dia, algumas horas depois. Nada aqui esta em aberto.**

## 2026-07-19/20

### O DECISOES estava certo; os PROMPTS e que tinham derivado (re-alinhamento, nao redecisao)
**Contexto:** higiene de prompts da squad. Duas regras ja decididas aqui estavam sendo contrariadas pelos arquivos executaveis dos agentes.
**Nao sao decisoes novas — sao consertos de drift:**
- **`picture_ids` = 10.** A decisao "Capa = ambientalizada SEM texto" ja fechava: "1 ambientalizada (capa) + 9 StorySelling = 10". Mas `felipe-fotos.agent.md` e `step-07-fotos.md` mandavam "fotos_cor + as 10 = 11 itens" — o anuncio sairia com DUAS capas, a segunda na cor-heroi (podendo nao ser a cor que o comprador escolheu). Os dois arquivos foram alinhados ao 10; varredura confirmou que ninguem mais ensina 11.
- **Escala por framing, nao por razao em texto.** Ja decidido ("Ratio em texto NAO funciona no Nano — usar framing de fotografo/marcos"). Mas o TEMPLATE 1 do `photo-templates.md` ainda dizia "= ATE 1/3 e na real MENOS (~0,28)" — a forma que o proprio `prompt_lint` bloqueia. Trocado por wide shot + marco fisico ("o topo da tampa chega na gaveta de baixo do gabinete").
**Motivo do registro:** o padrao a vigiar nao e so "prompt contradiz prompt", e **"decisao registrada nao chegou no arquivo que o agente le"**. Ao decidir algo aqui, conferir se o prompt/template correspondente foi atualizado.

### Campo `BRAND` da ficha ML = marca do FABRICANTE (estende a regra SEM MARCA)
**Contexto:** a regra SEM MARCA (19/06) cobre foto, titulo e descricao, mas era **silenciosa sobre o campo estruturado `BRAND`** da ficha tecnica. Os 3 gabaritos da Renata traziam `BRAND: "Terra Casa Decor"` — e esse campo aparece na caixa de Caracteristicas do anuncio, ou seja, a marca da loja aparecia mesmo com a regra valendo.
**Decisao (Almir):** `BRAND` recebe a marca do **fabricante** (`dossie.marca`). Sem fabricante no dossie, usar o valor padrao do ML para produto sem marca, nunca inventar e nunca a loja.
**Motivo:** fecha a regra SEM MARCA de ponta a ponta (o objetivo era nao prender o anuncio a um rebrand). Custo aceito: expoe o fabricante a quem olhar a ficha.

### Arquetipo de overlay: faixa clara no slot 6 (Clareza), scrim no slot 5 (Lifestyle)
**Contexto:** o mapa no `felipe-fotos.agent.md` mandava faixa clara nos slots 3/5/9 e scrim nos 6/7/8/10 — resquicio da hierarquia antiga, quando o slot 5 era Clareza. Na hierarquia canonica atual, 5 = LIFESTYLE_EMOCIONAL e 6 = CLAREZA_ABSOLUTA.
**Decisao (Almir):** trocar os dois. **Faixa clara** (painel de texto legivel) vai para o slot 6, que precisa declarar a limitacao do produto sem ambiguidade; **scrim** (sombra suave) vai para o slot 5, que e respiro emocional e pede pouco texto.

### `cor_heroi` sempre preenchida + confirmacao POR EXCECAO no step-04b
**Contexto:** Helena, step-04, Felipe e step-07 ensinavam `cor_heroi: null` ("Felipe assume a primeira variacao"), mas o `brief.schema.json` e o `validar_brief.py` exigem string — e o **step-04b nunca mencionava a cor**, entao ela passava batida na auto-aprovacao. A cor-heroi define as 9 StorySelling do anuncio inteiro.
**Decisao (Almir):** a Helena SEMPRE propoe uma cor + justificativa (nunca `null`). O step-04b **compara com a primeira variacao do dossie**: igual = criterio padrao, nao ha decisao, auto-aprova e so registra; diferente = a Helena escolheu por causa das reviews, entao PARA e pede confirmacao. Felipe e step-07 param e reportam se a cor vier vazia, em vez de adivinhar.
**Motivo:** confirmar sempre mataria o caminho automatico do checkpoint; confirmar nunca deixava passar a decisao que mais custa caro. Por excecao pega o caso que importa sem cobrar presenca no lote limpo.

### Guarda anti-claim-falso estendida a copy (nao so as fotos)
**Contexto:** o `validar_claims.py` varria apenas o overlay das fotos. Titulo e descricao da Renata — que o comprador le ANTES de olhar foto por foto — nao passavam por trava nenhuma. Um "com balde interno removivel" na descricao de um produto sem balde nao seria barrado por nada.
**Decisao:** `validar_claims.py --copy anuncio-{pai_sku}.yaml` poe titulos e blocos da descricao sob as mesmas checagens (claim falso, feature de alto risco), mais um aviso quando uma limitacao do brief nao e declarada em lugar nenhum da copy. Negacao segue valendo como transparencia ("sem balde" passa, "com balde" bloqueia).

### Quando o prompt e a trava discordarem, a TRAVA vence — e a regra sai do prompt
**Contexto:** Helena e Felipe tinham dezenas de itens de "Never Do / Always Do / Quality Criteria" que os validadores ja conferem deterministicamente. Instrucao repetida nao adiciona capacidade; a trava sim.
**Decisao:** onde uma trava ja confere a regra, **apagar a regra do texto** e apontar para o validador, com a frase explicita "quando este texto e a trava discordarem, a trava esta certa". Na Helena isso eliminou 18 de 25 itens; no Felipe, 33 itens viraram uma tabela das 5 travas + 4 erros que trava nenhuma pega.
**Motivo:** evita que o prompt volte a divergir do codigo, que foi exatamente o defeito encontrado (o gabarito "alta confianca" da Helena era REPROVADO pela propria trava).

### Bug de producao: `"vista 3/4"` nao e razao de escala (`prompt_lint.py`)
**Contexto:** o linter tratava `3/4` como razao de tamanho e bloqueava — inclusive quem seguia o proprio `photo-templates.md`, que manda "lixeira sempre na DIAGONAL (vista 3/4)".
**Decisao:** excecao no `prompt_lint.py` para `3/4` em contexto de camera (vista/angulo/view/three-quarter), neutralizado antes da checagem de razao. Feito com TDD; um dos testes garante que razao de tamanho de verdade continua bloqueada (a correcao nao abriu buraco).

## 2026-07-12

### Fechar o loop do pipeline por CIMA do Opensquad (não reconstruir) — Juiz Visual primeiro
**Contexto:** estudados 4 artigos do Addy Osmani sobre agentic engineering. Almir perguntou se, para automatizar o loop de criação de anúncio (hoje "conferência atrás de conferência sem veredito"), valia remover a skill Opensquad e recomeçar no novo conceito. Auditado o pipeline real: o Opensquad já tem maker≠checker (Felipe/Vinícius), veredito determinístico (`qa_imagens.py`) e loops de auto-correção no `runner.pipeline.md`. Os 2 pontos que ainda exigem o Almir: (1) a inspeção ESTÉTICA do step-08(ii) é a olho humano (escala 1/3, materiais, sem-marca, foto×slot — o que `qa_imagens.py` não mede); (2) checkpoints obrigatórios por regra.
**Decisão:** NÃO remover nem reiniciar o Opensquad. O loop engineering fica um andar ACIMA do harness (artigo 1) — reconstruir jogaria fora a intenção já codificada (dívida de intenção). Adicionar 3 peças: **A) Juiz Visual** (Camada 1 estende `qa_imagens.py` no que é geometria; Camada 2 = `juiz_visual.py` novo, manda cada JPG a um modelo de VISÃO via OpenRouter — Gemini 3 Pro/Claude — que julga materiais/slot-fit/sem-marca e devolve confiança; escala aprova sozinho + escala pro Almir só o duvidoso). **B) heartbeat/fila externa** de SKUs. **C) checkpoints condicionais** (segue sozinho quando a evidência passa; pergunta só em incerteza/risco). Fazer A primeiro; B/C só depois. **Antes de plugar A, CALIBRAR contra o 5L FECHADO** (rodar o juiz nas fotos já aprovadas/reprovadas e ajustar até concordar com o Almir — artigo 2, "meça na sua própria base").
**Motivo:** autonomia segue a verificação (artigo 3): o que prende o Almir é justamente a parte do veredito que ainda não é mensurável por máquina. Automatizar esse veredito é o único desbloqueio; sem confiança calibrada no juiz, o Almir reconfere tudo e não se ganha nada. Plano detalhado em `PLANO-LOOP-JUIZ-VISUAL.md`.

### Regra geral de arquitetura de loop nos projetos do workspace (levantado nesta sessão)
**Contexto:** Almir perguntou se todo projeto (existentes e novos) precisa de um plano de implementação como este e se deve sempre rodar a skill Opensquad.
**Decisão:** (1) O tamanho do esforço de loop escala com a dificuldade de AUTOMATIZAR O VEREDITO daquele projeto, não é fixo. Projeto com "done" fácil de medir (ex.: reposição n8n = workflow rodou verde / SQL retornou o esperado) quase não precisa de plano; projeto com veredito de julgamento (estético, como este) precisa. (2) Para projeto NOVO: decidir logo no início qual é o veredito automático (Quality→Verdict, artigo 4), mas sem cerimônia pesada em projeto pequeno/descartável (blast radius — artigo 2). Começar em autonomia baixa e subir a escada conforme acumula verificação. (3) Opensquad NÃO é padrão universal: serve para trabalho que se decompõe em etapas/papéis estáveis e repetíveis (estrategista→curador→copy→foto→validador). Não usar para integração event-driven (isso é n8n) nem para tarefa única (basta 1 agente + boa verificação). Escolher o harness pela FORMA do trabalho.
**Motivo:** evitar over-engineering e evitar aplicar o Opensquad por hábito onde ele não encaixa.

## 2026-06-26

### Cor-herói é definida pelo ALMIR por anúncio (não default do brief)
**Contexto:** no início do 8L (VIE_1067) o brief defaultava cor-herói = Branco (1ª variação). Almir: "quero sempre definir a cor herói por anúncio".
**Decisão:** **8L = herói PRETO.** A cor-herói nunca herda o default do brief/Helena — perguntar e confirmar com o Almir em cada anúncio antes de gerar as StorySelling (elas saem todas na cor-herói, compartilhadas entre as 3 cores). Bônus: quando a herói é uma cor que já temos foto real do fornecedor, travar o produto DIRETO da foto real (sem recolor de IA = zero drift). Foi o caso do 8L preto (fotos WhatsApp 15/06).
**Motivo:** decisão do dono; trocar a herói depois de gerar custa retrabalho e geração ($).

### MIRROR-FINISH + escala 1/3 exata: render-in-scene → recorta → encolhe → recompõe
**Contexto:** Almir exige a lixeira a **≤1/3 da bancada** (34cm/90cm) E realista. Bati num impasse com 7 capas: (a) **one-shot Pro** = realista mas o Gemini SEMPRE infla o produto a ~0,5–0,66 e NÃO desce a 1/3 (limitação documentada — "orbita ~metade"); (b) **compose.py do PNG-travado de estúdio** = escala exata (0,33) mas vira **ADESIVO** — porque o inox é espelhado e o PNG reflete o ESTÚDIO, não a cozinha (Almir reprovou a v4: "parece figurinha colada"); (c) **--edit encolher** = distorce a proporção (vira squat, perde a silhueta alta). Causa raiz do adesivo: produto mirror-finish PRECISA refletir a cena real; recorte de estúdio reflete o ambiente errado.
**Decisão (validada por medida; aguarda OK visual do Almir):** para produto mirror em lifestyle com escala dura — **NÃO** compor do PNG de estúdio. Em vez disso: (1) gerar a lixeira DENTRO da cozinha por one-shot Pro (`capa-v7`, reflexos/luz reais da cena, ~0,5); (2) `--edit` remover a lixeira → cena vazia idêntica (`cena-v7-vazia`); (3) recortar a lixeira realista da v7 (BiRefNet num box justo) → PNG com os reflexos da cozinha já embutidos; (4) `compose.py` colar essa lixeira encolhida no `target-h` exato (1/3) na MESMA cena vazia, **sem `--harmonize`** (a cor/reflexo já casam), sombra de contato reforçada (`--shadow-alpha 155`). Resultado `capa-v8`: razão MEDIDA **0,32** + integração realista (não-adesivo). Scripts: `generate.py --edit` (remover), `cutout.alpha_mask` (recorte), `compose.py` (recolar).
**Motivo:** reconcilia escala exata (compose dá controle de pixel) com realismo (os reflexos vêm de uma render real da própria cena). Aplicável a TODA lifestyle de produto mirror com escala dura — provável receita das StorySelling 8L (capa,2,5,8) e futuros.

### Lembrete de processo: rodar o CHECKLIST antes de apresentar (reforço)
**Contexto:** nesta sessão apresentei a v4 (compose-adesivo) sem checar realismo — Almir cobrou "passou no seu checklist?". Mesma classe de falha do gate de enquadramento (24/06).
**Decisão:** reafirmado — NUNCA apresentar imagem (mesmo "só pra alinhar rumo") sem o checklist COMPLETO medido/olhado. Escala mede-se com grade de pixels (script ad-hoc: linhas de y a cada 50/100px, ler topo/base da lixeira e chão→tampo). Mostrar no Chrome só o que passou.
**Motivo:** "uma vez orientado, não deveria receber de novo uma imagem com o mesmo erro" (Almir).

## 2026-06-24

### GATE de enquadramento da faixa-clara — pre-validacao vira CODIGO inpulavel (nao checklist)
**Contexto:** ao montar a base studio do slot 9 (infografico faixa-clara), reaproveitei o hero fiel centralizado sem simular onde a faixa cai e mandei 2× pro Almir uma imagem com o **pedal cortado**. Causa raiz medida (nao suposta): o `render_faixa.py` desenha a faixa creme nos 486px de baixo (band_top=714) **com um fade de 40px ACIMA** (y674→714) que dissolve no creme qualquer parte do produto abaixo de y674. Coloquei a base do produto em y700 → os 26px de baixo sumiram no fade. NAO foi deteccao falha: `cutout.alpha_mask` (BiRefNet) e dark-pixel CONCORDAM no fundo real (~y1012 no master) e excluem a sombra de chao. O erro foi a regra viver so num checklist de memoria — **dependia de eu lembrar de rodar** (mesma classe de falha do edit-drift).

**Decisao:** a parte MENSURAVEL da pre-validacao saiu da memoria e virou gate em codigo, igual ao `--lock`/`prompt_lint`. Novo `skills/image-overlay/scripts/framing_gate.py`: (a) `autofit()` reescala/reposiciona o produto p/ caber inteiro acima do fade (so encolhe; so atua em fundo ~uniforme) — PREVINE; (b) `check_clip()` mede o fundo do produto (alpha_mask, exclui sombra) vs topo do fade e exige folga >=8px — PEGA. Integrados no `render_faixa.py` (layout faixa, nao scrim): autofit roda antes; o gate roda antes do save e, se reprovar, manda pra `_rejeitado/` + `exit 3` (override `no_qa:true`). **Nao da pra eu mostrar um "aprovado" sem o gate ter passado.** O checklist de memoria fica so pro que exige olho humano (cor-heroi, props, gosto).

**Motivo:** infalibilidade tem que ser por construcao, nao por promessa de atencao — Almir apontou que "se mandei sem pre-validar, a regra nao estava amarrada". Provado end-to-end: base ruim (master inteiro, produto y1012) → autofit conserta sozinho (x0.68, folga OK); com autofit off → REPROVA exit3 + `_rejeitado/`. 11 testes novos (`test_framing_gate.py`), suite 71→82 verdes. Vale p/ todo infografico futuro (slots 6,10, 8L, proximos produtos).

### Layout `plate` de overlay + 3 arquetipos por contexto
**Contexto:** o `scrim` joga o texto no rodape-esquerda; numa cena lifestyle com a lixeira no lower-left, o texto cobria o produto (reclamacao Almir 24/06: "o texto ficou em cima do que mais importa, a lixeira").
**Decisao:** 3 arquetipos no `render_faixa.py`, escolhidos por contexto — estudio/fundo claro = `faixa-clara` (faixa creme + framing_gate); lifestyle escuro/foto cheia = `scrim`; **lifestyle com PAREDE/area clara vazia = `plate`** (texto tinta escura + halo branco no espaco negativo, sem faixa/scrim, nao escurece nem cobre o produto). Regra de composicao: a cena lifestyle com texto deve ser GERADA com espaco negativo deliberado de um lado (produto do outro), e CONFERIR que a zona do texto nao toca o produto antes de aplicar.
**Motivo:** texto nunca sobre o produto, por construcao (nao por sorte de layout). Usado no slot7-maos e slot8 da 5L.

### Inox natural em lifestyle + proporcao + fidelidade (numeros/regras duras — Almir 24/06)
**Contexto:** Almir cansou de repetir as mesmas orientacoes de imagem ("e esse tipo de reajuste que estou tentando limar"). Fixados como regra dura (memoria + processo):
**Decisao:** (1) **inox_cast/dourado vale SO p/ STUDIO**; em ambientalizada/lifestyle o **reflexo NATURAL do ambiente e PREFERIDO** (o cromado reflete madeira/luz quente; nao forcar neutro, nao rodar inox_cast como gate). Ref: `_final/foto-06-pedal.jpg`. (2) **Proporcao lixeira÷bancada (chao→tampo): MAX 0,33, IDEAL 0,28, MEDIDA antes de apresentar.** Ratio em texto ("1/3", "half") NAO funciona no Nano (prompt_lint barra) — usar framing de fotografo/marcos ("chega na gaveta de baixo"). **EXCECAO foto de ACAO** (pe-no-pedal): a lixeira fica no foreground (onde o pe esta) e a perspectiva infla p/ ~0,38-0,47 MESMO sendo do tamanho certo (28cm) — ≤0,33 e demo-de-acao sao incompativeis; em foto de acao aceita-se ~0,4 (Almir escolheu manter a acao no slot 7). ≤0,33 vale p/ fotos de CONTEXTO (capa/lifestyle). (3) **Saco plastico NAO acompanha o produto** — nunca mostrar saco no interior (cria expectativa errada→devolucao); interior aberto = inox vazio (master `branco-studio-fiel.jpg`). (4) **Tampa = plastico BRANCO** (topo E por baixo), nao inox; so corpo+interior sao aco.
**Motivo:** tirar o que e mensuravel/factual da "memoria-que-eu-posso-esquecer" e fixar em regra/codigo; reduzir reajustes repetitivos.

## 2026-06-23

### ARQUITETURA PRODUTO-TRAVADO — produto NAO e re-renderizado, e composto (council + teste ao vivo)
**Contexto:** gerar as 10 fotos StorySelling via Nano Banana (Gemini 3 Pro Image / OpenRouter) virou caro e improdutivo. Causa raiz: o modo `--edit` **re-renderiza a cena inteira** a cada ajuste (amnesia) — corrigir 1 detalhe (ex.: geometria do aro) REGREDIA outros ja aprovados (some saco, muda reflexo, distorce pe). Slot 6 custou 9 iteracoes (~US$1,80). A disciplina (boas praticas + checklist) dependia da ATENCAO do assistente, nao de trava de maquina.

**Decisao:** o produto fiel vira um **PNG travado** (recorte BiRefNet do hero aprovado, com sha256 num manifesto `pipeline/data/produtos-travados/{pai_sku}.json`) e e **colado por codigo** (`compose.py` + Pillow) sobre uma CENA — a unica coisa que a IA gera. Politica por slot: studio/neutro (3,4,9,10) = composicao (fundo por codigo, custo IA 0); lifestyle (capa,2,5,8) = hibrido (compor + harmonizar; fallback one-shot do hero fiel sem `--edit`); slot 7 (pedal c/ pe) = one-shot com `--lock`. **`--edit` PROIBIDO p/ corrigir o produto.** Fidelidade vira INVARIANTE de engenharia (hash/proveniencia na composicao; disaster-check + olho humano + inox_cast no one-shot), nao meta de otimizacao do modelo.

**Motivo:** teste ao vivo (23/06) provou: composto studio = produto byte-a-byte fiel, drift zero, custo IA zero; recorte do inox espelhado pelo BiRefNet saiu impecavel. So o lifestyle tem o "vale da iluminacao" (inox reflete o estudio antigo) — dai o hibrido. Amarracao estrutural = gate embutido no `generate.py` (`--lock`, igual ao `prompt_lint`: inpulavel, override `--no-qa`) + `check_produto_fiel` no `qa_imagens.py` + trava `produto_travado` no `pipeline.yaml`. Custo/anuncio esperado: ~US$2-7 → <US$1. Bonus: o PNG travado e asset reutilizavel pro catalogo. Plano: `~/.claude/plans/bubbly-sleeping-ember.md`. 71 testes verdes.

## 2026-05-16

### Workflow "ML Publicar" hospedado em n8n cloud - estrategia de fotos
**Contexto:** spec original previa que Paula enviaria caminhos locais de fotos (`pictures_local_paths`) no payload do webhook. Mas o n8n esta em cloud (`dryboxjellyfish-n8n.cloudfy.live`), nao acessa o disco local.

**Decisao:** opcao A - fotos sao salvas previamente pelo Felipe no bucket publico `tcd-produtos` do Supabase Storage. Paula envia apenas as URLs publicas. ML baixa server-side via `pictures: [{source: "https://..."}]` no POST /items.

**Motivo:** workflow fica mais simples (~6 nos a menos, sem upload de fotos). ML aceita URLs publicas no payload. As fotos vao ficar publicas no anuncio publicado de qualquer jeito, entao expor no Storage publico nao adiciona risco.

### Tabela ml_tools.publicacoes sem RLS
**Contexto:** Supabase alertou que RLS esta desabilitado na tabela `ml_tools.publicacoes`.

**Decisao:** manter sem RLS.

**Motivo:** tabela e usada apenas pelo workflow n8n via service_role. Nao contem dados sensiveis (so log de publicacoes proprias). Se a chave anon nao vazar, esta seguro. Adicionar RLS exigiria criar policies para cada cliente futuro.

### Available_quantity inicial fixo em 1 no POST /items ML
**Contexto:** Tiny ERP detecta anuncios na conta "ML PADRAO" e sobrescreve o estoque com o valor real do ERP. Workflow nao precisa enviar estoque correto.

**Decisao:** workflow forca `available_quantity: 1` no payload ML, ignorando o que Paula enviar.

**Motivo:** garante consistencia (Tiny e a fonte da verdade do estoque). Evita descompasso entre planilha e ERP. ML aceita anuncio com qualquer estoque > 0.

### No "POST Tiny" mantido no workflow (substitui varredura manual) — **REVOGADA em 2026-05-17**
**Contexto:** descoberta - hoje Almir varre manualmente o painel Tiny para importar cada anuncio ML novo. A integracao nativa Tiny<->ML nao importa sozinha.

**Decisao:** manter o no "POST Tiny" no workflow chamando `POST https://api.tiny.com.br/public-api/v3/anuncios` (com `conta: "ML PADRAO"`).

**Motivo:** automatiza a varredura manual. Reduz tempo manual do Almir. Endpoint exato e estrutura do payload sao "best guess" ate validar com MCP da Tiny (pendencia).

**REVOGADA:** endpoint `/anuncios` nao existe na API v3 do Tiny (verificado via swagger.json oficial em 17/05). Ver decisao "Vinculo SKU↔MLB manual no painel Tiny" abaixo.

### Sanitizacao defensiva de description no workflow
**Contexto:** ML rejeita `description.plain_text` com HTML/emojis/`<` `>` (erro `item.description.type.invalid`). Renata pode produzir texto com formatacao inadvertidamente.

**Decisao:** defesa em 3 camadas - (1) Renata escreve plain text por instrucao, (2) Vinicius valida via quality-criteria com regex, (3) workflow Code "Montar Payload" sanitiza por seguranca.

**Motivo:** redundancia previne falha total. Se Renata erra ou Vinicius nao pega, workflow ainda salva o anuncio.

### Bucket publico vs privado no Supabase Storage
**Contexto:** fotos dos produtos precisam ser acessadas pelo ML para download server-side.

**Decisao:** bucket `tcd-produtos` configurado como publico.

**Motivo:** as fotos viram publicas no anuncio do ML de qualquer jeito - o bucket publico e apenas o intermediario. Alternativa privada (signed URLs com expiracao) foi considerada mas adicionaria complexidade no Felipe sem ganho de seguranca real.

## 2026-05-17

### Vinculo SKU↔MLB manual no painel Tiny (substitui "POST Tiny mantido")
**Contexto:** investigacao do MCP Tiny revelou que a API v3 NAO tem endpoint para criar mapeamento Tiny↔MLB (busca em paths/summaries/schemas: zero hits para `anuncio/marketplace/mlb/mercado/mapeamento`). API v2 documentada tambem nao tem. Doc oficial e fontes terceiras (Arcos Scale, Marketfacil, suporte Olist) confirmam: integracao nativa Tiny↔ML nao detecta MLBs novos criados via API externa nem cria anuncios novos no ML.

**Decisao:** apos cada publicacao bem-sucedida no ML, o operador faz o vinculo SKU↔MLB **manualmente** no painel Tiny (Integracoes > ML PADRAO > Relacionar Anuncios). Workflow responde com `tiny_sync: { status: "manual_pending", instrucao: "..." }` para sinalizar a pendencia.

**Motivo:** unico caminho documentado e estavel hoje. API v2 legacy (`incluir-mapeamento-anuncio.php`, folclore de forum) foi considerada mas sem doc oficial - apostaria no escuro. Custo operacional baixo no volume atual (esperado 1-5 publicacoes/dia).

### Query do "Buscar Publicacao Existente" com COALESCE para sempre retornar 1 linha
**Contexto:** n8n Postgres node nao propaga downstream quando query retorna 0 linhas. Query antiga `SELECT mlb_id FROM publicacoes WHERE sku = X AND mlb_id IS NOT NULL LIMIT 1` retornava 0 linhas para SKU novo, matando o workflow silenciosamente.

**Decisao:** envolver a query em `SELECT COALESCE((subquery), '') AS mlb_id` que sempre retorna 1 linha (string vazia ou MLB-id). IF `notEmpty` continua roteando certo (vazio -> publica; nao-vazio -> already_published).

**Motivo:** corrige bug estrutural sem mudar a logica do IF. Padrao aplicavel a outros nos Postgres do projeto que fazem lookup de chave estrangeira opcional.

### SELLER_SKU em attributes complementa seller_custom_field
**Contexto:** workflow originalmente enviava SKU apenas em `seller_custom_field` (campo legado do ML).

**Decisao:** `Montar Payload` injeta automaticamente `{ id: 'SELLER_SKU', value_name: sku }` em `attributes` (se nao vier no input). Mantem `seller_custom_field` tambem.

**Motivo:** SELLER_SKU em attributes e o padrao ML moderno e a forma que a integracao nativa Tiny lê o SKU para tentar fazer matching. Manter ambos (atributos + seller_custom_field) e redundancia barata sem conflito.

### listing_type_id validado contra lista
**Contexto:** fallback antigo `input.listing_type_id || 'gold_special'` aceitava qualquer string vinda do webhook.

**Decisao:** validar contra `['gold_special', 'gold_pro']`; valor invalido (ou vazio) cai em `gold_special`.

**Motivo:** previne erro 400 do ML caso a planilha tenha typo ou valor inesperado. Lista pode crescer se outros tipos forem usados (ex: `free`).

### MCP olist-docs apenas como referencia de documentacao
**Contexto:** MCP em `api-docs.erp.olist.com/mcp` foi identificado como **MCP de documentacao** (Mintlify), nao executor.

**Decisao:** adicionado ao `.mcp.json` como `olist-docs`. Para consulta de doc da API v3 Tiny (substitui ter que baixar swagger.json toda vez). NAO substitui chamada HTTP real ao Tiny - operacao real continua via HTTP Request node no n8n com OAuth2.

**Motivo:** util como "enciclopedia" durante desenvolvimento. Nao existe MCP oficial executor da Olist publicado.

### Metodo StorySelling absorvido na squad — fonte de reviews = concorrentes ML
**Contexto:** absorvido conceito do GPT externo "Cientific Selling: O anuncio bionico da Himmel" — fotos baseadas em quebra de objecao a partir de reviews + FAQ. Squad ml-anuncios e para produtos NOVOS sem reviews proprios.

**Decisao:** Helena Estrategista usa Playwright para scrapear reviews + FAQ dos 3 `concorrentes_top` (com `permalink`) que Cibele ja coleta no step-03. Amostra agregada (~50-100 reviews + 10-30 perguntas por SKU) alimenta diagnostico psicologico que vai gerar tanto a copy (Renata) quanto as fotos (Felipe).

**Motivo:** concorrentes ML capturam linguagem real do mesmo publico-alvo brasileiro. Reaproveita estrutura existente (Cibele ja tem permalinks). Alternativas (reviews multi-marketplace, manual, hibrido) descartadas por complexidade vs ganho.

### Helena Estrategista como agente novo separado (nao ampliar Felipe)
**Contexto:** metodo StorySelling tem duas camadas — diagnostico psicologico e execucao do prompt cinematografico.

**Decisao:** criar agente novo `helena-estrategista` (icone 🎯) para diagnostico; Felipe Fotos vira executor puro (consome brief, nao decide).

**Motivo:** separacao de responsabilidade (preserva principio da squad). Brief da Helena tambem alimenta Renata (copy), entao precisa ser produto compartilhavel, nao logica interna do Felipe.

### Texto em overlay pos-producao, nao embutido na imagem AI
**Contexto:** metodo Himmel poe headline, badge, selos visualmente dentro da imagem. Modelos de IA renderizam texto inconsistente (fontes variam, letras erram).

**Decisao:** modelo de IA (Gemini Nano Banana) gera imagem LIMPA. Skill nova `image-overlay` aplica todo o texto via HTML/CSS renderizado por Playwright (depende de `image-creator`).

**Motivo:** tipografia consistente, edicao posterior facil, fonte controlada (Inter), zero risco de letra errada. Tradeoff aceito: 1 passo a mais no pipeline.

### Image-to-image obrigatorio (foto base do dossie sagrada)
**Contexto:** GPT Himmel insiste "USE A IMAGEM ANEXADA — NAO ALTERE O PRODUTO". Comprador recebe o produto real, nao versao reimaginada pela IA.

**Decisao:** toda foto gerada e image-to-image sobre `foto_base_url` do dossie (capturada por Caio). Modelo so altera cenario e iluminacao. Se modelo distorce produto, retry 1 vez; ainda distorceu = veto.

**Motivo:** fidelidade visual reduz devolucao. Text-to-image puro foi descartado (alto risco de produto entregue diferente da foto).

### Modelo de IA = Gemini 2.5 Flash Image (Nano Banana) — **ATUALIZADA em 2026-05-25**
**Contexto:** GPT Himmel recomenda Gemini Pro. Skill `image-ai-generator` precisa de modelo image-to-image bom, barato, com API estavel.

**Decisao:** padronizar em `gemini-2.5-flash-image` (Nano Banana) via Google AI Studio para todas as 10 fotos. Custo estimado ~$0.04/imagem ($0.40 por SKU).

**Motivo:** image-to-image nativo bom, custo baixo, API estavel, aceita prompt JSON estruturado. GPT Image 1 (OpenAI) considerado mas image-to-image fraco e mais caro ($0.19).

**ATUALIZADA:** o codigo nunca usou Google AI Studio direto nem o `gemini-2.5-flash-image`. Ver decisao "Geracao de imagem via OpenRouter + Nano Banana 2" em 2026-05-25 abaixo.

### Inteligencia de Conversao alimenta copy E fotos (step entre categorizacao e copywriting)
**Contexto:** diagnostico psicologico das reviews tambem serve para Renata escrever titulo/descricao, nao so para Felipe gerar fotos.

**Decisao:** novo step-04 (Inteligencia de Conversao) entre Cibele (step-03) e Renata (step-05). Brief estrategico compartilhado: Renata usa para copy, Felipe usa para fotos.

**Motivo:** maxima sinergia — copy e fotos contam a mesma historia. Custo de scraping pago 1 vez por SKU, beneficio em 2 entregaveis. Pipeline cresceu de 10 para 11 steps.

### Renata gera 3-5 titulos com scoring (D7 absorvido do GPT "Gerador de Titulos ML")
**Contexto:** GPT publico "Gerador de Titulos ML" entrega 3-5 opcoes com explicacao de potencial. Versao anterior da Renata entregava 1 titulo.

**Decisao:** Renata propõe 3-5 alternativas, cada uma com `score_busca` (0-10), `score_conversao` (0-10), `justificativa` e `recomendado` (1 por SKU). Checkpoint humano (step-06) escolhe.

**Motivo:** reduz risco de "titulo unico ruim". Cria log de alternativas para iteracao. Casa com Himmel (que tambem gera 3 titulos SEO).

### Caio Curador formaliza campos canonicos (D8)
**Contexto:** Renata precisa de inputs estruturados previsiveis (produto, marca, modelo, categoria, especificacoes, publico, compatibilidade).

**Decisao:** dossie do Caio sempre carrega `tipo`, `marca`, `modelo`, `categoria_sugerida_livre`, `publico_genero` e `compatibilidade` (mesmo que `null` para a maior parte do catalogo).

**Motivo:** padroniza vocabulario downstream. `null` explicito > campo ausente. Inferir agora evita refator depois quando entrar categoria com gênero (roupas) ou compatibilidade (panela inducao).

### Tamanho de foto 1200x1200 px e PADRAO FIXO (nao minimo)
**Contexto:** versao anterior dizia "resolucao minima 1200x1200", o que permitia fotos maiores (ex: 1500x1500).

**Decisao:** toda foto entregue tem dimensao EXATA 1200x1200. Maior OU menor e veto automatico. Felipe redimensiona se Nano Banana retornar diferente.

**Motivo:** templates de overlay (image-overlay) assumem canvas 1200x1200 fixo — outras dimensoes quebram posicionamento de selos/headlines. Padronizacao visual no marketplace. Conformidade com tamanho recomendado pelo ML.

## 2026-05-25

### Geracao de imagem via OpenRouter + Nano Banana 2 (substitui "Gemini 2.5 / Google AI Studio")
**Contexto:** ao retomar os proximos passos, descobri divergencia entre doc e codigo. `CLAUDE.md`/`REFERENCIA.md`/DECISOES diziam `gemini-2.5-flash-image` via Google AI Studio (~$0.04/foto), mas o `generate.py` da skill `image-ai-generator` sempre usou **OpenRouter** (`OPENROUTER_API_KEY`), com producao em `google/gemini-3.1-flash-image-preview` (= Nano Banana 2) e teste em `sourceful/riverflow-v2-fast`.

**Decisao:** manter **OpenRouter** como gateway e **Nano Banana 2** (`google/gemini-3.1-flash-image-preview`) nas 10 fotos. Docs alinhadas a essa realidade. Nano Banana Pro (`gemini-3-pro-image-preview`) fica de reserva para a capa caso queira mais fidelidade no futuro.

**Motivo:** ja estava cabeado e funcionando (zero setup), mais barato (~R$0,07-0,10/foto) do que a estimativa Google da doc antiga, e OpenRouter pay-per-use evita throttling de tier gratis (problema que ja queimou o projeto reposicao no Groq). Nano Banana 2 e geracao mais nova que o "Nano Banana" original (2.5). O Pro nao compensa por ora: sua maior vantagem e renderizar texto na imagem, e aqui o texto vem do `image-overlay`, nao da IA — a IA so precisa preservar o produto. Almir confirmou a escolha em 25/05.

### 10 templates HTML do image-overlay versionados (antes eram lazy)
**Contexto:** a skill `image-overlay` previa gerar os 10 templates de slot sob demanda na primeira execucao; a pasta `references/templates/` estava vazia, bloqueando o teste E2E.

**Decisao:** criar e versionar os 10 `{SLOT}.html` + README a partir da spec da SKILL.md (tabela de posicionamento + identidade Terra Casa Decor), com auto-ocultacao de campos vazios (`.classe:empty{display:none}`).

**Motivo:** tira a aleatoriedade de "gerar na hora", deixa o layout auditavel/estavel e desbloqueia o E2E. Pendencia: ainda nao renderizados ponta a ponta com o `image-creator` (fonte Inter pode faltar no ambiente de render — validar na primeira execucao).

### Suporte a variacoes = Abordagem A (unidade = anuncio; simples = N=1)
**Contexto:** input real do Tiny e sempre pai (agrupamento) + filhos (cores). A esteira so fazia anuncio simples (1 SKU). Precisava fazer simples E com variacoes.

**Decisao:** a unidade de trabalho da esteira passa a ser o ANUNCIO; "simples" e o caso N=1 (uma variacao, sem cor). Um caminho de codigo so; o `modo` (simples/variacoes) so muda o payload final ao ML. Alternativas B (adaptador so na publicacao) e C (esteira paralela) descartadas — B gera copy/fotos 3x; C diverge com o tempo.

**Motivo:** sem duplicacao, custo controlado, manutencao simples.

### Payload ML de variacoes (POST /items)
**Contexto:** publicar 1 anuncio com 3 cores.

**Decisao:** `variations[]` com `attribute_combinations` (`COLOR` value_id+value_name), `price` (uniforme entre variacoes — regra do ML), `available_quantity: 1` por variacao (Tiny e a fonte de estoque), `attributes` (SELLER_SKU + EAN por variacao), `picture_ids` por cor = [ambientalizada da cor] + [fotos compartilhadas]. `pictures` item-level = uniao de todas. Idempotencia por `pai_sku` (variacoes) ou `sku` (simples). Coluna `modo` em `ml_tools.publicacoes`.

**Motivo:** COLOR e `defines_picture` (cada cor precisa de imagem distinta -> ambientalizada); ML exige preco uniforme; SKU vai em SELLER_SKU (nao seller_custom_field).

### Fotos: 10 StorySelling compartilhadas + 1 ambientalizada por cor
**Contexto:** num anuncio com 3 cores, gerar 10 fotos por cor (30) seria caro.

**Decisao:** 10 fotos StorySelling geradas 1x por anuncio (na cor "heroi") + 1 foto AMBIENTALIZADA por cor (image-to-image, produto da cor num cenario) que e a imagem distinta/capa da variacao. ~13 fotos IA por anuncio.

**Motivo:** controla custo; satisfaz o `defines_picture` do ML (cada cor com imagem distinta); beneficios do produto sao iguais entre cores.

### v2 — Fonte de dados = "Descricao complementar" do Tiny (substitui "2a planilha")
**Contexto:** primeiro plano previa uma 2a planilha de atributos (material/tamanho/caracteristicas).

**Decisao:** DESCARTAR a 2a planilha. A info do produto vem da coluna "Descricao complementar" do proprio export Tiny (`descricao_complementar`, lido pelo tradutor). O que faltar, a Helena enriquece a partir dos anuncios concorrentes top de venda no ML (durante o scraping que ela ja faz). Fonte unica do dado consolidado = `curadoria/dossies.json`.

**Motivo:** um arquivo so pro Almir (a planilha que ele ja baixa), menos friccao.

### v2 — Checkpoint de dados (step-04b) + notificacao na esteira
**Contexto:** o enriquecimento por concorrente pode faltar info, nao achar concorrente, ou divergir entre concorrentes.

**Decisao:** novo checkpoint HUMANO `step-04b-checkpoint-dados` entre Helena (step-04) e copy (step-05). Pausa e notifica o Almir (na propria esteira, sem Telegram) pra decidir/completar. Gate duro: dimensoes do produto resolvidas antes das fotos.

**Motivo:** o Almir quer decidir quando ha lacuna/divergencia; consistente com os checkpoints de copy/publicacao ja existentes.

### v2 — Profundidade do produto e OPCIONAL (foto tecnica)
**Contexto:** uma das fotos e a foto tecnica (slot novo `FICHA_TECNICA_DIMENSOES`) com as dimensoes do PRODUTO. Lixeiras sao redondas (Altura x Diametro, sem profundidade).

**Decisao:** o gate exige apenas `altura` + `largura` (largura = diametro em produto redondo) com `status: ok`; `profundidade` e opcional (`nao_aplicavel` quando ausente, nao bloqueia). A foto tecnica esconde a linha de profundidade quando vazia.

**Motivo:** exigir 3 medidas interromperia o fluxo a toa em produto redondo.

## 2026-06-15

### Capa = ambientalizada SEM texto (texto migra para as StorySelling)
**Contexto:** o plano antigo (PROGRESSO 26/05) previa a capa = foto ambientalizada por cor COM overlay de texto. Ao revisar a 1a geracao, o overlay na capa ficou amador e o Almir definiu que a capa deve ser limpa.

**Decisao:** a capa de cada variacao e a foto ambientalizada SEM nenhuma fonte escrita. Todo o texto/overlay vive nas 9 fotos StorySelling (fotos 2-10), que sao compartilhadas entre as cores (texto neutro de cor).

**Motivo:** capa limpa converte melhor e evita o overlay amador; concentra o esforco de tipografia num lugar so. `picture_ids` por variacao continua = 1 ambientalizada (capa) + 9 StorySelling = 10.

### Formula do "gabinete cortado" para conciliar destaque + escala 1/3
**Contexto:** destaque do produto e prova da escala (lixeira = 1/3 da bancada de 90cm) brigam: pra PROVAR o 1/3 a bancada inteira tem que caber no quadro, o que deixa a lixeira pequena; trazer pra frente pra dar destaque estoura a escala. A IA tambem nao obedece tamanho exato por prompt (orbita ~40-50% por mais que se escreva "1/3").

**Decisao:** quando os dois objetivos conflitam, NAO mostrar a bancada inteira. Dar zoom no produto (foreground hero) e CORTAR o tampo/bancada fora do topo do quadro — mostra so a parte de baixo de um gabinete alto que claramente sobe pra fora da imagem; a lixeira fica baixa contra ele (terco de baixo). O olho entende que e pequena mesmo grande no frame. Reforcar com pistas de tamanho que sobrevivem ao corte (piso, rodape, gaveta). Quando NAO ha conflito, mostrar o ambiente mais aberto.

**Motivo:** sacada do Almir. Resolve a oscilacao "arruma um lado, desarruma o outro". Evidencia passa a vir de luz/foco/composicao, nao de tamanho.

### Coerencia/harmonia dos objetos com o ambiente nas fotos
**Contexto:** numa capa o cenario tinha toalha dobrada no chao e um vaso de mesa no chao — objetos fora do lugar real.

**Decisao:** todo prop tem que estar onde realmente ficaria. Toalha = toalheiro/bancada (nunca no chao); vaso/planta pequena, sabonete, difusor = na bancada/prateleira; no chao so o que e de chao (tapete, planta de piso em vaso grande, cesto). Se a bancada esta cortada fora do quadro, OMITIR os itens de bancada (nao jogar no chao pra preencher).

**Motivo:** coerencia visual = credibilidade. Regra geral pra qualquer produto da squad.

### Dimensoes reais do produto vencem o dossie + bases reais por cor
**Contexto:** o dossie do Caio trazia 5L 25x19 / 8L 35x22 (errado). A escala das fotos depende da medida real.

**Decisao:** usar as medidas reais informadas pelo Almir: 5L 18x25, 8L 18x34 (mesma largura, 8L so mais alto ~38% da bancada). Gerar cada cor da foto-base REAL do bucket `tcd-produtos/<SKU_VARIACAO>/foto-01.jpg` (existem para as 6 variacoes), nao recolorir a branca. Quirk: a base do 8L e visualmente igual a da 5L (fornecedor reusou a imagem) — a silhueta mais alta do 8L tem que ser FORCADA no prompt.

**Motivo:** fidelidade de produto e escala correta. Bases reais por cor garantem tom certo (ex.: "cinza" Viel e um taupe quente, nao cinza neutro).

### generate.py: referencia tratada como "produto exato", nao "logo/mascote"
**Contexto:** o wrapper do `image-ai-generator/scripts/generate.py` embrulhava todo prompt com referencia como "Generate an image using the logo/mascot shown in the reference" — pessimo para fidelidade de produto.

**Decisao:** reescrito para "The reference image above IS the exact product to depict. Faithfully reproduce it... but you MAY place it at a different, more flattering camera angle and inside a new scene."

**Motivo:** liberou usar angulo 3/4 / cenario novo SEM perder a fidelidade do produto (requisito no 1 do Almir). Mudanca afeta toda geracao image-to-image da squad.

## 2026-06-16/17

### Identidade da marca = Montserrat + marrom/terracota/verde (raspada do site/IG)
**Contexto:** o overlay anterior usava Inter + verde-ML berrante (ficou amador — "observacao 5" do Almir).
**Decisao:** ancorar todo o visual das fotos na identidade real da Terra Casa Decor (raspada em 16/06): fonte **Montserrat**; **marrom #541D03** (primaria/titulos), **terracota #EBB28A** (assinatura), **verde #228D40** (CTA/confirmacao), creme. Logo real (arvore) extraido sem fundo. Doc em `squads/ml-anuncios/_memory/brand-identity.md`.
**Motivo:** consistencia com a marca; o overlay generico nao convertia/destoava.

### Render do overlay = Python/Pillow, NAO browser
**Contexto:** a skill image-overlay previa renderizar HTML via Playwright/chrome-devtools. No Windows o chrome-devtools fica com devicePixelRatio 0.5 e janela ~1366x577, cortando a imagem; Playwright local tem package.json corrompido.
**Decisao:** renderizar o overlay deterministicamente em **Pillow** (`skills/image-overlay/scripts/render_faixa.py`, config JSON -> 1200x1200). Ferramentas auxiliares `fit_scale.py` e `compose_two.py`.
**Motivo:** determinismo, zero dependencia de browser/viewport instavel, reutilizavel no lote.

### Foto tecnica = cota de engenharia, referencia na BASE com limiar alto (ignora sombra)
**Contexto:** as cotas (25cm altura x 19cm largura + selo 5L) precisam imitar o modelo de foto tecnica que o Almir ja usa: linhas de chamada, seta dupla, largura diagonal em perspectiva.
**Decisao:** `render_faixa.py dim_style=finas` desenha cota de engenharia (linhas de chamada marcando limites, seta dupla, largura diagonal na base). A deteccao da base usa **limiar alto (diff>90)** pra excluir a sombra (limiar baixo lia a sombra como base e jogava a cota pra longe). Folga uniforme dos dois lados referenciada na base.
**Motivo:** num cilindro (base alarga, sombra) a deteccao ingenua erra; uniforme + linhas de chamada = igual ao modelo do cliente.

### Processo: rodar CHECKLIST das orientacoes antes de mandar imagem pra validacao
**Contexto:** o Almir reclamou que eu mandava "aprova?" sem verificar todas as regras, e as vezes consertava um lado quebrando outro.
**Decisao (regra de trabalho):** antes de apresentar qualquer imagem pra validacao, rodar o **checklist de TODAS as orientacoes do Almir** e reportar o status real de cada uma (medido, nao no olho). Se um ajuste quebrar outra regra, avisar e mostrar o resultado final — nunca apresentar como certo quando nao esta.
**Motivo:** rigor; evita retrabalho e perda de confianca.

## 2026-06-17

### NAO comprar FLUX.1 Kontext nem Nano Banana Pro (resultado do council)
**Contexto:** outra sessao sugeriu um stack pago (driver Replicate/fal.ai + Nano Banana Pro pra texto + FLUX.1 Kontext pra restaging + remove.bg/BiRefNet pra cutout). Almir so quer pagar com melhoria comprovavel.
**Decisao:** NAO adotar FLUX nem Nano Banana Pro. O texto por IA (pitch do Nano Pro) e irrelevante — overlay e Pillow de proposito. Trocar o gerador por FLUX jogaria fora a receita v9 (tunada por semanas) por ganho incerto. Unico upgrade aprovado: cutout real (gratis).
**Motivo:** council (5 perspectivas + peer review) convergiu nisso; as 3 lacunas reais se resolvem sem custo recorrente.

### Deteccao de produto = BiRefNet local (rembg), substitui a heuristica do pixel-de-canto
**Contexto:** `render_faixa.py`/`fit_scale.py`/`compose_two.py` detectavam o produto por diff do pixel do canto — fragil (inox espelhado em fundo branco some; fundo degrade estoura o bbox pra imagem inteira). Bake-off em `tests/cutout-bakeoff/` comprovou.
**Decisao:** novo `skills/image-overlay/scripts/cutout.py` (BiRefNet via `rembg`, modelo `birefnet-general`, offline R$0) vira a fonte de mascara/bbox dos 3 scripts. Fallback automatico pra heuristica antiga se rembg faltar ou `CUTOUT_DISABLE=1`. Deps: `pip install rembg onnxruntime`. **Supera** a deteccao por diff>90 da foto tecnica (decisao 2026-06-16/17 "Foto tecnica = ... limiar alto"): a mascara ja exclui a sombra.
**Motivo:** detecção robusta em qualquer fundo; cobertura do produto subiu de ~22% pra ~85% nos casos de inox; resolve tambem a escala (vira bbox/alvo).

### Lacuna #1 (inox dourado) = quality-gate de cor, NAO correcao em pos
**Contexto:** Nano Banana 2 as vezes deixa o inox dourado/champanhe (creme/madeira puxam calor). A marca QUER reflexo quente pontual, mas nao o corpo todo dourado.
**Decisao:** `skills/image-overlay/scripts/inox_cast.py` mede calor normalizado RGB (`100*(R-B)/(R+G+B)`) no corpo metalico (mask do cutout); `w_med>=14` ou `warm_frac>=0.5` = `dourado` -> pedir retry (instrucao reforcada). NAO corrigir o tom em pos (achataria os reflexos quentes desejados) — regenerar. Usar RGB, nao o `convert("LAB")` do Pillow (neste build nao centra a/b em 128 e da lixo).
**Motivo:** validado 100% contra ground-truth visual (folga: bons<=12, ruins>=15); correcao automatica brigaria com a estetica aprovada.

## 2026-06-18/19

### Gemini 3 Pro Image + geracao em 1 tacada (substitui composicao manual)
- `generate.py` ganhou modo **`pro` = `google/gemini-3-pro-image`** (OpenRouter tem pro-image/-preview, 3.1-flash-image=Nano Banana 2, 2.5-flash-image). **Pro e MUITO mais fiel e acerta de 1a** que o Flash.
- Cenas/lifestyle/antes-depois: **gerar a cena inteira numa tacada** a partir de prompt JSON rico (a IA integra o produto) — NAO compor recorte no Pillow (vira "figurinha"/adesivo) nem iterar 14×. Metodo veio do projeto-referencia do Almir; ja documentado em `pipeline/data/photo-templates.md`.
- Por que o Pro perde fidelidade: (1) pedir tampa FECHADA com referencia ABERTA → reverte pro vies (tampa de inox abaulada) — FIX: ref no mesmo estado (`branco-studio-fiel-fechada.jpg`); (2) cena quente doura o aco — FIX: travar "cool neutral silver, neutral white balance" + medir cropando a regiao do produto.

### Modo `faithful` na generate.py + heros fieis como referencia mestra
- `faithful:true` reproduz a foto IDENTICA + so aplica a edicao (recolor/variacao). Usado p/ criar os heros fieis (recolor preto→branco da foto real) e os macros de detalhe (recorte da foto real + faithful = zero alucinacao). Gerar do zero perdia o produto.

### SEM MARCA em TODO o anuncio (DEFINITIVA)
- Nenhuma foto leva logo Terra, slogan, nem se apoia nas cores da marca — pra nao prender o anuncio a um rebrand futuro. `render_faixa.py` nao desenha marca por padrao (gate `show_brand`, off).
- **Ampliacao (Almir 19/06, mesmo dia):** a regra passou a valer tambem para TITULO e DESCRICAO. Nome "Terra Casa Decor" e slogan "O seu melhor lugar e a sua casa" **nao aparecem em nenhuma parte do anuncio** (foto, titulo nem descricao). PMME do titulo so usa marca de FABRICANTE real (Tramontina etc.), nunca a loja; descricao fecha com frase acolhedora generica. So o **tom/voz** acolhedor permanece na copy. Propagado em: CLAUDE.md, renata-redatora, step-05-copywriting, vinicius-validador, research-brief, anti-patterns, storyselling-framework, output-examples, quality-criteria, design.yaml, photo-templates, felipe-fotos, step-07/08, brand-identity, memories.md. **Hook que exigia o slogan: RESOLVIDO 19/06** — era a feature de pattern-rules por-edicao do plugin `security-guidance` v2.0.6; desligada via `ENABLE_PATTERN_RULES=0` no bloco `env` do `~/.claude/settings.json` (mantem o review de seguranca no Stop e em commit/push; sobrevive a updates do plugin).

### Coerencia de cena = automatica + Escala MEDIDA
- `generate.py` anexa `SCENE_COHERENCE` em toda geracao de cena (toalha no toalheiro/bancada NUNCA no chao; no chao so tapete/planta de piso/cesto; nada flutuando).
- Escala: MEDIR lixeira÷bancada (chao→tampo) em px; alvo 5L ≈ 1/3 (~33%). NAO confundir com "% do frame". O Gemini tende a ~metade; cozinha incha mais que banheiro (5L e produto de banheiro). zoom_out.py (composicao) DEPRECADO — borra lateral; preferir gerar de novo.

### Concorrencia: Firecrawl scrape (nao extract) + Helena
- `firecrawl_scrape` funciona no ML; `firecrawl_extract` ALUCINA → usar scrape + grep das URLs reais mlstatic. Helena raspa via Playwright (nao hidrata JS do ML) — migrar p/ Firecrawl no futuro.

### Validar briefing da Helena vs agente-referencia StorySelling
- Almir vai enviando as respostas do agente-referencia (FASE 0 inteligencia, titulos, descricao, 10 imagens JSON) pra checar se a Helena traz o briefing certo; corrigir a Helena se divergir. Hierarquia difere: foto tecnica = nossa foto 3 (escolha do Almir) → imagem 3 do ref = nossa foto 8. NAO usar selo "+N avaliacoes" (era do concorrente; nosso produto e novo).
