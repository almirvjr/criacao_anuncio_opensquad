# PROGRESSO

> Atualizado 2026-10-16 (1ª publicação pelo botão: boleira MLB7828103466). **Frentes:** (1) **esteira de anúncio SEM fotos** — 1º teste com a Viel 5L e 8L (seção 0); (2) **ficha técnica dos anúncios no ar** (seção 5), parada esperando 4 decisões suas; (3) **Raio-X do anúncio** e (4) **entrar em catálogo sem oferta** — prontos e em uso. O trabalho de fotos do 8L foi encerrado aqui e vai para um projeto de fotos separado (HISTORICO 07/10).

## 0. Esteira sem fotos — 1º teste CONCLUÍDO em 08/10/2026 (Viel 5L e 8L, 3 cores cada)
**No ar, ativos, estoque vindo do Tiny (10 por cor), Flex ligado, descrição gravada:** 5L (R$ 92,71) Branco MLB7771661140 · Cinza MLB5354173009 · Preto MLB7771661510; 8L (R$ 112,71) Branco MLB7771685954 · Cinza MLB7771661556 · Preto MLB7771706672. Marca Terra Casa Decor, códigos de barras novos da GS1, caixa da cubagem.
**Como ficou a esteira:** aprovação do texto na tela (`tools/aprovacao/`, botão `2 - Aprovar anuncios` em `G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS`); publicação no **modelo novo do ML** (um anúncio por cor, `family_name`, preta primeiro, descrição e Flex em 2º envio) — ver `DECISOES.md` 2026-10-08 e step-10.
**Botão `1 - Criar anuncios` construído em 09/10/2026** (`tools/esteira_auto/`, ver DECISOES 2026-10-09): falta o ensaio real com a boleira Brinox `BRI-coza34-40652_3009` até a tela e a 1ª publicação com o Almir.
**1ª publicação pelo botão FEITA em 16/10/2026:** boleira `MLB7828103466` (HISTORICO 16/10).
**PRÓXIMO PASSO:** (1) melhorias da tela vistas na boleira (HISTORICO 16/10); (1b) levar a publicação (`ML Publicar`) do n8n para o Supabase (regra do hub de 09/10; virada com volta-atrás); (2) planilha de preços definitivos por canal (o preço do Tiny é simbólico, R$ 10); (3) minors adiados da tela (ver spec/plano 2026-10-08); (4) o `ML Publicar` ainda manda a descrição junto (ignorada) — poderia gravar ele mesmo no 2º envio.

## 4. Pendências
- Branch `esteira-sem-fotos` **no GitHub desde 15/10** (varrida sem segredo; repo PÚBLICO — conferir de novo a cada push). Fica fora do `main` enquanto o Almir testa.
- **Revisão de segurança 15/10 — falta o item 3:** `tools/esteira_auto/maestro.py` apontado como "dá pra pular a trava de aprovação" (decide pelo código de saída da tela). Confirmar se é real antes de mexer. Itens 1 (tela) e 2 (capas) corrigidos.
- **`ML Publicar`** (`0rzNJ7RLqLzMbKnf`) **LIGADO em 16/10/2026** (1ª publicação da boleira). Levar para o Supabase continua pendente.

## 5. Ficha técnica dos anúncios NO AR — `tools/auditoria_ficha/`
371 campos preenchidos em 146 anúncios (06-10/08). Nada alterou preço/fotos/estoque/variações.
**Esperando decisão do Almir:** (1) 6 anúncios com litros divergentes entre título e ficha — corrijo qual? (2) 5 travados no catálogo, só via "Sugerir correções" um a um; (3) 41 campos de vela — 1 cor por anúncio ou vazio? (4) 112 suspeitas (63 de caixa menor que o produto, mexe em frete; 49 de "Kit N" com ficha dizendo 1).
⚠️ Antes de qualquer lote: filtrar `catalog_listing=false` (catálogo responde 200 e IGNORA), rodar `validar_sugestoes.ps1`, comparar título antes/depois.
