# Tela de aprovação do anúncio — Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Página local, aberta por clique duplo, onde o Almir vê tudo do anúncio, escolhe/edita título, Marca, Modelo e descrição com conferência ao vivo, e aprova ou devolve — gravando no `anuncio-{pai}.yaml`.

**Architecture:** `tools/aprovacao/aprovacao.py` tem a lógica pura (ler pendentes, conferir com as travas da esteira, aprovar/devolver com cópia de segurança e gravação segura) e um servidor da biblioteca padrão em `127.0.0.1` que serve `pagina.html` e responde em JSON. `Aprovar anuncios.bat` chama o programa, que abre o Chrome.

**Tech Stack:** Python 3 (stdlib `http.server`, `json`, `webbrowser`) + `yaml` (já instalado); HTML/JS puro, sem nada da internet; testes `pytest`.

**Spec:** `docs/superpowers/specs/2026-10-08-tela-aprovacao-design.md`

## Global Constraints

- Escuta só em `127.0.0.1`; porta livre escolhida pelo sistema (porta 0).
- Nada da internet na página (sem CDN); só a biblioteca padrão do Python + `yaml`.
- Bloqueio só para título vazio ou acima de 60 caracteres; todo o resto é aviso e a aprovação grava `avisos_aceitos`.
- As travas são as da esteira, importadas: `validar_ficha_seo.validar_ficha`, `validar_ficha_seo.descricao_do_copy`, `validar_claims.validar_claims(brief, copy_doc=..., sem_fotos=True)`.
- Antes de gravar: cópia em `copywriting/_antes/anuncio-{pai}-<AAAAMMDD-HHMMSS>.yaml`; gravação em arquivo temporário + `os.replace`.
- Texto da página em português simples (Almir não é dev).
- `pai_sku` vindo da página só aceita `^[A-Za-z0-9_-]+$` (nunca vira caminho fora da pasta).
- Repo é público: nada de segredo nos arquivos (não há segredo nesta peça).

## Review Focus

1. **Anúncio já aprovado** (`status_copy: aprovado`) não reaparece como pendente nem pode ser aprovado de novo por engano — `listar_pendentes` filtra; `aprovar` em anúncio já aprovado responde erro.
2. **Brief ausente** — a conferência de promessas não roda; tem que aparecer como erro visível ("não achei a pesquisa"), nunca como "tudo ok".
3. **Edição apaga um bloco inteiro da descrição** — bloco vazio grava vazio e a trava de limitação/descrição reclama; não pode cair no texto antigo calado.
4. **Arquivo do anúncio com defeito** — aquele cartão mostra o erro; os outros continuam funcionando.
5. **Pedido de outro site para a porta local** — só aceita `Content-Type: application/json` (navegador obriga pré-checagem, que o servidor não autoriza), então um site qualquer não consegue aprovar por fora.

---

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| Create `tools/aprovacao/aprovacao.py` | lógica + servidor + linha de comando |
| Create `tools/aprovacao/pagina.html` | a tela |
| Create `tools/aprovacao/Aprovar anuncios.bat` | clique duplo |
| Create `tools/aprovacao/tests/test_aprovacao.py` | testes da lógica e do servidor |
| Modify `squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md` | aprovação pela tela |

Rodar testes: `cd tools/aprovacao && python -m pytest tests -q`.

---

### Task 1: Ler os anúncios pendentes

**Files:** Create `tools/aprovacao/aprovacao.py`, `tools/aprovacao/tests/test_aprovacao.py`

**Interfaces:**
- Produces: `listar_pendentes(saida: Path) -> list[dict]`; cada cartão: `{pai_sku, nome_base, titles:[{texto,recomendado,justificativa}], titulo_inicial, marca, modelo, descricao:{bloco_*: str}, ficha:{campo: valor}, observacoes:[str], precos:[{cor,sku,preco}], preco_provisorio:bool, peso_kg, caixa_cm, capas:[{cor,urls}]|None}` ou `{arquivo, erro}`.

- [ ] **Step 1: Teste que falha**

