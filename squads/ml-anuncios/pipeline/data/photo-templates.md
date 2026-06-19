# Photo Templates — JSON Cinematográficos para Felipe Fotos

10 templates JSON parametrizados para Felipe Fotos consumir. Cada template é a estrutura base de um slot da hierarquia psicológica. Felipe substitui os placeholders `{{...}}` por valores vindos do `strategic-brief.yaml` da Helena.

## Convenções

- `{{slot}}` — placeholder obrigatório.
- `{{slot|default}}` — placeholder com valor padrão se vazio.
- Bloco `produto` é fixo: sempre `"USE A IMAGEM ANEXADA — não altere o produto, apenas cenário e iluminação"`.
- `formato` é sempre `"1:1 marketplace Mercado Livre"`.
- **`dimensao` é sempre `"1200x1200 px exatos"`** (regra global do projeto — não usar outras dimensões).
- `qualidade` é sempre `"ultra realista 8k"`.
- Paleta Terra Casa Decor: `["branco quente", "bege sofisticado", "madeira clara", "verde natural leve", "prata escovado quando aplicável"]`.

## Tamanho padrão fixo

**Todos os 10 templates abaixo produzem imagem 1200×1200 px exatos.** Quando o Felipe chamar `image-ai-generator`, deve solicitar saída em 1200×1200 e validar a dimensão antes de salvar. Se o Gemini Nano Banana retornar dimensão diferente (acontece eventualmente), redimensionar/recortar para 1200×1200 mantendo o produto centralizado.

## Modelo de IA

Todos os templates são otimizados para **Gemini 2.5 Flash Image (Nano Banana)** em modo image-to-image. Felipe sempre anexa a `foto_base_url` do dossiê como imagem de referência.

---

## TEMPLATE 1 — CAPA PURPLE COW

```json
{
  "imagem": 1,
  "nome": "CAPA_PURPLE_COW",
  "objetivo_meclabs": "+m+v",
  "headline": "{{headline_capa}}",
  "subheadline": "{{subheadline_capa|null}}",
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO — NÃO ALTERE O PRODUTO, apenas cenário e iluminação.",
    "estilo_visual": "fotografia de produto premium hero shot estilo capa de marketplace líder",
    "composicao": "produto gigante centralizado no frame, ocupando 70% da área visual, fundo limpo dramático",
    "cenario": {
      "fundo": "branco puro com sombra suave radial para destacar o produto",
      "estilo": "clean, sofisticado, alta legibilidade em thumbnail"
    },
    "produto": {
      "posicao": "centro do frame, hero shot",
      "destaque": "produto totalmente nítido e dominante",
      "visibilidade": "100% visível, todas as features principais aparentes"
    },
    "iluminacao": {
      "tipo": "studio light premium com reflexo suave",
      "efeito": "produto parecer aspiracional e desejável",
      "direcao": "frontal superior, leve key light lateral"
    },
    "camera": {
      "lente": "85mm",
      "angulo": "frontal levemente abaixo (hero angle)",
      "foco": "produto ultra sharp",
      "profundidade": "fundo levemente desfocado"
    },
    "paleta_cores": ["branco quente", "bege sofisticado", "{{cor_produto}}"],
    "elementos_graficos": [],
    "film_grain": "não",
    "sensacao_emocional": ["{{emocao_alvo|desejo}}", "modernidade", "sofisticação acessível"],
    "direcao_de_arte": [
      "o produto precisa parar o scroll em menos de 1 segundo",
      "headline aparece em overlay pós-produção, deixar área superior ou inferior limpa",
      "evitar elementos competindo com o produto"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "neutro",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_capa`, `subheadline_capa`, `cor_produto`, `emocao_alvo`.

**Overlay pós-produção:** `headline_capa` (grande, top ou bottom), `subheadline_capa` (menor, abaixo da headline).

---

## TEMPLATE 2 — ANTES vs DEPOIS

