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


def test_texto_roda_as_tres_travas(tmp_path):
    vistos = []
    def falso(cmd, **kw):
        vistos.append(os.path.basename(cmd[1]))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=falso) == {}
    assert vistos == ["validar_claims.py", "validar_ficha_seo.py", "validar_ficha_nsa.py"]


def test_capas_sem_foto_nao_para_e_anota(tmp_path):
    # Almir 26/10/2026: a esteira nao exige foto; a trava e so na hora de publicar no canal
    saida = "B: \n\nCAPAS INCOMPLETAS - 1:\n  - B: falta capa da cor 'Preto'"
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, saida, "")
    (tmp_path / "capas").mkdir(); (tmp_path / "capas" / "_busca.json").write_text("{}")
    assert travas.conferir("capas", tmp_path, ["A", "B"], rodar=falso) == {}
    caderno = (tmp_path / "andamento.txt").read_text(encoding="utf-8")
    assert "B: falta capa da cor 'Preto'" in caderno and "segue sem" in caderno
    assert "B: B:" not in caderno


def test_capas_programa_quebrado_ainda_reprova(tmp_path):
    falso = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "Traceback: deu ruim", "")
    (tmp_path / "capas").mkdir(); (tmp_path / "capas" / "_busca.json").write_text("{}")
    assert travas.conferir("capas", tmp_path, ["A"], rodar=falso) == {"A": "Traceback: deu ruim"}


def test_ficha_nsa_recebe_a_lista_de_campos_quando_existe(tmp_path):
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "campos-A.json").write_text("[]", encoding="utf-8")
    vistos = []
    def falso(cmd, **kw):
        vistos.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")
    travas.conferir("texto", tmp_path, ["A"], rodar=falso)
    nsa = [c for c in vistos if c[1].endswith("validar_ficha_nsa.py")][0]
    assert nsa[-1].endswith("campos-A.json")


def _anuncio(tmp_path, longos, **extra):
    (tmp_path / "copywriting").mkdir(exist_ok=True)
    (tmp_path / "copywriting" / "anuncio-A.yaml").write_text(yaml.safe_dump(
        {"pai_sku": "A", "titulos_longos": longos, **extra}, allow_unicode=True), encoding="utf-8")


def _ok(cmd, **kw):
    return subprocess.CompletedProcess(cmd, 0, "", "")


def test_titulos_longos_conferidos_pelo_tamanho_de_verdade(tmp_path):
    bom = [{"texto": "x" * 100, "length": 100, "recomendado": True}, {"texto": "y" * 85, "recomendado": False}]
    _anuncio(tmp_path, bom)
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
    # tamanho fora de 85-100 nao para mais o produto (04/11/2026, pedido 627): vira aviso no caderno, contado pelo texto
    _anuncio(tmp_path, [bom[0], {"texto": "y" * 101, "length": 99, "recomendado": False}])  # length mente
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
    assert travas.titulos_longos_fora(tmp_path / "copywriting" / "anuncio-A.yaml") == [101]
    _anuncio(tmp_path, [dict(bom[0]), dict(bom[1], recomendado=True)])
    assert "recomendado" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _anuncio(tmp_path, [bom[0]])
    assert "2 a 3" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _anuncio(tmp_path, None)
    assert "titulos longos" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]


def test_titulos_longos_nao_cobram_anuncio_ja_aprovado(tmp_path):
    _anuncio(tmp_path, None, status_copy="aprovado")
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}


def _lote_decisao(tmp_path, attrs, pendentes=(), decisoes=None):
    (tmp_path / "categorizacao").mkdir(exist_ok=True)
    (tmp_path / "categorizacao" / "campos-A.json").write_text(json.dumps(
        [{"id": "SHAPE"}, {"id": "DIAMETER"}]), encoding="utf-8")
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "A", "decisoes_almir":
        decisoes if decisoes is not None else [{"campo": "SHAPE", "valor": "Redonda", "sku": None},
                                               {"campo": "SALE_FORMAT", "valor": "Unidade", "sku": None}]}]}),
        encoding="utf-8")
    longos = [{"texto": "x" * 95, "recomendado": True}, {"texto": "y" * 95, "recomendado": False}]
    _anuncio(tmp_path, longos, attributes=attrs, campos_pendentes=list(pendentes))


def test_texto_segue_a_decisao_do_almir(tmp_path):
    _lote_decisao(tmp_path, {"SHAPE": "redonda "})  # maiuscula/espaco nao importam; SALE_FORMAT fora da categoria
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}
    _lote_decisao(tmp_path, {"SHAPE": "Quadrada"})
    assert "Almir" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _lote_decisao(tmp_path, {}, pendentes=["SHAPE"])
    assert "SHAPE" in travas.conferir("texto", tmp_path, ["A"], rodar=_ok)["A"]
    _lote_decisao(tmp_path, {"SHAPE": "Quadrada"}, decisoes=[])  # sem decisao, a esteira decide
    assert travas.conferir("texto", tmp_path, ["A"], rodar=_ok) == {}


