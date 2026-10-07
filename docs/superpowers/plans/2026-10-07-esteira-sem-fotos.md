# Esteira de anúncio ML sem fotos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A squad `ml-anuncios` cria e publica o anúncio completo (texto, ficha, categoria, preço, medidas) usando capas que o Almir sobe no Cloudinary, sem gerar nenhuma foto.

**Architecture:** As travas determinísticas (Python) ganham um modo "sem fotos": `validar_brief` e `validar_claims` deixam de exigir o roteiro das 10 fotos e a transparência passa a ser cobrada no texto. Duas peças novas: `capas.py` (transforma o resultado da busca no Cloudinary em lista de fotos por cor, já em 1200×1200) e `validar_ficha_seo.py` (regra de Marca/Modelo de 07/10). O montador de pacote (`payload_builder.py`) passa a aceitar 1–10 fotos e ganha um comando (`montar_payload.py`) que a Paula usa em vez de montar o JSON na mão. Os `.md` das etapas são reescritos para o fluxo novo; o material de foto vai para `_arquivo-fotos/`, nada é apagado.

**Tech Stack:** Python 3 (stdlib + PyYAML + openpyxl + xlrd 2.0.2), pytest/unittest, MCP Cloudinary (`search-assets`), workflow n8n `ML Publicar` (`0rzNJ7RLqLzMbKnf`).

**Spec:** `docs/superpowers/specs/2026-10-07-esteira-sem-fotos-design.md`

## Global Constraints

- Raiz de trabalho: `C:\Users\Almir\workspace\projects\criacao_anuncio_opensquad` (abaixo, `<raiz>`). Todo caminho deste plano é relativo a ela.
- Nuvem Cloudinary: `wa5lvi98`. Etiqueta da capa: `capa-anuncio`. Cada foto tem também a etiqueta do SKU **da cor**, exatamente como no Tiny (ex.: `VIE-1066-3402-BR`).
- Foto entregue ao ML: `https://res.cloudinary.com/wa5lvi98/image/upload/c_pad,w_1200,h_1200,b_white,q_auto/<versão>/<public_id>.jpg` — 1200×1200, sem mexer no original.
- Fotos por cor: mínimo 1, máximo 10. Faltou capa de uma cor = para.
- Marca começa pelo fornecedor; Mundiart (`MDA`) = `Terra Casa Decor` e só. Marca e Modelo ~30 caracteres (passar de 30 = aviso, não bloqueio). Palavra da Marca (fora o nome do fornecedor) ou do Modelo que já está no título = bloqueio.
- "Terra Casa Decor" nunca no título; na descrição só para `MDA` (e aí obrigatório).
- Mapa de fornecedor por prefixo (regra do Almir, memória `sku_prefixos_fornecedor`): `VIE`=Viel, `PAR`=Paramount, `BRI`=Brinox, `EMB`=Embalixo, `MMP`=Passerini, `SEC`=Secalux, `MDA`=Terra Casa Decor. **Prefixo fora do mapa = parar e perguntar ao Almir, nunca deduzir pela sigla.**
- Peso e medida: planilha `G:\Meu Drive\TERRA CASA DECOR\ESTOQUE\CUBAGEM DOS PRODUTOS.xlsx`, aba `Produtos` (colunas: SKU, Descrição, Fornecedor, Peso bruto kg, Largura, Altura, Comprimento). Lá o SKU usa `_`; no Tiny os produtos novos usam `-` → casar trocando `_` por `-`.
- Preço provisório deste teste: R$ 100,00 (Almir, 07/10). A tela de conferência final mostra em destaque.
- Repositório é **público**: nada de segredo em arquivo commitado. Commits locais; **sem push** salvo pedido do Almir.
- Comunicação com o Almir: português simples, efeito primeiro, sem jargão (CLAUDE.md do hub).
- Testes dos validadores: `cd squads/ml-anuncios/pipeline/validators && python -m pytest -q tests/<arquivo>`. Testes do `tools`: `cd tools && python -m pytest -q esteira/tests/<arquivo>`.

## Review Focus

- **Capa marcada com o SKU do pai ou com `_` em vez de `-`** → `capas.py` tem que dizer exatamente qual cor ficou sem capa (não "erro genérico"), para o Almir corrigir a etiqueta. Teste: `test_sku_com_underscore_nao_casa_e_avisa_qual_falta` (Task 4).
- **Foto subida em PNG ou com nome com acento (`Aço`)** → o endereço para o ML sai em `.jpg`, com a parte codificada preservada. Teste: `test_url_ml_png_com_acento` (Task 4).
- **Pai sem medida na cubagem (só os filhos têm)** → o anúncio pega a maior medida/peso entre as cores, não zero. Teste: `test_anuncio_usa_maior_medida_dos_filhos` (Task 5).
- **Almir escolhe no checkpoint um título diferente do recomendado** → a checagem de repetição Marca/Modelo × título usa o `titulo_final`, não o recomendado. Teste: `test_usa_titulo_final_quando_existe` (Task 3).
- **Atributo COLOR da Renata no nível do anúncio em anúncio com cores** → não pode ir junto com as variações (o ML recusa ou anexa a cor no título). Teste: `test_color_sai_do_item_em_variacoes` (Task 6).

---

### Task 0: Fotografia do código atual (commit de base)

O código da squad está sem commit desde julho (PROGRESSO §4). Antes de mudar, salvar o estado atual para ter para onde voltar.

**Files:**
- Commit: arquivos já rastreados e modificados (`git add -u`), nada novo.

- [ ] **Step 1: Procurar segredo no que vai ser salvo**

Run:
```bash
cd <raiz> && git diff | grep -nEi "(api[_-]?key|secret|senha|password|token|shpat_|sk-[a-z0-9]{10}|eyJ[a-zA-Z0-9]{20})" | head -40
```
Expected: só nomes de variável/explicação (ex.: "`OPENROUTER_API_KEY` no `.env`"), nenhum valor. Se aparecer valor → PARAR e avisar o Almir (não commitar).

- [ ] **Step 2: Rodar os testes existentes (linha de base)**

Run:
```bash
cd <raiz>/squads/ml-anuncios/pipeline/validators && python -m pytest -q tests/test_validar_brief.py tests/test_validar_claims.py
cd <raiz>/tools && python -m pytest -q esteira/tests
```
Expected: `35 passed` e `14 passed`.

- [ ] **Step 3: Commit**

```bash
cd <raiz> && git add -u && git commit -m "chore: base da squad antes da esteira sem fotos (codigo pendente desde julho)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: `validar_brief` modo sem fotos

**Files:**
- Modify: `squads/ml-anuncios/pipeline/validators/validar_brief.py` (função `validate_brief` linha ~126; `main` linha ~305)
- Test: `squads/ml-anuncios/pipeline/validators/tests/test_validar_brief.py`

**Interfaces:**
- Produces: `validate_brief(brief, raw_dir=None, com_fotos=True) -> list[tuple[str,str]]`; CLI `validar_brief.py <brief> [--raw-dir X] [--sem-fotos]`.

- [ ] **Step 1: Escrever os testes que falham** (acrescentar ao fim da classe de testes existente; `brief_valido()` é o construtor de brief completo já existente no arquivo)

```python
    def test_sem_fotos_dispensa_briefing_e_cor_heroi(self):
        b = brief_valido()
        b.pop("briefing_fotos")
        b.pop("cor_heroi")
        erros = [e for e in validate_brief(b, com_fotos=False) if not e[0].startswith("WARN")]
        self.assertEqual(erros, [])

    def test_com_fotos_continua_exigindo_briefing(self):
        b = brief_valido()
        b.pop("briefing_fotos")
        codigos = [e[0] for e in validate_brief(b)]
        self.assertIn("FALTA_CAMPO", codigos)

    def test_sem_fotos_continua_exigindo_limitacoes_e_diagnostico(self):
        b = brief_valido()
        b.pop("briefing_fotos")
        b.pop("limitacoes")
        b["diagnostico"]["ansiedades"] = []
        codigos = [e[0] for e in validate_brief(b, com_fotos=False)]
        self.assertIn("FALTA_CAMPO", codigos)
        self.assertIn("SEM_ANSIEDADES", codigos)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest -q tests/test_validar_brief.py -k sem_fotos`
Expected: FAIL com `TypeError: validate_brief() got an unexpected keyword argument 'com_fotos'`.

- [ ] **Step 3: Implementar**

Na assinatura e nos campos de topo:
```python
def validate_brief(brief, raw_dir=None, com_fotos=True):
    """... com_fotos=False (esteira sem fotos, 07/10/2026): dispensa briefing_fotos e
    cor_heroi; o resto da trava (diagnostico, limitacoes, ancora) continua igual."""
    ...
    obrigatorios = ["pai_sku", "nome_base", "confianca", "dados_produto", "diagnostico",
                    "escada_e_dai", "limitacoes"]
    if com_fotos:
        obrigatorios += ["cor_heroi", "briefing_fotos"]
    for campo in obrigatorios:
        if campo not in brief or brief[campo] in (None, "", []):
            if campo == "limitacoes" and "limitacoes" in brief:
                continue
            E("FALTA_CAMPO", f"Campo de topo obrigatorio ausente/vazio: '{campo}'.")
```
E envolver o bloco inteiro de `# --- briefing_fotos: 10 slots ...` até o fim da checagem `SLOT_EXTRA` (inclusive) em `if com_fotos:` (indentar uma vez; nada dentro muda).

No `main`:
```python
    ap.add_argument("--sem-fotos", action="store_true",
                    help="Esteira sem fotos: nao exige roteiro das 10 fotos nem cor-heroi")
    ...
    erros = validate_brief(brief, raw_dir=raw_dir, com_fotos=not args.sem_fotos)
```

