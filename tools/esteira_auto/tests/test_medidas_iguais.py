import yaml

from esteira_auto import travas as T


def _anuncio(tmp_path, attrs, mg=None, sp=None):
    a = {"attributes": attrs}
    if mg is not None:
        a["ficha_magalu"] = {"categoria_id": "X", "campos": mg}
    if sp is not None:
        a["ficha_shopee"] = {"categoria_id": "Y", "campos": sp}
    f = tmp_path / "anuncio.yaml"
    f.write_text(yaml.safe_dump(a, allow_unicode=True), encoding="utf-8")
    return f


def test_mesma_medida_igual_passa_mesmo_com_virgula_e_unidade(tmp_path):
    f = _anuncio(tmp_path, {"DIAMETER": "27 cm", "HEIGHT": "2 cm"},
                 mg=[{"nome": "Diâmetro", "valor": "27cm"}, {"nome": "Altura do Produto", "valor": "20 mm"}],
                 sp=[{"nome": "Diâmetro", "valor": "27,0 cm"}])
    assert T._medidas_iguais(f) is None


def test_numero_diferente_reprova_e_diz_os_valores(tmp_path):
    # conversao de 09/11/2026: altura 2 cm no ML x 2,7 cm no Magalu
    f = _anuncio(tmp_path, {"HEIGHT": "2 cm"}, mg=[{"nome": "Altura do Produto", "valor": "2,7cm"}])
    e = T._medidas_iguais(f)
    assert e and "Altura" in e and "Mercado Livre 2 cm" in e and "Magalu 2,7cm" in e


def test_capacidade_em_ml_e_litro_compara_e_palavra_nao_trava(tmp_path):
    f = _anuncio(tmp_path, {"VOLUME_CAPACITY": "3500 mL", "MATERIAL": "Melamina"},
                 mg=[{"nome": "Capacidade", "valor": "3,5 L"}, {"nome": "Material", "valor": "Plástico"}])
    assert T._medidas_iguais(f) is None


def test_sem_numero_ou_um_canal_so_nao_cobra(tmp_path):
    f = _anuncio(tmp_path, {"DIAMETER": "não se aplica"}, mg=[{"nome": "Diâmetro", "valor": "22cm"}])
    assert T._medidas_iguais(f) is None
