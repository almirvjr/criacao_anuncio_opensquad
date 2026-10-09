# Botão "1 - Criar anuncios" — Plano de construção

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** o Almir cria anúncio do ML sozinho: planilha em `ANUNCIOS\A CRIAR` → clique → a esteira roda sem conversa → uma tela mostra tudo o que vai pro anúncio, ele decide, põe o preço e publica (descrição e Flex gravados sozinhos).

**Architecture:** um maestro em Python (`tools/esteira_auto/`) conduz as etapas de um lote (uma planilha = uma pasta própria com caderno de andamento). As etapas que precisam de cabeça chamam `claude -p` com instrução fixa e permissões fechadas; as fixas rodam código que já existe (`tiny_to_esteira.py`, `capas.py`, validadores). A tela de aprovação que já existe (`tools/aprovacao/`) cresce: quadro "faltou ou divergiu", preço, código de barras por cor, e publicação pelo `ML Publicar` do n8n (sem mexer nele) seguida de `completar_anuncio` (descrição + Flex).

**Tech Stack:** Python 3 (biblioteca padrão + `yaml`, `openpyxl`, `xlrd`, `pytest`, já instalados), HTML/JS puro numa página só, Claude Code CLI 2.1.x em modo `-p`.

**Spec:** `docs/superpowers/specs/2026-10-09-botao-criar-anuncios-design.md` (ler junto).

## Global Constraints

- **Nada novo no n8n.** A publicação usa o `ML Publicar` (`0rzNJ7RLqLzMbKnf`) como está, via `tools/disparar_publicacao.py`. Não editar o workflow.
- **Só o Almir publica.** Nenhuma chamada `claude -p` pode publicar: negar `disparar_publicacao.py`, `completar_anuncio.py`, leitura do `.env`, `python -c`, `curl` e o MCP n8n.
- **Segredo nunca impresso** (regra do hub): token do ML, endereço do webhook e token do Tiny só circulam dentro dos scripts; mensagem de erro nunca leva `str(e)` cru, só `type(e).__name__` ou texto fixo.
- **Arquivos temporários só dentro do projeto** (hook `check-write-path.ps1`).
- **Preta primeiro:** a ordem de publicação é a de `build_payloads_familia` (já põe a preta na frente). Não reordenar.
- **Título/nome da família ≤ 60 caracteres.** Modelo ≤ 30 (contador, não trava).
- **Texto para o Almir em português simples**, sem jargão (janela, tela, caderno).
- **Gravação segura:** escrever em arquivo `.novo` e trocar com `os.replace`; cópia em `_antes/` antes de reescrever um anúncio (padrão de `aprovacao._gravar_seguro`).
- Cubagem: `G:\Meu Drive\TERRA CASA DECOR\ESTOQUE\CUBAGEM DOS PRODUTOS.xlsx`. Pasta de entrada: `G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR` (feitos em `A CRIAR\FEITOS`).
- Testes: `python -m pytest -q tools/aprovacao/tests tools/esteira/tests tools/esteira_auto/tests` a partir da raiz do projeto; os 80 testes de hoje continuam verdes.

## Review Focus

1. **Clicar duas vezes em "Aprovar e publicar"** (ou recarregar a página no meio) não pode publicar a mesma cor duas vezes — cor com `mlb` gravado é pulada. Teste na Task 4.
2. **Produto sem cor** (a boleira, `modo: simples`, `cor: None`) tem que aparecer como uma linha só, título sem cor no fim, e publicar. Testes nas Tasks 4 e 6.
3. **SKU com `_`** (`BRI-coza34-40652_3009`) passa por nome de arquivo, URL da tela e etiqueta do Cloudinary sem virar `-`. Teste na Task 6.
4. **Fechar a janela preta no meio da esteira** e clicar de novo retoma da etapa seguinte, sem refazer as pagas. Teste na Task 2/8.
5. **Preço digitado com vírgula** ("129,90") vira 129.9; vazio, zero ou texto travam a publicação com frase clara. Teste na Task 6.

---

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `tools/esteira_auto/__init__.py` | pacote vazio |
| `tools/esteira_auto/chamar_claude.py` | monta e roda `claude -p` com permissões fechadas; devolve (ok, resumo) |
| `tools/esteira_auto/lote.py` | pasta do lote, caderno `andamento.json` + `andamento.txt`, retomada |
| `tools/esteira_auto/precheck.py` | etapa "entrada": planilha → `anuncios-entrada.json` + conferência de peso/caixa |
| `tools/esteira_auto/travas.py` | roda os validadores por anúncio e devolve motivo em português |
| `tools/esteira_auto/maestro.py` | ordem das etapas, nova tentativa, devolvidos, tela, `FEITOS` |
| `tools/esteira_auto/instrucoes/*.md` | instrução fixa de cada etapa com cabeça |
| `tools/esteira_auto/Criar anuncios.bat` | clique duplo |
| `tools/esteira_auto/tests/test_*.py` | testes |
| `tools/disparar_publicacao.py` | ganha função `enviar(corpo: dict) -> dict` (CLI continua igual) |
| `tools/completar_anuncio.py` | `completar` passa a devolver `{"descricao": bool, "flex": bool}` |
| `tools/montar_payload.py` | `montar(..., preco=None)` sobrescreve o preço de todas as cores |
| `tools/aprovacao/publicar.py` | publica um anúncio cor a cor, grava resultado, pula cor já publicada |
| `tools/aprovacao/olist_ean.py` | relê o código de barras de um SKU no Olist e atualiza a entrada |
| `tools/aprovacao/quadro.py` | monta o quadro "faltou ou divergiu" a partir do brief |
| `tools/aprovacao/aprovacao.py` | cartão completo, aprovar+publicar, tirar, tentar de novo, reler |
| `tools/aprovacao/pagina.html` | a tela |

---

### Task 1: Chamar o Claude sem conversa

**Files:**
- Create: `tools/esteira_auto/__init__.py` (vazio), `tools/esteira_auto/chamar_claude.py`, `tools/esteira_auto/tests/__init__.py` (vazio), `tools/esteira_auto/tests/test_chamar_claude.py`

**Interfaces:**
- Produces: `montar_comando(instrucao: str) -> list[str]`; `chamar(instrucao: str, raiz: Path, timeout_s: int = 2400, rodar=subprocess.run) -> tuple[bool, str]` (ok, resumo curto em português); constantes `PERMITIDAS: list[str]`, `NEGADAS: list[str]`.

- [ ] **Step 1: Sonda manual das opções do CLI (sem gastar etapa real)**

Run (na raiz do projeto, Git Bash):
```bash
claude --help | grep -E -- "--print|--allowedTools|--disallowedTools|--output-format|--permission-mode|--max-turns"
claude -p "Liste os nomes das ferramentas mcp__cloudinary e mcp__playwright que voce tem. Responda so os nomes." --output-format json --allowedTools "mcp__cloudinary__search-assets" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('is_error'), str(d.get('result'))[:400])"
```
Expected: as 6 opções existem; a resposta cita `mcp__cloudinary__search-assets` e alguma `mcp__playwright__*`. Se o MCP do projeto (`playwright`) não aparecer em modo `-p`, anotar e acrescentar `--mcp-config .mcp.json` no `montar_comando` (Step 3). Registrar o resultado no `HISTORICO.md` ao fim do plano.

- [ ] **Step 2: Escrever o teste que falha**

```python
# tools/esteira_auto/tests/test_chamar_claude.py
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import chamar_claude as cc  # noqa: E402


def test_comando_fecha_publicacao():
    cmd = cc.montar_comando("faz a etapa")
    assert cmd[:3] == ["claude", "-p", "faz a etapa"]
    negadas = cmd[cmd.index("--disallowedTools") + 1]
    for proibido in ("disparar_publicacao", "completar_anuncio", ".env", "python -c", "curl", "mcp__n8n"):
        assert proibido in negadas
    assert "--output-format" in cmd and cmd[cmd.index("--output-format") + 1] == "json"


def test_chamar_ok(tmp_path):
    def falso(cmd, **kw):
        assert kw["cwd"] == str(tmp_path)
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"is_error": False, "result": "feito"}), stderr="")
    assert cc.chamar("x", tmp_path, rodar=falso) == (True, "feito")


def test_chamar_erro_nao_vaza_excecao(tmp_path):
    def estoura(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)
    ok, txt = cc.chamar("x", tmp_path, rodar=estoura)
    assert not ok and "tempo" in txt


def test_chamar_saida_nao_json(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="lixo", stderr="segredo123")
    ok, txt = cc.chamar("x", tmp_path, rodar=falso)
    assert not ok and "segredo123" not in txt
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python -m pytest -q tools/esteira_auto/tests/test_chamar_claude.py`
Expected: FAIL (`No module named esteira_auto.chamar_claude`).

- [ ] **Step 4: Implementar**

```python
# tools/esteira_auto/chamar_claude.py
"""Chama o Claude sem conversa (claude -p) para uma etapa da esteira.

Permissoes fechadas: pode ler/escrever arquivos, rodar python (validadores, tiny_to_esteira),
buscar no Cloudinary e usar o navegador escondido da Helena. NAO pode publicar: o disparo
e o 2o envio sao negados, assim como ler o .env, python -c, curl e o MCP do n8n.
Nunca devolve texto cru de erro (pode carregar segredo)."""
import json
import subprocess
from pathlib import Path

PERMITIDAS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task", "WebSearch", "WebFetch",
    "Bash(python *)", "Bash(ls *)", "Bash(mkdir *)",
    "mcp__cloudinary__search-assets", "mcp__playwright", "mcp__mercadolibre",
]
NEGADAS = [
    "Bash(python tools/disparar_publicacao.py*)", "Bash(python tools/completar_anuncio.py*)",
    "Bash(python -c*)", "Bash(curl*)", "Read(./.env)", "Read(**/.env)", "mcp__n8n",
]


def montar_comando(instrucao):
    return ["claude", "-p", instrucao, "--output-format", "json",
            "--allowedTools", ",".join(PERMITIDAS), "--disallowedTools", ",".join(NEGADAS)]


def chamar(instrucao, raiz, timeout_s=2400, rodar=subprocess.run):
    try:
        r = rodar(montar_comando(instrucao), cwd=str(Path(raiz)), capture_output=True,
                  text=True, encoding="utf-8", errors="replace", timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return False, f"passou do tempo ({timeout_s // 60} min)"
    except FileNotFoundError:
        return False, "nao achei o programa do Claude neste computador"
    try:
        d = json.loads(r.stdout or "")
    except ValueError:
        return False, f"o Claude terminou sem resposta legivel (codigo {r.returncode})"
    if r.returncode != 0 or d.get("is_error"):
        return False, f"o Claude terminou com erro (codigo {r.returncode})"
    return True, str(d.get("result") or "")[:500]
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python -m pytest -q tools/esteira_auto/tests/test_chamar_claude.py` → Expected: 4 passed.

- [ ] **Step 6: Sonda de permissão real (a trava trava?)**

Run:
```bash
python -c "import sys; sys.path.insert(0,'tools'); from esteira_auto.chamar_claude import chamar; from pathlib import Path; print(chamar('Rode: python tools/disparar_publicacao.py x y . Depois diga se conseguiu rodar ou se foi negado.', Path('.'), timeout_s=300))"
```
Expected: `(True, '...negad...')` — a resposta diz que foi negado e **nenhum** arquivo `y` foi criado (`ls y` → não existe). Se rodou, a trava não serve: parar e rever `NEGADAS` antes de seguir.

- [ ] **Step 7: Commit**

```bash
git add tools/esteira_auto/__init__.py tools/esteira_auto/chamar_claude.py tools/esteira_auto/tests/
git commit -m "feat(esteira-auto): chamar o Claude sem conversa com permissao fechada"
```

---

### Task 2: Lote e caderno de andamento

**Files:**
- Create: `tools/esteira_auto/lote.py`, `tools/esteira_auto/tests/test_lote.py`

**Interfaces:**
- Produces:
  - `ETAPAS = ["entrada", "capas", "curadoria", "categoria", "pesquisa", "texto", "revisao", "tela"]`
  - `criar_lote(planilha: Path, raiz_lotes: Path, agora: datetime) -> Path`
  - `ler(lote: Path) -> dict` (`{"planilha", "criado_em", "feitas": [..], "parados": {pai: motivo}, "concluido": bool}`)
  - `marcar_feita(lote, etapa, agora)`, `parar_pai(lote, pai, motivo, agora)`, `anotar(lote, texto, agora)`, `concluir(lote, agora)`
  - `proxima(lote) -> str | None`
  - `lote_aberto(raiz_lotes) -> Path | None` (o mais antigo não concluído)