- [ ] **Step 4: Rodar tudo**

Run: `python -m pytest -q tests/test_validar_brief.py`
Expected: todos passam (os antigos + 3 novos).

- [ ] **Step 5: Commit**

```bash
git add squads/ml-anuncios/pipeline/validators/validar_brief.py squads/ml-anuncios/pipeline/validators/tests/test_validar_brief.py
git commit -m "feat(validar_brief): modo --sem-fotos

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `validar_claims` modo sem fotos

Sem fotos, a limitação (ex.: "sem balde interno") tem que estar declarada **no texto** — vira bloqueio.

**Files:**
- Modify: `squads/ml-anuncios/pipeline/validators/validar_claims.py` (`validar_claims` ~linha 152; `main` ~linha 270)
- Test: `squads/ml-anuncios/pipeline/validators/tests/test_validar_claims.py`

**Interfaces:**
- Produces: `validar_claims(brief, overlays_extra=None, copy_doc=None, sem_fotos=False) -> (blocks, warns)`; CLI `--sem-fotos` (exige `--copy`).

- [ ] **Step 1: Testes que falham** (usar `brief_base()` já existente no arquivo)

```python
class TestSemFotos(unittest.TestCase):
    def _brief(self):
        b = brief_base()
        b.pop("briefing_fotos")
        return b

    def test_sem_fotos_exige_copy(self):
        blocks, _ = validar_claims(self._brief(), sem_fotos=True)
        self.assertIn("COPY_OBRIGATORIA", [c for c, _ in blocks])

    def test_sem_fotos_limitacao_fora_da_copy_bloqueia(self):
        copy_doc = {"titles": [{"texto": "Lixeira Inox 5L Pedal", "recomendado": True}],
                    "description": {"bloco_1_abertura": "Lixeira bonita para a casa."}}
        blocks, _ = validar_claims(self._brief(), copy_doc=copy_doc, sem_fotos=True)
        self.assertIn("LIMITACAO_FORA_DA_COPY", [c for c, _ in blocks])

    def test_sem_fotos_limitacao_declarada_passa_e_nao_cobra_foto(self):
        copy_doc = {"titles": [{"texto": "Lixeira Inox 5L Pedal", "recomendado": True}],
                    "description": {"bloco_3": "Importante: modelo sem balde interno, usa saco comum."}}
        blocks, warns = validar_claims(self._brief(), copy_doc=copy_doc, sem_fotos=True)
        self.assertEqual(blocks, [])
        self.assertNotIn("LIMITACAO_NAO_DECLARADA", [c for c, _ in warns])

    def test_sem_fotos_claim_falso_na_copy_continua_bloqueando(self):
        copy_doc = {"titles": [{"texto": "Lixeira Inox 5L com balde interno", "recomendado": True}],
                    "description": {"bloco_3": "Modelo sem balde interno."}}
        blocks, _ = validar_claims(self._brief(), copy_doc=copy_doc, sem_fotos=True)
        self.assertIn("CLAIM_FALSO_COPY", [c for c, _ in blocks])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest -q tests/test_validar_claims.py -k SemFotos`
Expected: FAIL `unexpected keyword argument 'sem_fotos'`.

- [ ] **Step 3: Implementar**

```python
def validar_claims(brief, overlays_extra=None, copy_doc=None, sem_fotos=False):
    """... sem_fotos=True (esteira sem fotos, 07/10/2026): nao ha foto para declarar a
    limitacao, entao a transparencia passa a ser cobrada NA COPY (bloqueio) e a copy
    vira obrigatoria."""
    blocks, warns = [], []
    if not isinstance(brief, dict):
        return [("BRIEF_INVALIDO", "brief nao e mapa")], []
    if sem_fotos and not copy_doc:
        return [("COPY_OBRIGATORIA",
                 "Modo sem fotos: rode com --copy anuncio-{pai_sku}.yaml (a limitacao e "
                 "declarada no texto, nao ha foto).")], []
```
Envolver o bloco `# 2) TRANSPARENCIA` inteiro em `if not sem_fotos:`.
No bloco `# 4)`, trocar o `warns.append(("LIMITACAO_FORA_DA_COPY", ...))` por:
```python
                destino = blocks if sem_fotos else warns
                destino.append(("LIMITACAO_FORA_DA_COPY", ...mesma mensagem...))
```
No `main`:
```python
    ap.add_argument("--sem-fotos", action="store_true",
                    help="Esteira sem fotos: limitacao tem que estar no texto; exige --copy")
    ...
    blocks, warns = validar_claims(brief, overlays_extra=extra, copy_doc=copy_doc,
                                   sem_fotos=args.sem_fotos)
```

- [ ] **Step 4: Rodar tudo**

Run: `python -m pytest -q tests/test_validar_claims.py`
Expected: todos passam.

- [ ] **Step 5: Commit**

```bash
git add squads/ml-anuncios/pipeline/validators/validar_claims.py squads/ml-anuncios/pipeline/validators/tests/test_validar_claims.py
git commit -m "feat(validar_claims): modo --sem-fotos cobra limitacao no texto

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `validar_ficha_seo.py` (regra Marca/Modelo de 07/10)

**Files:**
- Create: `squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py`
- Test: `squads/ml-anuncios/pipeline/validators/tests/test_validar_ficha_seo.py`

**Interfaces:**
- Produces: `fornecedor_do_sku(sku) -> str|None`; `validar_ficha(pai_sku, titulo, marca, modelo, descricao) -> list[(codigo, msg)]` (códigos `WARN_*` não bloqueiam); `titulo_do_copy(copy_doc) -> str`; CLI `validar_ficha_seo.py <anuncio-{pai_sku}.yaml>` (sai 1 se houver bloqueio).

- [ ] **Step 1: Testes que falham**

```python
#!/usr/bin/env python3
"""Testes da regra Marca/Modelo (Almir 07/10/2026). Stdlib unittest."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validar_ficha_seo import fornecedor_do_sku, validar_ficha, titulo_do_copy  # noqa: E402

TIT = "Lixeira Inox 5L com Pedal e Tampa para Cozinha e Banheiro"
DESC = "Lixeira de inox com pedal para o dia a dia da casa."


def codigos(erros, so_bloqueio=True):
    return [c for c, _ in erros if not (so_bloqueio and c.startswith("WARN"))]


class TestFornecedor(unittest.TestCase):
    def test_prefixos(self):
        self.assertEqual(fornecedor_do_sku("VIE-1066-PAI"), "Viel")
        self.assertEqual(fornecedor_do_sku("MMP_123"), "Passerini")
        self.assertEqual(fornecedor_do_sku("MDA_9"), "Terra Casa Decor")
        self.assertIsNone(fornecedor_do_sku("KOU_1"))


class TestFicha(unittest.TestCase):
    def test_viel_ok(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica Antiodor", "Lixo Quarto Escritório", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_sem_fornecedor_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Lixeira Higiênica Viel", "Quarto", DESC)
        self.assertIn("MARCA_SEM_FORNECEDOR", codigos(e))

    def test_palavra_do_titulo_repetida_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Lixeira Inox", "Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_acento_nao_engana_repeticao(self):
        e = validar_ficha("VIE-1066-PAI", "Lixeira Aço Inox 5L Pedal Cozinha Banheiro Higiênica",
                          "Viel Higienica", "Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_marca_e_modelo_nao_repetem_entre_si(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Escritório", "Escritório Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_MARCA_MODELO", codigos(e))

    def test_acima_de_30_so_avisa(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica Antiodor Escritório", "Quarto", DESC)
        self.assertEqual(codigos(e), [])
        self.assertIn("WARN_MARCA_LONGA", codigos(e, so_bloqueio=False))

    def test_vazios_bloqueiam(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "", "", DESC)
        self.assertIn("MARCA_VAZIA", codigos(e))
        self.assertIn("MODELO_VAZIO", codigos(e))

    def test_prefixo_desconhecido_bloqueia(self):
        e = validar_ficha("KOU_1", TIT, "Kou Algo", "Quarto", DESC)
        self.assertIn("FORNECEDOR_DESCONHECIDO", codigos(e))

    def test_loja_na_descricao_de_nao_mundiart_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica", "Quarto", DESC + " Terra Casa Decor.")
        self.assertIn("DESCRICAO_CITA_LOJA", codigos(e))

    def test_loja_no_titulo_sempre_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Terra Casa Decor Sala", "Terra Casa Decor", "Arte Moderna",
                          "Quadro da Terra Casa Decor.")
        self.assertIn("TITULO_CITA_LOJA", codigos(e))

    def test_mundiart_ok(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala Abstrato Grande", "Terra Casa Decor",
                          "Arte Moderna Parede", "Um quadro da marca Terra Casa Decor para sua casa.")
        self.assertEqual(codigos(e), [])

    def test_mundiart_marca_com_palavra_chave_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala", "Terra Casa Decor Arte", "Parede",
                          "Marca Terra Casa Decor.")
        self.assertIn("MARCA_MUNDIART", codigos(e))

    def test_mundiart_descricao_sem_marca_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala", "Terra Casa Decor", "Parede", "Quadro lindo.")
        self.assertIn("DESCRICAO_SEM_MARCA_PROPRIA", codigos(e))


class TestTitulo(unittest.TestCase):
    def test_usa_titulo_final_quando_existe(self):
        doc = {"titulo_final": "Escolhido Pelo Almir",
               "titles": [{"texto": "Recomendado", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "Escolhido Pelo Almir")

    def test_cai_no_recomendado(self):
        doc = {"titles": [{"texto": "A", "recomendado": False}, {"texto": "B", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "B")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest -q tests/test_validar_ficha_seo.py`
Expected: FAIL `ModuleNotFoundError: No module named 'validar_ficha_seo'`.

- [ ] **Step 3: Implementar**

```python
#!/usr/bin/env python3
"""
validar_ficha_seo.py — regra de Marca e Modelo da ficha (Almir, 07/10/2026).

