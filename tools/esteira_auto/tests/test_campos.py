import json
import os
import sys

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from esteira_auto import campos  # noqa: E402

API = [
    {"id": "BRAND", "name": "Marca", "value_type": "string", "tags": {"required": True}},
    {"id": "SHAPE", "name": "Forma", "value_type": "string", "tags": {"hidden": True}},
    {"id": "PACKAGE_WEIGHT", "name": "Peso", "value_type": "number_unit", "tags": {"read_only": True}},
    {"id": "WITH_PEDESTAL", "name": "Com pé", "value_type": "boolean", "tags": {}, "values": [{"name": "Não"}, {"name": "Sim"}]},
    {"id": "GTIN", "name": "Código", "value_type": "string", "tags": {"variation_attribute": True}},
    {"id": "SELLER_SKU", "name": "SKU", "value_type": "string", "tags": {}},
    {"id": "APGID", "name": "APGID", "value_type": "string", "tags": {"hidden": True}},
    {"id": "IEPS", "name": "IEPS", "value_type": "list", "tags": {"hidden": True, "read_only": True}},
    {"id": "COLOR", "name": "Cor", "value_type": "string", "tags": {}},
]


def _lote(tmp_path, modo):
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump(
        {"categorias": [{"pai_sku": "P", "category_id": "MLB1", "modo": modo}]}), encoding="utf-8")
    return tmp_path


def test_so_os_campos_que_o_comprador_ve(tmp_path):
    lt = _lote(tmp_path, "simples")
    assert campos.buscar_campos(lt, ler=lambda cat: API) == []
    c = json.loads((lt / "categorizacao" / "campos-P.json").read_text(encoding="utf-8"))
    # oculto entra marcado; so-leitura, controle do ML, GTIN e SKU (a esteira poe) ficam fora
    assert [x["id"] for x in c] == ["BRAND", "SHAPE", "WITH_PEDESTAL", "COLOR"]
    assert c[1].get("oculto") is True and "oculto" not in c[0]
    assert c[2]["values"] == ["Não", "Sim"]


def test_com_cores_a_cor_vem_da_variacao(tmp_path):
    lt = _lote(tmp_path, "variacoes")
    campos.buscar_campos(lt, ler=lambda cat: API)
    c = json.loads((lt / "categorizacao" / "campos-P.json").read_text(encoding="utf-8"))
    assert "COLOR" not in [x["id"] for x in c]


def test_falha_de_rede_nao_para_a_esteira(tmp_path):
    lt = _lote(tmp_path, "simples")
    def quebra(cat):
        raise OSError("sem rede")
    assert campos.buscar_campos(lt, ler=quebra) == ["P"]
    assert not (lt / "categorizacao" / "campos-P.json").exists()


def test_sem_lista_de_categorias_nao_quebra(tmp_path):
    assert campos.buscar_campos(tmp_path, ler=lambda cat: 1 / 0) == ["(lista de categorias)"]


def test_codigo_de_categoria_estranho_nao_vira_pedido_com_o_acesso_da_loja(tmp_path):
    # categorias.yaml e escrito pelo Claude sem conversa: valor de fora nao pode virar outro endereco do ML
    (tmp_path / "categorizacao").mkdir()
    (tmp_path / "categorizacao" / "categorias.yaml").write_text(yaml.safe_dump({"categorias": [
        {"pai_sku": "P", "category_id": "MLB1/../../users/me"},
        {"pai_sku": "../../fora", "category_id": "MLB2"}]}), encoding="utf-8")
    pedidos = []
    falhou = campos.buscar_campos(tmp_path, ler=lambda cat: pedidos.append(cat) or API)
    assert pedidos == [] and sorted(falhou) == ["../../fora", "P"]
    assert not (tmp_path / "fora.json").exists() and not list(tmp_path.parent.glob("campos-*.json"))