- [ ] **Step 1: Teste que falha**

```python
# tools/esteira_auto/tests/test_lote.py
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L  # noqa: E402

T = datetime(2026, 10, 9, 14, 30, 0)


def test_lote_novo_comeca_na_entrada(tmp_path):
    pl = tmp_path / "boleira.xls"; pl.write_text("x")
    lt = L.criar_lote(pl, tmp_path / "lotes", T)
    assert lt.name == "2026-10-09-143000"
    assert L.ler(lt)["planilha"] == str(pl)
    assert L.proxima(lt) == "entrada"


def test_retoma_da_proxima(tmp_path):
    lt = L.criar_lote(tmp_path / "a.xls", tmp_path / "lotes", T)
    L.marcar_feita(lt, "entrada", T); L.marcar_feita(lt, "capas", T)
    assert L.proxima(lt) == "curadoria"
    L.marcar_feita(lt, "capas", T)  # repetir nao duplica
    assert L.ler(lt)["feitas"] == ["entrada", "capas"]


def test_caderno_em_portugues(tmp_path):
    lt = L.criar_lote(tmp_path / "a.xls", tmp_path / "lotes", T)
    L.parar_pai(lt, "VIE-1-PAI", "faltou capa do Preto", T)
    txt = (lt / "andamento.txt").read_text(encoding="utf-8")
    assert "VIE-1-PAI" in txt and "faltou capa do Preto" in txt
    assert L.ler(lt)["parados"] == {"VIE-1-PAI": "faltou capa do Preto"}


def test_lote_aberto_pula_concluido(tmp_path):
    raiz = tmp_path / "lotes"
    a = L.criar_lote(tmp_path / "a.xls", raiz, T)
    b = L.criar_lote(tmp_path / "b.xls", raiz, datetime(2026, 10, 9, 15, 0, 0))
    assert L.lote_aberto(raiz) == a
    L.concluir(a, T)
    assert L.lote_aberto(raiz) == b
    assert L.proxima(a) is None


def test_lote_aberto_sem_pasta(tmp_path):
    assert L.lote_aberto(tmp_path / "nada") is None
```

- [ ] **Step 2: Rodar e ver falhar** — `python -m pytest -q tools/esteira_auto/tests/test_lote.py` → FAIL (módulo não existe).

- [ ] **Step 3: Implementar**

```python
# tools/esteira_auto/lote.py
"""Lote = uma planilha, uma pasta propria. O caderno (andamento.json) diz o que ja foi feito;
andamento.txt e o mesmo em portugues, para o Almir e para o Claude lerem depois."""
import json
import os
from pathlib import Path

ETAPAS = ["entrada", "capas", "curadoria", "categoria", "pesquisa", "texto", "revisao", "tela"]
NOMES = {"entrada": "lendo a planilha", "capas": "conferindo as capas", "curadoria": "organizando os dados",
         "categoria": "escolhendo a categoria", "pesquisa": "pesquisando concorrentes",
         "texto": "escrevendo o texto", "revisao": "revisando", "tela": "esperando voce na tela"}


def _salvar(lote, d):
    p = Path(lote) / "andamento.json"
    tmp = p.with_name(p.name + ".novo")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def ler(lote):
    return json.loads((Path(lote) / "andamento.json").read_text(encoding="utf-8"))


def anotar(lote, texto, agora):
    with open(Path(lote) / "andamento.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{agora:%d/%m %H:%M} - {texto}\n")


def criar_lote(planilha, raiz_lotes, agora):
    lote = Path(raiz_lotes) / f"{agora:%Y-%m-%d-%H%M%S}"
    lote.mkdir(parents=True, exist_ok=False)
    _salvar(lote, {"planilha": str(planilha), "criado_em": f"{agora:%Y-%m-%d %H:%M}",
                   "feitas": [], "parados": {}, "concluido": False})
    anotar(lote, f"lote criado para a planilha {Path(planilha).name}", agora)
    return lote


def marcar_feita(lote, etapa, agora):
    d = ler(lote)
    if etapa not in d["feitas"]:
        d["feitas"].append(etapa)
        _salvar(lote, d)
        anotar(lote, f"pronto: {NOMES.get(etapa, etapa)}", agora)


def parar_pai(lote, pai, motivo, agora):
    d = ler(lote)
    d["parados"][pai] = motivo
    _salvar(lote, d)
    anotar(lote, f"PAROU {pai}: {motivo}", agora)


def concluir(lote, agora):
    d = ler(lote)
    d["concluido"] = True
    _salvar(lote, d)
    anotar(lote, "lote concluido", agora)


def proxima(lote):
    d = ler(lote)
    if d.get("concluido"):
        return None
    return next((e for e in ETAPAS if e not in d["feitas"]), None)


def lote_aberto(raiz_lotes):
    raiz = Path(raiz_lotes)
    if not raiz.is_dir():
        return None
    for p in sorted(x for x in raiz.iterdir() if (x / "andamento.json").is_file()):
        if not ler(p).get("concluido"):
            return p
    return None
```

- [ ] **Step 4: Rodar e ver passar** — 5 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/esteira_auto/lote.py tools/esteira_auto/tests/test_lote.py
git commit -m "feat(esteira-auto): lote com caderno de andamento e retomada"
```

---

### Task 3: Etapa "entrada" (planilha + peso e caixa)

**Files:**
- Create: `tools/esteira_auto/precheck.py`, `tools/esteira_auto/tests/test_precheck.py`

**Interfaces:**
- Consumes: `tools/tiny_to_esteira.py` (CLI: `entrada saida --cubagem PATH`), `esteira.payload_builder.atributos_embalagem(anuncio) -> list`.
- Produces: `CUBAGEM: Path`; `ler_planilha(planilha: Path, lote: Path, cubagem: Path = CUBAGEM, rodar=subprocess.run) -> list[str]` (lista de problemas; vazia = ok; grava `lote/anuncios-entrada.json`); `faltas_de_caixa(entrada: dict) -> list[str]`.

- [ ] **Step 1: Teste que falha**

```python
# tools/esteira_auto/tests/test_precheck.py
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import precheck as P  # noqa: E402

BOM = {"pai_sku": "BRI-1", "modo": "simples", "peso_bruto_kg": 1.2,
       "dim_embalagem_cm": {"largura": 30, "altura": 12, "comprimento": 30},
       "variacoes": [{"sku": "BRI-1", "cor": None, "ean": "7891", "preco_venda": 10}]}


def test_caixa_ok():
    assert P.faltas_de_caixa({"anuncios": [BOM]}) == []


def test_caixa_faltando_diz_qual():
    ruim = dict(BOM, pai_sku="BRI-2", peso_bruto_kg=None)
    faltas = P.faltas_de_caixa({"anuncios": [BOM, ruim]})
    assert len(faltas) == 1 and "BRI-2" in faltas[0] and "cubagem" in faltas[0]


def test_planilha_vazia(tmp_path):
    def falso(cmd, **kw):
        (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": []}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    probs = P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso)
    assert probs and "nenhum produto" in probs[0]


def test_planilha_que_nao_abre(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "Traceback ... segredo")
    probs = P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso)
    assert probs and "nao consegui ler a planilha" in probs[0] and "segredo" not in probs[0]


def test_planilha_boa(tmp_path):
    def falso(cmd, **kw):
        assert "--cubagem" in cmd
        (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [BOM]}), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert P.ler_planilha(tmp_path / "x.xls", tmp_path, cubagem=tmp_path / "c.xlsx", rodar=falso) == []
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar**

```python
# tools/esteira_auto/precheck.py
"""Etapa 'entrada': planilha do Olist -> anuncios-entrada.json do lote, com peso e caixa da
cubagem. Falta peso/caixa = para ja, dizendo o SKU (o frete do ML sairia errado)."""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
from esteira.payload_builder import atributos_embalagem  # noqa: E402

CUBAGEM = Path(r"G:\Meu Drive\TERRA CASA DECOR\ESTOQUE\CUBAGEM DOS PRODUTOS.xlsx")


def faltas_de_caixa(entrada):
    return [f"{a['pai_sku']}: sem peso ou medida da caixa — confira a linha dele na cubagem"
            for a in entrada.get("anuncios", []) if not atributos_embalagem(a)]


def ler_planilha(planilha, lote, cubagem=CUBAGEM, rodar=subprocess.run):
    saida = Path(lote) / "anuncios-entrada.json"
    cmd = [sys.executable, str(RAIZ / "tools" / "tiny_to_esteira.py"), str(planilha), str(saida),
           "--cubagem", str(cubagem)]
    r = rodar(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not saida.is_file():
        return ["nao consegui ler a planilha: ela e o export de produtos do Olist (.xls ou .xlsx)?"]
    entrada = json.loads(saida.read_text(encoding="utf-8"))
    if not entrada.get("anuncios"):
        return ["a planilha nao tem nenhum produto (so o cabecalho?)"]
    return faltas_de_caixa(entrada)
```

- [ ] **Step 4: Rodar e ver passar** — 5 passed. Conferir que `atributos_embalagem` devolve lista vazia quando `peso_bruto_kg` é `None` (ler `tools/esteira/payload_builder.py`); se devolver algo, ajustar o teste `test_caixa_faltando_diz_qual` para o campo que de fato zera e registrar no commit.

- [ ] **Step 5: Commit**

```bash
git add tools/esteira_auto/precheck.py tools/esteira_auto/tests/test_precheck.py
git commit -m "feat(esteira-auto): etapa de entrada com conferencia de peso e caixa"
```

---

### Task 4: Publicar um anúncio cor a cor (sem tela ainda)

**Files:**
- Modify: `tools/disparar_publicacao.py` (extrair `enviar`), `tools/completar_anuncio.py` (`completar` devolve dict), `tools/montar_payload.py` (`preco=`)
- Create: `tools/aprovacao/publicar.py`, `tools/aprovacao/tests/test_publicar.py`

**Interfaces:**
- Produces:
  - `disparar_publicacao.enviar(corpo: dict, timeout=120) -> dict` → `{"http": int|None, "resposta": dict}` (nunca imprime o endereço)
  - `completar_anuncio.completar(payload, mlb, tk) -> dict` → `{"descricao": bool, "flex": bool}` (o `__main__` sai 0 se ambos True)
  - `montar_payload.montar(entrada, categorias, copy, capas, pai, preco=None) -> list[dict]`
  - `publicar.publicar_anuncio(saida: Path, pai: str, enviar=..., completar=..., token=...) -> list[dict]` — um item por cor: `{"sku", "cor", "ok": bool, "mlb", "link", "descricao": bool, "flex": bool, "erro": str|None}`; grava em `anuncio-{pai}.yaml` → `publicacao: {sku: {...}}`; cor com `mlb` já gravado é pulada (não chama `enviar`).
  - `publicar.publicar_cor(saida, pai, sku, ...)` → mesmo item, só aquela cor (para "Tentar de novo").
  - `publicar.situacao(doc) -> "nao_publicado" | "em_parte" | "publicado"`

- [ ] **Step 1: Teste que falha**

