# Plano de Blindagem do Método StorySelling (Helena ↔ Felipe)

> Objetivo: garantir que TODO anúncio novo siga o método StorySelling de ponta a ponta
> — da análise dos concorrentes (Helena) até o prompt no Nano Banana Pro (Felipe) —
> **sem depender de o agente lembrar**. Cada regra do método vira trava de máquina.
> Criado: 2026-06-20. Decisão do Almir: tornar o processo infalível.

## Princípio único

Nada de regra que vive só em prosa ("o agente deve..."). Cada regra crítica precisa virar:
- **(a)** campo OBRIGATÓRIO num schema que **trava** se faltar, ou
- **(b)** um **script** que confere e **bloqueia** o avanço.

Analogia: hoje o método é um "manual que pedimos pro funcionário seguir". O plano transforma
em "esteira que não deixa a peça passar pra próxima etapa sem o carimbo".

---

## Diagnóstico do que NÃO é travado hoje (origem do problema)

1. Brief da Helena não tem schema → ninguém valida se os 10 slots estão completos e ancorados.
2. Citação de review é auto-declarada → a Helena pode citar review que não existe; ninguém confere no `_raw/`.
3. Não existe campo de LIMITAÇÕES do produto → "sem balde interno" só aparece se a Helena lembrar.
4. Não existe guarda anti-claim-falso → o Felipe copia headline/selo da Helena sem checar se o produto tem aquilo.
5. **O validador (Vinícius) nunca olha as imagens** — lê o `metadata.yaml` que o próprio Felipe escreveu. (maior buraco)
6. Gate de cor do inox (`inox_cast.py`) não bloqueia: marca "falha_cor_dourada" e segue.
7. Prompt do Felipe não é verificado contra o template → ele pode improvisar e ninguém percebe.
8. Não existe slot de prova social no conjunto de templates.
9. O checkpoint de dados (step-04b) auto-aprova em silêncio se as dimensões estiverem ok — o brief StorySelling nunca é revisado.

---

## FASE 1 — Travar a ENTRADA: schema do brief da Helena ✅ CONCLUÍDA (2026-06-21)
**Entregue:** `validators/validar_brief.py` (trava determinística) + `validators/brief.schema.json` (contrato) + `validators/tests/test_validar_brief.py` (15 testes, todos passando). Costurado em step-04 (passo 6b limitações + passo 11 trava obrigatória + vetos 12/13), step-04b (gate `gate_brief_storyselling` + bloqueio da auto-aprovação) e no agente da Helena (princípio 5 + Always Do 8). Validado no brief real do 5L: reprovou por `limitacoes` ausente + 1 review parafraseada — exatamente os 2 buracos que tinham ido pra produção.

**Problema:** brief incompleto/inventado passa.
**Trava:**
- Criar `pipeline/data/brief.schema.json` com campos OBRIGATÓRIOS:
  - os 10 slots, cada um com `objecao_alvo`, escada `feature→logico→emocional`, `objetivo_meclabs`, `headline`.
  - **novo campo obrigatório `limitacoes[]`** — puxado de `dados_produto` (ex.: "sem balde interno", "haste de nylon").
  - cada `ansiedade`/afirmação do diagnóstico com `evidencia` (trecho literal de review).
- Script `validar_brief.py` roda no fim do step-04: **rejeita** brief com slot vazio, sem `limitacoes`, ou afirmação sem evidência.
- **Verificador de âncora:** o script confere se cada trecho de review citado EXISTE em `_raw/{mlb_id}.json`. Citação que não bate = bloqueia. (mata review inventada)

**Resultado:** a Helena não consegue entregar brief raso, sem limitação registrada, ou com prova inventada.

## FASE 2 — Guarda anti-claim-falso (a trava do "balde") ✅ CONCLUÍDA (2026-06-21)
**Entregue:** `validators/validar_claims.py` + 11 testes (26 no total, todos passando). Deriva os "termos policiados" das `limitacoes[]`, varre todo overlay dos 10 slots, **bloqueia claim de feature inexistente** (distingue "com balde" de "sem balde" por negação) e **exige a declaração da limitação** na `disclosure_foto`. Costurado em step-07 (gate 3b + veto 6c), step-04 (passo 11 roda os 2 validadores) e agente Felipe (princípio 1b). Template 7 corrigido (linha 452): recorte favorável OK, mas ausência de feature nunca vira claim — limitação declarada nas fotos 5/9. Demo real: brief 5L afirmando "balde interno removível" → 2 bloqueios (CLAIM_FALSO + LIMITACAO_NAO_DECLARADA).

