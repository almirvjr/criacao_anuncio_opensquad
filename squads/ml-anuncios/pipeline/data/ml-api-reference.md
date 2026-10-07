# Mercado Livre + Tiny ERP — API Reference

Resumo prático dos endpoints usados pela squad. Documentação completa: https://developers.mercadolivre.com.br/.

## Autenticação ML

Token Bearer puxado da tabela `public.access_token_ML` no Supabase, filtrando `app_name = 'pre-venda'`. Refresh automático pelo plugin `ml-kit` em cada sessão.

Header: `Authorization: Bearer <token>`

## Endpoints ML — Públicos (sem auth)

### Predizer categoria a partir de título

> ⚠️ O endpoint antigo `/sites/MLB/category_predictor/predict` foi **descontinuado** — hoje responde **404**. Use `domain_discovery/search`. Verificado em 2026-07-20.

```http
GET https://api.mercadolibre.com/sites/MLB/domain_discovery/search?limit=3&q=lixeira inox com pedal 15 litros
```

Funciona **sem token**. Resposta (array, mais provável primeiro):
```json
[
  {
    "domain_id": "MLB-WASTE_BASKETS",
    "domain_name": "Lixeiras",
    "category_id": "MLB33375",
    "category_name": "Lixeiras",
    "attributes": [ /* atributos já pré-preenchidos a partir do título */ ]
  }
]
```

**Sempre confirmar que a categoria aceita anúncio** antes de usar: precisa ser folha (`children_categories` vazio) e ter `settings.listing_allowed == true`.

```http
GET https://api.mercadolibre.com/categories/MLB33375
```
```json
{
  "id": "MLB33375",
  "name": "Lixeiras",
  "path_from_root": [
    {"id": "MLB1574", "name": "Casa, Móveis e Decoração"},
    {"id": "MLB1618", "name": "Cozinha"},
    {"id": "MLB436298", "name": "Armazenamento e Organização"},
    {"id": "MLB33375", "name": "Lixeiras"}
  ],
  "children_categories": [],
  "settings": { "listing_allowed": true, "status": "enabled" }
}
```

### Buscar produtos em uma categoria

```http
GET https://api.mercadolibre.com/sites/MLB/search?category=MLB33375&q=lixeira inox 15L&sort=sold_quantity_desc&limit=10
```

Retorna lista de resultados com `id` (MLB...), `title`, `price`, `sold_quantity`, `seller.id`, `permalink`.

### Detalhes da categoria

```http
GET https://api.mercadolibre.com/categories/MLB33375
```

### Atributos obrigatórios da categoria

```http
GET https://api.mercadolibre.com/categories/MLB33375/attributes
```

Retorna lista. Filtrar `tags.required == true` para obrigatórios.

## Endpoints ML — Autenticados

### Upload de imagem

```http
POST https://api.mercadolibre.com/pictures/items/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

file=@foto-01.jpg
```

Resposta: `{"id": "123456-MLB12345...", "variations": [...]}`. Salvar o `id` (picture_id) para usar no POST do anúncio.

### Criar anúncio

```http
POST https://api.mercadolibre.com/items
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Lixeira Inox 15L Pedal Tampa Antiodor Cozinha Banheiro",
  "category_id": "MLB33375",
  "price": 159.90,
  "currency_id": "BRL",
  "available_quantity": 50,
  "buying_mode": "buy_it_now",
  "listing_type_id": "gold_special",
  "condition": "new",
  "description": {"plain_text": "..."},
  "pictures": [
    {"id": "picture_id_1"},
    {"id": "picture_id_2"}
  ],
  "attributes": [
    {"id": "BRAND", "value_name": "Terra Casa Decor"},
    {"id": "MODEL", "value_name": "TCD-LXI15"},
    {"id": "MATERIAL", "value_name": "Aço inox"}
  ],
  "shipping": {
    "mode": "me2",
    "free_shipping": false
  },
  "seller_custom_field": "TCD-LXI15"
}
```

Resposta com sucesso: `201 Created` + JSON com `id` (MLB...), `permalink`, etc.

### Criar anúncio com variações

Usado quando o produto tem variações de **cor** (um único anúncio "pai" com várias cores). O corpo é o mesmo do anúncio simples, mas inclui o array `variations[]` e algumas regras adicionais.