```python
# tools/aprovacao/tests/test_publicar.py
import json
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import publicar as pub  # noqa: E402

PAI = "VIE-1-PAI"


@pytest.fixture
def saida(tmp_path):
    for d in ("copywriting", "categorizacao", "capas"):
        (tmp_path / d).mkdir()
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{
        "pai_sku": PAI, "modo": "variacoes", "peso_bruto_kg": 0.7,
        "dim_embalagem_cm": {"largura": 28, "altura": 21, "comprimento": 21},
        "variacoes": [{"sku": "VIE-1-BR", "cor": "Branco", "ean": "789001", "preco_venda": 10.0},
                      {"sku": "VIE-1-PT", "cor": "Preto", "ean": "789002", "preco_venda": 10.0}]}]}),
        encoding="utf-8")
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump(
        {"categorias": [{"pai_sku": PAI, "category_id": "MLB33375", "cor_value_map": {}}]}), encoding="utf-8")
    (tmp_path / "capas" / f"capas-{PAI}.yaml").write_text(yaml.safe_dump({"pai_sku": PAI, "picture_ids_por_variacao": [
        {"sku_variacao": "VIE-1-BR", "cor": "Branco", "picture_ids": ["https://x/br.jpg"]},
        {"sku_variacao": "VIE-1-PT", "cor": "Preto", "picture_ids": ["https://x/pt.jpg"]}]}), encoding="utf-8")
    (tmp_path / "copywriting" / f"anuncio-{PAI}.yaml").write_text(yaml.safe_dump({
        "pai_sku": PAI, "status_copy": "aprovado", "titulo_final": "Lixeira Inox 5 Litros Pedal",
        "preco": 92.71, "attributes": {"BRAND": "Viel", "MODEL": "Cesto"},
        "description": {"bloco_1_abertura": "Texto."}}, allow_unicode=True), encoding="utf-8")
    return tmp_path


def _doc(saida):
    return yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))


def test_publica_preta_primeiro_com_preco_da_tela(saida):
    enviados = []
    def enviar(corpo):
        enviados.append(corpo)
        return {"http": 200, "resposta": {"status": "success", "mlb_id": f"MLB{len(enviados)}", "permalink": "http://l"}}
    r = pub.publicar_anuncio(saida, PAI, enviar=enviar, completar=lambda p, m, t: {"descricao": True, "flex": True}, token=lambda: "tk")
    assert [c["sku"] for c in enviados] == ["VIE-1-PT", "VIE-1-BR"]
    assert all(c["price"] == 92.71 for c in enviados)
    assert all(i["ok"] and i["descricao"] and i["flex"] for i in r)
    assert pub.situacao(_doc(saida)) == "publicado"


def test_nao_publica_duas_vezes(saida):
    chamadas = []
    def enviar(corpo):
        chamadas.append(corpo["sku"])
        return {"http": 200, "resposta": {"status": "success", "mlb_id": "MLB9", "permalink": "http://l"}}
    ok = lambda p, m, t: {"descricao": True, "flex": True}
    pub.publicar_anuncio(saida, PAI, enviar=enviar, completar=ok, token=lambda: "tk")
    pub.publicar_anuncio(saida, PAI, enviar=enviar, completar=ok, token=lambda: "tk")
    assert chamadas == ["VIE-1-PT", "VIE-1-BR"]


def test_falha_numa_cor_nao_para_a_outra(saida):
    def enviar(corpo):
        if corpo["sku"] == "VIE-1-PT":
            return {"http": None, "resposta": {"texto_cru": "falha de conexao"}}
        return {"http": 200, "resposta": {"status": "success", "mlb_id": "MLB2", "permalink": "http://l"}}
    r = pub.publicar_anuncio(saida, PAI, enviar=enviar, completar=lambda p, m, t: {"descricao": True, "flex": False}, token=lambda: "tk")
    pt, br = r
    assert not pt["ok"] and "nao respondeu" in pt["erro"]
    assert br["ok"] and br["flex"] is False
    assert pub.situacao(_doc(saida)) == "em_parte"


def test_tentar_de_novo_so_a_cor(saida):
    falhou = {"http": 200, "resposta": {"status": "failed", "error_message": "categoria invalida"}}
    pub.publicar_anuncio(saida, PAI, enviar=lambda c: falhou, completar=None, token=lambda: "tk")
    r = pub.publicar_cor(saida, PAI, "VIE-1-PT",
                         enviar=lambda c: {"http": 200, "resposta": {"status": "success", "mlb_id": "MLB7", "permalink": "http://l"}},
                         completar=lambda p, m, t: {"descricao": True, "flex": True}, token=lambda: "tk")
    assert r["ok"] and r["mlb"] == "MLB7"
    assert _doc(saida)["publicacao"]["VIE-1-BR"]["ok"] is False


def test_sem_preco_nao_publica(saida):
    d = _doc(saida); d.pop("preco")
    (saida / "copywriting" / f"anuncio-{PAI}.yaml").write_text(yaml.safe_dump(d), encoding="utf-8")
    with pytest.raises(ValueError, match="preco"):
        pub.publicar_anuncio(saida, PAI, enviar=lambda c: 1 / 0, completar=None, token=lambda: "tk")


def test_produto_sem_cor(saida):
    e = json.loads((saida / "anuncios-entrada.json").read_text(encoding="utf-8"))
    e["anuncios"][0].update(modo="simples", variacoes=[{"sku": "BRI-coza34-40652_3009", "cor": None, "ean": "789", "preco_venda": 10}])
    e["anuncios"][0]["pai_sku"] = PAI
    (saida / "anuncios-entrada.json").write_text(json.dumps(e), encoding="utf-8")
    (saida / "capas" / f"capas-{PAI}.yaml").write_text(yaml.safe_dump({"pai_sku": PAI, "picture_ids_por_variacao": [
        {"sku_variacao": "BRI-coza34-40652_3009", "cor": None, "picture_ids": ["https://x/a.jpg"]}]}), encoding="utf-8")
    enviados = []
    pub.publicar_anuncio(saida, PAI, enviar=lambda c: enviados.append(c) or {"http": 200, "resposta": {"status": "success", "mlb_id": "MLB1", "permalink": "l"}},
                         completar=lambda p, m, t: {"descricao": True, "flex": True}, token=lambda: "tk")
    assert len(enviados) == 1 and enviados[0]["sku"] == "BRI-coza34-40652_3009"
    assert not any(a["id"] == "COLOR" for a in enviados[0]["attributes"])
```

- [ ] **Step 2: Rodar e ver falhar** — `python -m pytest -q tools/aprovacao/tests/test_publicar.py` → FAIL (módulo `publicar` não existe).

- [ ] **Step 3: `enviar` em `tools/disparar_publicacao.py`** — substituir o corpo de `main()` por uma chamada a `enviar` e acrescentar a função (o CLI continua imprimindo o mesmo JSON):

```python
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) terra-esteira/1.0"


def enviar(corpo, timeout=120):
    """POST de um pacote (dict) ao ML Publicar. Devolve {'http', 'resposta'}; nunca o endereco."""
    url = endereco()
    if not url:
        return {"http": None, "resposta": {"texto_cru": "N8N_WEBHOOK_ML_PUBLICAR ausente no .env"}}
    req = urllib.request.Request(url, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            http, txt = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        http, txt = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        http, txt = None, f"falha de conexao ({type(e).__name__})"
    try:
        resp = json.loads(txt)
    except Exception:  # noqa: BLE001
        resp = {"texto_cru": txt[:2000]}
    return {"http": http, "resposta": resp if isinstance(resp, dict) else {"texto_cru": str(resp)[:2000]}}


def main():
    payload, saida = Path(sys.argv[1]), Path(sys.argv[2])
    corpo = json.loads(payload.read_text(encoding="utf-8"))
    envio = datetime.now().isoformat(timespec="seconds")
    r = enviar(corpo)
    if r["http"] is None and "ausente" in str(r["resposta"].get("texto_cru")):
        print("N8N_WEBHOOK_ML_PUBLICAR ausente no .env"); sys.exit(2)
    resp = r["resposta"]
    doc = {"pai_sku": corpo["pai_sku"], "http_webhook": r["http"], "hora_envio": envio,
           "hora_resposta": datetime.now().isoformat(timespec="seconds"), "n8n_response": resp}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"http": r["http"], "status": resp.get("status"), "mlb_id": resp.get("mlb_id"),
                      "permalink": resp.get("permalink"), "stage": resp.get("stage"),
                      "error_code": resp.get("error_code"), "error_message": resp.get("error_message"),
                      "tiny_sync": resp.get("tiny_sync")}, ensure_ascii=False))
```

- [ ] **Step 4: `completar` devolve dict** — em `tools/completar_anuncio.py`, trocar `ok = True` / `ok &= ...` / `return ok` por:

```python
def completar(payload, mlb, tk):
    res = {"descricao": False, "flex": False}
    st, d = _chamar("GET", f"/items/{mlb}/description", tk)
    if st == 200 and (d.get("plain_text") or "").strip():
        res["descricao"] = True
        print(f"{mlb} descricao: ja existe")
    else:
        st, d = _chamar("POST", f"/items/{mlb}/description", tk, {"plain_text": texto_descricao(payload)})
        res["descricao"] = st in (200, 201)
        print(f"{mlb} descricao: {'gravada' if res['descricao'] else 'FALHOU HTTP %s %s' % (st, d.get('message'))}")
    st, d = _chamar("GET", f"/flex/sites/MLB/items/{mlb}/v2", tk)
    if st == 200 and d.get("has_flex"):
        res["flex"] = True
        print(f"{mlb} flex: ja ligado")
    else:
        st, d = _chamar("POST", f"/flex/sites/MLB/items/{mlb}/v2", tk)
        res["flex"] = st in (200, 201, 204)
        print(f"{mlb} flex: {'ligado' if res['flex'] else 'FALHOU HTTP %s %s' % (st, d.get('message'))}")
    return res
```
e no `__main__`: `r = completar(payload, sys.argv[2], tk); sys.exit(0 if all(r.values()) else 1)`.

- [ ] **Step 5: `preco=` em `montar_payload.montar`** — nova assinatura `def montar(entrada, categorias, copy, capas, pai, preco=None):` e, logo depois de achar `anuncio`:

```python
    if preco is not None:
        for v in anuncio["variacoes"]:
            v["preco_venda"] = round(float(preco), 2)
```

- [ ] **Step 6: Implementar `tools/aprovacao/publicar.py`**

```python
"""Publica um anuncio aprovado na tela: uma cor por vez, preta primeiro, pelo ML Publicar
(n8n, sem mudanca) e, logo depois, descricao + Flex (completar_anuncio). Cor ja publicada
(com mlb gravado) e pulada: clicar duas vezes nao duplica."""
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import montar_payload  # noqa: E402


def _caminho(saida, pai):
    return Path(saida) / "copywriting" / f"anuncio-{pai}.yaml"


def _ler(p):
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _gravar(p, doc):
    tmp = p.with_name(p.name + ".novo")
    with open(tmp, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, allow_unicode=True, sort_keys=False, width=100000)
    os.replace(tmp, p)


def _padrao_enviar(corpo):
    from disparar_publicacao import enviar
    return enviar(corpo)


def _padrao_completar(payload, mlb, tk):
    from completar_anuncio import completar
    return completar(payload, mlb, tk)


def _padrao_token():
    from conferir_no_ml import token
    return token()


def pacotes(saida, pai):
    saida = Path(saida)
    doc = _ler(_caminho(saida, pai))
    if not doc.get("preco"):
        raise ValueError("Anuncio sem preco: digite o preco na tela antes de publicar.")
    return montar_payload.montar(saida / "anuncios-entrada.json", saida / "categorizacao" / "categorias.yaml",
                                 _caminho(saida, pai), saida / "capas" / f"capas-{pai}.yaml", pai,
                                 preco=doc["preco"])


def _uma(pacote, enviar, completar, token):
    item = {"sku": pacote["sku"], "cor": next((a["value_name"] for a in pacote["attributes"] if a["id"] == "COLOR"), None),
            "ok": False, "mlb": None, "link": None, "descricao": False, "flex": False, "erro": None,
            "em": datetime.now().strftime("%Y-%m-%d %H:%M")}
    r = enviar(pacote)
    resp = r.get("resposta") or {}
    if r.get("http") is None or r.get("http") >= 500:
        item["erro"] = "o sistema de publicacao nao respondeu; nada foi publicado nesta cor"
        return item
    if resp.get("status") not in ("success", "partial") or not resp.get("mlb_id"):
        item["erro"] = f"o Mercado Livre recusou: {resp.get('error_message') or resp.get('error_code') or 'sem motivo'}"
        return item
    item.update(ok=True, mlb=resp["mlb_id"], link=resp.get("permalink"))
    tk = token()
    if not tk:
        item["erro"] = "publicado, mas nao consegui o acesso ao ML para gravar descricao e Flex"
        return item
    c = completar(pacote, item["mlb"], tk)
    item.update(descricao=bool(c.get("descricao")), flex=bool(c.get("flex")))
    return item


def publicar_anuncio(saida, pai, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    lista = pacotes(saida, pai)
    feitos = []
    for pacote in lista:
        doc = _ler(caminho)
        doc["_total_cores"] = len(lista)
        anterior = (doc.get("publicacao") or {}).get(pacote["sku"]) or {}
        if anterior.get("mlb"):
            feitos.append(anterior)
            continue
        item = _uma(pacote, enviar, completar, token)
        doc.setdefault("publicacao", {})[pacote["sku"]] = item
        _gravar(caminho, doc)
        feitos.append(item)
    return feitos


def publicar_cor(saida, pai, sku, enviar=_padrao_enviar, completar=_padrao_completar, token=_padrao_token):
    caminho = _caminho(saida, pai)
    pacote = next((p for p in pacotes(saida, pai) if p["sku"] == sku), None)
    if pacote is None:
        raise ValueError(f"Cor {sku} nao e deste anuncio.")
    doc = _ler(caminho)
    anterior = (doc.get("publicacao") or {}).get(sku) or {}
    if anterior.get("mlb"):
        return anterior
    item = _uma(pacote, enviar, completar, token)
    doc.setdefault("publicacao", {})[sku] = item
    _gravar(caminho, doc)
    return item


def situacao(doc):
    pub = doc.get("publicacao") or {}
    if not pub:
        return "nao_publicado"
    oks = [bool(v.get("mlb")) for v in pub.values()]
    return "publicado" if all(oks) and len(oks) == doc.get("_total_cores", len(oks)) else "em_parte"
```

