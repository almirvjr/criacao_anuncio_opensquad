---
name: image-ai-generator
description: >
  Generates images via the Openrouter API using Nano Banana (Gemini image) models, and
  edits ONLY the background/scenery of an existing image. Encodes the Nano Banana
  interaction protocol: natural-language first generation, background-only isolated edits
  (the PRODUCT is never fixed with --edit — that is composition/one-shot, to avoid
  edit-drift), photographic framing for scale control, and style/reference transfer.
description_pt-BR: >
  Gera imagens via API do Openrouter usando Nano Banana (Gemini image) e edita APENAS o
  fundo/cenario de uma imagem existente. Codifica o protocolo de interacao com o Nano
  Banana: 1a geracao em linguagem natural, edicoes isoladas so de fundo (o PRODUTO nunca
  se conserta com --edit — isso e composicao/one-shot, pra evitar edit-drift), framing de
  fotografo pra controlar escala, e transferencia de estilo por referencia.
type: script
version: "2.0.0"
script:
  path: scripts/generate.py
  runtime: python3
  invoke: "python3 {skill_path}/scripts/generate.py --prompt \"{prompt}\" --output \"{output}\" --mode \"{mode}\""
env:
  - OPENROUTER_API_KEY
categories: [assets, images, ai, generation]
---

# Image Generator — Protocolo Nano Banana (Felipe)

Esta skill NÃO é só "chamar a API". É **como o Felipe se relaciona com o Nano Banana** pra acertar
de forma confiável, sem queimar geração. Baseado nas práticas oficiais do Google (Gemini image /
Nano Banana Pro) + benchmark. Detalhe técnico e fontes em `[[nano_banana_prompt_engineering]]`.

## Trava automática (infalível)

O `generate.py` roda um **linter de prompt** (`prompt_lint.py`) em TODA geração — impossível
chamar a ferramenta sem as boas práticas serem checadas. Ele **BLOQUEIA** antes da API:
- **razão de escala em texto** na 1ª geração ("1/3 da bancada", "28% da altura") → o modelo ignora;
- **JSON cru** no `--prompt` → usar prosa.
E **avisa** termos de câmera que incham o produto (close-up/low-angle/macro/f1.8). Em modo `--edit`,
fração vira só aviso (ali é direção relativa). Override consciente: `--no-lint`.

## Qual API (17/09/2026)

Por padrao (`--api images`) a skill chama **`/images/generations`**, nao `/chat/completions`.
Motivo: so essa aceita tamanho. Gera em **2048x2048** e reduz pra **1200x1200**, o canvas
que os moldes do overlay exigem. O caminho antigo devolve 1024 e ignora `--size`; ele
continua valendo pra `--edit` e pra `--api chat`.

🔴 **A referencia so chega pelo parametro `input_references`.** Com o nome errado
(`image`, `image_urls`) a API **aceita, cobra e ignora a referencia em silencio** — sai
outro produto, sem erro nenhum. Ha trava embutida (confere `prompt_tokens`), mas quem
mexer aqui confere a IMAGEM, nao o codigo.

Modos: `test` · `production` (Nano Banana 2 Flash) · `pro` (Nano Banana Pro) ·
**`gpt` (GPT Image 2) — PADRAO desde 17/09/2026** (o padrao era `test`). No bake-off do 8L (`tests/motor-bakeoff/`) o `gpt` errou a
escala pela metade do `pro`. Nenhum acerta sozinho — medir continua obrigatorio.

## A regra de ouro: o PRODUTO nunca se conserta com `--edit`

Pedir "regere/edite pra corrigir o detalhe X do produto" é o maior erro: o Nano Banana **recalcula a
cena do zero** e regride o que já estava aprovado no produto (a "amnésia" = *edit-drift*; o slot 6
custou 9 iterações). Por isso a **arquitetura produto-travado (CLAUDE.md, 2026-06-23, DEFINITIVA)**:
o produto **NÃO é re-renderizado, é composição** — recorte fiel (PNG travado por hash) colado por
código sobre a cena.

