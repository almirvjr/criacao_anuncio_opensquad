# Research Brief — Squad ML Anúncios

## Objetivo da Squad

Automatizar a criação, revisão e publicação de anúncios no Mercado Livre para a Terra Casa Decor a partir de uma planilha de produtos novos, com sincronização final no Tiny ERP.

## Empresa: Terra Casa Decor

- **Setor:** E-commerce de Casa & Decoração (São Paulo)
- **Tom:** Casual, acolhedor, acessível (próximo, de "casa", do dia a dia). **NÃO citar a marca da loja nem slogan no anúncio** — regra SEM MARCA (Almir 19/06); o tom é a voz, não o nome.
- **Catálogo:** Decoração, organização, mesa posta, cozinha, banheiro, móveis
- **Diferenciais:** Frete grátis acima de R$140 (Grande SP), entrega no mesmo dia, 5% no Pix, cashback

## Mercado Livre — Padrões Descobertos na Investigação

### Padrão de título (50-70 caracteres)
`[Tipo de produto] + [Material] + [Capacidade/Tamanho] + [Features mecânicas] + [Ambientes de uso] + [+Marca opcional]`

Exemplo: `Lixeira Inox 15L Pedal Tampa Antiodor Cozinha Banheiro LHP`

**Regras:**
- 7 a 10 tokens
- Categoria/material/capacidade SEMPRE nas primeiras palavras (escaneabilidade na busca ML)
- Marca no fim (a não ser que seja marca forte tipo Tramontina, aí pode ir no início)
- Mencionar ambientes de uso aumenta cobertura de busca

### Padrão de descrição (3 blocos, ~280 palavras)

**Bloco 1 — Abertura (lifestyle/benefício):** parágrafo de 3-5 linhas conectando o produto a um benefício do dia a dia.

**Bloco 2 — Especificações técnicas em bullets:** listagem de specs como "Material: Aço inox AISI 430", "Capacidade: 15 litros", etc.

**Bloco 3 — Features e benefícios + fechamento:** bullets no formato `Feature: Benefício` + frase final acolhedora **sem citar marca nem slogan** (regra SEM MARCA, Almir 19/06).

### Ficha técnica obrigatória (para lixeiras inox; varia por categoria)
- Material
- Capacidade (litros)
- Cor
- Dimensões (Altura x Largura x Profundidade)
- Peso
- Acionamento (Pedal / Manual / Toque)
- Tipo de tampa
- Balde removível (Sim/Não)
- Base antiderrapante (Sim/Não)
- Marca
- Modelo
- Ambientes de uso (Cozinha, Banheiro, Quarto, etc.)
- Garantia

## API Mercado Livre — Endpoints Críticos

| Operação | Endpoint | Auth |
|----------|----------|------|
| Predizer categoria | `GET /sites/MLB/category_predictor/predict?title=...` | pública |
| Buscar concorrentes | `GET /sites/MLB/search?q=...` | pública |
| Detalhes de categoria | `GET /categories/{category_id}` | pública |
| Atributos obrigatórios | `GET /categories/{category_id}/attributes` | pública |
| Criar anúncio | `POST /items` | Bearer token |
| Atualizar anúncio | `PUT /items/{item_id}` | Bearer token |
| Upload de imagens | `POST /pictures/items/upload` | Bearer token |

**Token:** tabela `public.access_token_ML` (Supabase), `app_name = 'pre-venda'`. Refresh automático pelo plugin `ml-kit`.

## Tiny ERP — Integração

Token de API Tiny em `.env` (`TINY_TOKEN`). Endpoint usado:
- `POST https://api.tiny.com.br/api2/anuncio.incluir.alterar.php` — para vincular MLB-id ao produto Tiny via SKU.

## Estratégia de Fotos (mix supplier + IA)

1. Caio Curador captura URL do site do fornecedor (se disponível na planilha) na etapa 2
2. Felipe Fotos roda `image-fetcher` sobre essa URL → traz N fotos
3. Se N < 10, complementa com `image-ai-generator` usando descrição do produto + fotos existentes como referência (variações de ângulo, detalhes, ambientação)
4. Todas as fotos passam por `image-creator` para padronização: fundo branco, recorte 1200x1200 mínimo, hierarquia visual (foto 1 = principal, fotos 2-5 = ângulos, fotos 6-8 = detalhes, fotos 9-10 = ambientação)

## Fontes da Pesquisa

- Investigação de 6 anúncios concorrentes (lixeiras inox) salvos em `_build/investigation/`
- Documentação oficial ML: https://developers.mercadolivre.com.br/
- API Tiny ERP: https://developers.tiny.com.br/
