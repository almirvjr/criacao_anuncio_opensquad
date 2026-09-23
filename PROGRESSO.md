# PROGRESSO

> Atualizado 2026-09-23. **Frentes:** (1) **8L (VIE_1067) TRAVADO numa decisão de método** — ver seção 0; (2) **ficha técnica dos anúncios no ar** (seção 5), parada esperando 4 decisões suas; (3) **Raio-X do anúncio** e (4) **entrar em catálogo sem oferta** — prontos e em uso (HISTORICO 09/09 e 15/09).

## 0. 🔴 O que trava o 8L hoje (23/09)
**O StorySelling deste projeto contradiz o prompt original que o Almir trouxe.** As 5 fotos ambientadas saíram tecnicamente corretas e foram reprovadas: "são iguais". Reescritas a partir do brief + templates, continuam longe do que ele quer.

No slot 2 (antes/depois) o template manda **mesma temperatura de cor nos dois lados** e **"não exagerar o ANTES"**; o prompt original do Almir manda **luz fria e azulada na esquerda contra quente na direita**, **duas paletas** e **lixeira de plástico barata** no lado ruim. São instruções opostas. Comparação completa em DECISOES 2026-09-17/23.

**PRÓXIMO PASSO: o Almir traz os prompts originais das outras imagens → comparar template a template ANTES de gerar qualquer coisa.** Provável que o StorySelling precise ser corrigido no projeto, não só um prompt.

## 1. Estado do 8L (VIE_1067)
- **Cor-herói PRETO**; brief conformado em `output/2026-06-26-conforme-8L/inteligencia/`; dims REAIS 18Ø×34 cm; SEM marca; foto 6 = sem balde interno.
- 🔴 **Referência oficial = `_master/master-preto-fechado-CORRIGIDO.jpg`.** A antiga estava esticada 12% (mostrava 2,26; o real é 1,89) e o modelo copiava fielmente um produto errado. ⚠️ **A 5L aprovada tem o mesmo defeito** (`foto-08` mede 1,78 contra 1,39) — decidir se refaz.
- **Capa `VIE_1067-PAI/capa-8L-preto.jpg`** (17/09): checklist verde, procedência em `_procedencia-capa.json`. Pendente de OK — e possivelmente a refazer junto com o resto quando o StorySelling for resolvido.
- v8 DESCARTADA (montagem + escala de 5L).

## 2. Regras de trabalho (Almir) — INFALÍVEIS
- **CONFERIR medindo, nunca afirmar** + checklist COMPLETO antes de apresentar + aprovar SEMPRE no Chrome.
- **Escala = altura da lixeira ÷ altura do móvel (chão→tampo, 90 cm), POR PRODUTO.** Verdade física: 5L = 0,27 · 8L = 0,38. **Faixa aceita no 8L: 0,36 a 0,48** (decisão do Almir em 22/09 olhando a imagem). Nunca abaixo do piso — vira cara de 5L.
- **FORMA do produto = altura ÷ largura do corpo: 8L = 1,89 · 5L = 1,39**, ±5%. O motor entrega ~2,05 e não cede; corrigir com `corrigir_forma.py` (achata a foto inteira).
- **Método:** gerar a cena ABERTA (móvel inteiro no quadro) → MEDIR → só então aproximar (`enquadrar_capa.py`). Aproximar não muda a relação de tamanho.
- **Luz NEUTRA com materiais quentes.** Luz quente doura o inox (gate `inox_cast` reprovou 3 de 5).
- **Pedal = tamanho FIXO**; dobradiça da tampa no MESMO eixo do pedal (atrás dele). ⚠️ Essa última **não é automatizável** — é relação 3D que a silhueta não resolve. Olho humano.
- **SEM MARCA** em foto, título e descrição.

## 3. Ferramentas de medida (construídas 17-22/09)
| Ferramenta | O que faz |
|---|---|
| `validators/juiz_escala.py` | forma + escala. APROVA / REPROVA / **NAO_MEDIDO** (recusa em vez de chutar) |
| `validators/peneirar.py` | roda os portões em N tentativas e escolhe a melhor de cada foto |
| `image-overlay/corrigir_forma.py` | achata a foto até o produto bater com o real |
| `image-overlay/enquadrar_capa.py` | aproxima e centraliza DEPOIS de medir |

⚠️ **O detector (BiRefNet) é pesado e derrubou a máquina 3 vezes em 22/09.** Rodar em blocos pequenos. Melhoria pendente: a peneira remede o que a correção de forma já mediu — gravar e reaproveitar.

## 4. Pendências
- **SUPABASE_SERVICE_ROLE** p/ subir ao bucket `tcd-produtos`.
- **⚠️ Código da squad sem commit desde julho** (o /save só commita os 5 docs raiz). Somam agora as 4 ferramentas novas. ⚠️ Repo PÚBLICO — conferir antes.
- **`ML Publicar`** (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito; ao ligar, tirar `pictures_compartilhadas` do nó `Montar Payload`. O webhook no `.env` **já está preenchido**.
- Juiz Visual: camada 1 entregue; falta a **camada 2** (juiz que enxerga — é onde cabe o alinhamento dobradiça-pedal) e as Peças B e C. Ver `PLANO-LOOP-JUIZ-VISUAL.md`.

## 5. Ficha técnica dos anúncios NO AR — `tools/auditoria_ficha/`
371 campos preenchidos em 146 anúncios (06-10/08). Nada alterou preço/fotos/estoque/variações.
**Esperando decisão do Almir:** (1) 6 anúncios com litros divergentes entre título e ficha — corrijo qual? (2) 5 travados no catálogo, só via "Sugerir correções" um a um; (3) 41 campos de vela — 1 cor por anúncio ou vazio? (4) 112 suspeitas (63 de caixa menor que o produto, mexe em frete; 49 de "Kit N" com ficha dizendo 1).
⚠️ Antes de qualquer lote: filtrar `catalog_listing=false` (catálogo responde 200 e IGNORA), rodar `validar_sugestoes.ps1`, comparar título antes/depois.