**`--edit` serve SÓ pra FUNDO/CENÁRIO que não toca o produto** (trocar o ambiente, a luz, um prop do
fundo). NUNCA pra corrigir **escala, centro, cor, forma, partes ou acabamento do produto** — isso é
edit-drift garantido.

Como corrigir o PRODUTO, sem `--edit` (política por slot do CLAUDE.md):
- **Escala / centro / posição**: composição — `compose.py` cola o PNG travado no tamanho e lugar
  certos (fidelidade por hash, custo IA zero). É onde escala e centralização são resolvidas, não no
  modelo.
- **Cor / variação**: `--faithful` (recolor idêntico da base real) ou usar a base real da cor;
  produto travado por proveniência.
- **Forma / partes / desastre**: one-shot regenerado do hero fiel (SEM `--edit`), com gate de
  produto (`--lock`) + olho humano + `inox_cast`.

```bash
# 1) Cena base (uma vez)
python3 skills/image-ai-generator/scripts/generate.py --mode pro \
  --reference <base do produto> --output foto.jpg --prompt "<cena, linguagem natural>"

# 2) --edit SO pra mexer no fundo/cenario (o produto fica IDENTICO):
python3 .../generate.py --mode pro --edit --reference foto.jpg --output foto.jpg \
  --prompt "troque o fundo por um banheiro de piso de madeira clara, mantendo o produto igual"
python3 .../generate.py --mode pro --edit --reference foto.jpg --output foto.jpg \
  --prompt "deixe a luz do ambiente mais quente e suave, sem alterar o produto"

# 3) Escala/centro/cor do PRODUTO -> composicao (compose.py + PNG travado), NAO --edit.
```

**Regras do modo edição:** UMA mudança por chamada (nunca duas). Sempre `--reference` = a imagem
ATUAL. A mudança tem que ser SÓ de fundo/cenário. Se precisou mexer no produto, PARE o `--edit` e vá
pra composição ou one-shot — não insista editando.

## A 1ª geração: linguagem natural, NÃO JSON cru

O modelo entende **descrição em linguagem natural** muito melhor que um JSON rígido despejado (JSON
denso atrapalha a compreensão espacial). O `prompts/foto-NN.json` continua sendo o artefato de
auditoria, mas o texto enviado ao modelo (`--prompt`) é **prosa fluida** na ordem **6 fatores**:

1. **Sujeito** (hiper-específico): material, cor, partes — ex.: "lixeira de pedal 5L, corpo cilíndrico em aço inox prata neutro, tampa/aro/pedal/base em plástico branco".
2. **Ação/Estado**: tampa fechada/aberta, pedal em uso, etc.
3. **Cenário**: onde está (banheiro contemporâneo, piso de madeira clara, bancada de madeira).
4. **Estilo**: "fotografia comercial de e-commerce, hiper-realista, alta resolução".
5. **Composição/Iluminação**: enquadramento + luz (ver escala abaixo).
6. **Proporção**: 1:1 (Mercado Livre).

Na 1ª geração, foque em acertar **cena + produto + ângulo**. NÃO tente cravar escala e centro exatos
de uma vez — isso vem nas edições.

## Escala: razão em texto NÃO funciona — use linguagem de fotógrafo

O Nano Banana **não tem parâmetro de tamanho e ignora "1/3"** (vira palpite fraco; ele orbita ~metade
porque o viés é "produto = herói = grande"). Para controlar escala, em ordem de força:

1. **Referência com a escala já certa** (mais confiável): pré-compor o recorte do produto (BiRefNet)
   no tamanho px correto na cena e pedir só "reilumine/harmonize, mantenha tamanho e posição".
2. **Framing de fotógrafo**: "wide shot, câmera à altura dos olhos, ~2 m de distância, lente
   grande-angular". **EVITAR** "close-up / low-angle / macro / f1.8" → esses **incham** o produto.