```json
{
  "imagem": 2,
  "nome": "ANTES_DEPOIS",
  "objetivo_meclabs": "+v-a",
  "headline": "{{headline_transformacao|Um detalhe muda todo o ambiente}}",
  "subheadline": "{{subheadline_transformacao|null}}",
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO no lado DIREITO da composição. No lado ESQUERDO, mostre o mesmo ambiente SEM o produto (cenário antes).",
    "estilo_visual": "fotografia comparativa lifestyle split-screen",
    "composicao": "frame dividido 50/50 verticalmente: esquerda = ambiente sem produto (antes), direita = mesmo ambiente com o produto da imagem anexada (depois)",
    "cenario": {
      "antes": "{{ambiente_antes|ambiente residencial brasileiro comum, simples, levemente desorganizado}}",
      "depois": "{{ambiente_depois|mesmo ambiente, agora com o produto da imagem anexada integrado de forma harmoniosa}}",
      "estilo": "transformação visível mas crível, sem exagero artificial"
    },
    "produto": {
      "posicao": "lado direito do frame, integrado naturalmente ao ambiente",
      "destaque": "produto visível mas como elemento de ambiente, não em close",
      "visibilidade": "produto identificável a 2 segundos de olhar"
    },
    "iluminacao": {
      "tipo": "luz natural diurna brasileira",
      "efeito": "antes e depois com mesma temperatura de cor para a comparação ser justa",
      "direcao": "luz lateral suave de janela"
    },
    "camera": {
      "lente": "35mm",
      "angulo": "frontal nível do olhar",
      "foco": "ambos os lados nítidos",
      "profundidade": "média"
    },
    "paleta_cores": ["branco quente", "bege sofisticado", "madeira clara"],
    "elementos_graficos": [],
    "film_grain": "não",
    "sensacao_emocional": ["transformação", "ganho concreto", "antes era ok, agora é melhor"],
    "direcao_de_arte": [
      "a diferença entre antes e depois precisa ser visível em thumbnail",
      "evitar exagerar o ANTES como feio — deve ser comum, identificável, não caricato",
      "headline overlay aparece centralizada na divisão entre os dois lados"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_transformacao`, `subheadline_transformacao`, `ambiente_antes`, `ambiente_depois`.

---

## TEMPLATE 3 — BADGE DE TAMANHO

```json
{
  "imagem": 3,
  "nome": "BADGE_TAMANHO",
  "objetivo_meclabs": "-f",
  "headline": "{{headline_tamanho|Tamanho ideal para o dia a dia}}",
  "subheadline": "{{dimensoes_destaque}}",
  "badge": "{{badge_tamanho|null}}",
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO — NÃO ALTERE O PRODUTO. Adicione um objeto de referência de tamanho ao lado.",
    "estilo_visual": "foto técnica de produto com referência de escala",
    "composicao": "produto centralizado com objeto de referência de tamanho ao lado (mão humana, sacola de mercado, garrafa de água, conforme {{referencia_tamanho}})",
    "cenario": {
      "fundo": "branco neutro suave",
      "estilo": "clean técnico, fácil de entender"
    },
    "produto": {
      "posicao": "centro-esquerda do frame",
      "destaque": "produto totalmente visível",
      "visibilidade": "proporção real preservada"
    },
    "objeto_referencia": {
      "tipo": "{{referencia_tamanho|sacola de mercado padrão}}",
      "posicao": "lado direito do produto, em escala correta",
      "proposito": "permitir ao comprador estimar tamanho real em 1 segundo"
    },
    "iluminacao": {
      "tipo": "studio light uniforme",
      "efeito": "ambos os elementos com mesma luz para comparação justa",
      "direcao": "frontal suave"
    },
    "camera": {
      "lente": "50mm",
      "angulo": "frontal nível do olhar",
      "foco": "produto e referência ambos nítidos",
      "profundidade": "baixa"
    },
    "paleta_cores": ["branco", "{{cor_produto}}", "tons neutros"],
    "elementos_graficos": [
      "linhas de medida sutis se aplicável",
      "número da dimensão sobreposto em pós-produção"
    ],
    "film_grain": "não",
    "sensacao_emocional": ["clareza", "previsibilidade", "decisão fácil"],
    "direcao_de_arte": [
      "comprador precisa entender o tamanho real em menos de 2 segundos",
      "overlay com medidas (ex: '31 cm × 24 cm') aplicado em pós-produção em canto inferior",
      "evitar referências exóticas (use objetos cotidianos brasileiros)"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_tamanho`, `dimensoes_destaque`, `badge_tamanho`, `referencia_tamanho`, `cor_produto`.

---

## TEMPLATE 4 — ANTI-ANSIEDADE MATERIAL

