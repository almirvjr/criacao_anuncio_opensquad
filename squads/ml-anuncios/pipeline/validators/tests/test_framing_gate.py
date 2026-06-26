#!/usr/bin/env python3
"""Testes do gate de ENQUADRAMENTO da faixa-clara (2026-06-24).
Garante que o produto nunca invade o fade/faixa do render_faixa.py.
Usa CUTOUT_DISABLE=1 (heuristica de canto, sem BiRefNet/OOM). Stdlib unittest."""
import os
import sys
import tempfile
import unittest

os.environ["CUTOUT_DISABLE"] = "1"   # heuristica rapida; sem BiRefNet nos testes

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "image-overlay", "scripts"))

import framing_gate  # noqa: E402
import render_faixa  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W = H = 1200


def base_with_product(top, bottom, bg=(255, 255, 255), prod=(40, 40, 40),
                      x0=480, x1=720):
    """Canvas com um 'produto' (retangulo escuro) entre top e bottom."""
    im = Image.new("RGB", (W, H), bg)
    ImageDraw.Draw(im).rectangle([x0, top, x1, bottom], fill=prod)
    return im


class TestCheckClip(unittest.TestCase):
    def test_fade_top_e_674(self):
        self.assertEqual(framing_gate.fade_top(), 674)

    def test_produto_acima_do_fade_passa(self):
        im = base_with_product(200, 600)          # fundo 600 < 666
        r = framing_gate.check_clip(im)
        self.assertTrue(r["ok"], r["motivo"])

    def test_produto_dentro_do_fade_reprova(self):
        im = base_with_product(200, 700)          # fundo 700 > 674
        r = framing_gate.check_clip(im)
        self.assertFalse(r["ok"], r["motivo"])

    def test_produto_colado_no_limite_reprova_por_margem(self):
        im = base_with_product(200, 670)          # 670 > 666 (folga < 8)
        r = framing_gate.check_clip(im)
        self.assertFalse(r["ok"], r["motivo"])

    def test_sem_produto_reprova(self):
        im = Image.new("RGB", (W, H), (255, 255, 255))
        r = framing_gate.check_clip(im)
        self.assertFalse(r["ok"])


class TestAutofit(unittest.TestCase):
    def test_reenquadra_produto_cortado(self):
        im = base_with_product(200, 760)          # invade fade/faixa
        new, info = framing_gate.autofit(im)
        self.assertTrue(info["changed"], info)
        self.assertTrue(framing_gate.check_clip(new)["ok"],
                        "autofit deveria deixar o produto acima do fade")

    def test_noop_quando_ja_cabe(self):
        im = base_with_product(200, 600)
        new, info = framing_gate.autofit(im)
        self.assertFalse(info["changed"], info)

    def test_pula_fundo_nao_uniforme(self):
        # fundo em degrade -> cantos diferentes -> autofit nao mexe (gate ainda barra)
        im = Image.new("RGB", (W, H))
        px = im.load()
        for y in range(H):
            for x in range(W):
                px[x, y] = (200, 200, 200) if y < H // 2 else (120, 120, 120)
        ImageDraw.Draw(im).rectangle([480, 200, 720, 760], fill=(20, 20, 20))
        new, info = framing_gate.autofit(im)
        self.assertFalse(info["changed"])
        self.assertIn("uniforme", info["motivo"])


class TestRenderIntegration(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _cfg(self, base_img, **extra):
        bp = os.path.join(self.d, "base.jpg")
        base_img.save(bp)
        cfg = {"base": bp, "output": os.path.join(self.d, "out.jpg"),
               "eyebrow": "teste", "headline_ink": "Compre ",
               "headline_accent": "sem medo", "sub": "linha de apoio"}
        cfg.update(extra)
        return cfg

    def test_gate_barra_com_autofit_off(self):
        cfg = self._cfg(base_with_product(200, 760), autofit=False)
        with self.assertRaises(SystemExit) as cm:
            render_faixa.render(cfg)
        self.assertEqual(cm.exception.code, 3)
        self.assertFalse(os.path.exists(cfg["output"]))
        rej = os.path.join(self.d, "_rejeitado", "out.jpg")
        self.assertTrue(os.path.exists(rej), "deveria salvar em _rejeitado/")

    def test_autofit_salva_normalmente(self):
        cfg = self._cfg(base_with_product(200, 760))   # autofit default ON
        render_faixa.render(cfg)
        self.assertTrue(os.path.exists(cfg["output"]))

    def test_no_qa_ignora_gate(self):
        cfg = self._cfg(base_with_product(200, 760), autofit=False, no_qa=True)
        render_faixa.render(cfg)                        # nao deve sair com exit 3
        self.assertTrue(os.path.exists(cfg["output"]))


if __name__ == "__main__":
    unittest.main()
