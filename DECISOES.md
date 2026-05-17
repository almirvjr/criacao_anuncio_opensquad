# DECISOES

<!-- Decisoes tecnicas importantes. Formato: data - contexto - decisao - motivo. -->

## 2026-05-16

### Workflow "ML Publicar" hospedado em n8n cloud - estrategia de fotos
**Contexto:** spec original previa que Paula enviaria caminhos locais de fotos (`pictures_local_paths`) no payload do webhook. Mas o n8n esta em cloud (`dryboxjellyfish-n8n.cloudfy.live`), nao acessa o disco local.

**Decisao:** opcao A - fotos sao salvas previamente pelo Felipe no bucket publico `tcd-produtos` do Supabase Storage. Paula envia apenas as URLs publicas. ML baixa server-side via `pictures: [{source: "https://..."}]` no POST /items.

**Motivo:** workflow fica mais simples (~6 nos a menos, sem upload de fotos). ML aceita URLs publicas no payload. As fotos vao ficar publicas no anuncio publicado de qualquer jeito, entao expor no Storage publico nao adiciona risco.

### Tabela ml_tools.publicacoes sem RLS
**Contexto:** Supabase alertou que RLS esta desabilitado na tabela `ml_tools.publicacoes`.

**Decisao:** manter sem RLS.

**Motivo:** tabela e usada apenas pelo workflow n8n via service_role. Nao contem dados sensiveis (so log de publicacoes proprias). Se a chave anon nao vazar, esta seguro. Adicionar RLS exigiria criar policies para cada cliente futuro.

### Available_quantity inicial fixo em 1 no POST /items ML
**Contexto:** Tiny ERP detecta anuncios na conta "ML PADRAO" e sobrescreve o estoque com o valor real do ERP. Workflow nao precisa enviar estoque correto.

**Decisao:** workflow forca `available_quantity: 1` no payload ML, ignorando o que Paula enviar.

**Motivo:** garante consistencia (Tiny e a fonte da verdade do estoque). Evita descompasso entre planilha e ERP. ML aceita anuncio com qualquer estoque > 0.

### No "POST Tiny" mantido no workflow (substitui varredura manual)
**Contexto:** descoberta - hoje Almir varre manualmente o painel Tiny para importar cada anuncio ML novo. A integracao nativa Tiny<->ML nao importa sozinha.

**Decisao:** manter o no "POST Tiny" no workflow chamando `POST https://api.tiny.com.br/public-api/v3/anuncios` (com `conta: "ML PADRAO"`).

**Motivo:** automatiza a varredura manual. Reduz tempo manual do Almir. Endpoint exato e estrutura do payload sao "best guess" ate validar com MCP da Tiny (pendencia).

### Sanitizacao defensiva de description no workflow
**Contexto:** ML rejeita `description.plain_text` com HTML/emojis/`<` `>` (erro `item.description.type.invalid`). Renata pode produzir texto com formatacao inadvertidamente.

**Decisao:** defesa em 3 camadas - (1) Renata escreve plain text por instrucao, (2) Vinicius valida via quality-criteria com regex, (3) workflow Code "Montar Payload" sanitiza por seguranca.

**Motivo:** redundancia previne falha total. Se Renata erra ou Vinicius nao pega, workflow ainda salva o anuncio.

### Bucket publico vs privado no Supabase Storage
**Contexto:** fotos dos produtos precisam ser acessadas pelo ML para download server-side.

**Decisao:** bucket `tcd-produtos` configurado como publico.

**Motivo:** as fotos viram publicas no anuncio do ML de qualquer jeito - o bucket publico e apenas o intermediario. Alternativa privada (signed URLs com expiracao) foi considerada mas adicionaria complexidade no Felipe sem ganho de seguranca real.