def _magalu(tmp_path, ficha, decisoes=(), status="ok"):
    campos = [{"nome": "Marca", "obrigatorio": True}, {"nome": "Material", "obrigatorio": False},
              {"nome": "Peso do Produto", "obrigatorio": False}]
    cands = [{"id": "bc2b", "nome": "Prato", "campos": campos}, {"id": "a609", "nome": "Prato Decorativo", "campos": campos}]
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [
        {"pai_sku": "A", "magalu": {"candidatas": cands, "fixa": False, "decisoes": list(decisoes)}}]}), encoding="utf-8")
    (tmp_path / "copywriting").mkdir(exist_ok=True)
    an = tmp_path / "copywriting" / "anuncio-A.yaml"
    dado = {"status_copy": status}
    if ficha is not None:
        dado["ficha_magalu"] = ficha
    an.write_text(yaml.safe_dump(dado, allow_unicode=True), encoding="utf-8")
    return travas._ficha_magalu(tmp_path, "A", an)


def test_ficha_magalu_todo_campo_com_valor_ou_motivo(tmp_path):
    boa = {"categoria_id": "bc2b", "campos": [{"nome": "Marca", "valor": "Coza"}, {"nome": "Material", "valor": "Polipropileno"},
                                             {"nome": "Peso do Produto", "motivo": "sem a pesagem sem a caixa"}]}
    assert _magalu(tmp_path, boa) is None
    assert "falta a ficha do Magalu" in _magalu(tmp_path, None)
    assert "uma das candidatas" in _magalu(tmp_path, dict(boa, categoria_id="xx"))
    falta = dict(boa, campos=boa["campos"][:2])
    assert "Peso do Produto: sem resposta" in _magalu(tmp_path, falta)
    dois = dict(boa, campos=boa["campos"][:2] + [{"nome": "Peso do Produto", "valor": "1 kg", "motivo": "x"}])
    assert "precisa de valor OU de motivo" in _magalu(tmp_path, dois)
    marca = dict(boa, campos=[{"nome": "Marca", "motivo": "nao sei"}] + boa["campos"][1:])
    assert _magalu(tmp_path, marca) is None  # obrigatorio sem valor: pendencia para o Almir, nao reprova (04/11)
    assert travas.pendentes_magalu(tmp_path, "A") == ["Marca"]
    ench = dict(boa, campos=[{"nome": "Marca", "valor": "N/A"}] + boa["campos"][1:])
    assert "enchimento" in _magalu(tmp_path, ench)
    extra = dict(boa, campos=boa["campos"] + [{"nome": "Forma", "valor": "Redonda"}])
    assert "Forma: nao existe na categoria" in _magalu(tmp_path, extra)
    assert _magalu(tmp_path, None, status="aprovado") is None  # anuncio ja aprovado nao se cobra


def test_ficha_magalu_decisao_do_almir_vale(tmp_path):
    boa = {"categoria_id": "bc2b", "campos": [{"nome": "Marca", "valor": "Coza"}, {"nome": "Material", "valor": "Plastico"},
                                             {"nome": "Peso do Produto", "motivo": "sem pesagem"}]}
    dec = [{"categoria_id": "bc2b", "campo": "Material", "valor": "Polipropileno"}]
    assert "contra a decisao do Almir" in _magalu(tmp_path, boa, dec)
    assert _magalu(tmp_path, boa, [dict(dec[0], categoria_id="outra")]) is None  # decisao de outra categoria nao cobra


def test_ficha_magalu_sem_magalu_no_pedido_nao_cobra(tmp_path):
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "A"}]}), encoding="utf-8")
    (tmp_path / "copywriting").mkdir()
    (tmp_path / "copywriting" / "anuncio-A.yaml").write_text("status_copy: ok\n", encoding="utf-8")
    assert travas._ficha_magalu(tmp_path, "A", tmp_path / "copywriting" / "anuncio-A.yaml") is None


def _reais(tmp_path, attrs, reais=None, status="ok"):
    an = tmp_path / "anuncio-A.yaml"
    dado = {"status_copy": status, "attributes": attrs}
    if reais is not None:
        dado["atributos_reais"] = reais
    an.write_text(yaml.safe_dump(dado, allow_unicode=True), encoding="utf-8")
    return travas._atributos_reais(an)