**Problema:** o Felipe pode estampar feature que o produto não tem.
**Trava:**
- Do `dados_produto` + `limitacoes[]`, o sistema monta uma **lista do que PODE e do que NÃO PODE afirmar**.
- Script confere TODO texto de overlay (headline/badge/selo) contra essa lista. Afirmar feature inexistente (ex.: "balde removível" num produto sem balde) = **bloqueia**.
- **Inverter a regra ruim do template 7** ("esconder ponto fraco") → transparência da limitação vira OBRIGATÓRIA (foto 5/9).

**Resultado:** impossível publicar claim falso. Limitação vira selo de transparência, não buraco escondido.

## FASE 3 — Prender o prompt do Felipe ao template ✅ CONCLUÍDA (2026-06-21)
**Entregue:** `validators/validar_prompts.py` + 6 testes (47 no total, todos passando). Reusa `SLOTS_CANONICOS` (fonte única). Reprova `{{placeholder}}` não preenchido, `nome` fora da função canônica do slot, ou slot fixo faltando. Costurado em step-07 (passo 7a autocheck) + agente Felipe (princípio 5b).

**Problema:** o Felipe pode improvisar o prompt e ignorar o template cinematográfico.
**Trava:**
- Cada `prompts/foto-NN.json` é gerado preenchendo o template parametrizado de `photo-templates.md`.
- Script confere: todos os `{{placeholders}}` preenchidos + slot N corresponde à função N.
- Template não preenchido corretamente = não gera.

**Resultado:** o Felipe não free-forma; o prompt sempre nasce do template certo.

## FASE 4 — QA que OLHA a imagem (fecha o maior buraco) ✅ CONCLUÍDA (2026-06-21)
**Entregue:** `validators/qa_imagens.py` (gate determinístico) + 11 testes (37 no total, todos passando). Abre cada JPG e trava: **dimensão 1200×1200 exata**, **produto presente** (via `cutout.mask_bbox`), e **inox dourado BLOQUEIA** (re-roda `inox_cast.py` — acabou o "marca falha e segue (Vinicius decide)"). Reaproveita os scripts existentes (`cutout.py` BiRefNet + `inox_cast.py`). Costurado em: step-07 (passo 7b autocheck do Felipe — regenera dourado antes de entregar), step-08 (revisão visual em 2 partes: gate determinístico + Vinicius ABRE os JPGs pra checar marca-no-pixel/escala/materiais/slot — veto 4b/4c), agente Vinícius (checklist visual reescrito: abre JPG, não metadata; "mínimo 1200" → "exata"). Escala fica como check visual (lixeira÷bancada ≈1/3), não bbox — respeita a régua de vocês.

**Validado ao vivo (2026-06-21):** rodado no `_final` real do 5L → reprovou (exit 1). Pegou **3 fotos douradas que estavam aprovadas e live** (capa-cinza, capa-preto, foto-05-clareza) que a revisão por metadata tinha deixado passar. O gate é objetivo: discordou do olho humano nas duas direções (liberou 03/04/09 que pareciam douradas mas o metal estava ok; pegou as que o humano aprovou). Limitação conhecida: dourado pode dar falso-positivo quando a máscara pega objeto não-metálico dominante (caixa de papelão na foto-05) → resolvido com override estreito documentado pelo Vinícius (abre a imagem e confirma). **Nota operacional:** `qa_imagens.py` é pesado (~7,5 GB, BiRefNet); como `cutout` cacheia a sessão, rodar a pasta inteira num processo só carrega o modelo 1×. Otimização futura: lote único em vez de processo por imagem.

**Problema:** o validador nunca vê os JPGs.
**Trava — o gate de QA passa a abrir as imagens, não o metadata:**
- Re-roda `inox_cast.py` em toda foto de inox → **dourado BLOQUEIA** (acabou o "segue e Vinícius decide").
- Roda `cutout.py` pra confirmar produto presente + escala ~1/3.
- OCR/visão pra detectar marca/logo NA IMAGEM (SEM MARCA no pixel, não só no overlay).
- Visão pra confirmar que cada foto bate com a função do slot e com a headline.
- Imagem que falha qualquer item = **não publica**, volta pro Felipe.

**Resultado:** dourado, marca, produto distorcido ou foto fora do slot não escapam mais.