```json
{
  "imagem": 4,
  "nome": "ANTI_ANSIEDADE_MATERIAL",
  "objetivo_meclabs": "-a",
  "headline": "{{headline_material|Material que você pode confiar}}",
  "subheadline": "{{material_especifico}}",
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO. Faça close macro extremo na região onde {{regiao_material_critica}} é visível.",
    "estilo_visual": "fotografia macro publicitária mostrando textura e acabamento real do material",
    "composicao": "close-up extremo de {{regiao_material_critica}} ocupando 80% do frame",
    "cenario": {
      "fundo": "out of focus suave em tom complementar ao produto",
      "estilo": "macro premium, transmitir tactilidade"
    },
    "produto": {
      "posicao": "close em região específica do produto",
      "destaque": "textura/reflexo/acabamento do material",
      "visibilidade": "detalhes que provam autenticidade do material"
    },
    "iluminacao": {
      "tipo": "luz lateral dramática para revelar textura",
      "efeito": "destacar característica visual do material verdadeiro",
      "direcao": "lateral 45 graus + leve preenchimento"
    },
    "camera": {
      "lente": "100mm macro",
      "angulo": "frontal close",
      "foco": "ponto crítico do material ultra sharp",
      "profundidade": "muito baixa, fundo desfocado"
    },
    "paleta_cores": ["{{cor_produto}}", "tons neutros para fundo"],
    "elementos_graficos": [],
    "film_grain": "leve sutil para textura tátil",
    "sensacao_emocional": ["confiança", "qualidade real", "transparência"],
    "direcao_de_arte": [
      "esta foto responde a 'será que é {{material_declarado}} mesmo?'",
      "macro precisa mostrar evidência visual única daquele material (reflexo, textura, grão)",
      "headline overlay vai ao lado, deixar área lateral livre"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_material`, `material_especifico`, `material_declarado`, `regiao_material_critica`, `cor_produto`.

---

## TEMPLATE 5 — CLAREZA ABSOLUTA

```json
{
  "imagem": 5,
  "nome": "CLAREZA_ABSOLUTA",
  "objetivo_meclabs": "-a-f",
  "headline": "{{headline_clareza}}",
  "subheadline": "{{esclarecimento_principal}}",
  "badge": "{{badge_clareza|null}}",
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO. Crie composição que mostre de forma inequívoca a resposta à objeção: '{{objecao_alvo}}'.",
    "estilo_visual": "infográfico visual minimalista premium com produto real",
    "composicao": "produto à esquerda + bloco explicativo à direita com no máximo 1-2 elementos visuais claros",
    "cenario": {
      "fundo": "branco neutro com discreta grade ou linha guia",
      "estilo": "extremamente clean, foco em clareza"
    },
    "produto": {
      "posicao": "lado esquerdo do frame",
      "destaque": "totalmente nítido",
      "visibilidade": "ângulo que favorece a explicação"
    },
    "elemento_explicativo": {
      "tipo": "{{tipo_elemento|ilustração simples + ícone}}",
      "conteudo": "{{conteudo_visual_clareza}}",
      "posicao": "lado direito, em escala equivalente ao produto"
    },
    "iluminacao": {
      "tipo": "luz uniforme de catálogo",
      "efeito": "zero distração, máxima legibilidade",
      "direcao": "frontal direta"
    },
    "camera": {
      "lente": "50mm",
      "angulo": "frontal",
      "foco": "produto e elemento explicativo ambos nítidos",
      "profundidade": "baixa, sem desfoque"
    },
    "paleta_cores": ["branco", "preto suave", "{{cor_produto}}", "verde leve para confirmação"],
    "elementos_graficos": [
      "ícones minimalistas",
      "linhas finas modernas para callouts"
    ],
    "film_grain": "não",
    "sensacao_emocional": ["clareza", "alívio de dúvida", "confiança"],
    "direcao_de_arte": [
      "a foto precisa responder UMA dúvida específica em 2 segundos",
      "se houver texto importante na imagem, fica no overlay pós-produção, não na imagem gerada",
      "evitar excesso de elementos — clareza não é o mesmo que poluição informativa"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_clareza`, `esclarecimento_principal`, `badge_clareza`, `objecao_alvo`, `tipo_elemento`, `conteudo_visual_clareza`, `cor_produto`.

---

## TEMPLATE 6 — DETALHE TÉCNICO 1 (funcionamento)