```python
# tools/aprovacao/tests/test_aprovacao.py
import json
import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import aprovacao as ap  # noqa: E402

PAI = "VIE-1-PAI"
TIT_OK = "Lixeira Inox 5 Litros Pedal Banheiro Cozinha Sofisticada"


def _doc(**extra):
    d = {
        "pai_sku": PAI, "nome_base": "LIXEIRA 5L", "modo": "variacoes", "status_copy": "warning",
        "warnings": ["Garantia ausente."],
        "titles": [
            {"texto": "Lixeira Inox 5 Litros Pedal Banheiro Lavabo", "recomendado": False, "justificativa": "a"},
            {"texto": TIT_OK, "recomendado": True, "justificativa": "b"},
        ],
        "description": {
            "bloco_1_abertura": "Lixeira bonita. Este modelo nao tem balde interno removivel.\n",
            "bloco_2_specs": "- Capacidade: 5 litros\n",
            "bloco_3_features_beneficios": "- Pedal: abre sem as maos\n",
            "word_count": 20,
        },
        "titulo_final": None,
        "attributes": {"BRAND": "Viel", "MODEL": "Cesto Lixo Redondo", "VOLUME_CAPACITY": "5 L"},
    }
    d.update(extra)
    return d


@pytest.fixture
def saida(tmp_path):
    (tmp_path / "copywriting").mkdir()
    (tmp_path / "inteligencia").mkdir()
    (tmp_path / "copywriting" / f"anuncio-{PAI}.yaml").write_text(
        yaml.safe_dump(_doc(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    (tmp_path / "inteligencia" / f"brief-{PAI}.yaml").write_text(yaml.safe_dump({
        "pai_sku": PAI, "limitacoes": [{"texto": "Nao tem balde interno removivel"}],
        "dados_produto": {"caracteristicas": {}}}), encoding="utf-8")
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{
        "pai_sku": PAI, "preco_provisorio": True, "peso_bruto_kg": 0.7,
        "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
        "variacoes": [{"sku": "VIE-1-BR", "cor": "Branco", "preco_venda": 100.0},
                      {"sku": "VIE-1-PT", "cor": "Preto", "preco_venda": 100.0}]}]}), encoding="utf-8")
    return tmp_path


def _gravar(saida, doc):
    (saida / "copywriting" / f"anuncio-{PAI}.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")


class TestListar:
    def test_monta_o_cartao(self, saida):
        [c] = ap.listar_pendentes(saida)
        assert c["pai_sku"] == PAI
        assert c["titulo_inicial"] == TIT_OK
        assert c["marca"] == "Viel" and c["modelo"] == "Cesto Lixo Redondo"
        assert set(c["descricao"]) == {"bloco_1_abertura", "bloco_2_specs", "bloco_3_features_beneficios"}
        assert c["ficha"] == {"VOLUME_CAPACITY": "5 L"}
        assert c["precos"] == [{"cor": "Branco", "sku": "VIE-1-BR", "preco": 100.0},
                               {"cor": "Preto", "sku": "VIE-1-PT", "preco": 100.0}]
        assert c["preco_provisorio"] is True
        assert c["peso_kg"] == 0.7 and c["caixa_cm"]["largura"] == 28
        assert c["observacoes"] == ["Garantia ausente."]
        assert c["capas"] is None

    def test_titulo_final_ja_gravado_vem_primeiro(self, saida):
        _gravar(saida, _doc(titulo_final="Outro Titulo"))
        assert ap.listar_pendentes(saida)[0]["titulo_inicial"] == "Outro Titulo"

    def test_aprovado_e_devolvido_nao_aparecem(self, saida):
        _gravar(saida, _doc(status_copy="aprovado"))
        assert ap.listar_pendentes(saida) == []
        _gravar(saida, _doc(status_copy="devolvido"))
        assert ap.listar_pendentes(saida) == []

    def test_le_as_capas_quando_existem(self, saida):
        (saida / "capas").mkdir()
        (saida / "capas" / f"capas-{PAI}.yaml").write_text(yaml.safe_dump({
            "pai_sku": PAI, "picture_ids_por_variacao": [
                {"sku_variacao": "VIE-1-BR", "cor": "Branco", "picture_ids": ["https://x/a.jpg"]}]}),
            encoding="utf-8")
        assert ap.listar_pendentes(saida)[0]["capas"] == [{"cor": "Branco", "urls": ["https://x/a.jpg"]}]

    def test_arquivo_com_defeito_vira_cartao_de_erro(self, saida):
        (saida / "copywriting" / "anuncio-VIE-2-PAI.yaml").write_text("a: [", encoding="utf-8")
        cartoes = ap.listar_pendentes(saida)
        assert any(c.get("erro") and c["arquivo"] == "anuncio-VIE-2-PAI.yaml" for c in cartoes)
        assert any(c.get("pai_sku") == PAI for c in cartoes)

    def test_pasta_vazia(self, tmp_path):
        assert ap.listar_pendentes(tmp_path) == []
```

- [ ] **Step 2: Rodar — falha**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: erro de importação `No module named 'aprovacao'`.

- [ ] **Step 3: Implementar**

```python
#!/usr/bin/env python3
"""
aprovacao.py — tela de aprovacao do anuncio (Almir, 08/10/2026).

Le os anuncios parados no step-06, confere com as MESMAS travas da esteira e grava
a escolha do Almir no anuncio-{pai}.yaml. Spec:
docs/superpowers/specs/2026-10-08-tela-aprovacao-design.md

Uso:  python aprovacao.py [--saida PASTA] [--esperar] [--sem-navegador]
"""
import copy
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "squads" / "ml-anuncios" / "output"
sys.path.insert(0, str(RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"))
from validar_ficha_seo import validar_ficha, descricao_do_copy  # noqa: E402
from validar_claims import validar_claims  # noqa: E402

TETO_TITULO = 60
FINAIS = ("aprovado", "devolvido")


def _ler_yaml(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _entrada_por_pai(saida):
    p = Path(saida) / "anuncios-entrada.json"
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    return {a.get("pai_sku"): a for a in d.get("anuncios", [])}


def _titulo_inicial(doc):
    if doc.get("titulo_final"):
        return doc["titulo_final"]
    for t in doc.get("titles") or []:
        if isinstance(t, dict) and t.get("recomendado"):
            return t.get("texto", "")
    return ""


def _capas(saida, pai):
    p = Path(saida) / "capas" / f"capas-{pai}.yaml"
    if not p.is_file():
        return None
    doc = _ler_yaml(p) or {}
    return [{"cor": v.get("cor"), "urls": list(v.get("picture_ids") or [])}
            for v in doc.get("picture_ids_por_variacao") or []]


def _cartao(saida, doc, entrada):
    pai = doc.get("pai_sku")
    a = entrada.get(pai, {})
    attrs = doc.get("attributes") or {}
    desc = doc.get("description") or {}
    return {
        "pai_sku": pai,
        "nome_base": doc.get("nome_base"),
        "titles": [{"texto": t.get("texto", ""), "recomendado": bool(t.get("recomendado")),
                    "justificativa": t.get("justificativa", "")}
                   for t in doc.get("titles") or [] if isinstance(t, dict)],
        "titulo_inicial": _titulo_inicial(doc),
        "marca": attrs.get("BRAND") or "",
        "modelo": attrs.get("MODEL") or "",
        "descricao": {k: v for k, v in desc.items() if str(k).startswith("bloco") and isinstance(v, str)},
        "ficha": {k: v for k, v in attrs.items() if k not in ("BRAND", "MODEL")},
        "observacoes": list(doc.get("warnings") or []),
        "precos": [{"cor": v.get("cor"), "sku": v.get("sku"), "preco": v.get("preco_venda")}
                   for v in a.get("variacoes") or []],
        "preco_provisorio": bool(a.get("preco_provisorio")),
        "peso_kg": a.get("peso_bruto_kg"),
        "caixa_cm": a.get("dim_embalagem_cm"),
        "capas": _capas(saida, pai),
    }


def listar_pendentes(saida):
    saida = Path(saida)
    pasta = saida / "copywriting"
    if not pasta.is_dir():
        return []
    entrada = _entrada_por_pai(saida)
    cartoes = []
    for f in sorted(pasta.glob("anuncio-*.yaml")):
        try:
            doc = _ler_yaml(f)
            if not isinstance(doc, dict) or not doc.get("pai_sku"):
                raise ValueError("arquivo sem pai_sku")
        except Exception as e:  # noqa: BLE001
            cartoes.append({"arquivo": f.name, "erro": f"Este arquivo nao abriu ({type(e).__name__})."})
            continue
        if doc.get("status_copy") in FINAIS:
            continue
        cartoes.append(_cartao(saida, doc, entrada))
    return cartoes
```

