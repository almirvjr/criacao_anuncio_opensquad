---
type: checkpoint
---

# Step 04b: Checkpoint de Dados — Revisão de Atributos e Dimensões do Produto

## Apresentar ao usuário

Ler duas fontes:
1. `squads/ml-anuncios/output/curadoria/dossies.json` — dossiê do Caio (step-02) com o mapa `dados_produto` inicial (atributos vindos de `descricao_complementar` com `status: "ok"` e pendentes com `status: "pendente"`).
2. `squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml` — brief da Helena (step-04) com o `dados_produto` enriquecido (atributos antes `pendente` que a Helena resolveu ou marcou como `divergente` a partir dos concorrentes), mais as listas `pendencias[]` e `divergencias[]`.

Para cada anúncio do lote, consolidar as informações das duas fontes e verificar o estado final do campo `dados_produto`.

**GATE DURO — Brief StorySelling válido (Fase 1 da blindagem):** antes de qualquer auto-aprovação, rodar a trava do brief para CADA anúncio do lote:

```
python squads/ml-anuncios/pipeline/validators/validar_brief.py \
  squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml --sem-fotos
```

(o script auto-descobre o `_raw/` irmão para verificar as âncoras de review). Se **qualquer** brief sair com código diferente de 0, o checkpoint **NÃO pode auto-aprovar** — apresentar ao Almir a lista de erros do(s) brief(s) reprovado(s) e retornar ao step-04 para a Helena corrigir. A trava cobre: `limitacoes[]` declaradas, e toda evidência citada existindo de fato no texto bruto dos concorrentes (mata review inventada/parafraseada).

**Medidas (desde 07/10/2026, esteira sem fotos):** peso e medida da **caixa** vêm da planilha de cubagem (`tiny_to_esteira --cubagem`) e vão para o frete. Medida do **produto** (`dimensoes_produto`) é opcional: serve à ficha e à descrição quando existe, e **não bloqueia** — o gate duro de dimensões existia por causa da foto técnica, que saiu da esteira.

**Regra de auto-aprovação:** se TODOS os anúncios do lote (a) passarem na trava do brief acima com código 0, (b) não tiverem nenhum atributo `pendente` ou `divergente`e (c) tiverem peso e caixa preenchidos em `anuncios-entrada.json` (vindos da cubagem), o checkpoint passa **automaticamente sem interagir com o usuário**. Registrar a nota de auto-aprovação no dossiê e avançar para o step-05.

Nos demais casos (qualquer pendência, divergência ou anúncio sem peso/caixa da cubagem), apresentar ao Almir o relatório abaixo.

---

### Formato de apresentação (por anúncio com pendências)

```
=== TCD-LXI12 — Lixeira Inox 12L ===

⚠ sem_concorrente: true  (sem referência de preço/dimensão em concorrentes)

Atributos PENDENTES (sem valor):
  • material          — nenhuma fonte encontrou este dado
  • caracteristicas   — campo vazio no dossiê

Atributos DIVERGENTES (fontes discordam):
  • dimensoes_produto.altura
      Caio (descricao_complementar): 38 cm
      Helena (concorrente-MLB1234):  40 cm  → https://mercadolivre.com.br/...
      Helena (concorrente-MLB5678):  38 cm  → https://mercadolivre.com.br/...

  • dimensoes_produto.largura
      Caio (descricao_complementar): 20 cm
      Helena (concorrente-MLB1234):  22 cm  → https://mercadolivre.com.br/...

ℹ dimensoes_produto.altura → status: "pendente" (opcional — sem ela a descrição não cita altura)
⚠ INFO: dimensoes_produto.profundidade → status: "nao_aplicavel" (opcional — não bloqueia)
```

Sempre listar no fim da apresentação:
- Total de anúncios no lote.
- Total com `sem_concorrente: true`.
- Total de atributos pendentes / divergentes no lote.
- Quais anúncios estão sem peso/caixa da cubagem (esses bloqueiam: o frete sai errado).

---

## Decisão esperada (por anúncio com pendências)

Para cada atributo `pendente` ou `divergente` apresentado, o Almir pode:

1. **Confirmar um valor da lista divergente** — informar qual fonte escolhe (ex: "TCD-LXI12 altura: 38 cm").
2. **Fornecer o valor faltante** — digitar o valor para atributo `pendente` (ex: "TCD-LXI12 profundidade: 15 cm").
3. **Manter como divergente / aceitar risco** — o atributo permanece com `status: "divergente"` e a Renata recebe nota de cautela.

**O Almir NÃO pode avançar com anúncio sem peso e caixa** (vêm da planilha de cubagem; se o SKU não estiver lá, pedir os valores ao Almir). Medida do produto pendente não bloqueia.

---

## Registrar resoluções

