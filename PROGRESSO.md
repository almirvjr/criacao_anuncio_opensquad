# PROGRESSO

> Atualizado 2026-06-26. **8L (VIE_1067) EM ANDAMENTO.** 5L fechado/aprovado (ver HISTORICO 2026-06-24/26). Rodada 8L em `output/2026-06-26-conforme-8L/`. **RETOMAR EM: aprovar a capa v8 (capa-v8.jpg) → gerar as 9 StorySelling.**

## 0. Estado do 8L (VIE_1067) — feito nesta sessão
- **Cor-herói = PRETO** (escolha explícita do Almir; ele quer definir a herói por anúncio, sempre). As 9 StorySelling sairão em preto.
- **Produto-travado PRETO** em `pipeline/data/produtos-travados/VIE_1067-PAI.json` (+ `_aberto.png`/`_fechado.png`). Travado DIRETO das fotos reais pretas (`output/2026-05-26-091553/fotos/VIE_1067-PAI/_base/WhatsApp ...16.46.47/16.47.56`) → fidelidade máxima, sem recolor de IA. (Nota antiga "base 8L = squat do 5L" estava desatualizada; as fotos do WhatsApp 15/06 são o 8L alto real.)
- **Master branco** (recolor fiel) guardado em `.../_master/master-branco-*.jpg` — só p/ futura capa da variação Branco (não-herói).
- **Brief conformado** em `output/2026-06-26-conforme-8L/inteligencia/brief-VIE_1067-PAI.yaml`: hierarquia aprovada do 5L, SEM marca, **cozinha-líder** (only_factor 8L = tamanho útil + cabe a sacola de mercado), dims REAIS 18Ø×34cm, foto 6 = sem balde interno.
- **Capa v8** (`.../VIE_1067-PAI/_redesign/capa-v8.jpg`) — AGUARDANDO APROVAÇÃO DO ALMIR. Escala MEDIDA razão 0,32 (≤1/3, exigência do Almir) + realista (não-adesivo). Método novo (ver DECISOES 2026-06-26).

## 1. Próximas tarefas (ordem)
1. **Aprovar a capa v8** no Chrome (pendente). Se reprovar, iterar a posição/sombra/cena mantendo o método.
2. **Gerar as 9 StorySelling (fotos 2–10)** do 8L em PRETO, reusando a receita: studio compose (3,4,9,10) + lifestyle pelo método render-in-scene→recorta→encolhe→recompõe (capa,2,5,8) + ação no pedal (7). Texto NEUTRO de cor. Medir escala ≤1/3 (contexto) antes de apresentar cada uma.
3. Validar regras de imagem do ML (capa exige fundo branco?) antes de publicar.
4. Subir ao bucket `tcd-produtos` (precisa SERVICE_ROLE) → Step-08 → publicar.

## 2. Regras de trabalho (Almir) — INFALÍVEIS
- **CONFERIR medindo (não afirmar) + rodar checklist COMPLETO ANTES de apresentar** + aprovar SEMPRE no Chrome dedicado. (Furei isto na v4/v5 nesta sessão — Almir cobrou; não repetir.)
- **Escala em ambientada = 1/3 ou menos da bancada** (8L 34cm ÷ bancada 90cm). MEDIR (razão = alt. lixeira ÷ alt. chão→tampo). O Gemini fotorrealista orbita ~metade e NÃO desce a 1/3 — usar o método de compor a lixeira-já-renderizada-na-cena encolhida (DECISOES 26/06).
- **Pedal = tamanho FIXO** (igual no 5L e 8L). Numa lixeira mais alta o pedal deve parecer proporcionalmente menor — é a régua real do tamanho. Vem fiel no produto-travado.
- **SEM MARCA** em todo o anúncio. Cor-herói definida pelo Almir por anúncio.

## 3. Pendências
- **SUPABASE_SERVICE_ROLE** (a chave service_role do Supabase): re-fornecer p/ subir ao bucket.
- **step-10:** `N8N_WEBHOOK_ML_PUBLICAR` ausente; workflow "ML Publicar" (`0rzNJ7RLqLzMbKnf`) INATIVO de propósito.
- Custo da sessão 8L (OpenRouter Pro): ~$1,9 (master + cena + iterações de capa). Saldo OpenRouter ~$4,5.