- [ ] **Step 4: Rodar — passa**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add tools/aprovacao/aprovacao.py tools/aprovacao/tests/test_aprovacao.py
git commit -m "feat(aprovacao): ler anuncios pendentes do step-06"
```

---

### Task 2: Conferir a edição com as travas

**Interfaces:**
- Consumes: `listar_pendentes` (Task 1), `validar_ficha`, `descricao_do_copy`, `validar_claims`.
- Produces: `aplicar_edicao(doc, edicao) -> dict` (cópia); `conferir(saida, pai, edicao) -> list[{codigo, nivel, texto}]`, `nivel ∈ {"bloqueio","erro","aviso"}`; `edicao = {titulo, marca, modelo, descricao:{bloco_*}}`; `caminho_anuncio(saida, pai) -> Path` (levanta `ValueError` para `pai` inválido).

- [ ] **Step 1: Testes que falham** (acrescentar ao arquivo de testes)

```python
def _edicao(**kw):
    e = {"titulo": TIT_OK, "marca": "Viel", "modelo": "Cesto Lixo Redondo",
         "descricao": {"bloco_1_abertura": "Lixeira bonita. Este modelo nao tem balde interno removivel.\n",
                       "bloco_2_specs": "- Capacidade: 5 litros\n",
                       "bloco_3_features_beneficios": "- Pedal: abre sem as maos\n"}}
    e.update(kw)
    return e


def _codigos(itens, nivel=None):
    return [i["codigo"] for i in itens if nivel is None or i["nivel"] == nivel]


class TestConferir:
    def test_tudo_certo(self, saida):
        assert ap.conferir(saida, PAI, _edicao()) == []

    def test_titulo_acima_de_60_bloqueia(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(titulo="L" * 61))
        assert "TITULO_LONGO" in _codigos(itens, "bloqueio")

    def test_titulo_vazio_bloqueia(self, saida):
        assert "TITULO_VAZIO" in _codigos(ap.conferir(saida, PAI, _edicao(titulo="  ")), "bloqueio")

    def test_marca_fora_do_padrao_e_erro_nao_bloqueio(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(marca="Viel Inox"))
        assert "MARCA_FORA_DO_PADRAO" in _codigos(itens, "erro")
        assert _codigos(itens, "bloqueio") == []

    def test_promessa_falsa_aparece(self, saida):
        d = _edicao()["descricao"]
        d["bloco_3_features_beneficios"] = "- Com balde interno removivel\n"
        assert "CLAIM_FALSO_COPY" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)), "erro")

    def test_bloco_apagado_nao_volta_o_texto_antigo(self, saida):
        d = _edicao()["descricao"]
        d["bloco_1_abertura"] = ""
        assert "LIMITACAO_FORA_DA_COPY" in _codigos(ap.conferir(saida, PAI, _edicao(descricao=d)))

    def test_modelo_longo_e_aviso(self, saida):
        itens = ap.conferir(saida, PAI, _edicao(modelo="Cesto Redondo Consultorio Escritorio Lavabo"))
        assert "WARN_MODELO_LONGO" in _codigos(itens, "aviso")

    def test_sem_brief_e_erro_visivel(self, saida):
        (saida / "inteligencia" / f"brief-{PAI}.yaml").unlink()
        assert "BRIEF_AUSENTE" in _codigos(ap.conferir(saida, PAI, _edicao()), "erro")

    def test_pai_invalido(self, saida):
        with pytest.raises(ValueError):
            ap.conferir(saida, "../x", _edicao())

    def test_aplicar_nao_mexe_no_original(self):
        doc = _doc()
        novo = ap.aplicar_edicao(doc, _edicao(marca="Terra Casa Decor"))
        assert doc["attributes"]["BRAND"] == "Viel"
        assert novo["attributes"]["BRAND"] == "Terra Casa Decor"
        assert novo["titulo_final"] == TIT_OK
        assert novo["description"]["word_count"] == 20
```

- [ ] **Step 2: Rodar — falha**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: `AttributeError: module 'aprovacao' has no attribute 'conferir'` (10 falhas novas, 6 passam).

- [ ] **Step 3: Implementar** (acrescentar a `aprovacao.py`)

```python
PAI_OK = re.compile(r"^[A-Za-z0-9_-]+$")


def caminho_anuncio(saida, pai):
    if not PAI_OK.match(str(pai or "")):
        raise ValueError(f"SKU pai invalido: {pai!r}")
    return Path(saida) / "copywriting" / f"anuncio-{pai}.yaml"


def aplicar_edicao(doc, edicao):
    novo = copy.deepcopy(doc)
    novo["titulo_final"] = (edicao.get("titulo") or "").strip()
    attrs = novo.setdefault("attributes", {})
    attrs["BRAND"] = (edicao.get("marca") or "").strip()
    attrs["MODEL"] = (edicao.get("modelo") or "").strip()
    desc = novo.setdefault("description", {})
    for k, v in (edicao.get("descricao") or {}).items():
        if str(k).startswith("bloco"):
            desc[k] = v or ""
    return novo