3. **Forçar o objeto-âncora inteiro no quadro** (bancada do chão ao tampo) OU o inverso, a **fórmula
   "gabinete cortado"** (DECISOES.md): cortar o tampo fora do topo, lixeira baixa contra um gabinete
   que sobe pra fora do quadro — lê pequena mesmo grande no frame.
4. **Marcos comparativos** > frações: "chega só na altura do joelho / na gaveta de baixo do gabinete".
5. Se ainda ficou grande: **edição isolada** `--edit "deixe a lixeira menor, ~1/3 da bancada"`.

Lembrar a medida real (Almir): 5L 18×25 cm, 8L 18×34 cm; bancada ~90 cm → 5L é **ATÉ 1/3 e na real
~0,28** (bem pequena). MEDIR lixeira÷bancada (chão→tampo) em px, não "% do frame".

## Transferência de estilo por referência (consistência de catálogo)

Pra manter atmosfera/luz consistentes sem caçar palavras, **passe uma foto aprovada como molde de
estilo** (ex.: `_final/foto-08-lifestyle.jpg`, `_final/foto-02-antesdepois.jpg` — que o Almir
aprovou). Prompt: "use a atmosfera, iluminação e enquadramento da imagem de referência; aplique ao
produto anexado". Isso reduz drasticamente a tentativa-e-erro de descrever o ambiente.

## Recolor / fidelidade do produto

- Preferir a **base REAL da cor** (`tcd-produtos/<SKU_VARIACAO>/foto-01.jpg`). Recolorir uma base de
  OUTRA cor é OK **quando o objetivo é só pegar o ângulo certo** (ex.: usar a base preta porque ela
  está em 3/4 e a branca é frontal) — aí recolorir pra cor-herói.
- Template oficial: "change ONLY the finish/color to [...]; keep the exact shape, proportions, parts,
  lid, pedal unchanged". O `generate.py --faithful` reproduz idêntico aplicando só a edição descrita.

## Loop infalível (resumo operacional)

1. Escolher a base (real da cor; ou outra cor + recolor só pro ângulo 3/4).
2. **1ª geração** (`--mode pro`): prosa 6-fatores, framing de fotógrafo, foco em cena+produto+ângulo.
3. **Editar 1 coisa por vez** (`--edit`): escala → centro → cor → prop. Reusar a própria imagem.
4. Redimensionar pra **1200×1200**.
5. **Checklist antes de apresentar** (`[[feedback_checklist_imagem_antes_de_apresentar]]` +
   `qa_imagens.py`): dimensão, produto, eixo, dourado, escala medida, materiais, sem marca, sem texto.
6. Abrir no **Chrome dedicado** pro Almir ver.

## Modos do generate.py

- `--mode test` (`sourceful/riverflow-v2-fast`): layout barato.
- `--mode production` (`google/gemini-3.1-flash-image-preview`): Nano Banana 2 Flash.
- `--mode pro` (`google/gemini-3-pro-image`): **Nano Banana Pro** — muito mais fiel, usar pra cenas/lifestyle/capa.
- `--reference <img>`: contexto visual (produto/logo/molde de estilo).
- `--faithful`: reproduz a referência idêntica + aplica só a edição (recolor fiel).
- `--edit`: **edição só de FUNDO/CENÁRIO** — referência = imagem atual, prompt = UMA mudança que NÃO toca o produto (fundo/luz/prop). PROIBIDO pra corrigir escala/centro/cor/forma do produto (edit-drift) — isso é composição ou one-shot.

## Custo

**`--mode pro` (Nano Banana Pro) custa ~$0,136 por imagem (≈R$0,75)** — confirmado ao vivo via `usage.cost` do OpenRouter (não os ~$0,10 estimados). `--edit` custa o MESMO que gerar (manda imagem e recebe imagem). O `generate.py` loga o custo real por chamada e acumula em `_custos.csv` na pasta de saída. Implicação: **iterar por `--edit` e conferir antes de apresentar** (em vez de regerar 15×) economiza dinheiro de verdade — a saga da capa do 5L custou ~$5. Não gerar lote "de teste"; gerar 1 e iterar.
