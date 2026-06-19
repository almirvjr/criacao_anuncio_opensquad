# Squad Memory: ml-anuncios

## Estilo de Escrita

- **Acentuação correta sempre.** Títulos e descrições devem usar acentuação e cedilha corretas do português (ex: "aço", "você", "são", "escritório", "decoração"). NÃO escrever em ASCII puro. (Feedback Almir, 2026-05-26)

## Design Visual

- **Fidelidade absoluta ao produto nas fotos geradas por IA.** O produto na foto gerada (Nano Banana 2 image-to-image) tem que ser ESTRITAMENTE fiel à foto base de referência: mesma forma, proporção, acabamento, pedal, tampa. Qualquer alteração de design entre fotos = perda total de credibilidade pro cliente. Pode usar fotos de concorrente/site do fornecedor como referência adicional SÓ se houver evidência real de que é exatamente o mesmo produto. (Feedback Almir, 2026-05-26)

### Regras de geração de foto (Felipe) — refinadas pelo Almir em 2026-06-15

1. **Fidelidade é de PRODUTO, não de ângulo.** A foto base serve pra extrair o máximo de detalhes do produto (forma, acabamento, peças). A foto final NÃO deve copiar o ângulo/enquadramento da base — deve posicionar o produto num **ângulo estratégico** (ex: 3/4 levemente elevado) que realce a beleza dentro do ambiente. Repetir o ângulo frontal da base = foto chapada.
2. **Auto-correção de tonalidade.** Quando a foto base vier com cor adulterada (ex: o branco da lixeira Viel vem com tom azulado/acinzentado mesmo na base de estúdio), a IA deve corrigir pro tom REAL do produto (branco puro). Vale pra qualquer cor.
3. **Capa de cada variação/anúncio = ambientalizada SEM nenhuma fonte escrita.** Zero overlay de texto na capa. O texto/overlay vive só nas 9 fotos StorySelling (fotos 2–10). Isso muda o que estava no PROGRESSO (capa tinha overlay) — a capa agora é a ambientalizada limpa.
4. **Proporção produto × ambiente.** Respeitar a escala real do produto no cenário (lixeira 5L ≈ 25 cm de altura; 8L ≈ 35 cm). Erro concreto na 1ª geração: a lixeira saiu gigante ao lado da bancada/pia. Dar referência de escala no prompt (altura relativa a bancada ~85-90 cm, pia, toalhas).
5. **Overlay das StorySelling tem que ser profissional/atrativo.** Na 1ª geração a tipografia, a cor e a distribuição do texto ficaram amadoras. Redesenhar tipografia (peso/hierarquia), cor (contraste garantido sobre qualquer fundo, usar pílula/caixa quando necessário) e composição. Aplica-se às fotos 2–10 (não à capa, que é sem texto).

### Receita de capa fechada + dados reais do produto (lixeiras Viel 5L/8L, 2026-06-15)