> `situacao` usa `_total_cores` (gravado por `publicar_anuncio`) para não chamar de "publicado" um anúncio em que só parte das cores foi tentada. O teste `test_falha_numa_cor_nao_para_a_outra` cobre o caso "em_parte".

- [ ] **Step 7: Rodar e ver passar** — `python -m pytest -q tools/aprovacao/tests tools/esteira/tests` → todos passam (os 80 antigos + 6 novos).

- [ ] **Step 8: Commit**

```bash
git add tools/disparar_publicacao.py tools/completar_anuncio.py tools/montar_payload.py tools/aprovacao/publicar.py tools/aprovacao/tests/test_publicar.py
git commit -m "feat(publicacao): publicar cor a cor com descricao e Flex, sem duplicar"
```

---

### Task 5: Reler o código de barras no Olist

**Files:**
- Create: `tools/aprovacao/olist_ean.py`, `tools/aprovacao/tests/test_olist_ean.py`

**Interfaces:**
- Consumes: `projects/cadastro_tiny/scripts/senha_banco.token_do_tiny()` (senha do banco no cofre do Windows; **pode pedir senha no terminal** se o cofre estiver vazio — por isso a tela chama com `token` injetado que só usa o cofre).
- Produces: `reler_ean(saida: Path, sku: str, buscar=_buscar_no_olist) -> dict` → `{"ok": bool, "ean": str|None, "motivo": str|None}`; atualiza `anuncios-entrada.json` (escrita segura).

- [ ] **Step 1: Sonda manual do campo** (só leitura, um produto, sem imprimir token):

```bash
python - <<'EOF'
import json, sys, urllib.request
sys.path.insert(0, r"../cadastro_tiny/scripts")
from senha_banco import token_do_tiny
tk = token_do_tiny()
req = urllib.request.Request("https://api.tiny.com.br/public-api/v3/produtos?codigo=BRI-coza34-40652_3009",
                             headers={"Authorization": "Bearer " + tk, "Accept": "application/json"})
d = json.loads(urllib.request.urlopen(req, timeout=30).read())
it = (d.get("itens") or [{}])[0]
print(sorted(it.keys())); print("gtin:", it.get("gtin"), "id:", it.get("id"))
EOF
```
Expected: lista de campos com `gtin` e `id`. Se `gtin` não vier na lista, usar `GET /produtos/{id}` (campo `gtin`) em `_buscar_no_olist` — ajustar a implementação do Step 3 conforme o resultado e anotar no commit.

- [ ] **Step 2: Teste que falha**

```python
# tools/aprovacao/tests/test_olist_ean.py
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import olist_ean as oe  # noqa: E402


def _entrada(tmp_path, ean=None):
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "P", "variacoes": [
        {"sku": "BRI-coza34-40652_3009", "ean": ean}]}]}), encoding="utf-8")


def test_grava_codigo_novo(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: ("7898755999999", None))
    assert r == {"ok": True, "ean": "7898755999999", "motivo": None}
    e = json.loads((tmp_path / "anuncios-entrada.json").read_text(encoding="utf-8"))
    assert e["anuncios"][0]["variacoes"][0]["ean"] == "7898755999999"


def test_olist_ainda_sem_codigo(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: (None, None))
    assert not r["ok"] and "ainda nao tem" in r["motivo"]


def test_falha_de_acesso(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "BRI-coza34-40652_3009", buscar=lambda sku: (None, "sem acesso ao Olist"))
    assert not r["ok"] and r["motivo"] == "sem acesso ao Olist"


def test_sku_fora_do_lote(tmp_path):
    _entrada(tmp_path)
    r = oe.reler_ean(tmp_path, "OUTRO", buscar=lambda sku: ("1", None))
    assert not r["ok"] and "nao e deste lote" in r["motivo"]
```

- [ ] **Step 3: Implementar**

```python
# tools/aprovacao/olist_ean.py
"""Rele o codigo de barras de um SKU no Olist (depois de gerado pelo botao da GS1) e grava
na entrada do lote, sem recomecar a esteira. Token so do cofre do Windows: a tela nao
tem terminal para pedir senha. Nunca imprime token nem texto cru de erro."""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS_TINY = Path(__file__).resolve().parents[3] / "cadastro_tiny" / "scripts"
BASE = "https://api.tiny.com.br/public-api/v3"


def _token_do_cofre():
    try:
        import keyring
        sys.path.insert(0, str(SCRIPTS_TINY))
        import senha_banco
        senha = keyring.get_password(senha_banco.SERVICO, senha_banco.USUARIO)
        return senha_banco._token(senha) if senha else None
    except Exception:  # noqa: BLE001
        return None


def _buscar_no_olist(sku):
    tk = _token_do_cofre()
    if not tk:
        return None, "sem acesso ao Olist (rode uma vez o botao '1 - Conferir EANs' para guardar a senha)"
    url = f"{BASE}/produtos?codigo={urllib.parse.quote(sku)}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tk, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            itens = json.loads(r.read()).get("itens") or []
    except Exception as e:  # noqa: BLE001
        return None, f"o Olist nao respondeu ({type(e).__name__})"
    item = next((i for i in itens if str(i.get("sku") or i.get("codigo")) == sku), None)
    return ((item or {}).get("gtin") or None), None


def reler_ean(saida, sku, buscar=_buscar_no_olist):
    p = Path(saida) / "anuncios-entrada.json"
    entrada = json.loads(p.read_text(encoding="utf-8"))
    alvo = next((v for a in entrada.get("anuncios", []) for v in a.get("variacoes", []) if v.get("sku") == sku), None)
    if alvo is None:
        return {"ok": False, "ean": None, "motivo": f"{sku} nao e deste lote"}
    ean, erro = buscar(sku)
    if erro:
        return {"ok": False, "ean": None, "motivo": erro}
    if not ean:
        return {"ok": False, "ean": None, "motivo": "o Olist ainda nao tem codigo de barras para este SKU"}
    alvo["ean"] = str(ean)
    tmp = p.with_name(p.name + ".novo")
    tmp.write_text(json.dumps(entrada, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    return {"ok": True, "ean": str(ean), "motivo": None}
```

- [ ] **Step 4: Rodar e ver passar** — 4 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/aprovacao/olist_ean.py tools/aprovacao/tests/test_olist_ean.py
git commit -m "feat(aprovacao): reler codigo de barras no Olist pela tela"
```

---

### Task 6: Cartão completo e ações novas no servidor da tela

**Files:**
- Create: `tools/aprovacao/quadro.py`, `tools/aprovacao/tests/test_quadro.py`
- Modify: `tools/aprovacao/aprovacao.py`, `tools/aprovacao/tests/test_aprovacao.py`

**Interfaces:**
- Consumes: `publicar.publicar_anuncio`, `publicar.publicar_cor`, `publicar.situacao`, `olist_ean.reler_ean`.
- Produces:
  - `quadro.montar(brief: dict, ficha: dict) -> list[dict]`: um item por dado `pendente`/`divergente` → `{"chave": "dimensoes_produto.altura_cm", "rotulo": "Altura (cm)", "fontes": [{"origem": "almir|planilha|concorrente", "valor": str, "link": str|None}], "campo_ficha": "HEIGHT"|None, "unidade": "cm"|None}`
  - `quadro.SUGESTAO_DE_CAMPO = {"material": "MATERIAL", "altura_cm": "HEIGHT", "largura_cm": "WIDTH", "profundidade_cm": "LENGTH", "diametro_cm": "DIAMETER", "capacidade": "VOLUME_CAPACITY"}` (sugestão só vale se o ID existe na ficha do anúncio)
  - `aprovacao.ler_preco(texto) -> float` (aceita "129,90", "129.90", "R$ 129,90"; levanta `ValueError("Preco invalido...")` para vazio, ≤ 0 ou texto)
  - `aprovacao.aprovar_e_publicar(saida, pai, edicao, vistos, publicar=publicar.publicar_anuncio, agora=None) -> dict` — `edicao` ganha `preco` (texto) e `decisoes` (`[{"chave", "valor", "campo_ficha"}]`)
  - `aprovacao.tirar(saida, pai, agora=None) -> dict` → `status_copy: tirado`
  - Endpoints: `POST /api/aprovar` (passa a publicar), `POST /api/tentar` (`{pai, sku}`), `POST /api/tirar` (`{pai}`), `POST /api/reler-ean` (`{pai, sku}`)
  - `situacao_lote(saida)`: **0** = todo anúncio `tirado` ou publicado inteiro; **3** = algum `devolvido` (e nenhum pendente); **2** = algum pendente/aprovado em parte/defeito/lote vazio.
  - Cartão (`_cartao`) ganha: `categoria` (`breadcrumb` juntado com " > "), `tipo_anuncio` ("Premium" para `gold_special`), `parecer` (`{"status", "score", "resumo"}` de `revisao/parecer-{pai}.yaml` se existir), `cores` (`[{"sku","cor","ean","estoque","capas":[urls],"titulo_ml"}]`, preta primeiro), `preco` (gravado ou vazio), `quadro`, `publicacao` (o que já foi publicado), `situacao`.

- [ ] **Step 1: Teste do quadro (falha)**

```python
# tools/aprovacao/tests/test_quadro.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import quadro  # noqa: E402

BRIEF = {"dados_produto": {
    "material": {"valor": None, "fonte": None, "status": "pendente"},
    "dimensoes_produto": {
        "altura_cm": {"valor": 25, "fonte": "almir", "status": "divergente",
                      "valores_divergentes": [{"valor": 27, "fonte": "concorrente-MLB1", "permalink": "https://ml/1"}]},
        "largura_cm": {"valor": 18, "fonte": "almir", "status": "ok"},
        "nota": "texto solto"},
    "caracteristicas": {"valor": ["a"], "status": "ok"}}}


def test_so_pendente_e_divergente():
    q = quadro.montar(BRIEF, {"HEIGHT": "25 cm", "BRAND": "Viel"})
    assert [i["chave"] for i in q] == ["material", "dimensoes_produto.altura_cm"]


def test_divergente_traz_as_duas_fontes_e_campo():
    alt = quadro.montar(BRIEF, {"HEIGHT": "25 cm"})[1]
    assert [f["valor"] for f in alt["fontes"]] == ["25", "27"]
    assert alt["fontes"][1]["link"] == "https://ml/1"
    assert alt["campo_ficha"] == "HEIGHT" and alt["unidade"] == "cm"


def test_campo_inexistente_na_ficha_fica_sem_campo():
    mat = quadro.montar(BRIEF, {"HEIGHT": "25 cm"})[0]
    assert mat["campo_ficha"] is None and mat["fontes"] == []


def test_brief_vazio():
    assert quadro.montar({}, {}) == []
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar `quadro.py`**