def test_modelo_linha_material_levam_o_valor_real(tmp_path):
    ml = {"BRAND": "Coza", "MODEL": "Lava-louças Micro-ondas Jantar", "LINE": "Cozy Mesa Posta",
          "MATERIAL": "Polipropileno Colorido Criança"}
    reais = {"MODEL": "Cozy 10570", "LINE": "Cozy", "MATERIAL": "Polipropileno"}
    assert _reais(tmp_path, ml, reais) is None
    assert "MODEL: falta o valor real" in _reais(tmp_path, ml, {"LINE": "Cozy", "MATERIAL": "Polipropileno"})
    assert "MATERIAL: falta o valor real" in _reais(tmp_path, ml)
    assert "enchimento" in _reais(tmp_path, ml, dict(reais, LINE="-"))
    assert "BRAND: so Modelo" in _reais(tmp_path, ml, dict(reais, BRAND="Coza"))
    assert _reais(tmp_path, {"BRAND": "Coza", "LINE": "não se aplica"}) is None  # sem palavra de busca, nada a separar
    assert _reais(tmp_path, ml, status="aprovado") is None


def test_decisao_do_almir_em_modelo_vale_contra_o_valor_real(tmp_path):
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps({"anuncios": [{"pai_sku": "A", "decisoes_almir": [
        {"campo": "MODEL", "valor": "Cozy 10570"}]}]}), encoding="utf-8")
    an = tmp_path / "anuncio-A.yaml"
    an.write_text(yaml.safe_dump({"status_copy": "ok", "attributes": {"MODEL": "Prato Raso Jantar"},
                                  "atributos_reais": {"MODEL": "Cozy 10570"}}, allow_unicode=True), encoding="utf-8")
    assert travas._decisoes_almir(tmp_path, "A", an, tmp_path / "campos-A.json") is None
    an.write_text(yaml.safe_dump({"status_copy": "ok", "attributes": {"MODEL": "Prato Raso Jantar"},
                                  "atributos_reais": {"MODEL": "Cozy"}}, allow_unicode=True), encoding="utf-8")
    assert "MODEL = Cozy 10570" in travas._decisoes_almir(tmp_path, "A", an, tmp_path / "campos-A.json")


def test_pedido_947_materials_e_campo_de_busca(tmp_path):
    """Reprova no codigo antigo: 'MATERIALS: so Modelo, Linha e Material levam valor real separado' (categoria Bowl)."""
    (tmp_path / "copywriting").mkdir(exist_ok=True)
    arq = tmp_path / "copywriting" / "anuncio-A.yaml"
    arq.write_text(yaml.safe_dump({"attributes": {"MATERIALS": "Melamina Resistente"},
                                   "atributos_reais": {"MATERIALS": "Melamina"}}, allow_unicode=True), encoding="utf-8")
    assert travas._atributos_reais(arq) is None
    # sem o valor real de MATERIALS tambem passa (pedidos 491, 579, 627 e 629 eram assim e nao podem passar a parar)
    arq.write_text(yaml.safe_dump({"attributes": {"MATERIALS": "Melamina Resistente"}, "atributos_reais": {}},
                                  allow_unicode=True), encoding="utf-8")
    assert travas._atributos_reais(arq) is None
    # outro campo fora da lista continua barrando
    arq.write_text(yaml.safe_dump({"attributes": {}, "atributos_reais": {"COLOR": "Azul"}}, allow_unicode=True), encoding="utf-8")
    assert "COLOR" in (travas._atributos_reais(arq) or "")


def _anuncio_attrs(tmp_path, attrs, **extra):
    an = tmp_path / "anuncio-A.yaml"
    an.write_text(yaml.safe_dump({"pai_sku": "A", "attributes": attrs, **extra}, allow_unicode=True), encoding="utf-8")
    return an


def test_cauda_curta_pedido_1323_devolve_para_completar(tmp_path):
    # pedido 1323 (ROJ-2001-28311-KT04-BR, 05/11/2026): Modelo 22 letras e Material so "Melamina"
    r = travas._cauda_curta(_anuncio_attrs(tmp_path, {"MODEL": "Jantar Almoço Refeição", "MATERIAL": "Melamina"}))
    assert travas.so_completar(r)
    assert "Modelo (MODEL)" in r and "22 letras" in r and "Material (MATERIAL)" in r


def test_cauda_comprida_ou_nao_se_aplica_passa(tmp_path):
    ok = {"MODEL": "Jogo Prato Jantar Almoço Refeição", "MATERIAL": "Melamina Branco Leve Resistente"}
    assert travas._cauda_curta(_anuncio_attrs(tmp_path, ok)) is None
    assert travas._cauda_curta(_anuncio_attrs(tmp_path, {"MODEL": ok["MODEL"], "MATERIAL": "Não se aplica"})) is None
    assert travas._cauda_curta(_anuncio_attrs(tmp_path, {"MODEL": ok["MODEL"]})) is None  # categoria sem Material
    assert travas._cauda_curta(_anuncio_attrs(tmp_path, {"MODEL": "Curto"}, status_copy="aprovado")) is None


def test_motivo_de_verdade_nao_e_so_completar():
    assert not travas.so_completar("texto inventou balde")
