# Plano: Juiz Visual + fechar o loop (loop engineering sobre o Opensquad)

> Criado em 2026-07-12. Para implementar em próxima sessão.
> Origem: estudo dos 4 artigos do Addy Osmani sobre agentic engineering (loop
> engineering, code review, agência×orquestração, outer loop/accountability).

## Contexto / diagnóstico (já fechado nesta sessão)

O Opensquad da squad `ml-anuncios` já é ~85% um sistema de loop engineering:
- **Maker ≠ checker** já existe: Felipe (step-07 gera) → Vinícius (step-08 confere).
- **Veredito automático já roda**: `pipeline/validators/qa_imagens.py` abre cada JPG
  e reprova dimensão, produto ausente/distorcido, **eixo**, **inox dourado** e
  **procedência** (sha256 do produto travado).
- **Loops de auto-correção já embutidos** no `_opensquad/core/runner.pipeline.md`:
  retry de output vazio, veto (2 tentativas), review loop (`on_reject`), e o
  Felipe re-gera inox dourado sozinho até passar.
- **Estado + histórico**: `state.json` (painel) + `_memory/runs.md`.

**Não reconstruir nada.** Faltam fechar só 2 vazamentos que puxam o Almir de volta:

### Vazamento nº 1 — veredito ESTÉTICO entregue ao olho humano
`step-08-revisao.md` passo (ii): Vinícius abre cada JPG e confere **a olho** o que
a máquina não mede: **escala lixeira÷bancada ≈1/3, materiais corretos, foto bate
com a função do slot, sem marca no pixel**. Na prática esse "olho" é o Almir.
→ É a "conferência atrás de conferência". (Artigo 3: autonomia segue verificação;
o que não é mensurável, prende.)

### Vazamento nº 2 — checkpoints obrigatórios
`runner.pipeline.md`: "Nunca continue além de um checkpoint sem input do usuário."
`SKILL.md`: "SEMPRE apresente os checkpoints — nunca pule." O pipeline para e chama
o Almir em pontos fixos, independentemente de tudo estar verde.
→ (Artigo 4: quer humano *sobre* o loop, não *dentro*.)

## Peça A — Juiz Visual (o desbloqueio; implementar PRIMEIRO)

Objetivo: transformar a inspeção a olho do Vinícius (step-08 ii) num veredito
automático que o Almir só **amostra**. Encaixa no lugar exato do passo (ii); não
mexe no resto do pipeline.

**Camada 1 — determinística (estende `qa_imagens.py`, que já calcula o bbox do
produto via BiRefNet):**
- `check_escala`: comparar altura da caixa do produto com o quadro/superfície.
  Parte é geometria barata; achar a "bancada" pode cair na Camada 2. Decidir
  item a item na calibração.
- Custo zero, offline. Só amplia arquivo existente.

**Camada 2 — juiz de visão (`juiz_visual.py`, novo):**
- Manda cada JPG a um modelo que ENXERGA (Gemini 3 Pro / Claude via OpenRouter —
  `OPENROUTER_API_KEY` do `.env`). Aqui o modelo JULGA, não gera (Nano Banana
  segue só gerando).
- Régua = checklist de `squads/ml-anuncios/_memory/memories.md` (materiais,
  aba-pedal, sem marca, escala) + função esperada do slot (do brief da Helena).
- Saída estruturada por foto: `{materiais:{ok,motivo}, slot_fit:{ok,motivo},
  sem_marca:{ok,motivo}, confianca:0-1}`.

**Saída consolidada:** `veredito_visual.json` por SKU, alimenta o parecer do
Vinícius. Carrega a regra de escalonamento:
- Tudo passou + confiança alta → aprova sozinho → fila "pronto pra amostra"
  (Almir amostra ~1 em 4).
- Qualquer reprova OU confiança baixa → escala SÓ aquela foto pro Almir, com
  motivo escrito + imagem aberta. E o motivo estruturado volta pro Felipe re-gerar.

**O que continua do Almir (certo que continue — artigo 4):** a chamada de gosto
puro ("essa cena SENTE Terra Casa Decor?"). Escala sempre, mas sobre poucas fotos.

## Passo que compra confiança — CALIBRAR ANTES de plugar (artigo 2: "meça na sua base")

Rodar o juiz contra o **5L (FECHADO)** — fotos que o Almir já aprovou/reprovou —
e ajustar régua + corte de confiança até o juiz CONCORDAR com os vereditos
passados. Só depois plugar no step-08. Sem isso, o Almir reconfere tudo e não
ganhamos nada (memória: "nunca apresentar imagem sem checklist antes").

## Ordem de execução (próxima sessão)

1. Ler `squads/ml-anuncios/_memory/memories.md` (checklist completo) e localizar
   as imagens do **5L fechado**. ⚠️ QUESTÃO ABERTA: onde ficaram as fotos do 5L
   aprovadas? Procurar em `output/` e backups; se não achar, PEDIR AO ALMIR.
2. Escrever v1 do `juiz_visual.py` (Camada 2) + estender `qa_imagens.py` (Camada 1).
3. Rodar nas fotos do 5L e comparar com os vereditos conhecidos → mostrar taxa
   de acerto ao Almir.
4. Ajustar régua/threshold até concordar.
5. SÓ ENTÃO plugar no step-08 (substituir/aumentar o passo "(ii) inspeção visual").

## Depois (Peças B e C — só após A estar confiável)

- **Peça B — heartbeat/fila externa**: driver que pega uma fila de SKUs a fazer,
  roda o pipeline por SKU com teto de tentativas/custo, e entrega ao Almir só a
  fila-pronta-pra-amostra + os travados. (Artigo 1, bloco "automações".)
- **Peça C — virar a chave dos checkpoints**: de "sempre pergunta" para "segue
  sozinho quando a evidência passa; só pergunta em incerteza/risco alto".
  (Artigo 4: humano *sobre* o loop.)

## Referências no repo
- `_opensquad/core/runner.pipeline.md` — motor do pipeline (retries, vetos, review loops).
- `squads/ml-anuncios/pipeline/steps/step-07-fotos.md` / `step-08-revisao.md`.
- `squads/ml-anuncios/pipeline/validators/qa_imagens.py` — veredito determinístico atual.
- `squads/ml-anuncios/agents/vinicius-validador.agent.md` / `felipe-fotos.agent.md`.
- `CLAUDE.md` seção "Modelo de IA para imagens" (produto-travado, inox_cast).
