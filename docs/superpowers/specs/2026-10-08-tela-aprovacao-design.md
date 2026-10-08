# Tela de aprovação do anúncio — desenho

**Data:** 08/10/2026 · **Pedido do Almir:** no dia a dia a esteira roda fora do Claude; ele quer um jeito prático de **ver, editar e escolher** o texto do anúncio, com todas as informações num lugar só.

**Escopo (opção A do Almir):** só a tela. O atalho que dispara a esteira inteira com clique duplo é a próxima peça, fora deste trabalho.

## 1. Como o Almir usa

1. Clique duplo em `tools/aprovacao/Aprovar anuncios.bat` (mesmo molde do `Entrar no catalogo.bat`).
2. Abre uma janela preta pequena (é a tela funcionando — fechar ela encerra) e o Chrome abre sozinho na página.
3. Um cartão por anúncio que está esperando aprovação (`status_copy` diferente de `aprovado`).
4. Ele escolhe/edita, vê os avisos atualizarem na hora e clica **Aprovar** ou **Devolver pra refazer**.

Página local: só este computador enxerga (escuta em `127.0.0.1`), sem internet, sem senha, sem instalar nada além do Python que já existe (só biblioteca padrão + `yaml`, já instalado).

## 2. O que o cartão mostra

| Bloco | De onde vem | Editável? |
|---|---|---|
| Nome, SKU pai, cores | `anuncio-{pai}.yaml` | não |
| Preço por cor, com selo **provisório** quando o anúncio ainda está no preço provisório | `anuncios-entrada.json` | não (preço é no Tiny) |
| Capas por cor (miniatura) | `capas/capas-{pai}.yaml`, se já existir; senão "capas ainda não buscadas" | não |
| Título: as opções da Renata (recomendada marcada ⭐) + "escrever o meu", contador ao vivo `NN/60` | `titles` | sim |
| Marca, contador ao vivo | `attributes.BRAND` | sim (padrão = fornecedor; trocar por `Terra Casa Decor`) |
| Modelo, contador `NN/30` | `attributes.MODEL` | sim |
| Descrição: 3 caixas (abertura, medidas, benefícios) | `description.bloco_*` | sim |
| Ficha técnica (resto dos campos) | `attributes` | não |
| Peso e caixa | `anuncios-entrada.json` | não |
| Observações da Renata | `warnings` | não |
| Conferência: ✅/❌ por regra, com o motivo em português | travas | — |

## 3. Conferência ao vivo

A cada mudança (com uma pausa curta depois de parar de digitar), a página manda o texto atual para o programa local, que roda **as mesmas travas da esteira** — `validar_ficha_seo.validar_ficha` e `validar_claims` (modo sem fotos, com o brief do anúncio) — e devolve a lista.

- **Bloqueia** (botão Aprovar desliga): título vazio ou com mais de 60 caracteres (o ML recusaria).
- **Avisa** (vermelho, com motivo): todo o resto. O botão vira **"Aprovar mesmo assim"**, e a aprovação grava quais avisos o Almir aceitou (`avisos_aceitos`), para ficar registrado.
- Avisos `WARN_*` aparecem em amarelo.
- Os códigos das travas viram frases simples na página (ex.: `PALAVRA_REPETIDA_TITULO` → "Estas palavras do Modelo já estão no título: pedal").

## 4. O que os botões gravam

**Aprovar** reescreve `anuncio-{pai}.yaml` com:
- `titulo_final` = título escolhido/escrito;
- `attributes.BRAND`, `attributes.MODEL`, `description.bloco_*` = o que está na tela;
- `status_copy: aprovado`, `aprovado_em: <data e hora>`, `avisos_aceitos: [códigos]`.

Antes de gravar, guarda uma cópia do arquivo anterior em `copywriting/_antes/anuncio-{pai}-<data-hora>.yaml` (desfazer é copiar de volta). Depois de gravar, roda as travas de novo no arquivo gravado e mostra o resultado — é a mesma conferência que o step-06 faz hoje.

**Devolver pra refazer** grava `status_copy: devolvido` + `nota_almir: <texto que ele escreveu>`; a Renata lê isso na próxima rodada.

O cartão aprovado/devolvido sai da lista (fica um resumo "aprovado às 14:32" no topo).

## 5. Peças

| Arquivo | Faz |
|---|---|
| `tools/aprovacao/Aprovar anuncios.bat` | clique duplo; chama o programa; avisa se não achar o Python |
| `tools/aprovacao/aprovacao.py` | lê/grava os arquivos, roda as travas, responde à página (servidor local da biblioteca padrão), abre o Chrome |
| `tools/aprovacao/pagina.html` | a tela (um arquivo só, sem nada da internet) |
| `tools/aprovacao/tests/test_aprovacao.py` | testes da parte que lê, confere e grava |

`aprovacao.py` separa a lógica (funções testáveis: `listar_pendentes`, `conferir`, `aprovar`, `devolver`) da parte que conversa com a página.

## 6. Erros

- Pasta de saída sem anúncio pendente → página diz "nada esperando aprovação".
- Arquivo do anúncio com defeito (não abre) → aquele cartão aparece com o erro, os outros funcionam.
- Porta ocupada → usa outra livre.
- Gravação: escreve num arquivo novo e só então troca pelo antigo (nunca deixa o anúncio pela metade se der erro no meio).

## 7. Mudança no step-06

O step-06 passa a dizer: a aprovação é feita na tela (`Aprovar anuncios.bat`); a esteira espera `status_copy: aprovado` em todos os anúncios do lote antes de seguir para o step-07. Quem aprova por esta conversa continua podendo (mesmos campos gravados).

## 8. Primeiro teste

5L (`VIE-1066-PAI`) e 8L (`VIE-1067-PAI`), que estão parados no step-06. O Almir aprova pela tela; confiro que `titulo_final`, Marca, Modelo e descrição gravados passam nas travas.

## 9. Fora deste trabalho

Atalho que dispara a esteira inteira; usar a mesma tela para o "sim" final de publicação (step-09) — fica para depois de a tela de texto estar aprovada no uso.
