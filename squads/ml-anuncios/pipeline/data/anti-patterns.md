# Anti-Patterns — Squad ML Anúncios

Erros comuns que precisam ser evitados pela squad. Cada agente deve ler os anti-patterns da sua área antes de operar.

## Curadoria de dados (Caio)

### Nunca fazer
1. **Aceitar planilha sem validar headers obrigatórios** — sem isso, agentes downstream recebem campos vazios e geram conteúdo errado.
2. **Inventar specs faltantes** — se não achou o peso na web, registre `null`; nunca preencha por "estimativa".
3. **Confiar cegamente na descrição do fornecedor** — fornecedor exagera; valide número absurdos (ex: capacidade 999L).
4. **Bloquear o lote inteiro por um SKU com problema** — marque o problemático, siga o resto.

### Sempre fazer
1. Validar URL da foto base com um HEAD request antes de salvar.
2. Registrar fonte de cada enriquecimento (`fonte: "site fornecedor"`, `fonte: "estimado pelo agente"`).
3. Normalizar unidades para o padrão ML (cm, kg, L).

## Categorização (Cibele)

### Nunca fazer
1. **Escolher categoria pelo nome simples sem checar atributos obrigatórios** — categoria errada = anúncio reprovado pelo ML.
2. **Ignorar confiança do category_predictor** — confiança < 70% = risco alto, escale.
3. **Copiar palavras-chave de um único concorrente** — busque o padrão entre os top 3.
4. **Confiar em categorias antigas em cache** — sempre busque ao vivo, taxonomia ML muda.

### Sempre fazer
1. Validar a categoria com pelo menos 2 concorrentes top na mesma categoria.
2. Trazer atributos obrigatórios COM o nome correto que a API ML usa (não traduza).
3. Registrar range de preços para Renata calibrar.
4. Registrar `permalink` de cada concorrente top — Helena depende disso para fazer scraping de reviews.

## Inteligência de Conversão (Helena)

### Nunca fazer
1. **Inventar dor interna sem evidência em review** — qualquer afirmação do diagnóstico precisa citar trecho de review como âncora.
2. **Usar palavra na `linguagem_real_cliente` que não aparece textualmente nos reviews** — viola a regra de ancoragem.
3. **Esconder limitação real do produto** — se reviews dizem "não vem com balde", criar foto de Clareza para esclarecer, não pular o assunto.
4. **Forçar narrativa StoryBrand em produto utilitário** — declarar `diagnostico_neutro: true` quando nem reviews 5-estrelas têm carga emocional.
5. **Copiar headline do exemplo da Himmel literalmente** — referência, não template a colar; cada SKU tem reviews próprios.
6. **Declarar `confianca: alta` com menos de 100 reviews analisadas** — inconsistência.
7. **Pular um slot da hierarquia das 10 fotos** — todos obrigatórios, mesmo que minimalistas.
8. **Headline com mais de 8 palavras ou subheadline com mais de 14** — viola legibilidade.

### Sempre fazer
1. Citar trecho literal de review como evidência de cada item do diagnóstico.
2. Mapear cada ansiedade contra as 10 famílias do `objection-patterns.md`.
3. Preencher os 10 slots do briefing das fotos.
4. Salvar dados brutos do scraping em `output/inteligencia/_raw/{mlb_id}.json`.
5. Validar contagem de palavras das headlines antes de salvar.

## Copywriting (Renata)

### Nunca fazer
1. **Entregar apenas 1 título por SKU** — sempre 3-5 alternativas com scoring (D7).
2. **Marcar mais de um título como `recomendado`** — o checkpoint depende de UMA recomendação clara.
3. **Inventar palavra emocional que não está na `linguagem_real_cliente` do brief** — viola ancoragem (a menos que `diagnostico_neutro: true`).
4. **Usar emojis no título OU na descrição** — ML rejeita com erro `item.description.type.invalid`.
5. **Usar HTML na descrição** (`<br>`, `<b>`, `<p>`, qualquer tag) — ML aceita só plain text; tag vira erro 400.
6. **Usar markdown na descrição** (`**negrito**`, `# título`, asterisco em bullet) — vira literal no anúncio.
7. **Caracteres `<` ou `>` soltos na descrição** — ML rejeita.
8. **Repetir o título na descrição literalmente** — bloco 1 precisa ser narrativo.
9. **Inventar features que o produto não tem** — alucinação é veneno; só descreva o que está no dossiê.
10. **Usar tom Terra Casa Decor "premium/luxuoso"** — a marca é casual e acolhedora.
11. **Deixar atributo obrigatório vazio** — anúncio é rejeitado.
12. **Escrever o bloco 1 sem ancorar na `dor_interna` do brief** (quando brief não é neutro) — perde o ganho de conversão do StorySelling.
13. **Pular a `escada_e_dai` do brief no bloco 3** — bullets ficam só técnicos, sem benefício emocional.