```python
# tools/aprovacao/quadro.py
"""Quadro 'Faltou ou divergiu': cada dado do brief (step-04) com status pendente ou divergente,
com o que cada fonte disse, para o Almir decidir na tela."""

SUGESTAO_DE_CAMPO = {"material": "MATERIAL", "altura_cm": "HEIGHT", "largura_cm": "WIDTH",
                     "profundidade_cm": "LENGTH", "diametro_cm": "DIAMETER", "capacidade": "VOLUME_CAPACITY"}
ROTULOS = {"material": "Material", "altura_cm": "Altura (cm)", "largura_cm": "Largura (cm)",
           "profundidade_cm": "Profundidade (cm)", "diametro_cm": "Diâmetro (cm)",
           "capacidade": "Capacidade", "caracteristicas": "Características"}


def _folhas(d, prefixo=""):
    for k, v in (d or {}).items():
        if isinstance(v, dict) and "status" in v:
            yield (prefixo + k, k, v)
        elif isinstance(v, dict):
            yield from _folhas(v, prefixo + k + ".")


def _txt(v):
    return ", ".join(map(str, v)) if isinstance(v, list) else str(v)


def montar(brief, ficha):
    itens = []
    for chave, nome, v in _folhas((brief or {}).get("dados_produto")):
        if v.get("status") not in ("pendente", "divergente"):
            continue
        fontes = []
        if v.get("valor") not in (None, "", []):
            fontes.append({"origem": v.get("fonte") or "planilha", "valor": _txt(v["valor"]), "link": v.get("permalink")})
        for d in v.get("valores_divergentes") or []:
            fontes.append({"origem": d.get("fonte") or "concorrente", "valor": _txt(d.get("valor")), "link": d.get("permalink")})
        campo = SUGESTAO_DE_CAMPO.get(nome)
        itens.append({"chave": chave, "rotulo": ROTULOS.get(nome, nome), "status": v["status"], "fontes": fontes,
                      "campo_ficha": campo if campo in (ficha or {}) else None,
                      "unidade": "cm" if nome.endswith("_cm") else None})
    return itens
```

- [ ] **Step 4: Rodar e ver passar** — 4 passed.

- [ ] **Step 5: Testes novos em `test_aprovacao.py` (falham)** — acrescentar ao fim do arquivo (usa a fixture `saida` que já existe; `PAI = "VIE-1-PAI"`):

```python
def test_ler_preco():
    assert ap.ler_preco("129,90") == 129.9
    assert ap.ler_preco("R$ 1.299,90") == 1299.9
    assert ap.ler_preco("92.71") == 92.71
    for ruim in ("", "0", "-5", "abc"):
        with pytest.raises(ValueError, match="Preco"):
            ap.ler_preco(ruim)


def _edicao(**extra):
    e = {"titulo": TIT_OK, "marca": "Viel", "modelo": "Cesto Lixo Redondo",
         "descricao": _doc()["description"], "preco": "92,71", "decisoes": []}
    e.update(extra)
    return e


def test_aprovar_e_publicar_grava_preco_e_decisao(saida):
    chamadas = []
    def pub(s, pai):
        chamadas.append(pai)
        return [{"sku": "VIE-1-PT", "ok": True, "mlb": "MLB1"}]
    dec = [{"chave": "material", "valor": "Aço inox", "campo_ficha": "MATERIAL"}]
    vistos = [i["codigo"] for i in ap.conferir(saida, PAI, _edicao())]
    r = ap.aprovar_e_publicar(saida, PAI, _edicao(decisoes=dec), vistos=vistos, publicar=pub)
    assert r["ok"] and chamadas == [PAI]
    doc = yaml.safe_load((saida / "copywriting" / f"anuncio-{PAI}.yaml").read_text(encoding="utf-8"))
    assert doc["preco"] == 92.71 and doc["status_copy"] == "aprovado"
    assert doc["attributes"]["MATERIAL"] == "Aço inox"
    assert doc["dados_decididos"] == dec


def test_sem_preco_nao_aprova(saida):
    r = ap.aprovar_e_publicar(saida, PAI, _edicao(preco=""), vistos=[], publicar=lambda s, p: 1 / 0)
    assert not r["ok"] and "Preco" in r["motivo"]


def test_ean_vazio_trava(saida):
    e = json.loads((saida / "anuncios-entrada.json").read_text(encoding="utf-8"))
    e["anuncios"][0]["variacoes"][0]["ean"] = None
    e["anuncios"][0]["variacoes"][1]["ean"] = "7898755000001"
    (saida / "anuncios-entrada.json").write_text(json.dumps(e), encoding="utf-8")
    itens = ap.conferir(saida, PAI, _edicao())
    assert any(i["codigo"] == "SEM_EAN" and i["nivel"] == "bloqueio" and "Branco" in i["texto"] for i in itens)


def test_tirar_do_lote(saida):
    assert ap.tirar(saida, PAI)["ok"]
    assert ap.listar_pendentes(saida) == []
    assert ap.situacao_lote(saida) == 0


def test_aprovado_em_parte_continua_na_tela(saida):
    d = _doc(status_copy="aprovado", titulo_final=TIT_OK, preco=92.71, _total_cores=2,
             publicacao={"VIE-1-PT": {"sku": "VIE-1-PT", "ok": True, "mlb": "MLB1"},
                         "VIE-1-BR": {"sku": "VIE-1-BR", "ok": False, "mlb": None, "erro": "x"}})
    _gravar(saida, d)
    cart = ap.listar_pendentes(saida)
    assert len(cart) == 1 and cart[0]["situacao"] == "em_parte"
    assert ap.situacao_lote(saida) == 2


def test_cartao_tem_tudo(saida):
    c = ap.listar_pendentes(saida)[0]
    assert [x["cor"] for x in c["cores"]] == ["Preto", "Branco"]
    assert c["cores"][0]["titulo_ml"].endswith(" Preto")
    assert "quadro" in c and "categoria" in c and c["tipo_anuncio"] == "Premium"


def test_sku_com_sublinhado(saida):
    assert ap.caminho_anuncio(saida, "BRI-coza34-40652_3009").name == "anuncio-BRI-coza34-40652_3009.yaml"
```

E ajustar a fixture `saida` existente: cada variação ganha `"ean": "78987550000NN"`, e criar `categorizacao/categorias.yaml` com `{"categorias": [{"pai_sku": PAI, "category_id": "MLB33375", "breadcrumb": ["Casa", "Lixeiras"]}]}`.

- [ ] **Step 6: Rodar e ver falhar** — `python -m pytest -q tools/aprovacao/tests/test_aprovacao.py` → os novos falham (`ler_preco`, `aprovar_e_publicar`, `tirar` não existem).

- [ ] **Step 7: Implementar em `aprovacao.py`**

Acrescentar imports e constantes no topo:
```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publicar as pub  # noqa: E402
import quadro as quadro_mod  # noqa: E402
from olist_ean import reler_ean  # noqa: E402

FINAIS = ("aprovado", "devolvido", "tirado")
TIPOS = {"gold_special": "Premium", "gold_pro": "Premium", "gold": "Clássico"}
```

Funções novas:
```python
def ler_preco(texto):
    t = re.sub(r"[^\d,.\-]", "", str(texto or ""))
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        v = round(float(t), 2)
    except ValueError:
        raise ValueError("Preco invalido: digite so o valor, ex.: 129,90")
    if v <= 0:
        raise ValueError("Preco invalido: tem que ser maior que zero")
    return v


def _categoria(saida, pai):
    p = Path(saida) / "categorizacao" / "categorias.yaml"
    if not p.is_file():
        return {}
    return next((c for c in (_ler_yaml(p) or {}).get("categorias") or [] if c.get("pai_sku") == pai), {})


def _parecer(saida, pai):
    p = Path(saida) / "revisao" / f"parecer-{pai}.yaml"
    if not p.is_file():
        return None
    d = _ler_yaml(p) or {}
    return {"status": d.get("status"), "score": d.get("score_total"),
            "resumo": d.get("resumo") or d.get("correcoes_pendentes") or ""}


def _cores(saida, pai, a, titulo):
    capas = {k.get("sku_variacao") or k.get("cor"): k for k in
             ((_ler_yaml(Path(saida) / "capas" / f"capas-{pai}.yaml") or {}).get("picture_ids_por_variacao") or [])
             } if (Path(saida) / "capas" / f"capas-{pai}.yaml").is_file() else {}
    vs = sorted(a.get("variacoes") or [], key=lambda v: str(v.get("cor") or "").lower() != "preto")
    return [{"sku": v["sku"], "cor": v.get("cor"), "ean": v.get("ean"), "estoque": v.get("estoque"),
             "capas": list((capas.get(v["sku"]) or {}).get("picture_ids") or []),
             "titulo_ml": f"{titulo} {v['cor']}".strip() if v.get("cor") else titulo} for v in vs]
```

Em `_cartao`, acrescentar ao dicionário devolvido:
```python
        "categoria": " > ".join(_categoria(saida, pai).get("breadcrumb") or []) or _categoria(saida, pai).get("category_name"),
        "tipo_anuncio": TIPOS.get(_categoria(saida, pai).get("listing_type_id", "gold_special"), "Premium"),
        "parecer": _parecer(saida, pai),
        "cores": _cores(saida, pai, a, _titulo_inicial(doc)),
        "preco": doc.get("preco"),
        "quadro": quadro_mod.montar(_ler_yaml(Path(saida) / "inteligencia" / f"brief-{pai}.yaml")
                                    if (Path(saida) / "inteligencia" / f"brief-{pai}.yaml").is_file() else {},
                                    attrs),
        "publicacao": list((doc.get("publicacao") or {}).values()),
        "situacao": pub.situacao(doc),
```

Em `listar_pendentes`, trocar `if doc.get("status_copy") in FINAIS: continue` por:
```python
            st = doc.get("status_copy")
            if st in ("devolvido", "tirado") or (st == "aprovado" and pub.situacao(doc) == "publicado"):
                continue
```

Em `conferir`, depois do bloco do título, acrescentar a trava do código de barras:
```python
    try:
        a = _entrada_por_pai(saida).get(pai, {})
    except Exception:  # noqa: BLE001
        a = {}
    sem = [v.get("cor") or v["sku"] for v in a.get("variacoes") or [] if not v.get("ean")]
    if sem:
        itens.append({"codigo": "SEM_EAN", "nivel": "bloqueio",
                      "texto": f"Sem código de barras: {', '.join(sem)}. Gere pelo botão da GS1 e clique em Reler do Olist."})
```

`situacao_lote` novo:
```python
def situacao_lote(saida):
    """0 = tudo publicado ou tirado; 3 = algum devolvido; 2 = pendente, em parte, defeito ou vazio."""
    devolvido = False
    arquivos = sorted((Path(saida) / "copywriting").glob("anuncio-*.yaml"))
    if not arquivos:
        return 2
    for f in arquivos:
        try:
            doc = _ler_yaml(f) or {}
        except Exception:  # noqa: BLE001
            return 2
        st = doc.get("status_copy")
        if st == "devolvido":
            devolvido = True
        elif st == "tirado" or (st == "aprovado" and pub.situacao(doc) == "publicado"):
            continue
        else:
            return 2
    return 3 if devolvido else 0
```

`aprovar_e_publicar` e `tirar`:
```python
def aprovar_e_publicar(saida, pai, edicao, vistos=None, publicar=pub.publicar_anuncio, agora=None):
    agora = agora or datetime.now()
    try:
        preco = ler_preco(edicao.get("preco"))
    except ValueError as e:
        return {"ok": False, "motivo": str(e), "conferencia": []}
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    if doc.get("status_copy") != "aprovado":
        r = aprovar(saida, pai, edicao, vistos=vistos, agora=agora)
        if not r["ok"]:
            return r
        doc = _ler_yaml(caminho)
    doc["preco"] = preco
    decisoes = [d for d in edicao.get("decisoes") or [] if str(d.get("valor") or "").strip()]
    for d in decisoes:
        if d.get("campo_ficha"):
            doc.setdefault("attributes", {})[d["campo_ficha"]] = str(d["valor"]).strip()
    doc["dados_decididos"] = decisoes
    _gravar_seguro(caminho, doc, agora)
    try:
        resultado = publicar(saida, pai)
    except ValueError as e:
        return {"ok": False, "motivo": str(e), "conferencia": []}
    return {"ok": True, "publicacao": resultado}


def tirar(saida, pai, agora=None):
    agora = agora or datetime.now()
    caminho = caminho_anuncio(saida, pai)
    doc = _ler_yaml(caminho)
    doc["status_copy"] = "tirado"
    doc["tirado_em"] = f"{agora:%Y-%m-%d %H:%M}"
    _gravar_seguro(caminho, doc, agora)
    return {"ok": True}
```

