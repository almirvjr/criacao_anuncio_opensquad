"""Variacao que nao e de cor e medidas lidas nas fotos (hub, 25/10/2026: tigela BEL-4006-PAI M e G)."""
import json
import subprocess
import sys
from pathlib import Path

import yaml

from esteira_auto import variacoes as V

M, G = "BEL-4006-0761-M-PE", "BEL-4006-0762-G-PE"
RAIZ = Path(__file__).resolve().parents[3]
VAL = RAIZ / "squads" / "ml-anuncios" / "pipeline" / "validators"


def _lote(tmp_path, anuncio, eixo="tamanho", variacao_magalu=("Capacidade",), fotos=True):
    ent = {"anuncios": [{"pai_sku": "BEL-4006-PAI", "eixo_variacao": eixo,
                         "variacoes": [{"sku": M, "cor": "Peixes"}, {"sku": G, "cor": "Peixes"}],
                         "magalu": {"candidatas": [{"id": "tigela", "nome": "Tigela", "variacao": list(variacao_magalu)}]}}]}
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps(ent), encoding="utf-8")
    if fotos:
        for s in (M, G):
            p = tmp_path / "capas" / "fotos" / s
            p.mkdir(parents=True)
            (p / "04.jpg").write_bytes(b"x")
    arq = tmp_path / "anuncio.yaml"
    arq.write_text(yaml.safe_dump(anuncio, allow_unicode=True), encoding="utf-8")
    return arq


def _certo():
    return {
        "attributes": {"BRAND": "Bellagio", "SHAPE": "Oval"},
        "medidas_por_variacao": {
            M: {"comprimento_cm": 38.5, "largura_cm": 26, "altura_cm": 7.5, "capacidade": "3,5 L", "forma": "Oval", "fonte": "foto 04 e foto 09"},
            G: {"comprimento_cm": 42, "largura_cm": 29, "altura_cm": 8, "capacidade": "4,5 L", "forma": "Oval", "fonte": "foto 04 e foto 09"},
        },
        "por_variacao": {
            M: {"titulo_ml": "Tigela Oval Melamina Saladeira de Servir 38,5x26cm",
                "attributes": {"HEIGHT": "7,5 cm", "VOLUME_CAPACITY": "3,5 L"},
                "magalu": [{"nome": "Capacidade", "valor": "3,5 L"}]},
            G: {"titulo_ml": "Tigela Oval Melamina Saladeira de Servir 42x29cm",
                "attributes": {"HEIGHT": "8 cm", "VOLUME_CAPACITY": "4,5 L"},
                "magalu": [{"nome": "Capacidade", "valor": "4,5 L"}]},
        },
        "ficha_magalu": {"categoria_id": "tigela", "campos": []},
    }


def test_eixo_pela_grade():
    assert V.eixo([{"cor": "Peixes", "tamanho": "M"}, {"cor": "Peixes", "tamanho": "G"}]) == "tamanho"
    assert V.eixo([{"cor": "Preto"}, {"cor": "Branco"}]) == "cor"
    assert V.eixo([{"cor": "Preto", "tamanho": "M"}, {"cor": "Branco", "tamanho": "G"}]) == "cor"
    assert V.eixo([{"cor": "Preto"}]) is None


def test_tigela_certa_passa(tmp_path):
    assert V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, _certo())) is None


def test_o_que_aconteceu_com_a_tigela_reprova(tmp_path):
    a = _certo()
    a["attributes"]["SHAPE"] = "Redonda"                                   # forma de concorrente
    a["medidas_por_variacao"][M]["fonte"] = "anuncio do concorrente MLB25167925"
    a["por_variacao"][G]["titulo_ml"] = a["por_variacao"][M]["titulo_ml"]  # mesmo titulo nos dois
    a["por_variacao"][G]["magalu"] = [{"nome": "Capacidade", "valor": "3,5 L"}]  # mesma capacidade
    m = V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a))
    assert "SHAPE 'Redonda' diferente da forma nas fotos" in m
    assert f"{M}: a fonte das medidas" in m
    assert "titulo do ML igual" in m and "medida dele, junta: 42x29cm" in m
    assert "Magalu: 'Capacidade' igual" in m


