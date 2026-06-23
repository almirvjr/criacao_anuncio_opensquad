#!/usr/bin/env python3
"""Testes do gate de fidelidade do produto (pipeline produto-travado, 23/06).
Proveniencia (composicao) + disaster (one-shot). Stdlib unittest."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
# fidelity.py vive em skills/image-ai-generator/scripts (5 niveis acima)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "image-ai-generator", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "skills", "image-overlay", "scripts"))

import fidelity  # noqa: E402
from PIL import Image  # noqa: E402


class TestProvenancia(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.img = os.path.join(self.d, "foto-09.jpg")
        Image.new("RGB", (1200, 1200), (240, 240, 240)).save(self.img)
        self.man = os.path.join(self.d, "SKU.json")
        json.dump({"assets": {"aberto": {"sha256": "abc123", "png": "p.png"}}},
                  open(self.man, "w"))

    def _sidecar(self, sha):
        json.dump({"baseline_sha256": sha}, open(self.img + ".lock.json", "w"))

    def test_sem_sidecar_reprova(self):
        r = fidelity.verify_provenance(self.img, self.man)
        self.assertFalse(r["ok"])

    def test_sha_valido_passa(self):
        self._sidecar("abc123")
        self.assertTrue(fidelity.verify_provenance(self.img, self.man)["ok"])

    def test_sha_invalido_reprova(self):
        self._sidecar("zzz")
        self.assertFalse(fidelity.verify_provenance(self.img, self.man)["ok"])


class TestDisaster(unittest.TestCase):
    """Usa PNG RGBA com alpha real (evita BiRefNet no teste)."""
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def _png(self, frac_area):
        # produto = retangulo opaco central cobrindo frac_area da imagem
        im = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        import math
        side = int(1000 * math.sqrt(frac_area))
        o = (1000 - side) // 2
        for x in range(o, o + side):
            for y in range(o, o + side):
                im.putpixel((x, y), (180, 180, 185, 255))
        p = os.path.join(self.d, f"p_{int(frac_area*100)}.png")
        im.save(p)
        return p

    def test_produto_presente_passa(self):
        self.assertTrue(fidelity.disaster_check(self._png(0.30))["ok"])

    def test_produto_minusculo_reprova(self):
        self.assertFalse(fidelity.disaster_check(self._png(0.005))["ok"])

    def test_produto_ocupa_tudo_reprova(self):
        self.assertFalse(fidelity.disaster_check(self._png(0.99))["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
