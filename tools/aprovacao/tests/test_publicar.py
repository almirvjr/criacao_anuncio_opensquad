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


# --- revisao final (I5, I6) ---
def _ok_webhook(c):
    return {"http": 200, "resposta": {"status": "success", "mlb_id": "MLB" + c["sku"][-2:], "permalink": "https://l"}}


def test_erro_depois_do_webhook_nao_perde_o_mlb(saida):
    def completar_quebra(p, m, t):
        raise TimeoutError("rede caiu")
    r = pub.publicar_anuncio(saida, PAI, enviar=_ok_webhook, completar=completar_quebra, token=lambda: "tk")
    assert all(i["mlb"] and i["ok"] for i in r)
    assert all("descricao" in i["erro"] for i in r)
    gravado = _doc(saida)["publicacao"]
    assert gravado["VIE-1-PT"]["mlb"] == "MLBPT" and gravado["VIE-1-BR"]["mlb"] == "MLBBR"
    # clicar de novo nao manda de novo
    enviados = []
    pub.publicar_anuncio(saida, PAI, enviar=lambda c: enviados.append(c) or _ok_webhook(c),
                         completar=lambda p, m, t: {"descricao": True, "flex": True}, token=lambda: "tk")
    assert enviados == []


def test_token_que_estoura_nao_perde_o_mlb(saida):
    def token_quebra():
        raise OSError("sem rede")
    r = pub.publicar_anuncio(saida, PAI, enviar=_ok_webhook, completar=None, token=token_quebra)
    assert all(i["mlb"] for i in r)


def test_sem_resposta_nao_diz_que_nada_foi_publicado(saida):
    r = pub.publicar_anuncio(saida, PAI, enviar=lambda c: {"http": None, "resposta": {"texto_cru": "x"}},
                             completar=None, token=lambda: "tk")
    assert all("confira no ML" in i["erro"] and i["incerto"] for i in r)
    assert all("nada foi publicado" not in i["erro"] for i in r)
