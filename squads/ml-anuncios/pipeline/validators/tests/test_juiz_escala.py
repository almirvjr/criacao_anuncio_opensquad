"""Testes do juiz_escala (camada 1 do Juiz Visual).

Nao dependem de foto de verdade nem do BiRefNet: desenham silhuetas sinteticas
(cilindro escuro sobre fundo claro) com proporcao conhecida e monkeypatcham a
mascara. O que se testa e a REGRA, nao o detector.

O que cada teste prende (todos vieram de um caso real de 17-18/09/2026):
  - forma certa/errada -> aprova/reprova
  - tampa aberta -> recusa (a capa do 5L aprovada reprovava por isso)
  - produto cortado pelo quadro -> recusa (fotos 3/4/9 do 5L)
  - detector pegou outro objeto -> recusa (capa-v8: pegou o armario)
  - bancada fora do quadro -> recusa e manda medir na cena aberta (capa fechada em 65%)
  - uma borda so -> nao crava (foto-08 do 5L, banheiro de gabinete suspenso)
  - forma reprovada manda mais que escala sem medida
"""
import os
import sys

import numpy as np
import pytest
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..")))
import juiz_escala as J  # noqa: E402


def _cena(tmp_path, alt_prod, larg_prod, base_y, linha_bancada=None, lado=1200, nome="c.jpg"):
    """Fundo claro + retangulo escuro (o 'produto') + opcionalmente uma faixa
    horizontal que atravessa a imagem (a 'bancada')."""
    a = np.full((lado, lado, 3), 235, np.uint8)
    if linha_bancada is not None:
        # cinza MEDIO de proposito: tem que gerar borda forte, mas NAO entrar na
        # mascara do produto (que pega < 120), senao a silhueta atravessa a imagem.
        # DUAS linhas, como numa bancada de verdade (o tampo e a face de baixo):
        # o juiz exige 2 bordas concordantes pra cravar a escala.
        a[linha_bancada:linha_bancada + 6, :, :] = 150
        a[linha_bancada + 40:linha_bancada + 46, :, :] = 150
    x0 = lado // 2 - larg_prod // 2
    y0 = base_y - alt_prod
    a[y0:base_y, x0:x0 + larg_prod, :] = 40
    p = tmp_path / nome
    Image.fromarray(a).save(p, quality=97)
    return str(p), (x0, y0, x0 + larg_prod - 1, base_y - 1)


@pytest.fixture
def mascara(monkeypatch):
    """Faz a mascara ser exatamente o retangulo escuro, sem depender do BiRefNet."""
    def falsa(im):
        g = np.array(im.convert("L"))
        return Image.fromarray(((g < 120) * 255).astype(np.uint8))
    monkeypatch.setattr(J.cutout, "alpha_mask", falsa)


def test_forma_certa_e_escala_certa_aprova(tmp_path, mascara):
    # produto 34x18 (1,89) contra movel de ~895 px -> escala ~0,38
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=180, base_y=1100, linha_bancada=1100 - 895)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "APROVA", r
    assert r["forma"]["ok"] and r["escala"]["ok"]


def test_produto_esticado_reprova(tmp_path, mascara):
    # mesma altura, corpo mais estreito -> forma 2,43
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=140, base_y=1100, linha_bancada=205)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "REPROVA"
    assert "forma" in r["motivo"]


def test_escala_grande_demais_reprova(tmp_path, mascara):
    # forma certa, mas o movel e baixo demais -> lixeira ocupa muito
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=180, base_y=1100, linha_bancada=1100 - 600)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "REPROVA"
    assert "escala" in r["motivo"]


def test_tampa_aberta_recusa(tmp_path, mascara):
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=180, base_y=1100, linha_bancada=205)
    r = J.julgar(p, 34, 18, tampa="aberta")
    assert r["veredito"] == "NAO_MEDIDO"
    assert "tampa" in r["motivo"].lower()


def test_produto_cortado_pelo_quadro_recusa(tmp_path, mascara):
    # produto encostando na base do quadro
    p, _ = _cena(tmp_path, alt_prod=400, larg_prod=210, base_y=1200, linha_bancada=205)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "NAO_MEDIDO"
    assert "cortado" in r["motivo"]


def test_objeto_errado_recusa(tmp_path, mascara):
    # silhueta larga e baixa: nao e a lixeira (foi o caso da capa-v8, que pegou o armario)
    p, _ = _cena(tmp_path, alt_prod=300, larg_prod=600, base_y=1100, linha_bancada=205)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "NAO_MEDIDO"
    assert "detector" in r["motivo"] or "outra coisa" in r["motivo"]


def test_bancada_fora_do_quadro_recusa_e_orienta(tmp_path, mascara):
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=180, base_y=1100, linha_bancada=None)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "NAO_MEDIDO"
    assert "ABERTA" in r["escala"]["motivo"]


def test_forma_reprovada_manda_mesmo_sem_escala(tmp_path, mascara):
    """Forma se mede sozinha: reprova mesmo quando a bancada nao aparece."""
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=140, base_y=1100, linha_bancada=None)
    r = J.julgar(p, 34, 18)
    assert r["veredito"] == "REPROVA"
    assert "forma" in r["motivo"]


def test_alvos_saem_das_medidas_reais(tmp_path, mascara):
    """5L e 8L tem alvos diferentes — foi o erro que fez a v8 sair com cara de 5L."""
    p, _ = _cena(tmp_path, alt_prod=340, larg_prod=180, base_y=1100, linha_bancada=205)
    assert J.julgar(p, 34, 18)["alvos"] == {"forma": 1.89, "escala": 0.38}
    assert J.julgar(p, 25, 18)["alvos"] == {"forma": 1.39, "escala": 0.28}