Marca e Modelo sao os campos da ficha que mais indexam na busca do ML. Neles vao
palavras-chave que NAO estao no titulo. A Marca comeca pelo fornecedor. Mundiart
(MDA) e marca propria: Marca = "Terra Casa Decor" e so; a descricao apresenta o
produto como Terra Casa Decor. O titulo nunca cita a loja.

Uso:  python validar_ficha_seo.py <anuncio-{pai_sku}.yaml>
Saida: 0 = OK (avisos podem aparecer) | 1 = BLOQUEADO.
"""
import argparse
import os
import re
import sys
import unicodedata

FORNECEDOR_POR_PREFIXO = {
    "VIE": "Viel", "PAR": "Paramount", "BRI": "Brinox", "EMB": "Embalixo",
    "MMP": "Passerini", "SEC": "Secalux", "MDA": "Terra Casa Decor",
}
MARCA_PROPRIA = "Terra Casa Decor"
TETO = 30
STOP = {"de", "da", "do", "das", "dos", "com", "e", "para", "pra", "em", "a", "o", "as", "os", "c", "p"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.lower()


def tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", norm(s)) if t and t not in STOP and len(t) > 1}


def fornecedor_do_sku(sku):
    prefixo = re.split(r"[-_]", str(sku or ""))[0].upper()
    return FORNECEDOR_POR_PREFIXO.get(prefixo)


def validar_ficha(pai_sku, titulo, marca, modelo, descricao):
    err = []
    E = lambda c, m: err.append((c, m))  # noqa: E731
    fornecedor = fornecedor_do_sku(pai_sku)
    mundiart = fornecedor == MARCA_PROPRIA
    marca, modelo = (marca or "").strip(), (modelo or "").strip()
    loja = norm(MARCA_PROPRIA)

    if fornecedor is None:
        E("FORNECEDOR_DESCONHECIDO",
          f"Prefixo do SKU '{pai_sku}' fora do mapa de fornecedores: perguntar ao Almir "
          f"(nunca deduzir pela sigla).")
    if not marca:
        E("MARCA_VAZIA", "Campo Marca vazio.")
    if not modelo:
        E("MODELO_VAZIO", "Campo Modelo vazio.")
    if len(marca) > TETO:
        E("WARN_MARCA_LONGA", f"Marca com {len(marca)} caracteres (alvo ~{TETO}): '{marca}'.")
    if len(modelo) > TETO:
        E("WARN_MODELO_LONGO", f"Modelo com {len(modelo)} caracteres (alvo ~{TETO}): '{modelo}'.")
    if loja in norm(titulo):
        E("TITULO_CITA_LOJA", "O titulo nunca cita 'Terra Casa Decor'.")

    if mundiart:
        if marca and marca != MARCA_PROPRIA:
            E("MARCA_MUNDIART", f"Mundiart: Marca tem que ser exatamente '{MARCA_PROPRIA}', veio '{marca}'.")
        if loja not in norm(descricao):
            E("DESCRICAO_SEM_MARCA_PROPRIA",
              "Mundiart: a descricao precisa apresentar o produto como da marca Terra Casa Decor.")
        chaves_marca = set()
    else:
        if fornecedor and marca and not norm(marca).startswith(norm(fornecedor)):
            E("MARCA_SEM_FORNECEDOR", f"Marca tem que comecar por '{fornecedor}', veio '{marca}'.")
        if loja in norm(descricao):
            E("DESCRICAO_CITA_LOJA", "So produto Mundiart cita 'Terra Casa Decor' na descricao.")
        chaves_marca = tokens(marca) - tokens(fornecedor or "")

    chaves_modelo = tokens(modelo)
    rep_titulo = sorted((chaves_marca | chaves_modelo) & tokens(titulo))
    if rep_titulo:
        E("PALAVRA_REPETIDA_TITULO",
          f"Palavras de Marca/Modelo que ja estao no titulo: {rep_titulo}. Trocar por termos novos.")
    rep_mm = sorted(chaves_marca & chaves_modelo)
    if rep_mm:
        E("PALAVRA_REPETIDA_MARCA_MODELO", f"Mesma palavra na Marca e no Modelo: {rep_mm}.")
    return err


def titulo_do_copy(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    for t in doc.get("titles") or []:
        if isinstance(t, dict) and t.get("recomendado"):
            return t.get("texto", "")
    return ""


def descricao_do_copy(doc):
    desc = doc.get("description") or {}
    return "\n\n".join(str(v) for k, v in sorted(desc.items())
                       if str(k).startswith("bloco") and isinstance(v, str))


def main():
    import yaml
    ap = argparse.ArgumentParser(description="Regra de Marca/Modelo da ficha (07/10/2026).")
    ap.add_argument("copy", help="anuncio-{pai_sku}.yaml da Renata")
    args = ap.parse_args()
    if not os.path.isfile(args.copy):
        print(f"ERRO: arquivo nao encontrado: {args.copy}", file=sys.stderr)
        sys.exit(2)
    with open(args.copy, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    attrs = doc.get("attributes") or {}
    pai = doc.get("pai_sku") or doc.get("sku")
    erros = validar_ficha(pai, titulo_do_copy(doc), attrs.get("BRAND"), attrs.get("MODEL"),
                          descricao_do_copy(doc))
    for c, m in erros:
        if c.startswith("WARN"):
            print(f"  [aviso] {c}: {m}")
    hard = [(c, m) for c, m in erros if not c.startswith("WARN")]
    if hard:
        print(f"\nFICHA REJEITADA - {len(hard)} erro(s):")
        for c, m in hard:
            print(f"  [{c}] {m}")
        sys.exit(1)
    print(f"FICHA OK - {pai}: Marca='{attrs.get('BRAND')}' Modelo='{attrs.get('MODEL')}'.")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar**

Run: `python -m pytest -q tests/test_validar_ficha_seo.py`
Expected: todos passam.

- [ ] **Step 5: Commit**

```bash
git add squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py squads/ml-anuncios/pipeline/validators/tests/test_validar_ficha_seo.py
git commit -m "feat: validar_ficha_seo (Marca/Modelo como palavra-chave, regra 07/10)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `capas.py` (busca do Cloudinary → fotos por cor)

O passo "buscar capas" é feito pelo orquestrador com a ferramenta `search-assets` do MCP Cloudinary (não há chave de API em disco). O resultado é salvo em arquivo e este script, determinístico, monta a lista de fotos por cor e trava se faltar alguma.

**Files:**
- Create: `squads/ml-anuncios/pipeline/validators/capas.py`
- Test: `squads/ml-anuncios/pipeline/validators/tests/test_capas.py`

**Interfaces:**
- Consumes: `anuncios-entrada.json` (Task 5: `anuncios[].pai_sku`, `anuncios[].variacoes[].sku`, `.cor`); JSON da busca `{"resources": [{"public_id", "secure_url", "tags", "created_at", "width", "height", "asset_id"}]}`.
- Produces: `url_ml(secure_url) -> str`; `montar(resources, anuncios) -> (dict[pai_sku, dict], list[str])`; arquivo `capas-{pai_sku}.yaml` = `{pai_sku, picture_ids_por_variacao: [{sku_variacao, cor, picture_ids: [url], origem: [{asset_id, public_id, width, height}]}]}`; CLI `capas.py <busca.json> <anuncios-entrada.json> <pasta_saida>` (sai 1 se faltar capa).

- [ ] **Step 1: Testes que falham**

```python
#!/usr/bin/env python3
"""Testes do montador de capas (esteira sem fotos, 07/10/2026)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from capas import url_ml, montar  # noqa: E402

BASE = "https://res.cloudinary.com/wa5lvi98/image/upload/"
TR = "c_pad,w_1200,h_1200,b_white,q_auto"


def res(pid, tags, ext="png", criado="2026-10-07T18:52:19+00:00"):
    return {"asset_id": pid, "public_id": pid, "tags": tags, "created_at": criado,
            "width": 1254, "height": 1254, "secure_url": f"{BASE}v1791399139/{pid}.{ext}"}


def anuncio(pai, skus):
    return {"pai_sku": pai, "variacoes": [{"sku": s, "cor": s[-2:]} for s in skus]}


class TestUrl(unittest.TestCase):
    def test_url_ml_jpg(self):
        self.assertEqual(url_ml(f"{BASE}v1/foto.jpg"), f"{BASE}{TR}/v1/foto.jpg")

    def test_url_ml_png_com_acento(self):
        u = f"{BASE}v1791386078/3405_Lixeira_Corpo_em_A%C3%A7o_Inox.png"
        self.assertEqual(url_ml(u), f"{BASE}{TR}/v1791386078/3405_Lixeira_Corpo_em_A%C3%A7o_Inox.jpg")

    def test_url_ml_idempotente(self):
        u = url_ml(f"{BASE}v1/foto.jpg")
        self.assertEqual(url_ml(u), u)

    def test_url_de_outra_nuvem_recusa(self):
        with self.assertRaises(ValueError):
            url_ml("https://res.cloudinary.com/outra/image/upload/v1/x.jpg")