```json
{
  "imagem": 6,
  "nome": "DETALHE_TECNICO_FUNCIONAMENTO",
  "objetivo_meclabs": "-f+v",
  "headline": "{{headline_funcionamento|Como funciona na prática}}",
  "subheadline": "{{feature_destacada}}",
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO. Mostre {{feature_mecanica}} em uso, em close.",
    "estilo_visual": "fotografia técnica de produto em ação",
    "composicao": "close-up da feature em funcionamento, com indicação visual de movimento se aplicável",
    "cenario": {
      "fundo": "neutro suave, fora de foco",
      "estilo": "técnico publicitário"
    },
    "produto": {
      "posicao": "centro do frame, parte funcional em destaque",
      "destaque": "{{feature_mecanica}} no momento da ação",
      "visibilidade": "movimento ou estado funcional claro"
    },
    "iluminacao": {
      "tipo": "luz lateral para revelar tridimensionalidade",
      "efeito": "destacar mecanismo em ação",
      "direcao": "lateral + leve preenchimento frontal"
    },
    "camera": {
      "lente": "70mm",
      "angulo": "lateral próxima",
      "foco": "ponto de ação ultra sharp",
      "profundidade": "baixa"
    },
    "paleta_cores": ["{{cor_produto}}", "tons neutros"],
    "elementos_graficos": [
      "seta sutil indicando movimento (opcional, aplicar em overlay)"
    ],
    "film_grain": "não",
    "sensacao_emocional": ["praticidade", "engenhosidade", "vou conseguir usar fácil"],
    "direcao_de_arte": [
      "comprador precisa entender COMO usa o produto vendo essa foto",
      "se a feature é silenciosa/sutil, indicar com pista visual (mão posicionada, seta de movimento overlay)"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_funcionamento`, `feature_destacada`, `feature_mecanica`, `cor_produto`.

---

## TEMPLATE 7 — DETALHE TÉCNICO 2 (acabamento/durabilidade)

```json
{
  "imagem": 7,
  "nome": "DETALHE_TECNICO_DURABILIDADE",
  "objetivo_meclabs": "-a+v",
  "headline": "{{headline_durabilidade|Acabamento feito para durar}}",
  "subheadline": "{{ponto_durabilidade}}",
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO. Close em {{regiao_acabamento}}, mostrando qualidade construtiva.",
    "estilo_visual": "fotografia macro de acabamento premium",
    "composicao": "close em acabamento, encaixe, costura, solda ou junção",
    "cenario": {
      "fundo": "out of focus suave",
      "estilo": "macro tátil"
    },
    "produto": {
      "posicao": "close em {{regiao_acabamento}}",
      "destaque": "qualidade construtiva do detalhe",
      "visibilidade": "evidência de cuidado no acabamento"
    },
    "iluminacao": {
      "tipo": "luz rasante revelando textura",
      "efeito": "valorizar acabamento sem mascarar imperfeições",
      "direcao": "rasante 30 graus"
    },
    "camera": {
      "lente": "100mm macro",
      "angulo": "diagonal próxima",
      "foco": "ponto crítico de qualidade",
      "profundidade": "muito baixa"
    },
    "paleta_cores": ["{{cor_produto}}", "tons profundos para contraste"],
    "elementos_graficos": [],
    "film_grain": "leve",
    "sensacao_emocional": ["durabilidade", "produto bem feito", "vai durar"],
    "direcao_de_arte": [
      "foto precisa transmitir 'isso aqui não vai estragar no primeiro mês'",
      "se acabamento tem ponto fraco real, NÃO mostrar este — escolher região verdadeiramente forte"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_durabilidade`, `ponto_durabilidade`, `regiao_acabamento`, `cor_produto`.

---

## TEMPLATE 8 — LIFESTYLE / USO REAL

