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


class TestAnguloCameraNaoEEscala(unittest.TestCase):
    """'3/4' e vocabulario de ANGULO DE CAMERA (vista 3/4), nao razao de tamanho.

    Bug encontrado na higiene de prompts (2026-07-19): o photo-templates.md manda
    'lixeira sempre na DIAGONAL (vista 3/4)' na CAPA, e o linter bloqueava por
    RATIO_ESCALA — travando a geracao de quem seguia o proprio template.
    """

    def test_vista_3_4_nao_bloqueia(self):
        i = lint_prompt("lixeira na diagonal (vista 3/4), altura da bancada de 90 cm", edit=False)
        self.assertNotIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_angulo_3_4_diagonal_nao_bloqueia(self):
        i = lint_prompt("3/4 DIAGONAL levemente abaixo (hero angle), escala do produto no ambiente", edit=False)
        self.assertNotIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_three_quarter_view_nao_bloqueia(self):
        i = lint_prompt("three-quarter view of the bin next to the vanity height", edit=False)
        self.assertNotIn("RATIO_ESCALA", codes(i, "BLOCK"))

    def test_escala_real_continua_bloqueando(self):
        """A correcao nao pode abrir buraco: razao de TAMANHO segue bloqueada."""
        i = lint_prompt("vista 3/4 da lixeira, com 1/3 da altura da bancada", edit=False)
        self.assertIn("RATIO_ESCALA", codes(i, "BLOCK"))


class TestMacroYesNaoEUCamera(unittest.TestCase):
    """'Macro-Yes' e NOME DE SLOT (MECLABS), nao termo de camera.

    Bug encontrado na higiene de prompts (2026-07-22), mesma familia do 'vista 3/4':
    o slot 10 do storyselling-framework.md se chama 'Macro-Yes + CTA' e o regex
    \\bmacro\\b acusava CAMERA_INFLA em todo prompt que citasse o nome do slot.
    Aviso que nasce errado ensina o time a ignorar aviso.
    """

    def test_nome_do_slot_nao_avisa(self):
        i = lint_prompt("foto 10, slot Macro-Yes + CTA final, wide shot at eye level", edit=False)
        self.assertNotIn("CAMERA_INFLA", codes(i, "WARN"))

    def test_macro_yes_minusculo_nao_avisa(self):
        i = lint_prompt("cena da macro-yes com CTA, camera na altura dos olhos", edit=False)
        self.assertNotIn("CAMERA_INFLA", codes(i, "WARN"))

    def test_macro_de_camera_continua_avisando(self):
        """A correcao nao pode abrir buraco: 'macro' de lente segue avisando."""
        i = lint_prompt("macro shot of the pedal hinge", edit=False)
        self.assertIn("CAMERA_INFLA", codes(i, "WARN"))

    def test_slot_e_macro_de_camera_no_mesmo_prompt_avisa(self):
        i = lint_prompt("slot Macro-Yes, extreme macro lens on the steel body", edit=False)
        self.assertIn("CAMERA_INFLA", codes(i, "WARN"))