```http
POST https://api.mercadolibre.com/items
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Cuba Inox Para Cozinha 34x40 — várias cores",
  "category_id": "MLB33375",
  "price": 150,
  "currency_id": "BRL",
  "buying_mode": "buy_it_now",
  "listing_type_id": "gold_special",
  "condition": "new",
  "description": {"plain_text": "..."},
  "pictures": [
    {"source": "https://.../s1.jpg"},
    {"source": "https://.../branca.jpg"},
    {"source": "https://.../preta.jpg"}
  ],
  "attributes": [
    {"id": "BRAND", "value_name": "Viel"},
    {"id": "MATERIAL", "value_name": "Aço inox"}
  ],
  "variations": [
    {
      "attribute_combinations": [
        {"id": "COLOR", "value_id": "52049", "value_name": "Branco"}
      ],
      "price": 150,
      "available_quantity": 1,
      "attributes": [
        {"id": "SELLER_SKU", "value_name": "VIE_1066_3402_BR"},
        {"id": "EAN", "value_name": "7893633908576"}
      ],
      "picture_ids": [
        "https://.../branca.jpg",
        "https://.../s1.jpg"
      ]
    }
  ]
}
```

Regras importantes:

- **Preço uniforme**: o ML exige que `price` seja **igual em todas as variações**. Por isso o workflow pega `variacoes[0].price` e replica no item-level `price` e em cada `variations[].price`. Preços diferentes por cor são rejeitados.
- **`attribute_combinations`**: define a variação. Para cor, é o atributo `COLOR` com `value_id` (id da cor no catálogo ML) **e** `value_name` (rótulo legível, ex: "Branco"). O `value_id` é o que o ML usa de fato; o `value_name` é descritivo.
- **`COLOR` é `defines_picture`**: a cor é o atributo que determina quais fotos aparecem para cada variação. Por isso cada variação tem suas próprias `picture_ids`.
- **`pictures` (item-level) vs `picture_ids` (por variação)**:
  - `pictures` no nível do anúncio = **união** de todas as fotos compartilhadas (`pictures_compartilhadas`) + as fotos de cor de todas as variações, sem repetir.
  - `picture_ids` dentro de cada variação = as fotos daquela cor específica. O ML aceita a **URL da foto (source)** como referência de `picture_id`.
  - **Regra de integridade**: toda URL que aparece em qualquer `picture_ids` de variação **precisa** também estar presente no `pictures` do nível do anúncio. O workflow garante isso automaticamente.
- **`SELLER_SKU` por variação**: cada variação carrega seu próprio `SELLER_SKU` (SKU físico daquela cor) e `EAN` dentro de `attributes`. O SKU do "pai" (`pai_sku`) é usado só para idempotência/log, não vai no payload.
- **`available_quantity` sempre 1**: tanto no item quanto em cada variação. O Tiny é a fonte de verdade do estoque e corrige depois via integração ML PADRÃO.

### Códigos de erro comuns
- `401 Unauthorized` → token expirado, parar lote
- `403 Forbidden` → permissão; checar escopo do app
- `400 Bad Request` → payload inválido; campo obrigatório faltando
- `409 Conflict` → SKU duplicado

## API Tiny ERP

Documentação: https://developers.tiny.com.br/

Token em `.env` como `TINY_TOKEN`.

### Vincular MLB-id ao produto no Tiny

> 🔴 **ENDEREÇO INVENTADO — NÃO USAR. Conferido em 11/09/2026.**
> `anuncio.incluir.alterar.php` **não existe**. O servidor do Tiny responde `File not found.`,
> enquanto os endereços reais (ex.: `produto.obter.php`) respondem com erro em JSON do próprio Tiny.
> Também não existem `anuncio.php`, `anuncios.php`, `mapeamento.php`, `ecommerce.obter.php` nem
> `produto.mapeamento.incluir.php` — todos dão `File not found.`
>
> **O caminho real** para gravar o vínculo é `produto.alterar.php` mandando o array `mapeamentos[]`
> (`idEcommerce`, `skuMapeamento`, `urlProduto`, `urlImagem`), e ele **só é considerado com o header
> `Developer-Id` válido** — sem o header o Tiny ignora o campo **calado**, devolvendo sucesso.
> Na API v3 só existem 2 endpoints de anúncio, os dois de preço, e ambos exigem um `idMapeamento`
> que já exista. Ver memória `tiny_produto_cadastrado_vs_anuncio_vinculado`.
>
> O bloco abaixo fica só como registro do que foi alucinado.


```http
POST https://api.tiny.com.br/api2/anuncio.incluir.alterar.php
Content-Type: application/x-www-form-urlencoded

token=<TINY_TOKEN>
formato=json
anuncio={"sku":"TCD-LXI15","conta":"Mercado Livre","id_anuncio":"MLB5012345678","url":"https://..."}
```

Resposta com `status: "OK"` em caso de sucesso.

## Supabase — Logging

Schema `ml_tools`, tabela `publicacoes`:
```sql
CREATE TABLE ml_tools.publicacoes (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT NOT NULL,
  mlb_id TEXT,
  category_id TEXT,
  price NUMERIC,
  status TEXT, -- 'success' | 'failed'
  error_message TEXT,
  payload_request JSONB,
  payload_response JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Inserção via MCP supabase `execute_sql` ou via HTTP REST do PostgREST.