- **Dimensões REAIS (corrigem o dossiê, que tinha 5L 25×19 / 8L 35×22 errado):** 5L = **18 cm diâmetro × 25 cm altura** (baixa/compacta, h≈1,4×largura); 8L = **18 cm diâmetro × 34 cm altura** (mesmo diâmetro, porém mais alta/esbelta, h≈1,9×largura). A proporção tem que ir EXPLÍCITA no prompt da IA. **8L tem a MESMA largura da 5L** — deve parecer só um pouco mais alta (~38% de uma bancada de 90 cm), NUNCA uma lixeira de cozinha avantajada. Sem ancorar em % da bancada, a IA engorda o 8L.
- **Receita de capa aprovada pelo Almir (após 7 iterações no 5L Branco — `capa-v7.jpg`):** produto ambientalizado SEM texto; ângulo 3/4 levemente elevado (NÃO copiar o frontal chapado da base); cores quentes/aconchegantes (madeira clara, bege, planta, luz de manhã); lixeira **encaixada no canto junto à bancada** (não solta no meio do piso); pedal **esbelto** (não parrudo); branco corrigido pra puro (base vem azulada); ocupa ~35-42% do frame no 5L / ~42-50% no 8L. Centralizar o produto foi REJEITADO (aproxima demais, perde o ambiente). Prompts salvos em `output/<run>/fotos/*/\_redesign/batch-capa-v*.json`.
- **Fotos-base reais de TODAS as 6 variações estão no bucket público** `tcd-produtos` (Supabase enztfhxccgdlontehlfy): `tcd-produtos/<SKU_VARIACAO>/foto-01.jpg`. Não precisa "fingir" cor a partir da branca — baixar a base real de cada cor.
- **QUIRK: a foto-base do 8L (VIE_1067_*) é praticamente a mesma do 5L** (fornecedor reusou a imagem baixa/squat). Logo, a silhueta mais alta do 8L tem que ser FORÇADA no prompt ("ignore the squat reference, render tall slim 34cm"), pois a base não mostra.
- **Wrapper do `generate.py` corrigido (2026-06-15):** antes embrulhava o prompt como "logo/mascote da referência" (ruim p/ fidelidade); agora diz "the reference IS the exact product... you MAY place it at a different flattering angle". Isso liberou o ângulo 3/4 mantendo fidelidade.
- Cor "Cinza" da Viel na real é um **cinza quente/taupe** (não cinza neutro) — reproduzir o tom exato da base, não forçar cinza puro.

### Regra de PROPORÇÃO por medidas do ambiente (geral, Felipe — Almir 2026-06-15)

- **Sempre ancorar a proporção do produto em medidas-padrão reais do ambiente em que ele aparece.** A IA não acerta escala "no olho" — tem que receber a medida de referência no prompt. Âncoras úteis: bancada de banheiro/cozinha ≈ **90 cm**; mesa de jantar ≈ 75 cm; assento de cadeira/sofá ≈ 45 cm; porta ≈ 210 cm; ilha de cozinha ≈ 90 cm. Para cada produto novo, pegar a dimensão real (do dossiê) e expressar no prompt como fração de uma medida-padrão do cenário (ex.: "lixeira de 25 cm = no máx. 1/3 de uma bancada de 90 cm; compor mostrando a bancada inteira piso→tampo pra a escala ler"). Lição das lixeiras: sem isso a IA renderiza o produto grande demais (5L virava cara de 12L).
- **Evidência ≠ escala — são independentes.** Pra destacar um produto pequeno SEM violar a escala real: (1) produto em PRIMEIRO PLANO com a câmera mais próxima dele — perspectiva faz o foreground parecer maior no frame (~45-55%) enquanto a bancada continua íntegra ao fundo, com o tampo no alto do quadro (a escala 1/3 ainda lê); (2) hero light sobre o produto + fundo mais sombreado; (3) bokeh forte no fundo, produto nítido. NÃO baixar/achatar a câmera pra "crescer" o produto — isso encolhe a bancada e quebra a escala (erro das versões v4/v6 rejeitadas).

- **A IA NÃO obedece escala exata por prompt.** Mesmo escrevendo "1/3" várias vezes, ela orbita ~40-50% da bancada porque associa "destaque" a "maior". Reprompttar fica num cabo de guerra (arruma a escala / perde o destaque e vice-versa). NÃO confiar a escala exata ao texto.

- **FÓRMULA APROVADA (Almir 2026-06-15) — "gabinete cortado" pra destaque + escala juntos:** quando destaque do produto e escala 1/3 brigam, NÃO precisa mostrar a bancada inteira pra "provar" o 1/3. Dar o zoom que o produto merece (foreground hero ~45-55%, hero light + bokeh) E **cortar o tampo/bancada fora do topo do quadro**: mostra só a parte de baixo-ao-meio de um gabinete ALTO que claramente continua subindo pra fora da imagem; a lixeira fica BAIXA contra ele (topo da tampa no terço de baixo do gabinete visível, com gaveta/painel sobrando acima e saindo do quadro). Como o gabinete some cortado pra cima, o olho entende que o produto é pequeno mesmo ele sendo grande no frame. Reforçar com pistas de tamanho que sobrevivem ao corte: piso (tile grande ~60cm), rodapé/toe-kick, gaveta. **Quando destaque e escala NÃO brigam (ambiente comporta), mostrar o ambiente mais aberto** em vez de cortar.

