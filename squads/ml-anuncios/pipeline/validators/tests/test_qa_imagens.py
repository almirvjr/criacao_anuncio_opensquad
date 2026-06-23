#!/usr/bin/env python3
"""Testes do QA de imagens (Fase 4) — checagens puras + smoke. Stdlib unittest."""
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from qa_imagens import (  # noqa: E402
    check_dimensao, check_produto_presente, check_dourado, material_eh_inox,
    check_eixo, slot_do_arquivo, check_produto_fiel,
)
import json  # noqa: E402
import tempfile  # noqa: E402


class TestEixo(unittest.TestCase):
    def test_centralizado_ok(self):
        # bbox centrado: l=450 r=750 -> centro 600 = meio de 1200
        self.assertIsNone(check_eixo((450, 300, 750, 900), 1200))

    def test_fora_do_eixo_esquerda(self):
        # centro ~300, 25% a esquerda de 600
        e = check_eixo((150, 300, 450, 900), 1200)
        self.assertEqual(e[0], "FORA_DO_EIXO")
        self.assertIn("esquerda", e[1])

    def test_fora_do_eixo_direita(self):
        e = check_eixo((800, 300, 1100, 900), 1200)
        self.assertEqual(e[0], "FORA_DO_EIXO")
        self.assertIn("direita", e[1])

    def test_slot_do_arquivo(self):
        self.assertEqual(slot_do_arquivo("foto-01-capa.jpg"), 1)
        self.assertEqual(slot_do_arquivo("capa-5L-branco.jpg"), 1)
        self.assertEqual(slot_do_arquivo("foto-07.jpg"), 7)
        self.assertIsNone(slot_do_arquivo("ambientalizada-xyz.jpg"))


class TestDimensao(unittest.TestCase):
    def test_certo(self):
        self.assertIsNone(check_dimensao((1200, 1200)))

    def test_errado(self):
        e = check_dimensao((1024, 1024))
        self.assertEqual(e[0], "DIM_ERRADA")

    def test_quase(self):
        self.assertEqual(check_dimensao((1200, 1199))[0], "DIM_ERRADA")


class TestProdutoPresente(unittest.TestCase):
    def test_bbox_none(self):
        self.assertEqual(check_produto_presente(None, 1200, 1200)[0], "PRODUTO_AUSENTE")

    def test_produto_grande_ok(self):
        # bbox cobrindo ~1/4 da imagem -> presente
        self.assertIsNone(check_produto_presente((300, 300, 900, 900), 1200, 1200))

    def test_produto_minusculo_reprova(self):
        # bbox 10x10 num frame 1200x1200 = ~0.007% -> sumiu
        self.assertEqual(check_produto_presente((0, 0, 10, 10), 1200, 1200)[0], "PRODUTO_AUSENTE")


class TestDourado(unittest.TestCase):
    def test_dourado_bloqueia(self):
        self.assertEqual(check_dourado("dourado")[0], "COR_DOURADA")

    def test_ok_passa(self):
        self.assertIsNone(check_dourado("ok"))

    def test_neutro_passa(self):
        self.assertIsNone(check_dourado("neutro"))


class TestMaterialInox(unittest.TestCase):
    def test_detecta_inox(self):
        self.assertTrue(material_eh_inox({"dados_produto": {"material": {"valor": "Aco Inox / PP"}}}))

    def test_nao_inox(self):
        self.assertFalse(material_eh_inox({"dados_produto": {"material": {"valor": "Plastico PP"}}}))


class TestProdutoFiel(unittest.TestCase):
    """Proveniencia (rota composicao): sidecar .lock.json vs manifesto travado."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.img = os.path.join(self.d, "foto-09.jpg")
        open(self.img, "wb").close()  # arquivo dummy; check nao abre a imagem
        self.man = os.path.join(self.d, "SKU.json")
        json.dump({"assets": {"aberto": {"sha256": "abc123", "png": "x_aberto.png"}}},
                  open(self.man, "w"))

    def _sidecar(self, sha):
        json.dump({"baseline_sha256": sha}, open(self.img + ".lock.json", "w"))

    def test_sem_sidecar_nao_bloqueia(self):
        # foto one-shot legitima (sem proveniencia) -> None
        self.assertIsNone(check_produto_fiel(self.img, self.man))

    def test_sidecar_valido_passa(self):
        self._sidecar("abc123")
        self.assertIsNone(check_produto_fiel(self.img, self.man))

    def test_sidecar_sha_fora_do_manifesto_reprova(self):
        self._sidecar("0" * 64)
        e = check_produto_fiel(self.img, self.man)
        self.assertEqual(e[0], "PRODUTO_INFIEL")

    def test_sidecar_sem_manifesto_reprova(self):
        self._sidecar("abc123")
        e = check_produto_fiel(self.img, None)
        self.assertEqual(e[0], "PRODUTO_INFIEL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