def conferir(saida, pai, edicao):
    doc = _ler_yaml(caminho_anuncio(saida, pai))
    novo = aplicar_edicao(doc, edicao)
    titulo = novo["titulo_final"]
    itens = []
    if not titulo:
        itens.append({"codigo": "TITULO_VAZIO", "nivel": "bloqueio", "texto": "Falta escolher o titulo."})
    elif len(titulo) > TETO_TITULO:
        itens.append({"codigo": "TITULO_LONGO", "nivel": "bloqueio",
                      "texto": f"Titulo com {len(titulo)} letras; o Mercado Livre aceita ate {TETO_TITULO}."})
    attrs = novo["attributes"]
    for cod, msg in validar_ficha(pai, titulo, attrs["BRAND"], attrs["MODEL"], descricao_do_copy(novo)):
        itens.append({"codigo": cod, "nivel": "aviso" if cod.startswith("WARN") else "erro", "texto": msg})
    brief_p = Path(saida) / "inteligencia" / f"brief-{pai}.yaml"
    if not brief_p.is_file():
        itens.append({"codigo": "BRIEF_AUSENTE", "nivel": "erro",
                      "texto": "Nao achei a pesquisa deste anuncio: a conferencia de promessas NAO rodou."})
    else:
        blocks, warns = validar_claims(_ler_yaml(brief_p), copy_doc=novo, sem_fotos=True)
        itens += [{"codigo": c, "nivel": "erro", "texto": m} for c, m in blocks]
        itens += [{"codigo": c, "nivel": "aviso", "texto": m} for c, m in warns]
    return itens
```

- [ ] **Step 4: Rodar — passa**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: `16 passed`. Se `test_tudo_certo` falhar com aviso de claim não confirmado, ajustar o texto do fixture (não a lógica) e anotar Ruling.

- [ ] **Step 5: Commit**

```bash
git add tools/aprovacao
git commit -m "feat(aprovacao): conferir edicao com as travas da esteira"
```

---

### Task 3: Aprovar e devolver

**Interfaces:**
- Consumes: `conferir`, `aplicar_edicao`, `caminho_anuncio` (Task 2).
- Produces: `aprovar(saida, pai, edicao, agora=None) -> {"ok": bool, "motivo"?: str, "conferencia": list}`; `devolver(saida, pai, nota, agora=None) -> {"ok": bool, "motivo"?: str}`.

- [ ] **Step 1: Testes que falham**

```python
AGORA = datetime(2026, 10, 8, 14, 32, 5)