```json
{
  "imagem": 8,
  "nome": "LIFESTYLE_USO_REAL",
  "objetivo_meclabs": "+m",
  "headline": "{{headline_lifestyle|null}}",
  "subheadline": null,
  "badge": null,
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO integrado naturalmente em {{ambiente_uso}}.",
    "estilo_visual": "fotografia lifestyle editorial, casa real brasileira contemporânea",
    "composicao": "produto integrado ao ambiente, NÃO em destaque exagerado — natural como num lar",
    "cenario": {
      "ambiente": "{{ambiente_uso}}",
      "elementos": "{{elementos_ambiente|toalhas claras, planta natural, bancada clara, luz de manhã}}",
      "estilo": "Pinterest aspiracional acessível, NÃO luxo escuro"
    },
    "produto": {
      "posicao": "elemento do ambiente, não foco único",
      "destaque": "presença sutil mas reconhecível",
      "visibilidade": "claramente identificável a 2 segundos"
    },
    "elemento_humano": {
      "presenca": "{{presenca_humana|opcional desfocado ao fundo}}",
      "proposito": "criar identificação sem distrair do produto"
    },
    "iluminacao": {
      "tipo": "luz natural quente brasileira de manhã/tarde",
      "efeito": "aconchego, casa cuidada",
      "direcao": "luz lateral de janela"
    },
    "camera": {
      "lente": "35mm",
      "angulo": "nível do olhar humano",
      "foco": "produto nítido, ambiente levemente fora de foco",
      "profundidade": "média lifestyle"
    },
    "paleta_cores": ["branco quente", "bege sofisticado", "madeira clara", "verde natural leve"],
    "elementos_graficos": [],
    "film_grain": "leve cinematográfico",
    "sensacao_emocional": ["aspiração realista", "isso poderia ser minha casa", "aconchego"],
    "direcao_de_arte": [
      "ambiente precisa ser brasileiro contemporâneo, não estrangeiro/genérico",
      "produto integrado, não posando — como se já fosse parte da casa",
      "Terra Casa Decor: casual e acolhedor, NUNCA luxo intimidador"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "neutro",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_lifestyle`, `ambiente_uso`, `elementos_ambiente`, `presenca_humana`.

---

## TEMPLATE 9 — SOBRECORREÇÃO DE ANSIEDADE

```json
{
  "imagem": 9,
  "nome": "SOBRECORRECAO_ANSIEDADE",
  "objetivo_meclabs": "-a-f",
  "headline": "{{headline_sobrecorrecao|Compra transparente e sem surpresas}}",
  "subheadline": "{{subheadline_sobrecorrecao|null}}",
  "badge": "{{badge_envio|null}}",
  "cta": null,
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO — NÃO ALTERE O PRODUTO. Coloque produto centralizado em fundo branco premium minimalista.",
    "estilo_visual": "infográfico premium anti-ansiedade estilo marketplace líder",
    "composicao": "produto centralizado com área ao redor reservada para selos visuais (aplicados em overlay pós-produção)",
    "cenario": {
      "fundo": "branco premium minimalista com sombra suave",
      "estilo": "clean, fácil de escanear em 2 segundos"
    },
    "produto": {
      "posicao": "frontal central hero shot",
      "destaque": "acabamento iluminado suavemente",
      "visibilidade": "todas as features-chave claramente visíveis"
    },
    "selos_visuais_planejados": "{{selos_array}}",
    "callout_tecnico": {
      "presenca": "{{tem_callout|opcional}}",
      "titulo": "{{callout_titulo|Importante}}",
      "texto": "{{callout_texto|null}}"
    },
    "iluminacao": {
      "tipo": "premium soft studio light",
      "efeito": "transmitir honestidade, clareza, confiança",
      "direcao": "frontal suave uniforme"
    },
    "camera": {
      "lente": "60mm",
      "angulo": "frontal levemente superior",
      "foco": "produto completamente nítido",
      "profundidade": "limpa e objetiva"
    },
    "paleta_cores": ["branco", "cinza claro", "{{cor_produto}}", "preto suave", "verde leve para confirmação"],
    "elementos_graficos": [
      "ícones minimalistas (aplicados em overlay)",
      "linhas finas modernas",
      "selos clean premium"
    ],
    "film_grain": "não",
    "sensacao_emocional": ["segurança", "clareza", "compra sem risco", "honestidade"],
    "direcao_de_arte": [
      "visual extremamente fácil de entender em menos de 2 segundos",
      "transmitir honestidade acima de perfeição",
      "não esconder limitações do produto se houver — sobrecorrigir com transparência",
      "selos aplicados pelo overlay: deixar espaço ao redor do produto"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_sobrecorrecao`, `subheadline_sobrecorrecao`, `badge_envio`, `selos_array` (lista de objetos `{texto, objetivo}`), `tem_callout`, `callout_titulo`, `callout_texto`, `cor_produto`.