Ao concluir o checkpoint, gravar o `dados_produto` final consolidado (Caio + enriquecimento Helena + resoluções do Almir) de volta em `squads/ml-anuncios/output/curadoria/dossies.json` — **fonte única de verdade** que a Renata (step-05) vai ler. A Renata **não** leem o brief da Helena diretamente para obter `dados_produto`; eles leem `dossies.json` após este checkpoint.

Para atributos que a Helena enriqueceu com `status: "ok"` (vindos de concorrentes) e que ainda não constam em `dossies.json` com esse status, copiar o valor do brief para `dossies.json` mantendo `fonte: "concorrente"` e `permalink` de origem.

Para cada atributo resolvido pelo Almir (pendentes ou divergentes que o Almir decidiu), atualizar diretamente em `squads/ml-anuncios/output/curadoria/dossies.json`, no campo `dados_produto` do anúncio correspondente:

```json
{
  "valor": "<valor informado ou escolhido>",
  "fonte": "almir",
  "status": "ok",
  "permalink": null,
  "valores_divergentes": []
}
```

Para atributos aceitos como `divergente`, apenas registrar a escolha de `"manter_divergente": true` e não alterar `status`.

Para o checkpoint em si, gravar no dossiê o bloco de auditoria dentro de cada anúncio resolvido:

```json
"checkpoint_dados": {
  "aprovado_em": "<ISO timestamp>",
  "aprovado_por": "checkpoint humano",
  "auto_aprovado": false,
  "pendencias_resolvidas": ["material", "dimensoes_produto.profundidade"],
  "divergencias_resolvidas": ["dimensoes_produto.altura"],
  "divergencias_mantidas": []
}
```

Quando auto-aprovado:

```json
"checkpoint_dados": {
  "aprovado_em": "<ISO timestamp>",
  "aprovado_por": "checkpoint humano",
  "auto_aprovado": true,
  "pendencias_resolvidas": [],
  "divergencias_resolvidas": [],
  "divergencias_mantidas": []
}
```

---

## Output Format

Após gravar as resoluções, emitir resumo para o log do pipeline:

```yaml
checkpoint_dados:
  total_anuncios: <int>
  auto_aprovados: <int>
  revisados_pelo_almir: <int>
  atributos_resolvidos: <int>
  divergencias_mantidas: <int>
  anuncios_bloqueados_antes: <int>   # anúncios sem peso/caixa ao iniciar
  gate_caixa: "ok"                   # peso + caixa (cubagem) presentes em todos os anúncios
  gate_brief_storyselling: "ok"      # sempre "ok" ao concluir (validar_brief.py --sem-fotos código 0 em todos os anúncios)
```

---

## Veto Conditions

1. **GATE DURO — Sem peso ou caixa:** anúncio sem `peso_bruto_kg` ou com `dim_embalagem_cm` zerada em `anuncios-entrada.json` — o frete do ML sai errado. Bloquear até a cubagem (ou o Almir) fornecer.
1b. **GATE DURO — Brief StorySelling reprovado:** qualquer anúncio cujo `validar_brief.py` saia com código != 0 (`limitacoes[]` ausente, diagnóstico incompleto, ou evidência de review inexistente no `_raw/`) bloqueia a auto-aprovação e o avanço. Retornar ao step-04 para a Helena corrigir. Nenhum brief vai para a Renata sem `gate_brief_storyselling: "ok"`.
2. **Dossiê ausente ou vazio:** `dossies.json` não existe ou não contém nenhum anúncio — não apresentar checkpoint, retornar para step-04.
3. **Campo `dados_produto` ausente no dossiê:** a Helena não consolidou os atributos estruturados — retornar ao step-04 para reprocessamento.
4. **Avanço forçado sem caixa:** executar o step-05 sem que este checkpoint tenha gravado `"gate_caixa": "ok"` é veto automático.

---

## Quality Criteria

- [ ] Todos os anúncios do lote foram inspecionados (zero anúncios ignorados silenciosamente).
- [ ] Todo atributo com `status: "pendente"` ou `status: "divergente"` foi apresentado ao Almir ou marcado como sem pendências.
- [ ] Peso e caixa (cubagem) presentes em 100% dos anúncios ao sair do checkpoint.
- [ ] Todos os valores resolvidos pelo Almir foram gravados com `"fonte": "almir"` no `dossies.json`.
- [ ] O bloco `checkpoint_dados` foi gravado em cada anúncio do lote (inclusive nos auto-aprovados).
- [ ] O `gate_caixa: "ok"` foi emitido no resumo de saída do checkpoint.
- [ ] O `validar_brief.py` saiu com código 0 para 100% dos anúncios do lote e o `gate_brief_storyselling: "ok"` foi emitido (nenhum brief com `limitacoes[]` ausente ou review inventada).
- [ ] Atributos aceitos como `divergente` estão documentados em `divergencias_mantidas` para ciência da Renata.