- **Coerência/harmonia dos objetos com o ambiente (Almir 2026-06-15):** todo prop tem que estar onde realmente ficaria num ambiente real. Toalha = toalheiro/bancada (NUNCA dobrada no chão). Vaso/planta pequena de mesa, sabonete, difusor = em cima da bancada/prateleira (não no chão). No CHÃO só o que é de chão: tapete/capacho, planta de piso em vaso grande, cesto de roupa. Se a bancada está cortada fora do quadro (fórmula acima), simplesmente OMITIR os itens de bancada — não jogá-los no chão só pra preencher.

### ✅ CHECKLIST PRÉ-APROVAÇÃO de imagem (Almir exigiu — rodar em TODA imagem antes de pedir OK, 2026-06-18)

Antes de enviar QUALQUER imagem pra aprovação, conferir item a item no resultado (olhado/medido, não presumido). Se um ajuste consertou algo mas quebrou outro item desta lista, **não enviar** — corrigir antes e só então mostrar. Regra meta do Almir: "uma vez orientado, eu não deveria receber de novo uma imagem com o mesmo erro".

1. **Produto fiel ao real** — aro do topo estreito/reto, interior só aço (sem anel branco/forro preto/saco/balde), tampa fina, pedal e base brancos, proporção esbelta. Referência mestra = `_redesign-overlay/branco-studio-fiel.jpg` (recolor fiel da foto real).
   - **MATERIAIS (Almir 18/06):** tampa + aro/colar do topo + dobradiça + pedal + base = **PLÁSTICO branco**; APENAS o corpo cilíndrico é **aço inox**. Em macros, NÃO renderizar o aro/colar como metal — é plástico branco. Só o corpo reflete como cromado.
   - **Diversificação por shot (conselho 18/06):** variar TIPO de foto, não só cena — macro de detalhe (dobradiça/mecanismo, textura do inox), aberta hero, tamanho em contexto, lifestyle em ambiente real. Macros saem de **recorte da foto REAL** + `faithful` (zero alucinação), NUNCA gerados do zero (IA inventa parafuso/solda). Overlay por contexto: **fundo claro/estúdio → faixa-clara; lifestyle → scrim**.
2. **Aba/dobradiça da tampa ALINHADA com o pedal** — mesmo eixo frente-trás (dobradiça atrás, pedal na frente, na mesma linha). Almir já reclamou 2×; item fixo de conferência.
3. **Inox prata NEUTRO** — nunca dourado/rosa/cobre. Rodar `inox_cast.py` (reprova w_med>=14).
4. **Reflexo do corpo limpo/claro** — cromado espelhado brilhante; evitar faixa preta vertical dura E evitar inox pálido/fosco/esbranquiçado.
5. **Texto NUNCA cobre o produto** — pedal/tampa/corpo livres do texto. Conferir bbox (`cutout.mask_bbox`): base do produto ACIMA do início do texto.
   - **ESCALA em lifestyle (Almir 18/06, REGRA FIXA da 5L):** a lixeira **5L (VIE_1066) ≈ 1/3 da altura de uma bancada/pia (~90 cm → lixeira ~25-30 cm)**. Em QUALQUER cena com bancada/pia/armário visível, a lixeira NÃO pode ficar quase da altura do móvel — tem que ler como ~1/3 dele. O Nano engorda; ancorar a escala no prompt ("bin ~1/3 the height of the 90cm vanity; show the vanity top") e CONFERIR antes de aprovar. (8L = mais alta, ~38%, mas mesmo diâmetro.)