> `aprovar` grava `status_copy: aprovado` antes do preço existir; por isso `aprovar_e_publicar` lê o preço **antes** de chamar `aprovar`. `aprovar` continua recusando anúncio já em `FINAIS`; como `aprovar_e_publicar` só chama `aprovar` quando o status não é `aprovado`, "Tentar de novo" num aprovado em parte funciona.

No servidor (`do_POST`), trocar o ramo `/api/aprovar` e acrescentar os novos:
```python
                if self.path == "/api/aprovar":
                    r = aprovar_e_publicar(saida, pai, corpo.get("edicao") or {}, vistos=corpo.get("vistos") or [])
                elif self.path == "/api/tentar":
                    r = {"ok": True, "item": pub.publicar_cor(saida, pai, corpo.get("sku"))}
                elif self.path == "/api/tirar":
                    r = tirar(saida, pai)
                elif self.path == "/api/reler-ean":
                    caminho_anuncio(saida, pai)  # valida o pai
                    r = reler_ean(saida, corpo.get("sku"))
                elif self.path == "/api/devolver":
```
(o resto do `do_POST` fica igual; o encerramento com `--esperar` continua usando `_pendentes_validos`, que agora considera "aprovado em parte" como pendente.)

- [ ] **Step 8: Rodar e ver passar** — `python -m pytest -q tools/aprovacao/tests` → todos passam. Se algum teste antigo esperar o comportamento de `aprovar` sumir da lista após aprovar, ele agora só some depois de publicado: ajustar o teste antigo para gravar `publicacao` completa ou para checar `situacao == "nao_publicado"`, e dizer qual no commit.

- [ ] **Step 9: Commit**

```bash
git add tools/aprovacao/quadro.py tools/aprovacao/aprovacao.py tools/aprovacao/tests/
git commit -m "feat(aprovacao): cartao completo, preco, codigo de barras, quadro e publicar pela tela"
```

---

### Task 7: A tela (página)

**Files:**
- Modify: `tools/aprovacao/pagina.html`
- Test: `tools/aprovacao/tests/test_aprovacao.py` (teste de fumaça da página)

**Interfaces:**
- Consumes: cartão da Task 6 (`categoria`, `tipo_anuncio`, `parecer`, `cores`, `preco`, `quadro`, `publicacao`, `situacao`) e os endpoints `/api/aprovar` (`edicao.preco`, `edicao.decisoes`), `/api/tentar`, `/api/tirar`, `/api/reler-ean`.

- [ ] **Step 1: Teste de fumaça (falha)**

```python
def test_pagina_tem_as_secoes_novas():
    html = (Path(ap.__file__).parent / "pagina.html").read_text(encoding="utf-8")
    for marca in ("Faltou ou divergiu", "Preço", "Código de barras", "Reler do Olist",
                  "Aprovar e publicar", "Tirar do lote", "Tentar de novo", "/api/tentar", "/api/tirar", "/api/reler-ean"):
        assert marca in html
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Mudanças na página** (manter `el`, `api`, `contador`, a lógica de título/Marca/Modelo/descrição e a conferência ao vivo como estão):

1. `h1` → "Anúncios esperando você".
2. **Topo do cartão:** trocar o bloco de preços por `categoria`, `tipo_anuncio` e o parecer:
```js
const parecer = c.parecer ? el("div", {class: "just"}, `Revisão: ${c.parecer.status}${c.parecer.score != null ? " (" + c.parecer.score + "/100)" : ""}${c.parecer.resumo ? " — " + c.parecer.resumo : ""}`) : null;
```
3. **Tabela por cor** (no lugar da seção "Capas"):
```js
function tabelaCores(c, tituloAtual, aoReler) {
  const linhas = c.cores.map(v => {
    const ean = el("td", {}, v.ean || "");
    if (!v.ean) {
      const bt = el("button", {}, "Reler do Olist");
      bt.addEventListener("click", async () => {
        bt.disabled = true;
        const r = await api("/api/reler-ean", {pai: c.pai_sku, sku: v.sku});
        if (r.ok) { v.ean = r.ean; ean.replaceChildren(r.ean); aoReler(); } else { ean.replaceChildren("— ", el("span", {class: "falha"}, r.motivo)); }
      });
      ean.replaceChildren(el("span", {class: "falha"}, "sem código "), bt);
    }
    const tit = el("td", {});
    const atualiza = () => { const t = tituloAtual() + (v.cor ? " " + v.cor : ""); tit.textContent = `${t} (${t.length}/${TETO_TITULO})`; tit.classList.toggle("falha", t.length > TETO_TITULO); };
    atualiza(); v._atualiza = atualiza;
    return el("tr", {}, el("td", {}, v.cor || "—"), el("td", {}, v.sku), ean,
      el("td", {}, el("div", {class: "capas"}, v.capas.map((u, i) => el("img", {src: u, alt: `foto ${i + 1}`, title: i === 0 ? "capa principal" : `foto ${i + 1}`})))),
      el("td", {}, v.estoque ?? "do Olist"), tit);
  });
  return el("table", {}, el("tr", {}, ["Cor", "SKU", "Código de barras", "Fotos (1ª = capa)", "Estoque", "Título que o ML vai montar"].map(h => el("td", {}, el("b", {}, h)))), linhas);
}
```
   e no `mudou()` chamar `c.cores.forEach(v => v._atualiza && v._atualiza())` para o título por cor acompanhar.
4. **Preço:** `const preco = el("input", {type: "text", value: c.preco != null ? String(c.preco).replace(".", ",") : "", placeholder: "ex.: 129,90", inputmode: "decimal"});` com legenda "vale para todas as cores".
5. **Quadro "Faltou ou divergiu"** (só aparece se `c.quadro.length`):
```js
const decisoes = c.quadro.map(q => {
  const nome = "q_" + c.pai_sku + "_" + q.chave;
  const proprio = el("input", {type: "text", placeholder: "escrever outro valor"});
  const opcoes = q.fontes.map(f => el("label", {class: "opcao"}, el("input", {type: "radio", name: nome, value: f.valor}),
    el("span", {}, `${f.valor} `, el("span", {class: "just"}, f.origem), f.link ? el("a", {href: f.link, target: "_blank"}, " ver") : null)));
  const rProprio = el("input", {type: "radio", name: nome, value: "__proprio__"});
  const rVazio = el("input", {type: "radio", name: nome, value: "", checked: ""});
  proprio.addEventListener("focus", () => { rProprio.checked = true; });
  const bloco = el("div", {class: "secao"}, el("b", {}, `${q.rotulo} — ${q.status === "pendente" ? "ninguém achou" : "as fontes discordam"}`),
    opcoes, el("label", {class: "opcao"}, rProprio, el("span", {style: "flex:1"}, proprio)),
    el("label", {class: "opcao"}, rVazio, el("span", {}, "deixar vazio")),
    el("div", {class: "just"}, q.campo_ficha ? `vai para a ficha técnica (${q.campo_ficha})` : "não tem campo na ficha deste anúncio; se quiser no texto, edite a descrição"));
  return {bloco, ler: () => {
    const sel = bloco.querySelector(`input[name="${CSS.escape(nome)}"]:checked`);
    let valor = !sel ? "" : sel.value === "__proprio__" ? proprio.value : sel.value;
    if (valor && q.unidade && !/[a-z]/i.test(valor)) valor = `${valor} ${q.unidade}`;
    return {chave: q.chave, valor, campo_ficha: q.campo_ficha};
  }};
});
```
6. **Envio:** acrescentar "Frete grátis: o ML liga sozinho nessa faixa de preço" e "Flex: ligado depois de publicar".
7. `edicao()` passa a incluir `preco: preco.value, decisoes: decisoes.map(d => d.ler())`.
8. **Botões:** `btAprovar` com texto base "Aprovar e publicar" (e "Aprovar e publicar mesmo assim" com erro); `btTirar = el("button", {}, "Tirar do lote")` chamando `/api/tirar`; preço vazio desliga o botão com o texto "Aprovar e publicar (falta o preço)".
9. **Depois de publicar** (`r.ok` do `/api/aprovar`) e para cartões que já chegam com `situacao === "em_parte"`, trocar o corpo do cartão por um resumo por cor:
```js
function resumoPublicacao(c, itens) {
  return el("div", {class: "secao"}, el("b", {}, "Publicação"), el("ul", {class: "conf"}, itens.map(i => {
    if (i.ok) return el("li", {class: "tudook"}, `✅ ${i.cor || i.sku}: `, el("a", {href: i.link, target: "_blank"}, i.mlb),
      ` · descrição ${i.descricao ? "✅" : "❌"} · Flex ${i.flex ? "✅" : "❌"} · pausado até o ML baixar a foto (5 a 15 min), é normal`);
    const bt = el("button", {}, "Tentar de novo");
    bt.addEventListener("click", async () => {
      bt.disabled = true;
      const r = await api("/api/tentar", {pai: c.pai_sku, sku: i.sku});
      bt.closest("li").replaceWith(resumoPublicacao(c, [r.item]).querySelector("li"));
    });
    return el("li", {class: "erro"}, `❌ ${i.cor || i.sku}: ${i.erro} `, bt);
  })));
}
```
10. Lista vazia → "Nada esperando você. Pode fechar esta página."

- [ ] **Step 4: Rodar o teste de fumaça** → passa.

- [ ] **Step 5: Conferência visual com lote de mentira** — copiar a pasta de saída do 1º teste para `squads/ml-anuncios/output/lotes/_ensaio-tela/`, apagar `status_copy`/`publicacao` dos dois `anuncio-*.yaml` da cópia, e rodar `python tools/aprovacao/aprovacao.py --saida squads/ml-anuncios/output/lotes/_ensaio-tela --sem-navegador`. Abrir o endereço no Chrome dedicado (chrome-devtools) e conferir: tabela por cor com a preta primeiro, título por cor com contador, preço vazio trava o botão, quadro só aparece se houver pendência (forçar uma pondo `status: pendente` em `material` do brief da cópia), tema escuro legível, largura de celular sem rolagem lateral. **Não clicar em publicar.** Apagar `_ensaio-tela` ao fim.

- [ ] **Step 6: Commit**

```bash
git add tools/aprovacao/pagina.html tools/aprovacao/tests/test_aprovacao.py
git commit -m "feat(aprovacao): tela mostra tudo o que vai pro anuncio e publica"
```

---

### Task 8: Travas por anúncio e o maestro

**Files:**
- Create: `tools/esteira_auto/travas.py`, `tools/esteira_auto/maestro.py`, `tools/esteira_auto/instrucoes/{capas,curadoria,categoria,pesquisa,texto,revisao}.md`, `tools/esteira_auto/tests/test_travas.py`, `tools/esteira_auto/tests/test_maestro.py`

**Interfaces:**
- Consumes: `lote.*` (Task 2), `precheck.ler_planilha` (Task 3), `chamar_claude.chamar` (Task 1), validadores em `squads/ml-anuncios/pipeline/validators/`.
- Produces:
  - `travas.conferir(etapa: str, lote: Path, pais: list[str], rodar=subprocess.run) -> dict[str, str]` — `{pai: motivo}` só dos reprovados; `{}` = tudo ok. Etapas: `capas` (roda `capas.py` uma vez para o lote), `curadoria` (`curadoria/dossies.json` tem o pai), `categoria` (`categorizacao/categorias.yaml` tem o pai com `category_id`), `pesquisa` (`validar_brief.py ... --sem-fotos`), `texto` (`validar_claims.py` + `validar_ficha_seo.py`), `revisao` (`revisao/parecer-{pai}.yaml` existe).
  - `maestro.rodar_lote(lote, chamar=chamar_claude.chamar, conferir=travas.conferir, ler_planilha=precheck.ler_planilha, abrir_tela=_abrir_tela, agora=datetime.now, avisar=print) -> int` — 0 concluído, 1 parou (motivo no caderno), 2 tela fechada com pendência.
  - `maestro.main()` — pega `lote_aberto` ou cria lote para a planilha mais antiga de `A CRIAR` (`.xls`/`.xlsx`, ignora `~$*`); ao concluir, move a planilha para `A CRIAR\FEITOS` (nome repetido → acrescenta `-2`, `-3`); repete enquanto houver planilha.
  - `maestro.instrucao(etapa, lote, pais, motivo=None) -> str` — lê `instrucoes/{etapa}.md` e troca `{LOTE}`, `{PAIS}`, `{MOTIVO}`.

- [ ] **Step 1: Instruções fixas** — criar os 6 arquivos. Modelo (`curadoria.md`; os outros trocam o step e a saída conforme a tabela abaixo):

```markdown
Voce esta rodando SEM CONVERSA, chamado pelo maestro da esteira de anuncios. Ninguem vai responder pergunta: nao pergunte, decida pelo que esta escrito.