### Sempre fazer
1. Gerar 3-5 títulos com `score_busca`, `score_conversao`, `justificativa` e marcar exatamente UM como `recomendado`.
2. Checar contagem de caracteres de CADA título antes de finalizar (50-70).
3. Conectar feature → benefício emocional no bloco 3 (não só listar features).
4. Fechar a descrição com frase acolhedora genérica, **sem citar a marca ("Terra Casa Decor") nem o slogan** (regra SEM MARCA, Almir 19/06).
5. Manter consistência de números entre título recomendado, descrição e ficha.
6. Descrição em plain text puro: parágrafos separados por linha em branco, bullets com hífen `-`, sem formatação visual.
7. Registrar `brief_utilizado`, `dor_interna_referenciada`, `only_factor_referenciado` no output.

## Fotografia (Felipe — StorySelling)

### Nunca fazer
1. **Decidir headline ou objeção sem consultar o brief da Helena** — a fonte da verdade é o `brief-{sku}.yaml`, sempre.
2. **Pular image-to-image e usar foto do fornecedor crua** — viola fidelidade visual do método; também perde a aplicação da cena/iluminação do template.
3. **Embutir texto na imagem AI** — overlay vai à parte via `image-overlay`; modelo deve gerar imagem limpa.
4. **Pular slot da hierarquia** — todos os 10 slots são obrigatórios; substituir com Detalhe Técnico extra se o brief não trouxer conteúdo para algum.
5. **Aceitar foto onde o produto AI está distorcido** — comprador vai receber produto diferente da foto = devolução.
6. **Salvar foto sem o JSON do prompt em `prompts/`** — quebra auditoria.
7. **Mostrar mesma imagem em slots diferentes** — diversidade visual é regra.
8. **Entregar foto em qualquer dimensão diferente de 1200×1200 px** — padrão fixo do projeto. Maior (ex: 1500×1500) ou menor (ex: 1000×1000) é veto automático mesmo com qualidade visual boa. Overlay assume canvas 1200×1200; outras dimensões quebram o posicionamento.

### Sempre fazer
1. Validar dimensão antes de salvar: **exatamente 1200×1200 px**. Se o modelo retornou diferente, redimensionar/recortar para 1200×1200 antes de aplicar o overlay.
2. Comparar foto AI gerada com foto base para confirmar que o produto foi preservado.
3. Documentar retries no metadata quando ocorrerem.
4. Aplicar overlay via skill `image-overlay` — nunca tentar overlays manuais.
5. Slot 9 sempre com 4-6 selos visuais.
6. Slot 10 sempre com CTA. **SEM brand_signature/logo/slogan/cores da marca** em nenhuma foto (regra SEM MARCA, Almir 19/06 — a marca não aparece em nenhuma parte do anúncio: foto, título nem descrição).
7. Reportar custo estimado por SKU ao final.

## Revisão (Vinicius)

### Nunca fazer
1. **Aprovar sem checar 100% dos critérios** — checklist é checklist.
2. **Reprovar sem indicar correção específica** — feedback genérico = retrabalho infinito.
3. **Confiar que Renata respeitou contagem de caracteres** — meça.

### Sempre fazer
1. Rodar checklist completo (ver `quality-criteria.md`).
2. Indicar EXATAMENTE o que corrigir quando reprovar.
3. Aprovar apenas o que está pronto pra publicar.

## Publicação (Paula)

### Nunca fazer
1. **Publicar sem checkpoint humano aprovado** — irreversível em produção real.
2. **Continuar lote após erro 401/403** — token expirou ou faltou auth; pare imediatamente.
3. **Sincronizar Tiny antes de confirmar MLB-id válido** — gera registro órfão.
4. **Publicar com mesmo SKU de anúncio já existente** — duplicidade no ML.

### Sempre fazer
1. Confirmar HTTP 201 do POST /items antes de registrar no log.
2. Vincular no Tiny IMEDIATAMENTE após receber MLB-id.
3. Em caso de erro, registrar payload enviado + resposta recebida no log para auditoria.