class TestMontar(unittest.TestCase):
    def test_uma_capa_por_cor(self):
        rs = [res("a", ["capa-anuncio", "VIE-1066-3402-BR"]), res("b", ["VIE-1066-3405-PT", "capa-anuncio"])]
        capas, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])])
        self.assertEqual(erros, [])
        pv = capas["VIE-1066-PAI"]["picture_ids_por_variacao"]
        self.assertEqual([p["sku_variacao"] for p in pv], ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])
        self.assertEqual(pv[0]["picture_ids"], [f"{BASE}{TR}/v1791399139/a.jpg"])

    def test_sem_etiqueta_capa_ignora(self):
        rs = [res("a", ["VIE-1066-3402-BR"])]
        _, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR"])])
        self.assertTrue(any("VIE-1066-3402-BR" in e for e in erros))

    def test_sku_com_underscore_nao_casa_e_avisa_qual_falta(self):
        rs = [res("a", ["capa-anuncio", "VIE_1066_3402_BR"]), res("b", ["capa-anuncio", "VIE-1066-3405-PT"])]
        _, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])])
        self.assertEqual(len(erros), 1)
        self.assertIn("VIE-1066-3402-BR", erros[0])

    def test_mais_antiga_primeiro_e_teto_10(self):
        rs = [res(f"f{i:02d}", ["capa-anuncio", "S-1"], criado=f"2026-10-07T10:{i:02d}:00+00:00")
              for i in range(11, -1, -1)]
        capas, erros = montar(rs, [anuncio("P", ["S-1"])])
        self.assertTrue(any("mais de 10" in e for e in erros))
        self.assertTrue(capas["P"]["picture_ids_por_variacao"][0]["picture_ids"][0].endswith("/f00.jpg"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest -q tests/test_capas.py`
Expected: FAIL `ModuleNotFoundError: No module named 'capas'`.

- [ ] **Step 3: Implementar**

```python
#!/usr/bin/env python3
"""
capas.py — monta as fotos de cada cor a partir das capas que o Almir sobe no
Cloudinary (esteira sem fotos, 07/10/2026).

O Almir sobe a capa na pasta do fornecedor e etiqueta com o SKU DA COR + 'capa-anuncio'.
O orquestrador busca no Cloudinary (MCP search-assets, expression 'tags=capa-anuncio')
e salva o JSON da resposta; este script casa por SKU e trava se faltar cor.

Uso:  python capas.py <busca.json> <anuncios-entrada.json> <pasta_saida>
Saida: 0 = toda cor tem capa (grava capas-{pai_sku}.yaml) | 1 = falta capa (lista quais).
"""
import json
import os
import re
import sys

NUVEM = "wa5lvi98"
TAG_CAPA = "capa-anuncio"
TRANSF = "c_pad,w_1200,h_1200,b_white,q_auto"
PREFIXO = f"https://res.cloudinary.com/{NUVEM}/image/upload/"
MAX_FOTOS = 10


def url_ml(secure_url):
    """Endereco que o ML baixa: 1200x1200 em JPG, sem mexer no original."""
    if not str(secure_url).startswith(PREFIXO):
        raise ValueError(f"Foto fora da nuvem {NUVEM}: {secure_url}")
    resto = secure_url[len(PREFIXO):]
    if resto.startswith(TRANSF + "/"):
        resto = resto[len(TRANSF) + 1:]
    resto = re.sub(r"\.[A-Za-z0-9]+$", "", resto) + ".jpg"
    return f"{PREFIXO}{TRANSF}/{resto}"


def montar(resources, anuncios):
    capas_por_sku = {}
    for r in resources:
        tags = r.get("tags") or []
        if TAG_CAPA not in tags:
            continue
        for t in tags:
            if t != TAG_CAPA:
                capas_por_sku.setdefault(t, []).append(r)

    saida, erros = {}, []
    for a in anuncios:
        pv = []
        for v in a.get("variacoes", []):
            achadas = sorted(capas_por_sku.get(v["sku"], []), key=lambda r: r.get("created_at", ""))
            if not achadas:
                erros.append(f"{a['pai_sku']}: falta capa da cor '{v.get('cor')}' — nenhuma foto "
                             f"com as etiquetas '{TAG_CAPA}' + '{v['sku']}' (conferir se o SKU da "
                             f"etiqueta esta igual ao Tiny, com '-' e nao '_').")
                continue
            if len(achadas) > MAX_FOTOS:
                erros.append(f"{a['pai_sku']}: cor '{v.get('cor')}' tem {len(achadas)} fotos, "
                             f"mais de {MAX_FOTOS}. Usando as {MAX_FOTOS} mais antigas.")
                achadas = achadas[:MAX_FOTOS]
            pv.append({"sku_variacao": v["sku"], "cor": v.get("cor"),
                       "picture_ids": [url_ml(r["secure_url"]) for r in achadas],
                       "origem": [{k: r.get(k) for k in ("asset_id", "public_id", "width", "height")}
                                  for r in achadas]})
        saida[a["pai_sku"]] = {"pai_sku": a["pai_sku"], "picture_ids_por_variacao": pv}
    return saida, erros


def main():
    import yaml
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    busca, entrada, pasta = sys.argv[1:]
    with open(busca, encoding="utf-8") as fh:
        resources = json.load(fh).get("resources", [])
    with open(entrada, encoding="utf-8") as fh:
        anuncios = json.load(fh)["anuncios"]
    capas, erros = montar(resources, anuncios)
    os.makedirs(pasta, exist_ok=True)
    for pai, doc in capas.items():
        with open(os.path.join(pasta, f"capas-{pai}.yaml"), "w", encoding="utf-8") as fh:
            yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False)
        print(f"{pai}: " + ", ".join(f"{p['cor']}={len(p['picture_ids'])}"
                                     for p in doc["picture_ids_por_variacao"]))
    if erros:
        print(f"\nCAPAS INCOMPLETAS - {len(erros)}:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("CAPAS OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

Nota: a regra do teto "mais de 10" é um erro que **bloqueia** (sai 1) — o Almir decide quais tirar.

- [ ] **Step 4: Rodar**

Run: `python -m pytest -q tests/test_capas.py`
Expected: todos passam.

- [ ] **Step 5: Conferir 1 endereço de verdade**

Run:
```bash
curl -s -o /tmp/teste_capa.jpg -w "%{http_code} %{content_type}\n" "https://res.cloudinary.com/wa5lvi98/image/upload/c_pad,w_1200,h_1200,b_white,q_auto/v1791399139/Imagem_do_ChatGPT_7_de_out._de_2026_15_50_49-1.jpg" && python -c "from PIL import Image; print(Image.open('/tmp/teste_capa.jpg').size)"
```
(usar a pasta de rascunho da sessão no lugar de `/tmp`)
Expected: `200 image/jpeg` e `(1200, 1200)`.

- [ ] **Step 6: Commit**

```bash
git add squads/ml-anuncios/pipeline/validators/capas.py squads/ml-anuncios/pipeline/validators/tests/test_capas.py
git commit -m "feat: capas.py monta fotos por cor a partir das etiquetas do Cloudinary

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Tradutor do Tiny — `.xls`, fornecedor, cubagem e preço provisório

**Files:**
- Modify: `tools/tiny_to_esteira.py`
- Modify: `tools/esteira/normalizer.py` (`_anuncio`, `_variacao`)
- Test: `tools/esteira/tests/test_tiny_to_esteira.py` (novo), `tools/esteira/tests/test_normalizer.py`

**Interfaces:**
- Produces: `ler_linhas(path) -> list[tuple]`; `sku_chave(sku) -> str`; `carregar_cubagem(path) -> dict[str, dict]`; `aplicar_cubagem(records, cub) -> int` (quantos preencheu); CLI `tiny_to_esteira.py <planilha .xls|.xlsx> <saida.json> [--cubagem PATH] [--preco-provisorio VALOR]`. Cada anúncio ganha `fornecedor`, `peso_bruto_kg`, `dim_embalagem_cm` (maior entre as cores quando o pai vem zerado), `preco_provisorio: bool`; cada variação ganha `peso_bruto_kg` e `dim_embalagem_cm`.

- [ ] **Step 1: Testes que falham**

`tools/esteira/tests/test_tiny_to_esteira.py`:
```python
import openpyxl

from tiny_to_esteira import sku_chave, aplicar_cubagem, carregar_cubagem, ler_linhas


def test_sku_chave_iguala_traco_e_underline():
    assert sku_chave("VIE_1066_3402_BR") == sku_chave("vie-1066-3402-br") == "VIE-1066-3402-BR"


def test_aplicar_cubagem_preenche_so_o_zerado():
    recs = [{"sku": "VIE-1066-3402-BR", "peso_bruto": 0.0,
             "dim_cm": {"largura": 0.0, "altura": 0.0, "comprimento": 0.0}},
            {"sku": "VIE-1066-3405-PT", "peso_bruto": 1.5,
             "dim_cm": {"largura": 10, "altura": 10, "comprimento": 10}}]
    cub = {"VIE-1066-3402-BR": {"peso_bruto": 0.7, "largura": 28, "altura": 21, "comprimento": 21},
           "VIE-1066-3405-PT": {"peso_bruto": 0.7, "largura": 28, "altura": 21, "comprimento": 21}}
    assert aplicar_cubagem(recs, cub) == 1
    assert recs[0]["peso_bruto"] == 0.7 and recs[0]["dim_cm"]["largura"] == 28
    assert recs[1]["peso_bruto"] == 1.5  # nao sobrescreve o que ja tinha


def test_carregar_cubagem_le_aba_produtos(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Produtos"
    ws.append(["Codigo (SKU)", "Descricao", "Fornecedor", "Peso bruto (kg)", "Largura", "Altura", "Comprimento"])
    ws.append(["VIE_1067_3403_BR", "LIXEIRA 8L", "VIEL", 0.9, 37, 21, 21])
    p = tmp_path / "cub.xlsx"
    wb.save(p)
    cub = carregar_cubagem(str(p))
    assert cub["VIE-1067-3403-BR"] == {"peso_bruto": 0.9, "largura": 37, "altura": 21, "comprimento": 21}


def test_ler_linhas_xlsx(tmp_path):
    wb = openpyxl.Workbook()
    wb.active.append(["Código (SKU)", "Preço"])
    wb.active.append(["X-1", 10.0])
    p = tmp_path / "t.xlsx"
    wb.save(p)
    assert ler_linhas(str(p))[1] == ("X-1", 10.0)
```

Acrescentar em `tools/esteira/tests/test_normalizer.py`:
```python
def test_anuncio_usa_maior_medida_dos_filhos():
    recs = [
        {"sku": "P", "nome": "Pai", "peso_bruto": 0.0, "dim_cm": {"largura": 0, "altura": 0, "comprimento": 0}},
        {"sku": "P-BR", "cod_pai": "P", "variacoes_raw": "Cor:Branco||", "peso_bruto": 0.7,
         "dim_cm": {"largura": 28, "altura": 21, "comprimento": 21}, "fornecedor": "VIEL"},
        {"sku": "P-PT", "cod_pai": "P", "variacoes_raw": "Cor:Preto||", "peso_bruto": 0.9,
         "dim_cm": {"largura": 30, "altura": 21, "comprimento": 21}, "fornecedor": "VIEL"},
    ]
    a = normalize(recs)["anuncios"][0]
    assert a["peso_bruto_kg"] == 0.9
    assert a["dim_embalagem_cm"] == {"largura": 30, "altura": 21, "comprimento": 21}
    assert a["fornecedor"] == "VIEL"
    assert a["variacoes"][0]["peso_bruto_kg"] == 0.7
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd tools && python -m pytest -q esteira/tests`
Expected: FAIL (`ImportError: cannot import name 'sku_chave'` e o teste novo do normalizer).

- [ ] **Step 3: Implementar — `tools/tiny_to_esteira.py`**

Acrescentar `"fornecedor": "fornecedor",` ao `WANT`. Trocar `s()` e a leitura e acrescentar as funções:
```python
import argparse


def s(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)  # xlrd devolve numero como float: 7896835234023.0 -> "7896835234023"
    return str(v).strip() if v not in (None, "") else None


def ler_linhas(path):
    """Linhas da 1a aba. O Tiny exporta .xls (formato antigo) ou .xlsx."""
    if path.lower().endswith(".xls"):
        import xlrd
        sh = xlrd.open_workbook(path, ignore_workbook_corruption=True).sheet_by_index(0)
        return [tuple(sh.row_values(i)) for i in range(sh.nrows)]
    ws = openpyxl.load_workbook(path, data_only=True).active
    return list(ws.iter_rows(values_only=True))


def sku_chave(sku):
    return str(sku or "").strip().upper().replace("_", "-")


def carregar_cubagem(path):
    """Planilha de cubagem (regra do Almir: fonte de peso e medida). Casa por SKU."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)["Produtos"]
    out = {}
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r or not r[0]:
            continue
        out[sku_chave(r[0])] = {"peso_bruto": r[3], "largura": r[4], "altura": r[5], "comprimento": r[6]}
    return out


def _vazio(x):
    try:
        return not x or float(x) == 0
    except (TypeError, ValueError):
        return True


def aplicar_cubagem(records, cub):
    n = 0
    for rec in records:
        c = cub.get(sku_chave(rec["sku"]))
        if not c:
            continue
        mexeu = False
        if _vazio(rec.get("peso_bruto")) and not _vazio(c["peso_bruto"]):
            rec["peso_bruto"] = c["peso_bruto"]
            mexeu = True
        dim = rec.get("dim_cm") or {}
        if all(_vazio(dim.get(k)) for k in ("largura", "altura", "comprimento")):
            rec["dim_cm"] = {k: c[k] for k in ("largura", "altura", "comprimento")}
            mexeu = True
        if mexeu:
            rec["fonte_medida"] = "cubagem"
            n += 1
    return n
```
Em `main`, trocar `inp, outp = sys.argv[1], sys.argv[2]` e `ws = ...; rows = ...` por:
```python
    ap = argparse.ArgumentParser(description="Planilha Tiny -> anuncios-entrada.json")
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--cubagem", help="CUBAGEM DOS PRODUTOS.xlsx (fonte de peso e medida)")
    ap.add_argument("--preco-provisorio", type=float,
                    help="Sobrescreve o preco de todas as cores e marca preco_provisorio=true")
    args = ap.parse_args()
    inp, outp = args.entrada, args.saida
    rows = ler_linhas(inp)
```
No dicionário de cada record acrescentar `"fornecedor": s(cell("fornecedor")),`. Depois do laço, antes de `normalize`:
```python
    if args.cubagem:
        n = aplicar_cubagem(records, carregar_cubagem(args.cubagem))
        print(f"cubagem: peso/medida preenchidos em {n} SKU(s)", file=sys.stderr)
    if args.preco_provisorio is not None:
        for r in records:
            r["preco_venda"] = round(args.preco_provisorio, 2)
    out = normalize(records)
    for a in out["anuncios"]:
        a["preco_provisorio"] = args.preco_provisorio is not None
```

- [ ] **Step 4: Implementar — `tools/esteira/normalizer.py`**

```python
def _num(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _medidas(base, filhos):
    """Pai costuma vir zerado no Tiny e fora da cubagem: usa a maior medida entre as cores."""
    fontes = [base] + list(filhos)
    peso = max(_num(f.get("peso_bruto")) for f in fontes)
    dim = {k: max(_num((f.get("dim_cm") or {}).get(k)) for f in fontes)
           for k in ("largura", "altura", "comprimento")}
    dim = {k: (int(v) if float(v).is_integer() else v) for k, v in dim.items()}
    return (peso or None), dim
```
Em `_variacao` acrescentar:
```python
            "peso_bruto_kg": f.get("peso_bruto"), "dim_embalagem_cm": f.get("dim_cm", {}),
```
Em `_anuncio`: calcular `peso, dim = _medidas(base, filhos)` e usar `"peso_bruto_kg": peso, "dim_embalagem_cm": dim,` e acrescentar `"fornecedor": base.get("fornecedor") or next((f.get("fornecedor") for f in filhos if f.get("fornecedor")), None),`.

- [ ] **Step 5: Rodar os testes**

Run: `cd tools && python -m pytest -q esteira/tests`
Expected: todos passam (14 antigos + 5 novos).

- [ ] **Step 6: Rodar com a planilha real**

Run:
```bash
cd <raiz> && set PYTHONUTF8=1 && python tools/tiny_to_esteira.py "C:\Users\Almir\Downloads\produtos_2026-10-07-12-07-32.xls" squads/ml-anuncios/output/anuncios-entrada.json --cubagem "G:\Meu Drive\TERRA CASA DECOR\ESTOQUE\CUBAGEM DOS PRODUTOS.xlsx" --preco-provisorio 100 > NUL
python -c "import json;d=json.load(open('squads/ml-anuncios/output/anuncios-entrada.json',encoding='utf-8'));[print(a['pai_sku'],a['peso_bruto_kg'],a['dim_embalagem_cm'],a['fornecedor'],[(v['sku'],v['cor'],v['ean'],v['preco_venda']) for v in a['variacoes']]) for a in d['anuncios']]"
```
Expected: 2 anúncios; `VIE-1066-PAI 0.7 {largura 28, altura 21, comprimento 21}` e `VIE-1067-PAI 0.9 {37, 21, 21}`; 3 cores cada (Branco/Cinza/Preto), EAN de 13 dígitos sem `.0`, preço 100.0, fornecedor `VIEL INDUSTRIA METALURGICA LTDA.`; stderr `cubagem: ... 6 SKU(s)`.

- [ ] **Step 7: Commit**

```bash
git add tools/tiny_to_esteira.py tools/esteira/normalizer.py tools/esteira/tests/test_tiny_to_esteira.py tools/esteira/tests/test_normalizer.py
git commit -m "feat(tiny_to_esteira): le .xls, fornecedor, cubagem e preco provisorio

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Montador do pacote — 1 a 10 fotos, medida da caixa, comando `montar_payload.py`

**Files:**
- Modify: `tools/esteira/payload_builder.py`
- Create: `tools/montar_payload.py`
- Test: `tools/esteira/tests/test_payload_builder.py`, `tools/esteira/tests/test_montar_payload.py` (novo)

**Interfaces:**
- Consumes: `anuncios-entrada.json` (Task 5), `categorias.yaml` (Cibele: `categorias[].pai_sku/category_id/cor_value_map`), `anuncio-{pai}.yaml` (Renata: `titles`, `titulo_final`, `description.bloco_*`, `attributes{}`), `capas-{pai}.yaml` (Task 4).
- Produces: `build_payload(...)` igual à assinatura atual; `atributos_embalagem(anuncio) -> list[dict]`; `item_attributes_do_copy(attrs: dict, modo) -> list[dict]`; CLI `montar_payload.py --entrada E --categorias C --copy Y --capas K --pai P --saida S` grava o JSON que vai pro webhook.

- [ ] **Step 1: Ajustar/escrever os testes**

Em `test_payload_builder.py`: substituir `test_lista_de_fotos_com_tamanho_errado_falha` por:
```python
def test_aceita_de_1_a_10_fotos():
    ctx = _ctx()
    ctx["picture_ids_por_variacao"] = [
        {"sku_variacao": "VIE_1066_3402_BR", "picture_ids": ["http://b/capa-br.jpg"]},
        {"sku_variacao": "VIE_1066_3405_PT", "picture_ids": _fotos("VIE_1066_3405_PT", 10)},
    ]
    p = build_payload(_anuncio_var(), **ctx)
    assert p["variacoes"][0]["picture_ids"] == ["http://b/capa-br.jpg"]


def test_mais_de_10_fotos_falha():
    ctx = _ctx()
    ctx["picture_ids_por_variacao"][0]["picture_ids"] = _fotos("VIE_1066_3402_BR", 11)
    with pytest.raises(ValueError, match="11"):
        build_payload(_anuncio_var(), **ctx)


def test_validate_nao_exige_mais_foto_do_felipe():
    a = _anuncio_var()
    for v in a["variacoes"]:
        v["fotos_cor"] = []
    assert validate_anuncio(a) == []


def test_medida_da_caixa_vai_como_atributo():
    a = _anuncio_var()
    a["peso_bruto_kg"] = 0.7
    a["dim_embalagem_cm"] = {"largura": 28, "altura": 21, "comprimento": 21}
    p = build_payload(a, **_ctx())
    assert {"id": "SELLER_PACKAGE_WEIGHT", "value_name": "700 g"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_LENGTH", "value_name": "21 cm"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_WIDTH", "value_name": "28 cm"} in p["attributes"]
    assert {"id": "SELLER_PACKAGE_HEIGHT", "value_name": "21 cm"} in p["attributes"]


def test_sem_medida_nao_inventa_atributo():
    p = build_payload(_anuncio_var(), **_ctx())
    assert not [x for x in p["attributes"] if x["id"].startswith("SELLER_PACKAGE")]
```
(Se `test_variacao_sem_fotos_do_felipe_falha_alto` checa a mensagem com "Felipe"/"step-07", trocar o `match` para `"capa"`.)

`tools/esteira/tests/test_montar_payload.py`:
```python
import json

import yaml

from montar_payload import item_attributes_do_copy, montar


def test_color_sai_do_item_em_variacoes():
    attrs = {"BRAND": "Viel Higienica", "MODEL": "Quarto", "COLOR": "Preto", "CAPACITY": "5 L"}
    ids = [a["id"] for a in item_attributes_do_copy(attrs, "variacoes")]
    assert "COLOR" not in ids and "BRAND" in ids and "CAPACITY" in ids
    assert "COLOR" in [a["id"] for a in item_attributes_do_copy(attrs, "simples")]


def test_montar_ponta_a_ponta(tmp_path):
    entrada = {"anuncios": [{"modo": "variacoes", "pai_sku": "VIE-1066-PAI", "marca": None,
                             "peso_bruto_kg": 0.7, "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
                             "variacoes": [{"sku": "VIE-1066-3402-BR", "cor": "Branco", "ean": "789", "preco_venda": 100.0}]}]}
    cat = {"categorias": [{"pai_sku": "VIE-1066-PAI", "category_id": "MLB33375",
                           "cor_value_map": [{"cor": "Branco", "value_id": "52049", "value_name": "Branco"}]}]}
    copy_doc = {"pai_sku": "VIE-1066-PAI", "titulo_final": "Lixeira Inox 5L Pedal",
                "titles": [{"texto": "Outro", "recomendado": True}],
                "description": {"bloco_1_abertura": "Um.", "bloco_2_specs": "Dois."},
                "attributes": {"BRAND": "Viel Higienica", "MODEL": "Quarto", "COLOR": "Branco"}}
    capas = {"pai_sku": "VIE-1066-PAI", "picture_ids_por_variacao": [
        {"sku_variacao": "VIE-1066-3402-BR", "picture_ids": ["https://x/capa.jpg"]}]}
    p = {}
    for nome, doc in (("e.json", entrada), ("c.yaml", cat), ("y.yaml", copy_doc), ("k.yaml", capas)):
        f = tmp_path / nome
        f.write_text(json.dumps(doc) if nome.endswith(".json") else yaml.safe_dump(doc), encoding="utf-8")
        p[nome] = str(f)
    payload = montar(p["e.json"], p["c.yaml"], p["y.yaml"], p["k.yaml"], "VIE-1066-PAI")
    assert payload["title"] == "Lixeira Inox 5L Pedal"
    assert payload["description_plain"] == "Um.\n\nDois."
    assert payload["category_id"] == "MLB33375"
    assert payload["variacoes"][0]["picture_ids"] == ["https://x/capa.jpg"]
    assert payload["variacoes"][0]["price"] == 100.0
    assert "COLOR" not in [a["id"] for a in payload["attributes"]]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd tools && python -m pytest -q esteira/tests`
Expected: FAIL nos testes novos (`ModuleNotFoundError: montar_payload`, fotos != 10, falta SELLER_PACKAGE).

- [ ] **Step 3: Implementar — `payload_builder.py`**

```python
FOTOS_MIN, FOTOS_MAX = 1, 10   # esteira sem fotos (07/10/2026): capa do Almir, ate 10 por cor
```
Trocar `_fotos_da_variacao`:
```python
def _fotos_da_variacao(mapa, sku):
    fotos = mapa.get(sku)
    if not fotos:
        raise ValueError(
            f"Sem foto para a variacao {sku}: falta a capa dessa cor no Cloudinary "
            f"(etiquetas 'capa-anuncio' + '{sku}'). Anuncio nao vai ao ar sem foto.")
    if not (FOTOS_MIN <= len(fotos) <= FOTOS_MAX):
        raise ValueError(f"Variacao {sku} veio com {len(fotos)} fotos; o ML aceita de "
                         f"{FOTOS_MIN} a {FOTOS_MAX}.")
    return fotos
```
Em `validate_anuncio`, apagar as duas linhas do `fotos_cor`. Acrescentar:
```python
def atributos_embalagem(anuncio):
    """Medida da CAIXA (cubagem) — e a que manda no frete do ML. Sem medida: nao inventa."""
    peso = anuncio.get("peso_bruto_kg")
    dim = anuncio.get("dim_embalagem_cm") or {}
    try:
        peso = float(peso or 0)
        l, a, c = (float(dim.get(k) or 0) for k in ("largura", "altura", "comprimento"))
    except (TypeError, ValueError):
        return []
    if not (peso and l and a and c):
        return []
    fmt = lambda x: f"{int(x)}" if float(x).is_integer() else f"{x}"  # noqa: E731
    return [{"id": "SELLER_PACKAGE_HEIGHT", "value_name": f"{fmt(a)} cm"},
            {"id": "SELLER_PACKAGE_WIDTH", "value_name": f"{fmt(l)} cm"},
            {"id": "SELLER_PACKAGE_LENGTH", "value_name": f"{fmt(c)} cm"},
            {"id": "SELLER_PACKAGE_WEIGHT", "value_name": f"{int(round(peso * 1000))} g"}]
```
Em `build_payload`, logo no começo: `item_attributes = list(item_attributes) + atributos_embalagem(anuncio)` (antes de montar `base`).

- [ ] **Step 4: Implementar — `tools/montar_payload.py`**

```python
"""Monta o pacote que a Paula envia ao webhook ML Publicar (esteira sem fotos, 07/10/2026).

A Paula NAO monta o JSON na mao: roda este comando. Regras (1-10 fotos por cor, preco
igual, medida da caixa) moram no payload_builder e tem teste.

Uso:
  python montar_payload.py --entrada anuncios-entrada.json --categorias categorias.yaml \
      --copy anuncio-{pai}.yaml --capas capas-{pai}.yaml --pai {pai} --saida payload-{pai}.json
"""
import argparse
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esteira.payload_builder import build_payload, validate_anuncio  # noqa: E402


def _yaml(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def item_attributes_do_copy(attrs, modo):
    """Ficha da Renata -> lista do ML. Em anuncio com cores, COLOR vai na variacao, nao no item."""
    out = []
    for k, v in (attrs or {}).items():
        if v in (None, ""):
            continue
        if modo == "variacoes" and k == "COLOR":
            continue
        out.append({"id": k, "value_name": str(v)})
    return out


def _titulo(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    return next(t["texto"] for t in doc.get("titles", []) if t.get("recomendado"))


def _descricao(doc):
    desc = doc.get("description") or {}
    return "\n\n".join(str(v).strip() for k, v in sorted(desc.items())
                       if str(k).startswith("bloco") and isinstance(v, str))


def montar(entrada, categorias, copy, capas, pai):
    with open(entrada, encoding="utf-8") as fh:
        anuncio = next(a for a in json.load(fh)["anuncios"] if a["pai_sku"] == pai)
    cat = next(c for c in _yaml(categorias)["categorias"] if c["pai_sku"] == pai)
    doc = _yaml(copy)
    erros = validate_anuncio(anuncio)
    if erros:
        raise ValueError("; ".join(erros))
    return build_payload(
        anuncio, title=_titulo(doc), category_id=cat["category_id"],
        description_plain=_descricao(doc),
        picture_ids_por_variacao=_yaml(capas)["picture_ids_por_variacao"],
        cor_value_map=cat.get("cor_value_map"),
        item_attributes=item_attributes_do_copy(doc.get("attributes"), anuncio["modo"]))


def main():
    ap = argparse.ArgumentParser()
    for a in ("--entrada", "--categorias", "--copy", "--capas", "--pai", "--saida"):
        ap.add_argument(a, required=True)
    x = ap.parse_args()
    payload = montar(x.entrada, x.categorias, x.copy, x.capas, x.pai)
    with open(x.saida, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"PAYLOAD OK - {x.pai} -> {x.saida}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Rodar**

Run: `cd tools && python -m pytest -q esteira/tests`
Expected: todos passam.

- [ ] **Step 6: Commit**

```bash
git add tools/esteira/payload_builder.py tools/montar_payload.py tools/esteira/tests/test_payload_builder.py tools/esteira/tests/test_montar_payload.py
git commit -m "feat: pacote aceita 1-10 fotos, leva medida da caixa; comando montar_payload

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Etapas de texto (Helena e Renata) no fluxo novo

**Files:**
- Modify: `squads/ml-anuncios/pipeline/steps/step-04-inteligencia-conversao.md`, `step-04b-checkpoint-dados.md`, `step-05-copywriting.md`, `step-06-checkpoint-copy.md`
- Modify: `squads/ml-anuncios/agents/helena-estrategista.agent.md`, `squads/ml-anuncios/agents/renata-redatora.agent.md`

- [ ] **Step 1: step-04 (Helena)**
  - Remover o item 7 "Briefing das 10 fotos" inteiro, o veto 4 ("menos de 10 slots") e o checklist "Briefing das 10 fotos completo".
  - Item 6b (`limitacoes[]`): trocar `{texto, fonte, disclosure_foto}` por `{texto, fonte}` e a frase sobre slot por: "A limitação é declarada **na descrição** (a Renata cobre; a trava `validar_claims --sem-fotos` bloqueia se faltar)."
  - Linha 48: remover a nota "obrigatorio para fotos Felipe".
  - Bloco da trava (linhas ~86-91) vira:
    ```
    python squads/ml-anuncios/pipeline/validators/validar_brief.py squads/ml-anuncios/output/inteligencia/brief-{pai_sku}.yaml --sem-fotos
    ```
    "O step-04 só está concluído quando ela sai com código 0." (o `validar_claims` sai daqui e vai para o step-05, porque sem foto a limitação só pode ser conferida no texto).
  - Acrescentar ao fim de Instructions: "**Palavras-chave para a ficha:** levantar, nos títulos dos concorrentes e no autocompletar da busca do ML, as 8–12 palavras mais buscadas do produto e gravar em `keywords_busca: [..]` no brief — a Renata usa para Marca e Modelo."
- [ ] **Step 2: helena-estrategista.agent.md** — trocar toda menção à entrega "briefing das 10 fotos / slots / cor_heroi para fotos" por "o brief serve só ao texto e à ficha (esteira sem fotos desde 07/10/2026)"; acrescentar `keywords_busca` no formato de saída.
- [ ] **Step 3: step-04b** — comando da trava com `--sem-fotos`; remover a seção "Cor-herói — confirmação por exceção" e o veto que fala do step-07; o gate duro de dimensões passa a dizer "peso e medida da **caixa** vêm da cubagem (`tiny_to_esteira --cubagem`); medida do **produto** é opcional e só entra na descrição se existir"; texto "10 slots com função canônica" sai da descrição da trava.
- [ ] **Step 4: renata-redatora.agent.md** — substituir o parágrafo "**Campo `BRAND` da ficha:** recebe a marca do fabricante..." por:

  > **Campos `BRAND` (Marca) e `MODEL` (Modelo) — regra do Almir, 07/10/2026.** São os campos da ficha que mais indexam na busca. Neles vão as palavras-chave mais buscadas (`keywords_busca` do brief) **que não estão no título escolhido** — nada repetido entre título, Marca e Modelo. A Marca **começa pelo fornecedor** (Viel, Brinox, Bellagio, Passerini…) e segue com palavras-chave; ~30 caracteres em cada campo. **Mundiart (`MDA`)**: Marca = `Terra Casa Decor` e mais nada; a descrição apresenta o produto como da marca Terra Casa Decor (o título nunca cita a loja). A trava `validar_ficha_seo.py` é a autoridade.

  E no regra 3 ("Sem marca da loja"): acrescentar "— exceto Mundiart, ver campo `BRAND`". No gabarito: `BRAND: "Viel Higiênica Antiodor"` / `MODEL: "Lixo Quarto Escritório"` (o título do gabarito não pode conter essas palavras) e apagar o comentário "fabricante do dossiê — nunca o nome da loja". Gabarito: acrescentar `pai_sku:` no topo do YAML.
- [ ] **Step 5: step-05** — o bloco "A trava" vira:
  ```
  python squads/ml-anuncios/pipeline/validators/validar_claims.py <brief-{pai_sku}.yaml> --copy <anuncio-{pai_sku}.yaml> --sem-fotos
  python squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py <anuncio-{pai_sku}.yaml>
  ```
  "As duas têm que sair com código 0." Exemplo de `attributes` na linha ~169: `BRAND: "Viel Higiênica Antiodor"`, `MODEL: "Lixo Quarto Escritório"` (e o título do exemplo sem essas palavras).
- [ ] **Step 6: step-06** — remover "Antes de gerar fotos (etapa cara, ~$0.40 por SKU)" e o veto 4 (custo de fotos). Em "Registrar decisão", acrescentar: "Depois de gravar o `titulo_final`, rodar `validar_ficha_seo.py anuncio-{pai_sku}.yaml` de novo — se o Almir escolheu outro título, uma palavra de Marca/Modelo pode ter virado repetida. Reprovou → Renata troca Marca/Modelo, sem mexer no título escolhido."
- [ ] **Step 7: Conferir que nada ficou apontando para foto**

Run: `cd <raiz>/squads/ml-anuncios && grep -n -i "felipe\|step-07\|10 fotos\|slot\|cor_heroi\|cor-herói\|disclosure_foto" pipeline/steps/step-04*.md pipeline/steps/step-05*.md pipeline/steps/step-06*.md agents/helena-estrategista.agent.md agents/renata-redatora.agent.md`
Expected: nenhuma linha (ou só menção histórica explícita "até 07/10/2026").

- [ ] **Step 8: Commit**

```bash
git add squads/ml-anuncios/pipeline/steps/step-04-inteligencia-conversao.md squads/ml-anuncios/pipeline/steps/step-04b-checkpoint-dados.md squads/ml-anuncios/pipeline/steps/step-05-copywriting.md squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md squads/ml-anuncios/agents/helena-estrategista.agent.md squads/ml-anuncios/agents/renata-redatora.agent.md
git commit -m "docs(squad): Helena e Renata no fluxo sem fotos + regra Marca/Modelo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Capas, revisão e publicação no fluxo novo; arquivar o material de foto

**Files:**
- Create: `squads/ml-anuncios/pipeline/steps/step-07-capas.md`
- Move (git mv) para `squads/ml-anuncios/_arquivo-fotos/`: `pipeline/steps/step-07-fotos.md`, `agents/felipe-fotos.agent.md` (+ os `.snapshot-*` deles), `pipeline/data/photo-templates.md`, `pipeline/STORYSELLING-ENFORCEMENT-PLAN.md`
- Modify: `pipeline/pipeline.yaml`, `squad.yaml`, `squad-party.csv`, `pipeline/steps/step-08-revisao.md`, `step-09-checkpoint-publicacao.md`, `step-10-publicacao.md`, `agents/vinicius-validador.agent.md`, `agents/paula-publicacao.agent.md`

- [ ] **Step 1: Criar `step-07-capas.md`**

````markdown
---
execution: inline
inputFile: squads/ml-anuncios/output/anuncios-entrada.json
outputFile: squads/ml-anuncios/output/capas/
---

# Step 07: Buscar as capas no Cloudinary

Desde 07/10/2026 a squad **não gera foto**. O Almir sobe a capa de cada cor no Cloudinary
(pasta do fornecedor) com duas etiquetas: o **SKU da cor** exatamente como no Tiny e `capa-anuncio`.

## Instructions

1. Buscar com a ferramenta `search-assets` do MCP Cloudinary:
   `expression: "tags=capa-anuncio"`, `fields: "tags,secure_url,created_at,width,height"`, `max_results: 500`.
2. Gravar a resposta **inteira e sem editar** em `squads/ml-anuncios/output/capas/_busca.json`.
3. Rodar:
   ```
   python squads/ml-anuncios/pipeline/validators/capas.py squads/ml-anuncios/output/capas/_busca.json squads/ml-anuncios/output/anuncios-entrada.json squads/ml-anuncios/output/capas/
   ```
4. Código 0 → seguir. Código 1 → **parar** e mostrar ao Almir, em português simples, qual cor de qual
   produto está sem capa e o que conferir (etiqueta com o SKU da cor, `-` e não `_`, e `capa-anuncio`).
   Nunca completar com foto de outra cor.

## Veto Conditions

1. `capas.py` saiu com código diferente de 0.
2. `_busca.json` foi escrito à mão ou resumido (tem que ser a resposta da ferramenta).
````

- [ ] **Step 2: `pipeline.yaml`** — trocar `step-07-fotos.md` por `step-07-capas.md`. No bloco `gates`: `brief_storyselling` → `script: validators/validar_brief.py --sem-fotos`, `roda_em: [step-04, step-04b]`; `anti_claim_falso` → `script: validators/validar_claims.py --copy --sem-fotos`, `roda_em: [step-05, step-08]`; acrescentar `ficha_seo` (`validators/validar_ficha_seo.py`, `roda_em: [step-05, step-06, step-08]`, bloqueia "Marca sem fornecedor, palavra repetida do título, Mundiart fora da regra") e `capas` (`validators/capas.py`, `roda_em: [step-07]`, bloqueia "cor sem capa ou com mais de 10 fotos"); **remover** `prompt_preso_ao_template`, `qa_imagem`, `prompt_nano_banana`, `produto_travado` e o comentário da hierarquia das fotos, deixando uma linha: `# Gates de imagem arquivados em _arquivo-fotos/ (esteira sem fotos desde 07/10/2026).`
- [ ] **Step 3: `squad.yaml`** — tirar `image-ai-generator`, `image-overlay`, `image-creator` de `skills` e `pipeline/data/photo-templates.md` de `data`; trocar os 2 pré-requisitos de imagem (skills de imagem e Gemini) por `"MCP cloudinary conectado (busca das capas por etiqueta)"`. `squad-party.csv`: remover a linha do Felipe.
- [ ] **Step 4: Arquivar**

```bash
cd <raiz>/squads/ml-anuncios && mkdir -p _arquivo-fotos && git mv pipeline/steps/step-07-fotos.md* agents/felipe-fotos.agent.md* pipeline/data/photo-templates.md pipeline/STORYSELLING-ENFORCEMENT-PLAN.md _arquivo-fotos/
```
Criar `_arquivo-fotos/LEIA.md`: "Material de geração de imagem guardado em 07/10/2026, quando a esteira passou a usar capas do Almir. Nada aqui roda. O projeto de fotos (a criar) herda o que servir. Ferramentas ligadas a isso que continuam no lugar: `skills/image-*`, `pipeline/validators/{qa_imagens,validar_prompts,validar_prompt_nano,juiz_escala,peneirar}.py`."

- [ ] **Step 5: step-08 + vinicius-validador.agent.md**
  - Context Loading: trocar as linhas de `metadata-fotos.yaml` e dos JPGs do Felipe por `squads/ml-anuncios/output/capas/capas-{pai_sku}.yaml`.
  - Substituir o bloco "Mídia visual + StorySelling (QA que OLHA a imagem — Fase 4)" (i e ii) por:
    > **Capas (bloqueante):** para cada cor, abrir o endereço de `picture_ids[0]` (Chrome ou download) e confirmar: abre, é 1200×1200, é **este** produto **nesta** cor, sem logo/nome de loja/texto. Rodar `validar_ficha_seo.py anuncio-{pai_sku}.yaml` e `validar_claims.py brief-{pai_sku}.yaml --copy anuncio-{pai_sku}.yaml --sem-fotos` — os dois com código 0. Qualquer falha = `midia_visual: ok: false` com a cor e o motivo.
  - Bloco 8 (variações), item "Foto por cor": "cada cor tem ≥1 endereço em `capas-{pai_sku}.yaml`".
  - Vetos 4/4b viram: "Mídia visual `ok: true` sem ter aberto a capa de cada cor."
  - No checklist do Tom: "presença de 'Terra Casa Decor' só em Mundiart".
  - Exemplo de saída: `midia_visual: { ok: true, notas: ["3 cores, 1 capa cada, 1200x1200", "sem marca nas fotos"] }`.
- [ ] **Step 6: step-09** — tabela troca `nº fotos` por `fotos por cor (ex.: BR 1 · CI 1 · PT 1)`, lida de `capas-{pai_sku}.yaml`; acrescentar coluna `Marca / Modelo`. Acima da tabela, quando algum anúncio tiver `preco_provisorio: true`:
  > ⚠️ **PREÇO PROVISÓRIO: R$ X** — este preço foi colocado só para teste. Publicar com ele? (o anúncio fica à venda por esse valor)

  Veto 1 vira: "anúncio com `confianca_publicacao: baixa`, **ou com preço provisório sem 'sim' explícito do Almir para o preço**". Lembrar: "o anúncio sai com estoque 1 e precisa ser ligado ao produto no Tiny à mão depois".
- [ ] **Step 7: step-10 + paula-publicacao.agent.md**
  - Context Loading: trocar `metadata-fotos.yaml`/metadata do Felipe por `output/capas/capas-{pai_sku}.yaml`.
  - Instructions item 3 inteiro vira:
    > 3. **Montar o pacote com o comando (não à mão):**
    > ```
    > python tools/montar_payload.py --entrada squads/ml-anuncios/output/anuncios-entrada.json --categorias squads/ml-anuncios/output/categorizacao/categorias.yaml --copy squads/ml-anuncios/output/copywriting/anuncio-{pai_sku}.yaml --capas squads/ml-anuncios/output/capas/capas-{pai_sku}.yaml --pai {pai_sku} --saida squads/ml-anuncios/output/publicacao/payload-{pai_sku}.json
    > ```
    > Erro do comando = parar o anúncio e reportar a mensagem (ela diz qual cor/campo). Nunca editar o JSON gerado.
  - Item 4: o POST envia o conteúdo de `payload-{pai_sku}.json`.
  - paula agent: trocar "As fotos vêm PRONTAS do Felipe..." e "Faltou a lista... diferente de 10" por "As fotos vêm de `capas-{pai_sku}.yaml` (1 a 10 por cor) e quem monta o pacote é `tools/montar_payload.py`." Exemplo de payload: deixar 1 URL por variação no formato `https://res.cloudinary.com/wa5lvi98/image/upload/c_pad,w_1200,h_1200,b_white,q_auto/v.../x.jpg`.
- [ ] **Step 8: Conferir que nada ativo aponta para foto**

Run: `cd <raiz>/squads/ml-anuncios && grep -rn -i "felipe\|metadata-fotos\|step-07-fotos\|picture_ids\[10\]\|exatamente 10\|10 fotos" pipeline agents squad.yaml squad-party.csv | grep -v "_arquivo-fotos"`
Expected: nenhuma linha (menções históricas datadas são aceitas).

- [ ] **Step 9: Commit**

```bash
cd <raiz> && git add -A squads/ml-anuncios/pipeline squads/ml-anuncios/agents squads/ml-anuncios/_arquivo-fotos squads/ml-anuncios/squad.yaml squads/ml-anuncios/squad-party.csv
git commit -m "feat(squad): step-07 busca capas; revisao e publicacao sem fotos; material de foto arquivado

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Manual do projeto e progresso

**Files:**
- Modify: `CLAUDE.md` (projeto), `PROGRESSO.md`, `DECISOES.md`

- [ ] **Step 1: `CLAUDE.md`** — na frente 1: "pipeline de papéis (estrategista → categoria → **capas do Almir no Cloudinary** → copy → revisão → publicação) que produz título, descrição e ficha. **Desde 07/10/2026 não gera foto**: capa sobe o Almir, etiquetas = SKU da cor + `capa-anuncio`. Material de foto em `squads/ml-anuncios/_arquivo-fotos/`." Na seção "Modelo de IA para imagens", acrescentar no topo: "⚠️ **Fora da esteira desde 07/10/2026** — vale para o futuro projeto de fotos." Remover de "Regras Críticas" as regras exclusivamente de geração (tamanho fixo das fotos, folga da foto técnica, produto nunca re-renderizado, StorySelling de fotos, templates, checklist medido, escala/forma, luz) **movendo-as** para `_arquivo-fotos/REGRAS-DE-FOTO.md` (copiar texto integral, não resumir).
- [ ] **Step 2: `DECISOES.md`** — entrada `2026-10-07 — Esteira sem fotos`: motivo (dificuldade de chegar no resultado com IA), capa pelo Almir + etiquetas, Helena só texto (opção B), publicação real (opção A), Cloudinary (opção A), regra Marca/Modelo, Mundiart, recolor: ChatGPT site (ver `projects/imagens` I27), preço provisório R$ 100.
- [ ] **Step 3: `PROGRESSO.md`** — seção 0 vira "Esteira sem fotos — 1º teste: Viel 5L e 8L (3 cores cada)", com estado e o que falta; seções 1–3 (8L/medidas) vão para HISTORICO com a data.
- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md PROGRESSO.md DECISOES.md HISTORICO.md squads/ml-anuncios/_arquivo-fotos/REGRAS-DE-FOTO.md
git commit -m "docs: projeto passa a esteira sem fotos

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Primeiro teste real — Viel 5L e 8L

Não é código: é rodar a esteira. **Cada checkpoint para e espera o Almir.** Nada é publicado sem o "sim" dele no step-09.

- [ ] **Step 1: Entrada** — já gerada na Task 5 Step 6 (`anuncios-entrada.json`, preço 100, cubagem).
- [ ] **Step 2: Rodar steps 02 → 06** (Caio, Cibele, Helena, checkpoint de dados, Renata, checkpoint de copy). Travas: `validar_brief --sem-fotos`, `validar_claims --copy --sem-fotos`, `validar_ficha_seo` — todas código 0. Mostrar ao Almir no checkpoint de copy os títulos e a Marca/Modelo propostos.
- [ ] **Step 3: step-07 capas** — busca no Cloudinary + `capas.py`. Esperado: `VIE-1066-PAI: Branco=1, Cinza=1, Preto=1` e `VIE-1067-PAI: Branco=1, Cinza=1, Preto=1`, `CAPAS OK`.
- [ ] **Step 4: step-08 revisão** — Vinicius abre as 6 capas pelo endereço 1200 e confere cor × SKU.
- [ ] **Step 5: step-09** — mostrar a tabela com o aviso de **preço provisório R$ 100** e estoque 1/vínculo Tiny manual. Esperar "sim" explícito (com o preço).
- [ ] **Step 6: Ligar o workflow** — só depois do "sim": ativar `ML Publicar` (`0rzNJ7RLqLzMbKnf`) pelo MCP n8n, sem abrir o nó Webhook (memória `n8n_mcp_no_webhook_vaza_cabecalho`; usar `mode: structure`/`filtered` em nós que não sejam o Webhook).
- [ ] **Step 7: step-10** — `montar_payload.py` para os 2 anúncios e POST. Esperado: `status: success` com `mlb_id`.
- [ ] **Step 8: Conferir no ML** — ler o anúncio publicado (`/items/{mlb_id}`): título, preço 100, 3 variações com foto, `BRAND`/`MODEL` **exatamente** como enviados (se o ML trocou, registrar em DECISOES — é a conferência pedida na regra de 07/10), `SELLER_PACKAGE_*` presentes. Mostrar o link ao Almir.
- [ ] **Step 9: Perguntar ao Almir** se pausa os 2 anúncios até ter o preço real (o preço de R$ 100 é provisório) e lembrar do vínculo manual no Tiny.
- [ ] **Step 10: `/save`** — registrar o teste em PROGRESSO/HISTORICO.