**Overlay pós-produção:** aplicar `selos_array` ao redor do produto (4-6 selos típicos), `headline_sobrecorrecao` no topo, `badge_envio` no canto.

---

## TEMPLATE 10 — MACRO-YES + CTA FINAL

```json
{
  "imagem": 10,
  "nome": "MACRO_YES_CTA_FINAL",
  "objetivo_meclabs": "+i+v",
  "headline": "{{headline_macro_yes}}",
  "subheadline": "{{subheadline_macro_yes|null}}",
  "badge": "{{badge_incentivo|Excelente custo-benefício • Envio rápido}}",
  "cta": "{{cta_final|Compre agora e transforme seu ambiente}}",
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO em ambiente cinematográfico sofisticado.",
    "estilo_visual": "fotografia publicitária premium cinematográfica com estética de conquista",
    "composicao": "produto em destaque absoluto em ambiente contemporâneo sofisticado brasileiro, composição aspiracional",
    "cenario": {
      "ambiente": "{{ambiente_cinematografico|interior contemporâneo brasileiro premium acessível}}",
      "elementos": "{{elementos_cinematograficos|toalhas claras premium, bancada clean, planta minimalista, iluminação quente, acabamentos claros}}"
    },
    "produto": {
      "posicao": "centro do frame levemente à direita",
      "angulo": "hero shot cinematográfico",
      "destaque": "produto brilhando suavemente com aparência premium"
    },
    "elemento_humano": {
      "descricao": "ambiente transmitindo rotina organizada e agradável",
      "presenca": "{{presenca_humana|opcional desfocado ao fundo}}"
    },
    "iluminacao": {
      "tipo": "golden cinematic light",
      "efeito": "sensação de conquista, conforto, casa bonita",
      "direcao": "luz lateral quente sofisticada"
    },
    "camera": {
      "lente": "50mm",
      "angulo": "levemente baixo estilo hero premium",
      "foco": "produto ultra sharp, ambiente cinematográfico desfocado",
      "profundidade": "cinematográfica emocional"
    },
    "paleta_cores": ["branco quente", "bege sofisticado", "madeira clara", "verde natural leve", "{{cor_produto}}"],
    "elementos_graficos": [
      "CTA premium discreto (overlay)",
      "badges modernos minimalistas (overlay)",
      "acabamento visual clean"
    ],
    "area_assinatura": {
      "_regra": "SEM MARCA (Almir 19/06, DEFINITIVA): NÃO desenhar assinatura/logo/slogan/cores da marca nesta foto — evita retrabalho num rebrand. A marca não aparece em nenhuma parte do anúncio (foto, título nem descrição).",
      "posicionamento": "—",
      "texto": "",
      "estilo": "sem assinatura de marca na imagem"
    },
    "film_grain": "leve cinematográfico",
    "sensacao_emocional": ["conquista", "orgulho da casa", "compra inteligente", "modernidade acessível"],
    "direcao_de_arte": [
      "a imagem fecha a jornada emocional",
      "produto deve parecer desejo acessível, não luxo intimidador",
      "transmitir satisfação pós-compra"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_macro_yes`, `subheadline_macro_yes`, `badge_incentivo`, `cta_final`, `ambiente_cinematografico`, `elementos_cinematograficos`, `presenca_humana`, `cor_produto`.

---

## TEMPLATE 11 — FICHA TÉCNICA DE DIMENSÕES

> **Slot exclusivo para foto técnica.** Preenchido com `dados_produto.dimensoes_produto` (resolvido no checkpoint step-04b). `altura` e `largura` são obrigatórias — se qualquer uma não tiver `status: "ok"` ao iniciar o step-07, o step veta (ver seção de VETO no step-07-fotos.md). `profundidade` é opcional: passar vazio quando `status: "nao_aplicavel"` — a linha some do template HTML automaticamente.