def test_sem_medidas_com_foto_reprova_e_sem_foto_nao_cobra(tmp_path):
    a = _certo()
    del a["medidas_por_variacao"]
    a["por_variacao"] = {}
    m = V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a, eixo="cor", variacao_magalu=("Cor",)))
    assert f"{M}: falta medidas_por_variacao" in m and "Magalu: 'Cor' igual" in m


def test_cor_nao_pede_titulo_por_variacao(tmp_path):
    a = _certo()
    for x in a["por_variacao"].values():
        del x["titulo_ml"]
    assert V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a, eixo="cor")) is None


def test_valor_na_familia_e_na_variacao_reprova(tmp_path):
    a = _certo()
    a["attributes"]["HEIGHT"] = "8 cm"
    assert "HEIGHT esta na familia e na variacao" in V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a))


def test_ficha_nsa_aceita_valor_por_variacao(tmp_path):
    arq = tmp_path / "a.yaml"
    arq.write_text(yaml.safe_dump(_certo(), allow_unicode=True), encoding="utf-8")
    campos = tmp_path / "c.json"
    campos.write_text(json.dumps([{"id": "HEIGHT"}, {"id": "VOLUME_CAPACITY"}, {"id": "SHAPE"}]), encoding="utf-8")
    r = subprocess.run([sys.executable, str(VAL / "validar_ficha_nsa.py"), str(arq), str(campos)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    a = _certo()
    del a["por_variacao"][G]["attributes"]["HEIGHT"]  # uma variacao sem a altura: falta destino
    arq.write_text(yaml.safe_dump(a, allow_unicode=True), encoding="utf-8")
    r = subprocess.run([sys.executable, str(VAL / "validar_ficha_nsa.py"), str(arq), str(campos)], capture_output=True, text=True)
    assert r.returncode == 1 and "CAMPO_SEM_DESTINO HEIGHT" in r.stdout


def test_titulo_da_variacao_passa_pela_regra_da_marca():
    sys.path.insert(0, str(VAL))
    import validar_ficha_seo as S
    a = _certo()
    a["por_variacao"][M]["titulo_ml"] = "Tigela Bellagio 38,5x26cm"
    assert "Tigela Bellagio 38,5x26cm" in S.outros_titulos_do_copy(a)


def test_titulo_do_ml_sem_a_cor_e_com_medida_junta(tmp_path):
    a = _certo()
    a["titles"] = [{"texto": "Tigela Melamina Peixes Saladeira 25,7 Cm", "recomendado": True}]
    a["por_variacao"][M]["titulo_ml"] = "Tigela Oval Melamina Saladeira 38,5 x 26 cm"
    m = V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a))
    assert "titulo do ML com a cor (peixes)" in m and "Peixes Saladeira 25,7 Cm" in m
    assert m.count("medida separada por espaco") == 2
    assert V.MEDIDA_COM_ESPACO.search("Lixeira 5 maneiras de usar") is None


def test_modelo_real_e_so_o_modelo_do_fabricante(tmp_path):
    a = _certo()
    a["titles"] = [{"texto": "Tigela Oval Melamina Saladeira de Servir", "recomendado": True}]
    a["attributes"]["MATERIALS"] = "Melamina"
    a["atributos_reais"] = {"MODEL": "Tigela Oval Linha Oceano"}
    m = V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a))
    assert "Modelo real 'Tigela Oval Linha Oceano' tem tipo/forma/material/cor (oval, tigela)" in m
    a["atributos_reais"] = {"MODEL": "Linha Oceano"}
    (tmp_path / "anuncio.yaml").write_text(yaml.safe_dump(a, allow_unicode=True), encoding="utf-8")
    assert V.conferir(tmp_path, "BEL-4006-PAI", tmp_path / "anuncio.yaml") is None