6. **Zoom/enquadramento = SEMPRE gerar imagem nova** (nunca compor/escalar — `zoom_out.py` borra lateral e desalinha). Controlar tamanho pelo ÂNGULO DE CÂMERA no prompt.
7. **SEM MARCA em NENHUMA parte do anúncio (Almir 19/06, REGRA DEFINITIVA — ampliada no mesmo dia):** a marca — nome "Terra Casa Decor" e slogan "O seu melhor lugar é a sua casa" — NÃO aparece em foto, título NEM descrição. Fotos: sem logo/slogan e sem se apoiar nas cores da marca (`render_faixa.py` não desenha logo/slogan por padrão; só se `show_brand:true`, que não usamos). Título/descrição: não citar o nome da loja nem o slogan/assinatura; PMME só usa marca de fabricante real, nunca a loja; descrição fecha com frase acolhedora genérica. Motivo: não prender o anúncio a um rebrand futuro. O **tom/voz** ("casa", "lar", "dia a dia") permanece — é estilo, não citação. (Nas fotos já feitas, as cores foram mantidas — só removemos logo/slogan.)
8. **Cor-herói validada** com o Almir (não assumir).
9. **Versionar tudo** em `_redesign-overlay/_historico/` (nunca sobrescrever sem guardar).
10. **Coerência dos props na cena** — nada fora de lugar (toalha NUNCA no chão — vai no toalheiro/bancada; sabonete/planta/decor na bancada; no chão só tapete/planta de piso/cesto). Conferir antes de aprovar. (A `generate.py` já anexa a cláusula `SCENE_COHERENCE` automaticamente em toda geração de cena — modo não-faithful — desde 19/06.)
11. **Escala MEDIDA (não no olho):** medir altura da lixeira ÷ altura da bancada (chão→tampo) em px; alvo 5L ≈ 1/3 (~33%). NÃO confundir com "% do frame". (O Gemini tende a pousar em ~half; em cozinha incha mais que em banheiro.)

### Manhas do Nano Banana 2 (google/gemini-3.1-flash-image-preview) — aprender a cada erro (2026-06-18)

- **Ignora "produto pequeno / zoom-out".** Associa destaque a "maior" e enche o quadro. Pra reduzir e abrir chão pro texto: **ângulo de câmera ALTO olhando pra baixo** (~45°→produto ~60% da altura; ~30-35°→~75%; ~20-25°→~84%). Checar bbox e regerar se passar do alvo.
- **NÃO obedece alinhamento espacial preciso por texto** (ex.: dobradiça alinhada ao pedal). O texto ajuda mas não garante — VERIFICAR no resultado e regerar/escolher até alinhar.
- **Ambiente quente empurra inox pra dourado/rosa** → forçar "cool neutral silver chrome, NO golden/copper/rose" + luz neutra.
- **Ambiente muito claro deixa inox pálido/fosco** → forçar "highly reflective glossy mirror, contrasty, NOT pale/matte".
- **Tampa em ângulo alto fica ambígua (parece aberta)** → quando fechada: "lid FULLY CLOSED, thin flat disc, we do NOT see inside".

### Gemini PRO Image + geração em 1 tacada (2026-06-19)
- **`google/gemini-3-pro-image` (modo `pro` na generate.py) é MUITO mais fiel que o Flash e acerta de 1ª.** Usar **Pro** pras cenas/lifestyle/antes-depois. Gerar a **cena inteira numa tacada** a partir de prompt rico (a IA integra o produto) — NÃO compor recorte no Pillow (vira "figurinha"/adesivo). Método veio do projeto-referência do Almir (já em `photo-templates.md`).
- **Por que o Pro perdeu fidelidade de início (lição):** (1) pedir **tampa FECHADA com referência ABERTA** → o modelo não tem como copiar a tampa fechada e reverte pro VIÉS dele (tampa de inox abaulada). FIX: referência com a tampa NO MESMO estado desejado — criado `branco-studio-fiel-fechada.jpg` (recolor fiel da foto preta fechada → branca). (2) cena quente (madeira) deixa o aço **dourado/champanhe** mesmo no Pro → travar "steel stays COOL NEUTRAL SILVER, NOT golden/champagne, neutral white balance". Conferir cropando a região do produto e rodando `inox_cast` (não a imagem toda, ainda mais em split).
- Texto/overlay SEMPRE em Pillow (fonte Montserrat + marca), nunca deixar a IA escrever.

## Estrutura de Conteúdo