```json
{
  "imagem": 11,
  "nome": "FICHA_TECNICA_DIMENSOES",
  "objetivo_meclabs": "-f",
  "headline": "{{headline_dimensoes|Dimensões}}",
  "subheadline": null,
  "badge": null,
  "cta": null,
  "dim_altura": "{{dim_altura}}",
  "dim_largura": "{{dim_largura}}",
  "dim_profundidade": "{{dim_profundidade}}",
  "prompt": {
    "instrucao_principal": "USE A IMAGEM ANEXADA DO PRODUTO — NÃO ALTERE O PRODUTO. Apresente o produto completo com fundo neutro limpo, mostrando vista frontal ou levemente em perspectiva que permita entender as três dimensões.",
    "estilo_visual": "fotografia técnica de produto estilo catálogo com fundo branco neutro",
    "composicao": "produto centralizado ocupando 60-70% do frame, espaço lateral/inferior preservado para overlay do quadro de medidas (canto inferior direito)",
    "cenario": {
      "fundo": "branco puro ou cinza muito claro neutro",
      "estilo": "técnico limpo, sem distrações"
    },
    "produto": {
      "posicao": "centro do frame, levemente deslocado à esquerda para liberar espaço no canto inferior direito",
      "destaque": "produto inteiro visível — não usar close ou crop",
      "visibilidade": "todas as dimensões fisicamente compreensíveis"
    },
    "iluminacao": {
      "tipo": "studio light uniforme, sem sombras duras",
      "efeito": "produto claro e fácil de medir visualmente",
      "direcao": "frontal suave com leve fill lateral"
    },
    "camera": {
      "lente": "50mm",
      "angulo": "frontal ou 3/4 suave para indicar profundidade",
      "foco": "produto completamente nítido",
      "profundidade": "baixa, sem desfoque"
    },
    "paleta_cores": ["branco", "cinza claro", "{{cor_produto}}"],
    "elementos_graficos": [],
    "film_grain": "não",
    "sensacao_emocional": ["clareza", "transparência", "compra sem surpresa"],
    "direcao_de_arte": [
      "comprador precisa entender o tamanho real antes de comprar",
      "quadro de medidas aplicado em overlay pós-produção no canto inferior direito",
      "NÃO incluir texto ou setas de cota na imagem AI — medidas vêm 100% pelo overlay",
      "produto NÃO pode ser cortado nas bordas — mostrar integralmente"
    ],
    "checklist_cientifico": {
      "evidencia_visual": "sim",
      "reduz_ansiedade": "sim",
      "friccao_zero": "sim",
      "headline_beneficio": "sim"
    },
    "formato": "1:1 marketplace Mercado Livre",
    "dimensao": "1200x1200 px exatos",
    "qualidade": "ultra realista 8k"
  }
}
```

**Slots variáveis:** `headline_dimensoes`, `dim_altura`, `dim_largura`, `dim_profundidade`, `cor_produto`.

**Fonte dos dados:** `dados_produto.dimensoes_produto.altura` e `.largura` são obrigatórias — `status: "ok"` exigido antes de chegar ao step-07, caso contrário é VETO. `profundidade` é opcional — se `status: "nao_aplicavel"`, passar `dim_profundidade` vazio (a linha some do template HTML via `:has(.dim-value:empty)`).

**Overlay pós-produção:** quadro branco semi-transparente (painel) no canto inferior direito com as linhas de dimensão (`Altura` e `Largura / Diâmetro` sempre presentes; `Profundidade` apenas quando disponível); `headline_dimensoes` no topo (ex: "Dimensões"). **SEM `brand_signature` no rodapé** — regra SEM MARCA (Almir 19/06, DEFINITIVA): nenhuma foto leva logo/slogan/marca, para não prender a imagem a um eventual rebrand.

---

## Regras gerais para Felipe

1. **Não invente novos slots** — se a Helena pediu objeção específica fora desses 10, ela tem que rever o briefing.
2. **Preencha TODOS os placeholders** — `{{slot|null}}` permite vazio, mas `{{slot}}` sem default é obrigatório.
3. **Mantenha a estrutura do JSON** — Gemini Nano Banana espera campos consistentes.
4. **Sempre anexe `foto_base_url`** ao chamar o modelo, mesmo que o template não cite explicitamente.
5. **Não gere texto dentro da imagem** — texto vai como overlay pós-produção, independente do que o modelo "queira" renderizar.
6. **Salve o JSON final em `output/fotos/{sku}/prompts/foto-NN.json`** antes de chamar o gerador (auditoria).
7. **Valide a dimensão da saída: 1200×1200 px exatos.** Se o modelo entregou diferente, redimensionar antes de aplicar o overlay. O overlay assume canvas 1200×1200 — qualquer outro tamanho quebra o posicionamento dos selos e headlines.
