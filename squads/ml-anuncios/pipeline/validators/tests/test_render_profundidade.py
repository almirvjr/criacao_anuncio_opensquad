#!/usr/bin/env python3
"""Testes da COTA DE PROFUNDIDADE na foto tecnica (2026-07-22).

Ate aqui o render_faixa.py so desenhava altura e largura — o campo
`dim_profundidade` existia nos templates e no step-07 e NUNCA era lido
(o step mandava "deixar vazio"). Decisao do Almir em 22/07: implementar.

Usa CUTOUT_DISABLE=1 (heuristica de canto, sem BiRefNet/OOM), igual ao
test_framing_gate.py. Stdlib unittest.
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

os.environ["CUTOUT_DISABLE"] = "1"

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "image-overlay", "scripts"))

import render_faixa  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W = H = 1200
BG = (255, 255, 255)


def base_com_produto(x0=430, x1=700, top=250, bottom=620):
    im = Image.new("RGB", (W, H), BG)
    ImageDraw.Draw(im).rectangle([x0, top, x1, bottom], fill=(40, 40, 40))
    return im


def _cfg(**extra):
    c = {"dim_altura": "43 cm", "dim_largura": "28 cm"}
    c.update(extra)
    return c


def tinta_na_direita(img, x_produto_dir=700, topo=250, base=620):
    """Conta pixels marcados na faixa a DIREITA do produto (onde a cota entra)."""
    px = img.load()
    n = 0
    for y in range(max(0, topo - 60), min(H, base + 60)):
        for x in range(x_produto_dir + 12, W - 20):
            if px[x, y] != BG:
                n += 1
    return n


def render_tecnica(cfg, img=None):
    img = img or base_com_produto()
    draw = ImageDraw.Draw(img)
    buf = io.StringIO()
    with redirect_stdout(buf):
        render_faixa.draw_tecnica(img, draw, cfg)
    return img, buf.getvalue()


class TestProfundidadeOptIn(unittest.TestCase):
    def test_sem_o_campo_nada_muda_a_direita(self):
        """Comportamento antigo intacto: sem dim_profundidade, nada e desenhado ali."""
        img, _ = render_tecnica(_cfg())
        self.assertEqual(tinta_na_direita(img), 0)

    def test_com_o_campo_desenha_a_direita(self):
        img, _ = render_tecnica(_cfg(dim_profundidade="28 cm"))
        self.assertGreater(tinta_na_direita(img), 200)

    def test_valor_vazio_nao_desenha(self):
        """`dim_profundidade: ""` (produto redondo / nao_aplicavel) = nao desenha."""
        img, _ = render_tecnica(_cfg(dim_profundidade=""))
        self.assertEqual(tinta_na_direita(img), 0)


class TestProfundidadeNosTresEstilos(unittest.TestCase):
    def test_os_tres_estilos_desenham(self):
        for estilo in ("modelo", "cotas", "finas"):
            with self.subTest(estilo=estilo):
                img, _ = render_tecnica(_cfg(dim_profundidade="28 cm", dim_style=estilo))
                self.assertGreater(tinta_na_direita(img), 200, f"estilo {estilo} nao desenhou")


class TestProfundidadeSemEspaco(unittest.TestCase):
    def test_produto_colado_na_direita_avisa_e_nao_quebra(self):
        """Sem espaco pra cota: avisa no log em vez de sumir calado ou estourar."""
        img = base_com_produto(x0=430, x1=1150)
        img, log = render_tecnica(_cfg(dim_profundidade="28 cm"), img=img)
        self.assertIn("profundidade", log.lower())
        self.assertEqual(img.size, (W, H))

    def test_cota_nao_estoura_a_borda_do_canvas(self):
        """Produto largo mas com folga: a cota tem que caber dentro da margem."""
        img = base_com_produto(x0=430, x1=980)
        img, _ = render_tecnica(_cfg(dim_profundidade="28 cm"))
        px = img.load()
        for y in range(H):
            for x in range(W - 12, W):
                self.assertEqual(px[x, y], BG, f"tinta na borda em ({x},{y})")


class TestCotaCortadaAvisa(unittest.TestCase):
    """Bug PRE-EXISTENTE achado ao validar a profundidade (22/07): produto colado
    na borda faz a cota de altura/largura ser desenhada FORA do canvas e sumir sem
    erro nenhum. Nao se reposiciona (mudaria fotos aprovadas) — avisa."""

    def test_produto_colado_embaixo_avisa(self):
        img = base_com_produto(top=200, bottom=1150)
        _, log = render_tecnica(_cfg(), img=img)
        self.assertIn("largura", log.lower())
        self.assertIn("AVISO", log)

    def test_produto_colado_na_esquerda_avisa(self):
        img = base_com_produto(x0=20, x1=700)
        _, log = render_tecnica(_cfg(), img=img)
        self.assertIn("altura", log.lower())

    def test_produto_com_folga_nao_avisa(self):
        _, log = render_tecnica(_cfg())
        self.assertNotIn("AVISO", log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