def test_tamanho_junto_quando_a_categoria_aceita(tmp_path):
    a = _certo()
    for x in a["por_variacao"].values():
        del x["titulo_ml"]
    arq = _lote(tmp_path, a)
    (tmp_path / "categorizacao").mkdir()
    campos = tmp_path / "categorizacao" / "campos-BEL-4006-PAI.json"
    campos.write_text(json.dumps([{"id": "HEIGHT"}]), encoding="utf-8")  # so aceita a cor: separa
    assert "so aceita a cor como variacao" in V.conferir(tmp_path, "BEL-4006-PAI", arq)
    campos.write_text(json.dumps([{"id": "SIZE", "variacao": True}]), encoding="utf-8")  # aceita tamanho: juntos
    assert "campo de variacao da categoria (SIZE)" in V.conferir(tmp_path, "BEL-4006-PAI", arq)
    a["por_variacao"][M]["attributes"]["SIZE"] = "38,5x26cm"
    a["por_variacao"][G]["attributes"]["SIZE"] = "42x29cm"
    arq.write_text(yaml.safe_dump(a, allow_unicode=True), encoding="utf-8")
    assert V.conferir(tmp_path, "BEL-4006-PAI", arq) is None


def test_baixar_fotos_copia_pequena(tmp_path):
    (tmp_path / "capas").mkdir()
    url = "https://res.cloudinary.com/wa5lvi98/image/upload/c_pad,w_1200,h_1200,b_white,q_auto/v1/b/x.jpg"
    (tmp_path / "capas" / "capas-P.yaml").write_text(yaml.safe_dump(
        {"picture_ids_por_variacao": [{"sku_variacao": M, "picture_ids": [url, url]}]}), encoding="utf-8")
    pedidas = []

    class R:
        def __init__(self, u): pedidas.append(u)
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n=-1): return bytes([0xFF, 0xD8]) + b"jpg"
    assert V.baixar_fotos(tmp_path, abrir=lambda u, timeout: R(u)) == []
    assert (tmp_path / "capas" / "fotos" / M / "02.jpg").read_bytes() == bytes([0xFF, 0xD8]) + b"jpg"
    assert "c_pad,w_900,h_900" in pedidas[0]


def test_baixar_fotos_so_do_nosso_cloudinary(tmp_path):
    (tmp_path / "capas").mkdir()
    for nome, url in (("A", "file:///C:/Windows/win.ini"), ("B", "http://169.254.169.254/x.jpg")):
        (tmp_path / "capas" / f"capas-{nome}.yaml").write_text(yaml.safe_dump(
            {"picture_ids_por_variacao": [{"sku_variacao": nome + "-1", "picture_ids": [url]}]}), encoding="utf-8")
    chamou = []
    assert V.baixar_fotos(tmp_path, abrir=lambda u, timeout: chamou.append(u)) == ["A-1", "B-1"]
    assert chamou == []


def test_descricao_sem_recado_interno(tmp_path):
    a = _certo()
    a["description"] = {"bloco_3": "Nao informamos se vai ao micro-ondas: e uma escolha nossa, para nao prometer o que nao conferimos."}
    m = V.conferir(tmp_path, "BEL-4006-PAI", _lote(tmp_path, a))
    assert "descricao com recado interno" in m and "escolha nossa" in m
    a["description"] = {"bloco_3": "Pode ir a lava-loucas e ao freezer, mas nao vai ao micro-ondas."}
    (tmp_path / "anuncio.yaml").write_text(yaml.safe_dump(a, allow_unicode=True), encoding="utf-8")
    assert V.conferir(tmp_path, "BEL-4006-PAI", tmp_path / "anuncio.yaml") is None


def test_kit_com_itens_aprovados_nao_cobra_medida_da_foto(tmp_path):
    # Almir 26/10/2026, pedido 60: a medida do kit vem da ficha aprovada de cada item (mig 231), nao da foto do kit
    a = _certo()
    del a["medidas_por_variacao"]
    arq = _lote(tmp_path, a, eixo="cor", variacao_magalu=("Cor",))
    ent = json.loads((tmp_path / "anuncios-entrada.json").read_text(encoding="utf-8"))
    for v in ent["anuncios"][0]["variacoes"]:
        v["itens_kit"] = [{"sku": "ITEM", "quantidade": 1, "medidas": {"altura_cm": 7.5}}]
    (tmp_path / "anuncios-entrada.json").write_text(json.dumps(ent), encoding="utf-8")
    m = V.conferir(tmp_path, "BEL-4006-PAI", arq) or ""
    assert "medidas_por_variacao" not in m and "medidas incompletas" not in m
