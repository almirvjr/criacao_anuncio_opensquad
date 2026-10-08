from completar_anuncio import texto_descricao


def test_tira_html_e_emoji_e_junta_linhas_vazias():
    p = {"description_plain": "<b>Oi</b> 😀\r\n\r\n\r\n- Item 1  \n- Item 2"}
    assert texto_descricao(p) == "Oi\n\n- Item 1\n- Item 2"


def test_descricao_vazia_recusa():
    import pytest
    with pytest.raises(ValueError):
        texto_descricao({"description_plain": "   "})
