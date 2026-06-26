---
name: image-ai-generator
description: >
  Generates and ITERATIVELY EDITS images via the Openrouter API using Nano Banana
  (Gemini image) models. Encodes the Nano Banana interaction protocol: natural-language
  first generation, then single isolated edits (never regenerate to fix one detail),
  photographic framing for scale control, and style/reference transfer.
description_pt-BR: >
  Gera e EDITA imagens de forma iterativa via API do Openrouter usando Nano Banana
  (Gemini image). Codifica o protocolo de interacao com o Nano Banana: 1a geracao em
  linguagem natural, depois edicoes isoladas (nunca regerar pra corrigir um detalhe),
  framing de fotografo pra controlar escala, e transferencia de estilo por referencia.
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

## A regra de ouro: EDITE, não regere

O maior erro é pedir "regere a imagem com o detalhe X corrigido". O modelo **recalcula a cena do
zero** e estraga o que já estava certo (a "amnésia"). Quando a cena/produto já estão bons e falta
ajustar UMA coisa (escala, centro, cor, um prop), use o **modo edição** (`--edit`): ele muda só
aquilo e preserva o resto.

```bash
# 1) Gera a cena base (uma vez)
python3 skills/image-ai-generator/scripts/generate.py --mode pro \
  --reference <base do produto> --output foto.jpg --prompt "<cena, linguagem natural>"

# 2) Trava e ajusta UMA coisa por vez, reusando a propria imagem como referencia:
python3 .../generate.py --mode pro --edit --reference foto.jpg --output foto.jpg \
  --prompt "deixe a lixeira visivelmente menor, chegando so na gaveta de baixo do gabinete"
python3 .../generate.py --mode pro --edit --reference foto.jpg --output foto.jpg \
  --prompt "centralize a lixeira no eixo horizontal do quadro"
```

**Regras do modo edição:** UMA mudança por chamada (nunca duas). Sempre `--reference` = a imagem
ATUAL. Se a edição estragar algo, volte a editar (não regere a cena). Centralizar e redimensionar
são MUITO mais confiáveis como edição do que num one-shot.

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
- `--edit`: **edição iterativa** — referência = imagem atual, prompt = UMA mudança, preserva o resto.

## Custo

**`--mode pro` (Nano Banana Pro) custa ~$0,136 por imagem (≈R$0,75)** — confirmado ao vivo via `usage.cost` do OpenRouter (não os ~$0,10 estimados). `--edit` custa o MESMO que gerar (manda imagem e recebe imagem). O `generate.py` loga o custo real por chamada e acumula em `_custos.csv` na pasta de saída. Implicação: **iterar por `--edit` e conferir antes de apresentar** (em vez de regerar 15×) economiza dinheiro de verdade — a saga da capa do 5L custou ~$5. Não gerar lote "de teste"; gerar 1 e iterar.