class TestAprovar:
    def test_grava_a_escolha(self, saida):
        r = ap.aprovar(saida, PAI, _edicao(marca="Terra Casa Decor"), agora=AGORA)
        assert r["ok"] is True
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert doc["status_copy"] == "aprovado"
        assert doc["titulo_final"] == TIT_OK
        assert doc["attributes"]["BRAND"] == "Terra Casa Decor"
        assert doc["aprovado_em"] == "2026-10-08 14:32"
        assert doc["avisos_aceitos"] == []
        assert ap.listar_pendentes(saida) == []

    def test_guarda_copia_do_anterior(self, saida):
        antes = (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8")
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        copia = saida / "copywriting" / "_antes" / f"anuncio-{PAI}-20261008-143205.yaml"
        assert copia.read_text(encoding="utf-8") == antes

    def test_bloqueio_nao_grava(self, saida):
        antes = (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8")
        r = ap.aprovar(saida, PAI, _edicao(titulo="L" * 61), agora=AGORA)
        assert r["ok"] is False
        assert (saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8") == antes

    def test_aviso_aceito_fica_registrado(self, saida):
        ap.aprovar(saida, PAI, _edicao(marca="Viel Inox"), agora=AGORA)
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert "MARCA_FORA_DO_PADRAO" in doc["avisos_aceitos"]

    def test_ja_aprovado_nao_aprova_de_novo(self, saida):
        ap.aprovar(saida, PAI, _edicao(), agora=AGORA)
        r = ap.aprovar(saida, PAI, _edicao(titulo="Outro"), agora=AGORA)
        assert r["ok"] is False


class TestDevolver:
    def test_grava_a_nota(self, saida):
        r = ap.devolver(saida, PAI, "Trocar o titulo, quero cozinha primeiro", agora=AGORA)
        assert r["ok"] is True
        doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
        assert doc["status_copy"] == "devolvido"
        assert doc["nota_almir"] == "Trocar o titulo, quero cozinha primeiro"
        assert doc["devolvido_em"] == "2026-10-08 14:32"
        assert (saida / "copywriting" / "_antes" / f"anuncio-{PAI}-20261008-143205.yaml").is_file()

    def test_nota_vazia_nao_devolve(self, saida):
        assert ap.devolver(saida, PAI, "   ", agora=AGORA)["ok"] is False
```

E no topo do arquivo de testes: `from datetime import datetime`.

- [ ] **Step 2: Rodar — falha**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: 7 falhas por `has no attribute 'aprovar'`/`'devolver'`.

- [ ] **Step 3: Implementar**

```python
def _gravar_seguro(caminho, doc, agora):
    caminho = Path(caminho)
    antes = caminho.parent / "_antes"
    antes.mkdir(exist_ok=True)
    shutil.copy2(caminho, antes / f"{caminho.stem}-{agora:%Y%m%d-%H%M%S}.yaml")
    tmp = caminho.with_name(caminho.name + ".novo")
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100000)
    os.replace(tmp, caminho)


def aprovar(saida, pai, edicao, agora=None):
    agora = agora or datetime.now()
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    if doc.get("status_copy") in FINAIS:
        return {"ok": False, "motivo": f"Este anuncio ja esta '{doc['status_copy']}'.", "conferencia": []}
    itens = conferir(saida, pai, edicao)
    if any(i["nivel"] == "bloqueio" for i in itens):
        return {"ok": False, "motivo": "Tem bloqueio: corrija antes de aprovar.", "conferencia": itens}
    novo = aplicar_edicao(doc, edicao)
    novo["status_copy"] = "aprovado"
    novo["aprovado_em"] = f"{agora:%Y-%m-%d %H:%M}"
    novo["avisos_aceitos"] = [i["codigo"] for i in itens]
    _gravar_seguro(caminho, novo, agora)
    salvo = _ler_yaml(caminho)
    depois = conferir(saida, pai, {"titulo": salvo["titulo_final"], "marca": salvo["attributes"]["BRAND"],
                                   "modelo": salvo["attributes"]["MODEL"],
                                   "descricao": salvo.get("description") or {}})
    return {"ok": True, "conferencia": depois}


def devolver(saida, pai, nota, agora=None):
    agora = agora or datetime.now()
    nota = (nota or "").strip()
    if not nota:
        return {"ok": False, "motivo": "Escreva o que a Renata deve refazer."}
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    if doc.get("status_copy") in FINAIS:
        return {"ok": False, "motivo": f"Este anuncio ja esta '{doc['status_copy']}'."}
    doc["status_copy"] = "devolvido"
    doc["nota_almir"] = nota
    doc["devolvido_em"] = f"{agora:%Y-%m-%d %H:%M}"
    _gravar_seguro(caminho, doc, agora)
    return {"ok": True}
```

Nota: `conferir` é chamado depois da gravação com `status_copy: aprovado` no arquivo — `conferir` não olha o status, então funciona.

- [ ] **Step 4: Rodar — passa**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: `23 passed`.

- [ ] **Step 5: Commit**

```bash
git add tools/aprovacao
git commit -m "feat(aprovacao): aprovar e devolver com copia de seguranca"
```

---

### Task 4: Servidor local, página e atalho

**Interfaces:**
- Consumes: `listar_pendentes`, `conferir`, `aprovar`, `devolver`.
- Produces: `criar_servidor(saida, esperar=False) -> ThreadingHTTPServer` (atributo `.estado = {"devolvidos": int, "acoes": int}`); rotas `GET /`, `GET /api/pendentes`, `POST /api/conferir {pai, edicao}`, `POST /api/aprovar {pai, edicao}`, `POST /api/devolver {pai, nota}`; `main()` com `--saida`, `--esperar`, `--sem-navegador`; código de saída do `--esperar`: 0 todos aprovados, 3 algum devolvido.

- [ ] **Step 1: Testes que falham**

```python
import threading
import urllib.error
import urllib.request


def _subir(saida, esperar=False):
    srv = ap.criar_servidor(saida, esperar=esperar)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _post(url, corpo, tipo="application/json"):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST",
                                 headers={"Content-Type": tipo})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


class TestServidor:
    def test_pagina_e_pendentes(self, saida):
        srv, base = _subir(saida)
        try:
            html = urllib.request.urlopen(base + "/").read().decode("utf-8")
            assert "<title>Aprovar anúncios</title>" in html
            dados = json.loads(urllib.request.urlopen(base + "/api/pendentes").read())
            assert dados["cartoes"][0]["pai_sku"] == PAI
        finally:
            srv.shutdown()

    def test_conferir_e_aprovar(self, saida):
        srv, base = _subir(saida)
        try:
            assert _post(base + "/api/conferir", {"pai": PAI, "edicao": _edicao()})["itens"] == []
            assert _post(base + "/api/aprovar", {"pai": PAI, "edicao": _edicao()})["ok"] is True
        finally:
            srv.shutdown()

    def test_recusa_pedido_que_nao_e_json(self, saida):
        srv, base = _subir(saida)
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                _post(base + "/api/aprovar", {"pai": PAI, "edicao": _edicao()}, tipo="text/plain")
            assert e.value.code == 415
        finally:
            srv.shutdown()

    def test_pai_invalido_responde_400(self, saida):
        srv, base = _subir(saida)
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                _post(base + "/api/conferir", {"pai": "../x", "edicao": _edicao()})
            assert e.value.code == 400
        finally:
            srv.shutdown()

    def test_esperar_encerra_quando_acaba(self, saida):
        srv, base = _subir(saida, esperar=True)
        _post(base + "/api/devolver", {"pai": PAI, "nota": "refazer"})
        srv.encerrado.wait(5)
        assert srv.encerrado.is_set()
        assert srv.estado["devolvidos"] == 1
```

- [ ] **Step 2: Rodar — falha**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: 5 falhas `has no attribute 'criar_servidor'`.

- [ ] **Step 3: Implementar servidor** (acrescentar a `aprovacao.py`)

```python
import argparse
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGINA = Path(__file__).resolve().parent / "pagina.html"


def criar_servidor(saida, esperar=False):
    saida = Path(saida)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _responder(self, codigo, corpo, tipo="application/json; charset=utf-8"):
            dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            if self.path == "/":
                return self._responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/pendentes":
                return self._responder(200, {"cartoes": listar_pendentes(saida)})
            self._responder(404, {"erro": "nao existe"})

        def do_POST(self):
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._responder(415, {"erro": "so JSON"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                corpo = json.loads(self.rfile.read(n) or b"{}")
                pai = corpo.get("pai")
                if self.path == "/api/conferir":
                    return self._responder(200, {"itens": conferir(saida, pai, corpo.get("edicao") or {})})
                if self.path == "/api/aprovar":
                    r = aprovar(saida, pai, corpo.get("edicao") or {})
                elif self.path == "/api/devolver":
                    r = devolver(saida, pai, corpo.get("nota"))
                    if r["ok"]:
                        srv.estado["devolvidos"] += 1
                else:
                    return self._responder(404, {"erro": "nao existe"})
            except ValueError as e:
                return self._responder(400, {"erro": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._responder(500, {"erro": f"Falhou ({type(e).__name__}). Chame o Claude."})
            if r["ok"]:
                srv.estado["acoes"] += 1
                if esperar and not listar_pendentes(saida):
                    threading.Thread(target=lambda: (srv.shutdown(), srv.encerrado.set()), daemon=True).start()
            self._responder(200, r)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.estado = {"devolvidos": 0, "acoes": 0}
    srv.encerrado = threading.Event()
    return srv


def main():
    p = argparse.ArgumentParser(description="Tela de aprovacao do anuncio.")
    p.add_argument("--saida", default=str(SAIDA_PADRAO), help="pasta de saida da esteira")
    p.add_argument("--esperar", action="store_true",
                   help="encerra quando nao sobrar pendente; sai 0 = todos aprovados, 3 = algum devolvido")
    p.add_argument("--sem-navegador", action="store_true")
    a = p.parse_args()
    srv = criar_servidor(a.saida, esperar=a.esperar)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    pend = listar_pendentes(a.saida)
    print(f"Tela de aprovacao aberta em {url}")
    print(f"{len(pend)} anuncio(s) esperando aprovacao. Feche esta janela para desligar a tela.")
    if not a.sem_navegador:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    if a.esperar:
        sys.exit(3 if srv.estado["devolvidos"] else 0)


if __name__ == "__main__":
    main()
```

(Mover os `import` novos para o topo do arquivo, junto dos outros.)

- [ ] **Step 4: Criar `pagina.html`**

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aprovar anúncios</title>
<style>
:root{--fundo:#f4f5f7;--cartao:#fff;--texto:#1d2330;--suave:#667085;--borda:#d8dce3;--ok:#127a3e;--erro:#b42318;--aviso:#9a6700;--acento:#2457c5;--fundoerro:#fdecea;--fundoaviso:#fff6db;--fundook:#e7f6ec}
@media (prefers-color-scheme:dark){:root{--fundo:#14171c;--cartao:#1d2128;--texto:#e7e9ee;--suave:#9aa3b2;--borda:#343a45;--ok:#5ccf8a;--erro:#ff8a80;--aviso:#f0c75e;--acento:#7aa2ff;--fundoerro:#3a1d1b;--fundoaviso:#3a3017;--fundook:#18321f}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);font:15px/1.45 system-ui,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:8px 0 16px}
.cartao{background:var(--cartao);border:1px solid var(--borda);border-radius:10px;padding:16px;margin-bottom:20px}
.topo{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline}
.topo h2{font-size:17px;margin:0}
.sku{color:var(--suave);font-size:13px}
.selo{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;font-weight:600;background:var(--fundoaviso);color:var(--aviso)}
.secao{margin-top:14px}
.secao>b{display:block;margin-bottom:6px}
.capas{display:flex;gap:10px;flex-wrap:wrap}
.capas figure{margin:0;text-align:center;font-size:12px;color:var(--suave)}
.capas img{width:110px;height:110px;object-fit:contain;background:#fff;border:1px solid var(--borda);border-radius:6px}
label.opcao{display:flex;gap:8px;align-items:flex-start;padding:6px 8px;border-radius:6px;cursor:pointer}
label.opcao:hover{background:var(--fundo)}
.just{color:var(--suave);font-size:13px}
input[type=text],textarea{width:100%;font:inherit;color:inherit;background:var(--cartao);border:1px solid var(--borda);border-radius:6px;padding:7px 9px}
textarea{min-height:110px;resize:vertical}
.conta{font-size:12px;color:var(--suave);text-align:right}
.conta.passou{color:var(--erro);font-weight:600}
.linha2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:640px){.linha2{grid-template-columns:1fr}}
table{border-collapse:collapse;font-size:14px}
td{padding:2px 12px 2px 0;vertical-align:top}
td:first-child{color:var(--suave)}
ul.conf{list-style:none;padding:0;margin:0}
ul.conf li{padding:6px 8px;border-radius:6px;margin-bottom:4px}
li.bloqueio,li.erro{background:var(--fundoerro);color:var(--erro)}
li.aviso{background:var(--fundoaviso);color:var(--aviso)}
li.tudook{background:var(--fundook);color:var(--ok)}
.botoes{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;align-items:center}
button{font:inherit;padding:8px 16px;border-radius:6px;border:1px solid var(--borda);background:var(--cartao);color:var(--texto);cursor:pointer}
button.principal{background:var(--acento);border-color:var(--acento);color:#fff}
button.principal.mesmo{background:var(--erro);border-color:var(--erro)}
button:disabled{opacity:.45;cursor:not-allowed}
.feito{background:var(--fundook);color:var(--ok);border-radius:8px;padding:8px 12px;margin-bottom:8px}
.falha{background:var(--fundoerro);color:var(--erro);border-radius:8px;padding:8px 12px}
.vazio{color:var(--suave);padding:40px 0;text-align:center}
</style>
</head>
<body>
<main>
<h1>Anúncios esperando sua aprovação</h1>
<div id="feitos"></div>
<div id="lista"><p class="vazio">Carregando…</p></div>
</main>
<script>
const TETO_TITULO = 60, TETO_MODELO = 30;
const BLOCOS = {bloco_1_abertura: "Abertura", bloco_2_specs: "Medidas e materiais", bloco_3_features_beneficios: "Benefícios"};
const CAMPOS = {VOLUME_CAPACITY: "Capacidade", UNITS_PER_PACK: "Unidades", MATERIAL: "Material", COLOR: "Cor"};

function el(tag, attrs = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  for (const f of filhos.flat()) if (f != null) e.append(f instanceof Node ? f : document.createTextNode(String(f)));
  return e;
}
async function api(caminho, corpo) {
  const r = await fetch(caminho, corpo ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(corpo)} : {});
  const d = await r.json();
  if (!r.ok) throw new Error(d.erro || ("Erro " + r.status));
  return d;
}
const reais = v => v == null ? "—" : v.toLocaleString("pt-BR", {style: "currency", currency: "BRL"});

function contador(input, teto) {
  const c = el("div", {class: "conta"});
  const at = () => { c.textContent = `${input.value.length}/${teto}`; c.classList.toggle("passou", input.value.length > teto); };
  input.addEventListener("input", at); at();
  return c;
}

function cartao(c) {
  if (c.erro) return el("div", {class: "cartao"}, el("b", {}, c.arquivo), el("p", {class: "falha"}, c.erro + " Chame o Claude."));

  const nomeRadio = "t_" + c.pai_sku;
  const proprio = el("input", {type: "text", placeholder: "Escreva o seu título"});
  const opcoes = c.titles.map(t => {
    const r = el("input", {type: "radio", name: nomeRadio, value: t.texto});
    if (t.texto === c.titulo_inicial) r.checked = true;
    return el("label", {class: "opcao"}, r,
      el("span", {}, `${t.texto} (${t.texto.length})`, t.recomendado ? " ⭐ recomendado" : "", el("br"), el("span", {class: "just"}, t.justificativa)));
  });
  const rProprio = el("input", {type: "radio", name: nomeRadio, value: "__proprio__"});
  if (!c.titles.some(t => t.texto === c.titulo_inicial)) { rProprio.checked = true; proprio.value = c.titulo_inicial || ""; }
  proprio.addEventListener("focus", () => { rProprio.checked = true; mudou(); });
  const contaProprio = contador(proprio, TETO_TITULO);

  const marca = el("input", {type: "text", value: c.marca});
  const modelo = el("input", {type: "text", value: c.modelo});
  const caixas = {};
  for (const [k, v] of Object.entries(c.descricao)) { caixas[k] = el("textarea", {}); caixas[k].value = v; }

  const conf = el("ul", {class: "conf"}, el("li", {}, "Conferindo…"));
  const btAprovar = el("button", {class: "principal"}, "Aprovar");
  const nota = el("input", {type: "text", placeholder: "O que a Renata deve refazer?"});
  const btDevolver = el("button", {}, "Devolver pra refazer");
  const msg = el("div");

  const titulo = () => {
    const sel = document.querySelector(`input[name="${CSS.escape(nomeRadio)}"]:checked`);
    return !sel ? "" : sel.value === "__proprio__" ? proprio.value : sel.value;
  };
  const edicao = () => ({titulo: titulo(), marca: marca.value, modelo: modelo.value,
    descricao: Object.fromEntries(Object.entries(caixas).map(([k, t]) => [k, t.value]))});

  let espera, ultimo = [];
  async function conferirAgora() {
    try {
      const {itens} = await api("/api/conferir", {pai: c.pai_sku, edicao: edicao()});
      ultimo = itens;
      conf.replaceChildren(...(itens.length ? itens.map(i => el("li", {class: i.nivel},
        (i.nivel === "aviso" ? "⚠ " : "❌ ") + i.texto)) : [el("li", {class: "tudook"}, "✅ Tudo certo nas conferências")]));
      const bloq = itens.some(i => i.nivel === "bloqueio"), errado = itens.some(i => i.nivel === "erro");
      btAprovar.disabled = bloq;
      btAprovar.textContent = bloq ? "Aprovar (corrija o bloqueio)" : errado ? "Aprovar mesmo assim" : "Aprovar";
      btAprovar.classList.toggle("mesmo", errado && !bloq);
    } catch (e) { conf.replaceChildren(el("li", {class: "erro"}, "A conferência falhou: " + e.message)); btAprovar.disabled = true; }
  }
  function mudou() { clearTimeout(espera); espera = setTimeout(conferirAgora, 400); }
  [proprio, marca, modelo, ...Object.values(caixas)].forEach(i => i.addEventListener("input", mudou));

  const caixa = el("div", {class: "cartao"});
  btAprovar.addEventListener("click", async () => {
    btAprovar.disabled = true;
    try {
      const r = await api("/api/aprovar", {pai: c.pai_sku, edicao: edicao()});
      if (!r.ok) { msg.replaceChildren(el("p", {class: "falha"}, r.motivo)); btAprovar.disabled = false; return; }
      feito(`✅ ${c.nome_base} aprovado às ${new Date().toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"})}` +
        (ultimo.length ? ` (com ${ultimo.length} aviso(s) aceito(s))` : ""));
      caixa.remove(); vazio();
    } catch (e) { msg.replaceChildren(el("p", {class: "falha"}, "Não gravou: " + e.message)); btAprovar.disabled = false; }
  });
  btDevolver.addEventListener("click", async () => {
    try {
      const r = await api("/api/devolver", {pai: c.pai_sku, nota: nota.value});
      if (!r.ok) { msg.replaceChildren(el("p", {class: "falha"}, r.motivo)); return; }
      feito(`↩ ${c.nome_base} devolvido para a Renata`); caixa.remove(); vazio();
    } catch (e) { msg.replaceChildren(el("p", {class: "falha"}, "Não gravou: " + e.message)); }
  });
  caixa.addEventListener("change", e => { if (e.target.type === "radio") mudou(); });

  const capas = c.capas ? el("div", {class: "capas"}, c.capas.map(k => el("figure", {},
      k.urls[0] ? el("img", {src: k.urls[0], alt: "capa " + k.cor}) : el("div", {}, "sem foto"), el("figcaption", {}, `${k.cor} (${k.urls.length})`))))
    : el("p", {class: "just"}, "Capas ainda não buscadas.");
  const ficha = el("table", {}, Object.entries(c.ficha).map(([k, v]) => el("tr", {}, el("td", {}, CAMPOS[k] || k), el("td", {}, String(v)))));
  const cx = c.caixa_cm || {};

  caixa.append(
    el("div", {class: "topo"}, el("div", {}, el("h2", {}, c.nome_base), el("div", {class: "sku"}, c.pai_sku)),
      el("div", {}, c.precos.map(p => `${p.cor} ${reais(p.preco)}`).join(" · "), " ",
        c.preco_provisorio ? el("span", {class: "selo"}, "preço provisório") : null)),
    el("div", {class: "secao"}, el("b", {}, "Capas"), capas),
    el("div", {class: "secao"}, el("b", {}, "Título"), opcoes,
      el("label", {class: "opcao"}, rProprio, el("span", {style: "flex:1"}, proprio, contaProprio))),
    el("div", {class: "secao linha2"},
      el("div", {}, el("b", {}, "Marca"), marca, contador(marca, TETO_MODELO),
        el("div", {class: "just"}, "Só o fornecedor, ou só Terra Casa Decor.")),
      el("div", {}, el("b", {}, "Modelo"), modelo, contador(modelo, TETO_MODELO),
        el("div", {class: "just"}, "Palavras de busca que não estão no título."))),
    el("div", {class: "secao"}, el("b", {}, "Descrição"),
      Object.entries(caixas).map(([k, t]) => el("div", {style: "margin-bottom:8px"}, el("div", {class: "just"}, BLOCOS[k] || k), t))),
    el("div", {class: "secao linha2"},
      el("div", {}, el("b", {}, "Ficha técnica"), ficha),
      el("div", {}, el("b", {}, "Caixa de envio"),
        el("div", {}, `Peso: ${c.peso_kg ?? "—"} kg`), el("div", {}, `Medidas: ${cx.largura ?? "—"} × ${cx.altura ?? "—"} × ${cx.comprimento ?? "—"} cm`))),
    c.observacoes.length ? el("div", {class: "secao"}, el("b", {}, "Observações da Renata"), el("ul", {}, c.observacoes.map(o => el("li", {}, o)))) : null,
    el("div", {class: "secao"}, el("b", {}, "Conferência"), conf),
    el("div", {class: "botoes"}, btAprovar, el("span", {style: "flex:1"}), nota, btDevolver),
    msg);
  conferirAgora();
  return caixa;
}

const lista = document.getElementById("lista");
function feito(t) { document.getElementById("feitos").append(el("div", {class: "feito"}, t)); }
function vazio() { if (!lista.querySelector(".cartao")) lista.replaceChildren(el("p", {class: "vazio"}, "Nada esperando aprovação. Pode fechar esta página.")); }

api("/api/pendentes").then(({cartoes}) => {
  lista.replaceChildren(...cartoes.map(cartao)); vazio();
}).catch(e => lista.replaceChildren(el("p", {class: "falha"}, "A tela não conseguiu ler os anúncios: " + e.message + ". A janela preta está aberta?")));
</script>
</body>
</html>
```

- [ ] **Step 5: Criar `Aprovar anuncios.bat`**

```bat
@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Aprovar anuncios do ML
python "%~dp0aprovacao.py" %*
if errorlevel 9009 (
  echo Python nao encontrado neste computador. Chame o Claude.
  pause
)
```

- [ ] **Step 6: Rodar — passa**

Run: `cd tools/aprovacao && python -m pytest tests -q`
Expected: `28 passed`.

- [ ] **Step 7: Conferência visual** — subir com `python tools/aprovacao/aprovacao.py --saida <cópia da pasta output num diretório de teste do projeto> --sem-navegador`, abrir no Chrome dedicado (chrome-devtools), conferir: os 2 cartões aparecem, contador vermelho acima de 60, Marca "Viel Inox" mostra erro e o botão vira "Aprovar mesmo assim", tema escuro legível, largura de celular sem rolagem lateral. **Não aprovar na pasta real** — só na cópia. Apagar a cópia ao final.

- [ ] **Step 8: Commit**

```bash
git add tools/aprovacao
git commit -m "feat(aprovacao): servidor local, pagina e atalho de clique duplo"
```

---

### Task 5: Step-06 aponta para a tela + documentação

**Files:** Modify `squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md`, `CLAUDE.md` (lista das frentes), `PROGRESSO.md`.

- [ ] **Step 1:** No step-06, no início das instruções, acrescentar:

> **Aprovação pela tela (desde 08/10/2026):** o Almir aprova em `tools/aprovacao/Aprovar anuncios.bat` (clique duplo). A tela grava em `anuncio-{pai}.yaml`: `titulo_final`, `attributes.BRAND/MODEL`, `description.bloco_*`, `status_copy: aprovado`, `aprovado_em`, `avisos_aceitos`; ou `status_copy: devolvido` + `nota_almir`. A esteira só segue para o step-07 quando **todos** os anúncios do lote estão `aprovado`; `devolvido` volta para a Renata (step-05) com a `nota_almir`. Aprovar por esta conversa continua valendo, gravando os mesmos campos. Obs.: o consolidado `anuncios.yaml` não é atualizado pela tela — a fonte é o `anuncio-{pai}.yaml`.

- [ ] **Step 2:** No `CLAUDE.md` do projeto, frente 1: acrescentar "aprovação do texto pela tela `tools/aprovacao/Aprovar anuncios.bat`". No `PROGRESSO.md`, registrar o estado e o próximo passo (pasta `A CRIAR` + `Criar anuncios.bat`).

- [ ] **Step 3: Commit**

```bash
git add squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md CLAUDE.md PROGRESSO.md
git commit -m "docs: step-06 aprova pela tela"
```

---

### Task 6: Primeiro uso real (com o Almir)

- [ ] **Step 1:** Almir dá clique duplo em `tools/aprovacao/Aprovar anuncios.bat` e decide a 5L e a 8L na tela.
- [ ] **Step 2:** Conferir os arquivos gravados: `python squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py squads/ml-anuncios/output/copywriting/anuncio-VIE-1066-PAI.yaml` (e 1067) e `validar_claims.py ... --sem-fotos --copy ...`; o resultado tem que bater com o que a tela mostrou.
- [ ] **Step 3:** Seguir a esteira (step-07 em diante) conforme `PROGRESSO.md`.
