from completar_anuncio import texto_descricao


def test_tira_html_e_emoji_e_junta_linhas_vazias():
    p = {"description_plain": "<b>Oi</b> 😀\r\n\r\n\r\n- Item 1  \n- Item 2"}
    assert texto_descricao(p) == "Oi\n\n- Item 1\n- Item 2"


def test_descricao_vazia_recusa():
    import pytest
    with pytest.raises(ValueError):
        texto_descricao({"description_plain": "   "})


def _falso(respostas, chamadas):
    def chamar(metodo, caminho, tk, corpo=None):
        chamadas.append((metodo, caminho, corpo))
        return respostas.get((metodo, caminho), (200, {}))
    return chamar


def test_completar_grava_garantia_e_confere_loja(monkeypatch):
    import completar_anuncio as ca
    chamadas = []
    monkeypatch.setattr(ca, "_chamar", _falso({
        ("GET", "/items/MLB1/description"): (200, {"plain_text": "ja tem"}),
        ("GET", "/flex/sites/MLB/items/MLB1/v2"): (200, {"has_flex": True}),
        ("GET", "/items/MLB1"): (200, {"official_store_id": 458566, "sale_terms": []}),
    }, chamadas))
    r = ca.completar({"description_plain": "x"}, "MLB1", "tk")
    assert r == {"descricao": True, "flex": True, "garantia": True, "loja_oficial": True}
    put = [c for c in chamadas if c[0] == "PUT"]
    assert put and put[0][1] == "/items/MLB1" and put[0][2]["sale_terms"] == ca.GARANTIA


def test_completar_acusa_fora_da_loja_oficial(monkeypatch):
    import completar_anuncio as ca
    monkeypatch.setattr(ca, "_chamar", _falso({
        ("GET", "/items/MLB1/description"): (200, {"plain_text": "ja tem"}),
        ("GET", "/flex/sites/MLB/items/MLB1/v2"): (200, {"has_flex": True}),
        ("GET", "/items/MLB1"): (200, {"official_store_id": None,
                                       "sale_terms": [{"id": "WARRANTY_TIME", "value_name": "30 dias"},
                                                      {"id": "WARRANTY_TYPE", "value_name": "Garantia do vendedor"}]}),
    }, []))
    r = ca.completar({"description_plain": "x"}, "MLB1", "tk")
    assert r["loja_oficial"] is False and r["garantia"] is True
