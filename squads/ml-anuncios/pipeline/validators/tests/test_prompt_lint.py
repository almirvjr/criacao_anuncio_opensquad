#!/usr/bin/env python3
"""Testes da trava de boas praticas do prompt Nano Banana. Stdlib unittest."""
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from validar_prompt_nano import lint_prompt  # noqa: E402


def codes(issues, nivel=None):
    return [c for n, c, _ in issues if nivel is None or n == nivel]


class TestRatioEscala(unittest.TestCase):
    def test_fracao_na_1a_geracao_bloqueia(self):
        i = lint_prompt("a small can, 1/3 the height of the vanity", edit=False)
        self.assertIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_one_third_bloqueia(self):
        i = lint_prompt("the can reaches one third of the vanity height", edit=False)
        self.assertIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_porcentagem_de_altura_bloqueia(self):
        i = lint_prompt("the can is about 28% of the vanity height", edit=False)
        self.assertIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_em_edicao_e_so_aviso(self):
        i = lint_prompt("make the can smaller, about one quarter of the vanity height", edit=True)
        self.assertNotIn("RATIO_ESCALA", codes(i, "BLOCK"))
        self.assertIn("RATIO_ESCALA_EDIT", codes(i, "WARN"))

    def test_fracao_sem_contexto_de_escala_nao_dispara(self):
        # "1/3" sem palavra de tamanho perto -> nao e claim de escala
        i = lint_prompt("split the frame 1/3 to 2/3 between two color swatches", edit=False)
        self.assertNotIn("RATIO_ESCALA", codes(i))


class TestJsonCru(unittest.TestCase):
    def test_json_bloqueia(self):
        i = lint_prompt('{"subject": "trash can", "scene": "bathroom"}', edit=False)
        self.assertIn("JSON_CRU", codes(i, "BLOCK"))

    def test_prosa_passa(self):
        i = lint_prompt("a stainless trash can in a bright bathroom, wide shot at eye level", edit=False)
        self.assertEqual(codes(i, "BLOCK"), [])


class TestCameraInfla(unittest.TestCase):
    def test_close_up_avisa(self):
        i = lint_prompt("extreme close-up of the pedal", edit=False)
        self.assertIn("CAMERA_INFLA", codes(i, "WARN"))

    def test_low_angle_avisa(self):
        i = lint_prompt("low-angle hero shot of the can", edit=False)
        self.assertIn("CAMERA_INFLA", codes(i, "WARN"))


class TestLimpo(unittest.TestCase):
    def test_prompt_bom_passa_limpo(self):
        bom = ("a slim stainless steel pedal trash can in a clean bathroom, standing on the floor "
               "beside a wood vanity, wide shot at standing eye level about 2 meters back, soft daylight")
        self.assertEqual(lint_prompt(bom, edit=False), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
