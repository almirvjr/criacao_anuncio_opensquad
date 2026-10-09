# Botão "1 - Criar anuncios" — desenho

**Data:** 09/10/2026 · **Pedido do Almir:** criar anúncio sozinho, sem conversa com o Claude: planilha na pasta → clique → a esteira roda → ele confere e publica numa tela só. Inclui o item 2 do PROGRESSO (descrição e Flex gravados sozinhos depois de publicar).

**Combinado na conversa (09/10):** caminho de ponta a ponta (parte 1), cartão da tela (parte 2), maestro por dentro (parte 3). Preço digitado na tela até a planilha de preços existir. Dado que faltou/divergiu vira quadro na tela, decidido por ele. Tudo o que vai pro anúncio aparece na tela, inclusive o código de barras. Preço e "sim" final na mesma tela.

## 0. Regras que valem aqui

- **Nada novo no n8n** (regra do hub de 09/10/2026: automação nova = Supabase). A publicação **continua usando o `ML Publicar` (`0rzNJ7RLqLzMbKnf`) sem mexer nele**. Descrição e Flex ficam no `tools/completar_anuncio.py` (local), chamado sozinho depois de cada cor. Levar a publicação para o Supabase é trabalho à parte (virada com volta-atrás), fora deste.
- **Só o Almir publica.** O Claude chamado pelo maestro não tem permissão para disparar publicação; publicar só sai do botão da tela.
- O botão só funciona no hub (Python, `.env`, acesso ao ML), como os da GS1.

## 1. Caminho de ponta a ponta

1. Almir salva a planilha exportada do Olist em `G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR` e clica em `1 - Criar anuncios` (atalho na pasta `ANUNCIOS`).
2. Janela preta mostra o andamento em português.
3. **Pré-checagem (≈1 min, antes de gastar tempo):** a planilha abre e tem o formato esperado; todo SKU de cor tem linha na cubagem (peso + caixa); toda cor tem ao menos 1 foto `capa-anuncio` + SKU da cor no Cloudinary. Faltou → para e diz o quê, sem mexer na planilha.
4. Etapas com cabeça (Claude sem conversa): leitura/curadoria (step-01/02), categoria (03), pesquisa (04), texto (05). Etapas fixas por código: capas (07). Revisão do Vinicius (08) roda **antes** da tela.
5. O checkpoint de dados (04b) e o de copy (06) **não param mais**: o que faltou/divergiu vai para o quadro da tela; a aprovação do texto é na tela.
6. Tela abre sozinha (`aprovacao.py --saida <pasta do lote> --esperar`). Única parada do Almir.
7. **Aprovar e publicar** → publica cor a cor (preta primeiro) pelo `ML Publicar`, e depois de cada cor roda `completar_anuncio.py` (descrição + Flex).
8. **Devolver pra refazer** → o maestro chama de novo o texto (step-05) e a revisão (step-08) só daquele anúncio, com a `nota_almir`; o cartão volta para a tela.
9. Todos publicados ou tirados do lote → planilha vai para `A CRIAR\FEITOS`.

## 2. O cartão da tela (amplia `tools/aprovacao/`)

Um cartão por anúncio. Tudo o que vai para o ML aparece.

- **Topo:** nome, SKU pai, categoria no ML (caminho), parecer do Vinicius (aprovado / com ressalvas + motivo).
- **Tabela por cor (preta primeiro):** cor · SKU · código de barras · capa(s) em miniatura, na ordem em que vão · estoque (do Olist) · título que o ML vai montar (nome da família + cor) com contador `NN/60`.
  - **Código de barras vazio trava a publicação daquela cor.** Aviso: "gere o código pelo botão da GS1"; botão **Reler do Olist** busca o código de novo sem recomeçar a esteira.
  - Produto sem variação de cor = uma linha só, um anúncio.
- **Preço:** um campo, vale para todas as cores. Vazio trava o botão de publicar. (Quando a planilha de preços existir, ela preenche o campo.)
- **Texto (editável):** título/nome da família (opções da Renata ou o seu), Marca, Modelo, 3 blocos da descrição, com contadores — como já é hoje.
- **Quadro "Faltou ou divergiu" (novo):** um item por dado `pendente`/`divergente` do brief (step-04) e do dossiê (step-02). Mostra o valor de cada fonte (planilha, concorrente com link) e deixa escolher um, escrever outro ou deixar vazio. O escolhido entra na **ficha técnica**. A descrição não é reescrita sozinha: para o dado aparecer no texto, editar o bloco ou devolver com nota.
- **Ficha técnica completa:** todos os atributos que vão, só leitura (exceto os que vêm do quadro).
- **Envio:** peso e caixa da cubagem; frete grátis (o ML liga sozinho na faixa de preço); Flex ligado.
- **Conferência ao vivo:** as travas de hoje. ❌ trava o botão; ⚠️ permite "mesmo assim" e grava `avisos_aceitos`.
- **Botões:** **Aprovar e publicar** · **Devolver pra refazer** (com nota) · **Tirar do lote**.
- **Depois de publicar:** link de cada cor; ✅ descrição gravada · ✅ Flex ligado; "pausado até o ML baixar a foto (5 a 15 min)". Erro numa cor não afeta as outras; mensagem em português + **Tentar de novo** só naquela cor (a publicação já é protegida contra duplicar pelo `ML Publicar` e pela checagem de anúncio existente).