Faca SO a etapa abaixo e pare.

Etapa: squads/ml-anuncios/pipeline/steps/step-02-curadoria-produtos.md (leia o arquivo e siga, junto com o agente que ele indica em squads/ml-anuncios/agents/).
Pasta deste lote: {LOTE}
Onde o step disser `squads/ml-anuncios/output/`, use a pasta do lote no lugar. Nao leia nem escreva em outra pasta de saida.
Produtos deste lote: {PAIS}

Regras:
- Nao publique nada. Nao chame o webhook, nao rode disparar_publicacao.py nem completar_anuncio.py.
- Checkpoint humano (step-04b, step-06, step-09) NAO para a esteira: deixe pendencias e divergencias registradas no brief/dossie, a tela mostra ao Almir.
- Se o maestro mandou motivo de reprovacao abaixo, corrija exatamente isso.

Motivo da reprovacao anterior (vazio = primeira tentativa): {MOTIVO}

Ao terminar, responda em uma linha: "pronto" ou "nao consegui: <motivo curto>".
```

| arquivo | step | saída esperada no lote |
|---|---|---|
| `capas.md` | step-07-capas.md (manter a linha `Etapa: squads/ml-anuncios/pipeline/steps/step-07-capas.md` — o teste do maestro lê essa linha em toda instrução) — **só** a busca: rodar `mcp__cloudinary__search-assets` com `tags=capa-anuncio`, `max_results` 500, `with_field` tags, e gravar a resposta inteira em `{LOTE}/capas/_busca.json`. Não rodar `capas.py` (o maestro roda). | `capas/_busca.json` |
| `curadoria.md` | step-02 | `curadoria/dossies.json` |
| `categoria.md` | step-03 | `categorizacao/categorias.yaml` |
| `pesquisa.md` | step-04 | `inteligencia/brief-{pai}.yaml`, `inteligencia/briefs.yaml` |
| `texto.md` | step-05 — acrescentar: "Anúncio com `status_copy: devolvido` no `copywriting/anuncio-{pai}.yaml`: leia `nota_almir`, reescreva atendendo a nota e grave `status_copy: pendente` (mantenha `nota_almir` e `devolvido_em`). Anúncio `aprovado` ou `tirado`: não mexa." | `copywriting/anuncio-{pai}.yaml` |
| `revisao.md` | step-08 | `revisao/parecer-{pai}.yaml`, `revisao/pareceres.yaml` |

- [ ] **Step 2: Teste das travas (falha)**

```python
# tools/esteira_auto/tests/test_travas.py
import json
import os
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import travas  # noqa: E402


def test_categoria_falta_um(tmp_path):
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump(
        {"categorias": [{"pai_sku": "A", "category_id": "MLB1"}]}), encoding="utf-8")
    r = travas.conferir("categoria", tmp_path, ["A", "B"])
    assert list(r) == ["B"] and "categoria" in r["B"]


def test_pesquisa_reprovada_traz_saida_do_validador(tmp_path):
    def falso(cmd, **kw):
        ok = "brief-A.yaml" in " ".join(cmd)
        return subprocess.CompletedProcess(cmd, 0 if ok else 1, "" if ok else "BLOQUEIO: limitacoes vazias", "")
    r = travas.conferir("pesquisa", tmp_path, ["A", "B"], rodar=falso)
    assert r == {"B": "BLOQUEIO: limitacoes vazias"}


def test_texto_roda_duas_travas(tmp_path):
    vistos = []
    def falso(cmd, **kw):
        vistos.append(os.path.basename(cmd[1]))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=falso) == {}
    assert vistos == ["validar_claims.py", "validar_ficha_seo.py"]


def test_capas_lista_quem_falta(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "CAPAS INCOMPLETAS - 1:\n  - B: falta capa da cor 'Preto'", "")
    (tmp_path / "capas").mkdir(); (tmp_path / "capas" / "_busca.json").write_text("{}")
    r = travas.conferir("capas", tmp_path, ["A", "B"], rodar=falso)
    assert list(r) == ["B"] and "Preto" in r["B"]
```

- [ ] **Step 3: Rodar e ver falhar; implementar `travas.py`**

```python
# tools/esteira_auto/travas.py
"""Conferencia depois de cada etapa, por anuncio. Devolve so os reprovados: {pai: motivo}."""
import json
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
VAL = RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"


def _py(script, *args, rodar):
    r = rodar([sys.executable, str(VAL / script), *map(str, args)], capture_output=True, text=True,
              encoding="utf-8", errors="replace", cwd=str(RAIZ))
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()[-800:]


def conferir(etapa, lote, pais, rodar=subprocess.run):
    lote = Path(lote)
    ruins = {}
    if etapa == "capas":
        busca = lote / "capas" / "_busca.json"
        if not busca.is_file():
            return {p: "a busca das capas no Cloudinary nao foi gravada" for p in pais}
        cod, saida = _py("capas.py", busca, lote / "anuncios-entrada.json", lote / "capas", rodar=rodar)
        if cod != 0:
            for p in pais:
                linhas = [l.strip(" -") for l in saida.splitlines() if l.strip(" -").startswith(p + ":")]
                if linhas:
                    ruins[p] = " | ".join(linhas)
            if not ruins:
                ruins = {p: saida or "a conferencia das capas falhou" for p in pais}
        return ruins
    if etapa == "curadoria":
        f = lote / "curadoria" / "dossies.json"
        tem = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
        achados = {d.get("pai_sku") or d.get("sku") for d in tem.get("dossies") or []}
        return {p: "o dossie deste produto nao foi gravado" for p in pais if p not in achados}
    if etapa == "categoria":
        f = lote / "categorizacao" / "categorias.yaml"
        cats = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("categorias") if f.is_file() else []
        ok = {c.get("pai_sku") for c in cats or [] if c.get("category_id")}
        return {p: "nao foi escolhida a categoria do ML" for p in pais if p not in ok}
    for p in pais:
        brief = lote / "inteligencia" / f"brief-{p}.yaml"
        anuncio = lote / "copywriting" / f"anuncio-{p}.yaml"
        if etapa == "pesquisa":
            cod, s = _py("validar_brief.py", brief, "--sem-fotos", rodar=rodar)
            if cod != 0:
                ruins[p] = s or "a pesquisa foi reprovada"
        elif etapa == "texto":
            for script, args in (("validar_claims.py", (brief, "--copy", anuncio, "--sem-fotos")),
                                 ("validar_ficha_seo.py", (anuncio,))):
                cod, s = _py(script, *args, rodar=rodar)
                if cod != 0:
                    ruins[p] = s or f"{script} reprovou"
                    break
        elif etapa == "revisao":
            if not (lote / "revisao" / f"parecer-{p}.yaml").is_file():
                ruins[p] = "a revisao deste produto nao foi gravada"
    return ruins
```

> A trava de `texto` não deve rodar para anúncio já `aprovado`/`tirado` (no reprocesso de devolvidos, só os devolvidos voltam): o maestro passa só os pais certos em `pais`.

Run: `python -m pytest -q tools/esteira_auto/tests/test_travas.py` → 4 passed.

- [ ] **Step 4: Teste do maestro (falha)**

```python
# tools/esteira_auto/tests/test_maestro.py
import json
import os
import sys
from datetime import datetime

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import lote as L, maestro as M  # noqa: E402

T = lambda: datetime(2026, 10, 9, 14, 0, 0)


def _lote(tmp_path, pais=("A", "B")):
    lt = L.criar_lote(tmp_path / "p.xls", tmp_path / "lotes", T())
    def ler_planilha(planilha, lote):
        (lote / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": p} for p in pais]}), encoding="utf-8")
        return []
    return lt, ler_planilha


def test_ordem_e_tela(tmp_path):
    lt, lp = _lote(tmp_path)
    etapas = []
    chamar = lambda instr, raiz, **kw: (etapas.append(instr.split("Etapa: ")[1].split("\n")[0]) or (True, "pronto"))
    r = M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lp,
                     abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert r == 0
    assert [e.split("/")[-1] for e in etapas][1:] == ["step-02-curadoria-produtos.md", "step-03-categorizacao.md",
        "step-04-inteligencia-conversao.md", "step-05-copywriting.md", "step-08-revisao.md"]
    assert L.ler(lt)["concluido"]


def test_retoma_sem_refazer(tmp_path):
    lt, lp = _lote(tmp_path)
    for e in ("entrada", "capas", "curadoria"):
        L.marcar_feita(lt, e, T())
    chamadas = []
    chamar = lambda instr, raiz, **kw: (chamadas.append(1) or (True, "pronto"))
    M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lambda *a: 1 / 0,
                 abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert len(chamadas) == 4  # categoria, pesquisa, texto, revisao


def test_planilha_com_problema_para_cedo(tmp_path):
    lt, _ = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda *a, **k: 1 / 0, conferir=None,
                     ler_planilha=lambda p, l: ["BRI-1: sem peso ou medida da caixa"],
                     abrir_tela=None, agora=T, avisar=lambda *a: None)
    assert r == 1 and "sem peso" in (lt / "andamento.txt").read_text(encoding="utf-8")


def test_reprovado_duas_vezes_para_so_aquele(tmp_path):
    lt, lp = _lote(tmp_path)
    vistos = []
    def conferir(etapa, lote, pais):
        vistos.append((etapa, tuple(pais)))
        return {"B": "texto inventou balde"} if etapa == "texto" else {}
    M.rodar_lote(lt, chamar=lambda instr, raiz, **kw: (True, "pronto"), conferir=conferir, ler_planilha=lp,
                 abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert L.ler(lt)["parados"] == {"B": "texto inventou balde"}
    assert ("revisao", ("A",)) in vistos


def test_claude_falhou_nao_marca_etapa(tmp_path):
    lt, lp = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda instr, raiz, **kw: (False, "passou do tempo"), conferir=lambda e, l, p: {},
                     ler_planilha=lp, abrir_tela=lambda l: 0, agora=T, avisar=lambda *a: None)
    assert r == 1 and L.proxima(lt) == "capas"


def test_devolvido_refaz_texto_e_volta_pra_tela(tmp_path):
    lt, lp = _lote(tmp_path)
    (lt / "copywriting").mkdir()
    (lt / "copywriting" / "anuncio-A.yaml").write_text(yaml.safe_dump({"pai_sku": "A", "status_copy": "devolvido"}), encoding="utf-8")
    telas = iter([3, 0])
    instr = []
    def chamar(i, raiz, **kw):
        instr.append(i)
        return True, "pronto"
    r = M.rodar_lote(lt, chamar=chamar, conferir=lambda e, l, p: {}, ler_planilha=lp,
                     abrir_tela=lambda l: next(telas), agora=T, avisar=lambda *a: None)
    assert r == 0
    refeitas = [i for i in instr[-2:]]
    assert "step-05" in refeitas[0] and "Produtos deste lote: A" in refeitas[0] and "step-08" in refeitas[1]


def test_tela_fechada_com_pendencia(tmp_path):
    lt, lp = _lote(tmp_path)
    r = M.rodar_lote(lt, chamar=lambda i, raiz, **kw: (True, "pronto"), conferir=lambda e, l, p: {},
                     ler_planilha=lp, abrir_tela=lambda l: 2, agora=T, avisar=lambda *a: None)
    assert r == 2 and not L.ler(lt)["concluido"]


def test_mover_para_feitos_sem_sobrescrever(tmp_path):
    a_criar = tmp_path / "A CRIAR"; (a_criar / "FEITOS").mkdir(parents=True)
    (a_criar / "FEITOS" / "p.xls").write_text("velho")
    pl = a_criar / "p.xls"; pl.write_text("novo")
    destino = M.mover_para_feitos(pl)
    assert destino.name == "p-2.xls" and (a_criar / "FEITOS" / "p.xls").read_text() == "velho"