## FASE 5 — Upgrades do MÉTODO (conteúdo, vindos do referência) ✅ CONCLUÍDA (2026-06-21)
**Decisão Almir:** hierarquia **Equilibrado**. Nova ordem propagada por TUDO que a codifica (validador `SLOTS_CANONICOS` + 4 testes do slot 11, `brief.schema.json`, `storyselling-framework.md` §6, `photo-templates.md` 12 templates, step-04, agentes Helena/Felipe). 41 testes passando. Itens entregues:
- **Ritmo emocional:** `LIFESTYLE_EMOCIONAL` novo no slot 5 (respiro entre os racionais); slots 6=Clareza, 7=Detalhe Técnico (funde os 2 antigos), durabilidade absorvida no slot 4.
- **Prova social:** slot 11 `PROVA_SOCIAL` opcional + **trava anti-fabricação** (só com `reviews_proprios_confirmados: true`; sem isso o validador reprova). Template dormente.
- **Capa:** template 1 fixado **ambientalizado com produto ao centro, SEM texto** (decisão Almir).
- **Slot 10:** template proíbe assinatura de agência (inverso do rodapé Himmel do referência) — só CTA genérico, SEM MARCA.
- **Foto 9:** template + validador exigem os selos de transparência das `limitacoes[]` (disclosure_foto:9).
- Exemplo de brief da Helena reescrito pra nova hierarquia + `limitacoes[]` (era um modelo que reprovaria na própria trava).

## FASE 5 (descrição original) — Upgrades do MÉTODO (conteúdo, vindos do referência)
- **Ritmo emocional:** inserir um 2º respiro lifestyle no meio do bloco racional (hoje são 5 racionais seguidas). Atualizar a hierarquia das 10 fotos + templates.
- **Prova social:** criar template novo (review real). **Gated:** só ativa com avaliações REAIS nossas; sem reviews, fica dormante (nunca fabricar nem usar review de concorrente).
- **Capa:** mantém **ambientalizada com produto ao centro** (decisão do Almir 20/06). Fixar isso no template 1 pra não derivar pra fundo branco.
- **Slot 10 (fechamento):** CTA genérico, **SEM MARCA** e sem assinatura de agência — o inverso do que o referência (Himmel) faz no rodapé.
- **Foto 9:** selos de transparência obrigatórios ("compatível com saco comum", "sem balde interno") quando `limitacoes[]` tiver isso.

## FASE 6 — Checkpoints viram trava real ✅ CONCLUÍDA (2026-06-21)
- `step-04b` já não auto-aprova o conteúdo StorySelling em silêncio (Fase 1: exige `gate_brief_storyselling: "ok"`, não só dimensões).
- `pipeline.yaml`: seção `gates:` registra as 4 travas (brief, anti-claim, prompt, qa-imagem) como BLOQUEANTES, com `roda_em` e o que cada uma bloqueia. A hierarquia canônica aponta para a fonte única (`SLOTS_CANONICOS`).

---

## Ordem recomendada de execução (maior risco fechado primeiro)
1. **Fase 1** (schema + limitações + âncora) — base de tudo; sem `limitacoes[]` as outras fases não têm de onde puxar.
2. **Fase 2** (anti-claim-falso) — fecha exatamente o risco que originou esse plano (o balde).
3. **Fase 4** (QA que olha a imagem) — fecha o maior buraco estrutural; conserta dourado/marca/distorção.
4. **Fase 5** (upgrades do método) — ritmo, prova social, transparência, slot 10.
5. **Fase 3 + Fase 6** (template-binding + checkpoints) — aperto final.

## FASE 7 — Geração infalível no Nano Banana ✅ CONCLUÍDA (2026-06-22)
**Problema:** mesmo com brief/QA blindados, a GERAÇÃO em si era tentativa-e-erro (15 capas no escuro) porque os prompts brigavam com o modelo (razão de escala em texto, JSON cru, regerar pra corrigir 1 detalhe → "amnésia").
**Entregue:**
- **`generate.py --edit`**: edição iterativa (muda 1 coisa, preserva o resto) — destrava escala/centro/proporção sem regerar. Validado ao vivo (capa 5L fechada 100% por edição).
- **`prompt_lint.py` + `validar_prompt_nano.py`** (gate `prompt_nano_banana`, fase 5 do pipeline.yaml) + **12 testes** (61 no total): roda em TODA geração dentro do `generate.py` (impossível burlar) e **BLOQUEIA antes da API** razão de escala na 1ª geração + JSON cru; avisa close-up/low-angle/macro. Override `--no-lint`.
- **SKILL.md v2.0** do `image-ai-generator`: protocolo Nano Banana (editar≠regerar, prosa não-JSON, framing não-razão, transferência de estilo, recolor fiel). Costurado em Felipe (princípio 2b) + step-07.
- Base de pesquisa: `[[nano_banana_prompt_engineering]]` (fontes oficiais Google + benchmark).

## Como fica a régua mental (depois do plano)
- Helena: "não consigo entregar brief sem 10 slots ancorados em review real + limitações declaradas."
- Felipe: "não consigo gerar prompt fora do template, nem estampar claim que o produto não tem."
- QA: "não deixo publicar imagem dourada, com marca, distorcida ou fora do slot."
- Tudo verificado por máquina, não por memória.