- **Máximo 10 fotos por anúncio no ML.** Quando a capa é uma foto específica por variação (ambientalizada por cor), sobram só 9 espaços para fotos StorySelling compartilhadas. Montar `picture_ids` = 1 ambientalizada (capa) + 9 StorySelling = 10 total (NÃO 11). (Feedback Almir, 2026-05-26)
- **Fotos StorySelling compartilhadas entre cores NÃO podem citar cor no texto do overlay.** Como as 9 StorySelling são as mesmas para Branco/Preto/Cinza, nenhum headline/subheadline pode dizer "branca" etc. — manter texto neutro de cor. (Validação 2026-05-26)

- ~~**Assinatura final obrigatória na descrição:** toda descrição deve terminar com `Terra Casa Decor - O seu melhor lugar é a sua casa`. (Feedback Almir, 2026-05-26.)~~ **REVOGADO em 19/06 pela regra SEM MARCA (item 7):** a descrição NÃO leva mais nome da loja nem slogan — fecha com frase acolhedora genérica, sem marca.

## Proibições Explícitas

- **Nunca usar o nome da marca/fornecedor no TÍTULO** (ex: "Viel"). A marca já vai na ficha técnica (atributo BRAND), e o espaço do título deve ser usado para outra palavra-chave de busca. Regra geral. (Feedback Almir, 2026-05-26)
- **Nunca inventar features que não estão na ficha real** (`descricao_complementar` do Tiny). Caso concreto: "balde interno removível" foi atribuído por engano às lixeiras Viel 5L/8L (o Caio puxou do site da Viel, que lista balde em OUTROS modelos — 4.5/10.5/15L). As lixeiras 5L/8L só têm: aço inox + polipropileno, tampa pedal, capacidade, cores, garantia 30 dias. (Feedback Almir, 2026-05-26)

## Técnico (específico do squad)

- **API de busca pública do ML (`/sites/MLB/search`) está restringida (403, exige token e mesmo com token pre-venda dá forbidden).** Para descobrir concorrentes, usar a busca pública do SITE (`lista.mercadolivre.com.br/<termo>`) via Playwright (funciona sem login). `/highlights/MLB/category/{id}` funciona com token mas devolve a categoria inteira, sem filtro de tamanho. `/items/{id}` dá access_denied no pre-venda; `/products/{id}` e `/products/{id}/items` funcionam.
- **Caio (curadoria) pode contaminar `caracteristicas`/`features` com dados de OUTROS modelos do fabricante.** Sempre validar o que ele marca com `fonte: site_fornecedor` contra a `descricao_complementar` real do produto antes de propagar pra copy/fotos.
- **PDP de catálogo do ML só renderiza ~5-15 reviews destacadas inline em scraping headless**; a lista completa + Perguntas vivem em widget client-side que não hidrata. Isso limita a confiança da Helena a `media` mesmo com concorrentes grandes.
- **Geração de fotos (Nano Banana 2 `google/gemini-3.1-flash-image-preview` via OpenRouter):** `skills/image-ai-generator/generate.py` devolve bytes crus em **1024×1024** (às vezes JPEG com extensão .png) → normalizar pra 1200×1200 pós-geração. O script embrulha o prompt como "logo/mascote da imagem de referência" — RUIM pra fidelidade de produto; liderar o prompt com "a referência É o produto exato, reproduza com fidelidade". Render do overlay via MCP **chrome-devtools** (não playwright) com `emulate viewport 1200x1200x1` (resize_page/fullPage trava em 1200×641 nesta máquina). Fonte Inter via Google Fonts CDN funcionou. Custo real Nano Banana 2 ~$0,07-0,08/imagem. (Validação 2026-05-26)
- **OpenRouter precisa de saldo** (não roda Nano Banana 2 no free tier — HTTP 402). `OPENROUTER_API_KEY` do `.env` é válida; checar saldo em `GET https://openrouter.ai/api/v1/credits`.
- **Upload de ambientalizadas ao bucket `tcd-produtos`** precisa de `SUPABASE_SERVICE_ROLE` (formato novo `sb_secret_...`); não está no `.env` (não persistir em disco). Storage REST aceita a chave em `Authorization: Bearer` + `apikey` (o formato sb_secret às vezes exige os dois headers).