O que a aprovação grava: o mesmo de hoje (`titulo_final`, BRAND, MODEL, blocos, `status_copy`, `aprovado_em`, `avisos_aceitos`) **+** `preco`, `atributos_decididos` (os do quadro) e, depois de publicar, `publicacao` por cor (MLB, link, descrição ok, Flex ok, erro). Cópia de segurança antes de gravar, como hoje.

## 3. O maestro por dentro

- **Peças novas:** `tools/esteira_auto/maestro.py` (conduz as etapas), `tools/esteira_auto/Criar anuncios.bat` (clique duplo), atalho `1 - Criar anuncios` na pasta `ANUNCIOS`.
- **Lote = uma planilha, pasta própria:** `squads/ml-anuncios/output/lotes/<data-hora>/`. Duas planilhas em `A CRIAR` → rodam em sequência. Os caminhos de saída de cada etapa passam a ser relativos à pasta do lote (hoje é tudo em `output/` solto e um lote novo sobrescreveria o anterior).
- **Caderno de andamento:** `andamento.json` (para o maestro) + `andamento.txt` (em português, para o Almir e para o Claude ler depois). Etapa só é marcada feita depois de passar nas travas. Clicar de novo = continua da próxima etapa não feita; lote parado é retomado antes de começar planilha nova.
- **Claude sem conversa:** uma chamada de `claude -p` por etapa com cabeça, com instrução fixa guardada em arquivo (`tools/esteira_auto/instrucoes/step-XX.md`) apontando para o step da squad e para a pasta do lote. Permissões da chamada: ler/escrever só na pasta do lote, rodar os validadores, navegador escondido da Helena. Sem permissão para `disparar_publicacao.py` nem para o webhook.
- **Travas depois de cada etapa:** as do `pipeline.yaml` (`validar_brief`, `validar_claims`, `validar_ficha_seo`, `capas`). Reprovou → 1 nova chamada com o motivo; reprovou de novo → aquele anúncio para (motivo em português na janela e no caderno), os outros seguem.
- **Botão `2 - Aprovar anuncios`** continua: abre a tela com os lotes esperando o Almir (ex.: Chrome fechado sem querer).

## 4. Erros

| Situação | O que acontece |
|---|---|
| Faltou capa ou cubagem | Para na pré-checagem, diz qual cor/SKU |
| Acesso ao ML vencido | Renova como hoje (`access_token_ML`); se não der, para e avisa |
| Pesquisa sem concorrente | Segue; quadro "Faltou ou divergiu" mostra o que ficou sem fonte |
| `ML Publicar` fora do ar / sem resposta | Cor fica "não publicada" com **Tentar de novo**; nada pela metade |
| Planilha vazia / outro formato | Para na hora, diz o que esperava, não move a planilha |
| `claude -p` falhou ou estourou o tempo | Etapa não marcada; caderno registra; clicar de novo retoma |

A planilha só vai para `FEITOS` quando todos os anúncios dela estão publicados ou tirados do lote.

## 5. Testes

1. **Automáticos, sem custo e sem ML:** maestro com etapas de mentira — ordem, retomada, parada por falta de capa/cubagem, devolver → refaz só aquele, planilha para `FEITOS` só no fim. Tela: quadro "Faltou ou divergiu", preço obrigatório, código de barras vazio trava a cor, gravação do que foi decidido, publicação com `ML Publicar` simulado (sucesso, falha numa cor, tentar de novo).
2. **Ensaio real até a tela:** boleira Brinox `BRI-coza34-40652_3009`. Tela abre, cartão conferido completo, **sem publicar**.
3. **1ª publicação real com o Almir:** a mesma boleira; ele clica em Publicar; conferir no ML (título, fotos, código de barras, descrição, Flex) com `ler_anuncio_ml.py`.

## 6. Fora deste trabalho

Levar a publicação (`ML Publicar`) do n8n para o Supabase; planilha de preços por canal; vínculo automático com o Olist; geração de foto.