def test_proxima_planilha_ignora_temporario_do_excel(tmp_path):
    (tmp_path / "~$p.xlsx").write_text("x"); (tmp_path / "b.xls").write_text("x")
    assert M.proxima_planilha(tmp_path).name == "b.xls"
```

- [ ] **Step 5: Rodar e ver falhar; implementar `maestro.py`**

```python
# tools/esteira_auto/maestro.py
"""Maestro da esteira de anuncios: conduz um lote da planilha ate a tela, sem conversa.
Spec: docs/superpowers/specs/2026-10-09-botao-criar-anuncios-design.md"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from esteira_auto import chamar_claude, lote as L, precheck, travas  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
LOTES = RAIZ / "squads" / "ml-anuncios" / "output" / "lotes"
A_CRIAR = Path(r"G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR")
STEPS = {"capas": "step-07-capas.md", "curadoria": "step-02-curadoria-produtos.md",
         "categoria": "step-03-categorizacao.md", "pesquisa": "step-04-inteligencia-conversao.md",
         "texto": "step-05-copywriting.md", "revisao": "step-08-revisao.md"}
COM_CABECA = ["capas", "curadoria", "categoria", "pesquisa", "texto", "revisao"]


def instrucao(etapa, lote, pais, motivo=None):
    t = (Path(__file__).parent / "instrucoes" / f"{etapa}.md").read_text(encoding="utf-8")
    return (t.replace("{LOTE}", str(lote)).replace("{PAIS}", ", ".join(pais))
             .replace("{MOTIVO}", motivo or ""))


def _pais(lote):
    entrada = json.loads((Path(lote) / "anuncios-entrada.json").read_text(encoding="utf-8"))
    parados = L.ler(lote)["parados"]
    return [a["pai_sku"] for a in entrada.get("anuncios", []) if a["pai_sku"] not in parados]


def _devolvidos(lote):
    import yaml
    out = []
    for f in sorted((Path(lote) / "copywriting").glob("anuncio-*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("status_copy") == "devolvido":
            out.append(d.get("pai_sku"))
    return out


def _etapa(etapa, lote, pais, chamar, conferir, agora, avisar):
    """Roda uma etapa com cabeca + trava, com 1 nova tentativa por reprovacao. False = parar o lote."""
    avisar(f"{agora():%H:%M} {L.NOMES[etapa]}…")
    ok, resumo = chamar(instrucao(etapa, lote, pais), RAIZ)
    if not ok:
        L.anotar(lote, f"falhou em '{L.NOMES[etapa]}': {resumo}. Clique de novo para continuar daqui.", agora())
        return False
    ruins = conferir(etapa, lote, pais)
    if ruins:
        motivo = "; ".join(f"{p}: {m}" for p, m in ruins.items())
        L.anotar(lote, f"reprovado em '{L.NOMES[etapa]}', tentando de novo: {motivo}", agora())
        ok, resumo = chamar(instrucao(etapa, lote, list(ruins), motivo), RAIZ)
        ruins = conferir(etapa, lote, list(ruins)) if ok else ruins
        for p, m in ruins.items():
            L.parar_pai(lote, p, m, agora())
            avisar(f"  parou {p}: {m}")
    return True


def rodar_lote(lote, chamar=chamar_claude.chamar, conferir=travas.conferir,
               ler_planilha=precheck.ler_planilha, abrir_tela=None, agora=datetime.now, avisar=print):
    abrir_tela = abrir_tela or _abrir_tela
    while True:
        etapa = L.proxima(lote)
        if etapa is None:
            return 0
        if etapa == "entrada":
            avisar(f"{agora():%H:%M} {L.NOMES['entrada']}…")
            problemas = ler_planilha(Path(L.ler(lote)["planilha"]), lote)
            if problemas:
                for p in problemas:
                    L.anotar(lote, f"PAROU antes de comecar: {p}", agora())
                    avisar("  " + p)
                return 1
            L.marcar_feita(lote, "entrada", agora())
            continue
        if etapa == "tela":
            while True:
                avisar(f"{agora():%H:%M} abrindo a tela de aprovacao…")
                cod = abrir_tela(lote)
                if cod == 3:
                    dev = _devolvidos(lote)
                    for e in ("texto", "revisao"):
                        if not _etapa(e, lote, dev, chamar, conferir, agora, avisar):
                            return 1
                    continue
                if cod == 0:
                    L.marcar_feita(lote, "tela", agora())
                    L.concluir(lote, agora())
                    return 0
                L.anotar(lote, "tela fechada com anuncio pendente: clique de novo para reabrir", agora())
                return 2
        pais = _pais(lote)
        if not pais:
            L.anotar(lote, "nenhum produto sobrou neste lote", agora())
            L.concluir(lote, agora())
            return 1
        if not _etapa(etapa, lote, pais, chamar, conferir, agora, avisar):
            return 1
        L.marcar_feita(lote, etapa, agora())


def _abrir_tela(lote):
    r = subprocess.run([sys.executable, str(RAIZ / "tools" / "aprovacao" / "aprovacao.py"),
                        "--saida", str(lote), "--esperar"])
    return r.returncode


def mover_para_feitos(planilha):
    planilha = Path(planilha)
    feitos = planilha.parent / "FEITOS"
    feitos.mkdir(exist_ok=True)
    destino, n = feitos / planilha.name, 2
    while destino.exists():
        destino = feitos / f"{planilha.stem}-{n}{planilha.suffix}"
        n += 1
    shutil.move(str(planilha), str(destino))
    return destino


def proxima_planilha(pasta):
    pasta = Path(pasta)
    if not pasta.is_dir():
        return None
    cands = [p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in (".xls", ".xlsx")
             and not p.name.startswith("~$")]
    return min(cands, key=lambda p: p.stat().st_mtime) if cands else None


def main():
    while True:
        lote = L.lote_aberto(LOTES)
        if lote is None:
            pl = proxima_planilha(A_CRIAR)
            if pl is None:
                print("Nada para criar: a pasta A CRIAR esta vazia.")
                return 0
            lote = L.criar_lote(pl, LOTES, datetime.now())
            print(f"Lote novo: {pl.name}")
        else:
            print(f"Continuando o lote de {Path(L.ler(lote)['planilha']).name}")
        cod = rodar_lote(lote)
        if cod != 0 and not L.ler(lote).get("concluido"):
            print(f"\nParou. O que aconteceu esta em {lote / 'andamento.txt'}")
            return cod
        pl = Path(L.ler(lote)["planilha"])
        if pl.is_file():
            print(f"Planilha guardada em {mover_para_feitos(pl)}")


if __name__ == "__main__":
    sys.exit(main())
```

> `travas.conferir` recebe `(etapa, lote, pais)`; os testes passam lambdas com essa assinatura. A etapa `capas` também passa por `_etapa` (Claude grava `_busca.json`, a trava roda `capas.py`), e acontece logo depois da `entrada` — é a pré-checagem de capa do spec.

Run: `python -m pytest -q tools/esteira_auto/tests` → todos passam.

- [ ] **Step 6: Commit**

```bash
git add tools/esteira_auto/
git commit -m "feat(esteira-auto): maestro com travas, nova tentativa, devolvidos e FEITOS"
```

---

### Task 9: Botão, atalho e documentação

**Files:**
- Create: `tools/esteira_auto/Criar anuncios.bat`, atalho `G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\1 - Criar anuncios.lnk`, pasta `G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR\FEITOS`
- Modify: `CLAUDE.md` (frente 1), `squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md` (nota: na esteira automática a aprovação e a publicação são na tela), `PROGRESSO.md`, `DECISOES.md`

- [ ] **Step 1: `.bat`** (mesmo molde do `Aprovar anuncios.bat`):

```bat
@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Criar anuncios do ML
echo Esteira de anuncios. Pode deixar esta janela aberta e fazer outra coisa:
echo a tela de aprovacao abre sozinha quando o texto estiver pronto.
echo.
python "%~dp0maestro.py"
if errorlevel 9009 (
  echo Python nao encontrado neste computador. Chame o Claude.
  pause
  exit /b 9009
)
echo.
pause
```

- [ ] **Step 2: Atalho e pasta** (PowerShell, mesmo jeito do `2 - Aprovar anuncios.lnk`):

```powershell
New-Item -ItemType Directory -Force "G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\A CRIAR\FEITOS" | Out-Null
$s = (New-Object -ComObject WScript.Shell).CreateShortcut("G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\1 - Criar anuncios.lnk")
$s.TargetPath = "C:\Users\Almir\workspace\projects\criacao_anuncio_opensquad\tools\esteira_auto\Criar anuncios.bat"
$s.WorkingDirectory = "C:\Users\Almir\workspace\projects\criacao_anuncio_opensquad\tools\esteira_auto"
$s.Save()
```
Conferir: `Test-Path "G:\Meu Drive\TERRA CASA DECOR\ANUNCIOS\1 - Criar anuncios.lnk"` → True. Rodar o botão com `A CRIAR` vazia → janela diz "Nada para criar: a pasta A CRIAR esta vazia."

- [ ] **Step 3: Documentação** — em `CLAUDE.md` frente 1, acrescentar: "**Sem conversa desde 09/10/2026:** botão `1 - Criar anuncios` (pasta `ANUNCIOS`) → `tools/esteira_auto/maestro.py`; lote em `squads/ml-anuncios/output/lotes/<data-hora>/` com `andamento.txt`; aprovação, preço e publicação na tela; descrição e Flex gravados sozinhos depois de cada cor." Em `DECISOES.md`, entrada 2026-10-09 com as decisões do spec (seções 0, 1 e 3). Em `PROGRESSO.md`, trocar o "PRÓXIMO PASSO" da seção 0 pelo estado novo e acrescentar como próximo trabalho "levar a publicação (`ML Publicar`) do n8n para o Supabase".

- [ ] **Step 4: Commit**

```bash
git add "tools/esteira_auto/Criar anuncios.bat" CLAUDE.md DECISOES.md PROGRESSO.md squads/ml-anuncios/pipeline/steps/step-06-checkpoint-copy.md
git commit -m "feat(esteira-auto): botao Criar anuncios + documentacao"
```

---

### Task 10: Ensaio real até a tela (boleira Brinox, sem publicar)

**Pré-requisitos (do Almir):** fotos da boleira com a etiqueta `capa-anuncio` (hoje só têm o SKU); linha da boleira na cubagem; planilha exportada do Olist em `A CRIAR`.

- [ ] **Step 1: Conferir os pré-requisitos sem gastar nada** — Cloudinary `tags=capa-anuncio AND tags=BRI-coza34-40652_3009` (MCP) ≥ 1 foto; cubagem tem `BRI-COZA34-40652-3009` (chave normalizada por `sku_chave`); `A CRIAR` tem a planilha. Faltou → avisar o Almir e parar.

- [ ] **Step 2: Rodar o botão** (pela linha de comando, para acompanhar): `python tools/esteira_auto/maestro.py`. Acompanhar `andamento.txt`. Esperado: etapas até "esperando voce na tela", tela abre.

- [ ] **Step 3: Conferir o cartão no Chrome dedicado** — uma linha (sem cor), título sem cor no fim, código de barras presente (ou "Reler do Olist" funcionando), fotos na ordem, categoria, Premium, parecer, quadro (se houver pendência), peso e caixa. **Não publicar.** Fechar a tela (a janela preta diz "tela fechada com anuncio pendente").

- [ ] **Step 4: Retomada** — clicar de novo: deve ir direto à tela sem refazer nada (conferir `andamento.txt`: nenhuma etapa repetida).

- [ ] **Step 5: Registrar** no `HISTORICO.md` (tempo de cada etapa, custo, o que precisou de ajuste) e commit.

### Task 11: 1ª publicação real com o Almir

- [ ] **Step 1:** Almir abre o botão `2 - Aprovar anuncios` (ou o 1, que retoma), confere, digita o preço e clica **Aprovar e publicar**.
- [ ] **Step 2:** Conferir com `python tools/ler_anuncio_ml.py <MLB>`: título, GTIN, SELLER_SKU, caixa, fotos, preço; descrição gravada e Flex ligado (o cartão mostra ✅).
- [ ] **Step 3:** A planilha foi para `A CRIAR\FEITOS`; lote concluído.
- [ ] **Step 4:** `HISTORICO.md` + `PROGRESSO.md` atualizados; commit.
