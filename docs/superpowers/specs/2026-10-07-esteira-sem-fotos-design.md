# Esteira de anúncio ML sem fotos — desenho

**Data:** 07/10/2026 · **Pedido do Almir:** a squad `ml-anuncios` cria o anúncio completo, **menos as fotos**. Geração de imagem vira projeto separado (ainda não criado).

## 1. O que muda e o que fica

| # | Etapa | Muda? |
|---|---|---|
| 1-2 | Caio lê a planilha do Tiny e monta o dossiê | não |
| 3 | Cibele: categoria e campos obrigatórios | não |
| 4 | Helena pesquisa concorrentes **só para o texto** | **sim** — sai o roteiro das 10 fotos |
| 5 | Checkpoint de dados (Almir) | não |
| 6 | Renata: título, descrição, ficha | **sim** — regra nova de Marca/Modelo e exceção Mundiart |
| 7 | Checkpoint de copy (Almir) | não |
| 8 | **"Buscar capas"** (novo, substitui Felipe) | **sim** |
| 9 | Vinicius revisa | **sim** — foto: só o básico |
| 10 | Checkpoint de publicação (Almir) | **sim** — mostra nº de fotos e alerta de preço |
| 11 | Paula publica | **sim** — aceita 1 a 10 fotos |
| 12 | Relatório | não |

## 2. Fotos

- **Quem sobe é o Almir**, no Cloudinary (nuvem `wa5lvi98`), na pasta do fornecedor (`VIEL`, `Brinox`…).
- **Duas etiquetas por foto:** o SKU da **cor** exatamente como no Tiny + `capa-anuncio`.
- **Etapa 8** busca `tags=capa-anuncio AND tags=<SKU da cor>` para cada cor. Faltou a de alguma cor → a esteira **para** e diz qual falta (o ML exige ao menos 1 foto por cor).
- Endereço entregue ao ML já reduzido a 1200×1200 pelo próprio link do Cloudinary (`c_pad,w_1200,h_1200,b_white`), sem mexer no original.
- Conferência básica (Vinicius): abre, tem 1200×1200 depois do link, é o produto certo, sem logo/nome da loja.
- **Ferramentas de geração ficam guardadas, desligadas:** agente Felipe, step-07, gates de imagem (`qa_imagens`, `validar_prompts`, `validar_prompt_nano`, produto travado), templates StorySelling de foto. Nada apagado; o projeto de fotos herda o que servir.
- **Trocar cor de produto:** site do ChatGPT (ver `projects/imagens/DECISOES.md` I27).

## 3. Ficha técnica — Marca e Modelo (regra de 07/10)

- Marca e Modelo carregam **palavras-chave de busca que não estão no título**. Teto ~30 caracteres cada.
- Marca **começa pelo fornecedor** (ex.: `Viel Lixeira Banheiro Cozinha`).
- **Mundiart (`MDA_`):** Marca = `Terra Casa Decor` e só; a descrição apresenta o produto como Terra Casa Decor; título sem o nome.
- Fonte das palavras-chave: busca do ML (autocompletar + títulos dos concorrentes da Helena). Renata escolhe, Vinicius confere que não repete o título.

## 4. Publicação

- Workflow `ML Publicar` (`0rzNJ7RLqLzMbKnf`) **já aceita 1 a 10 fotos** — não precisa mudar. Ligar só no 1º teste, com o Almir.
- Paula: tira a trava "exatamente 10"; passa a exigir **≥1 por cor**.
- ⚠️ Anúncio sai com estoque 1; o vínculo com o Tiny continua **manual** (resposta `manual_pending`).
- ⚠️ **Preço provisório:** planilha do Tiny veio com R$ 10; Almir pediu **R$ 100** por enquanto. O checkpoint de publicação mostra o preço em destaque e só segue com "sim" explícito.
- Peso/medida: planilha de cubagem do Drive (Tiny veio zerado).

## 5. Primeiro teste

Viel 5L (`VIE-1066-PAI`: BR/CI/PT) e 8L (`VIE-1067-PAI`: BR/CI/PT). 6 capas já no Cloudinary com etiqueta, conferidas (proporção igual à preta). Planilha: `produtos_2026-10-07-12-07-32.xls`.

## 6. Fora deste trabalho

Projeto de fotos; ligar estoque/vínculo Tiny automático; troca do `_` por `-` nos SKUs antigos.
