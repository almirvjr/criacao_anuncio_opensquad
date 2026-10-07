#!/usr/bin/env python3
"""Testes da regra Marca/Modelo (Almir 07/10/2026). Stdlib unittest."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validar_ficha_seo import fornecedor_do_sku, validar_ficha, titulo_do_copy  # noqa: E402

TIT = "Lixeira Inox 5L com Pedal e Tampa para Cozinha e Banheiro"
DESC = "Lixeira de inox com pedal para o dia a dia da casa."


def codigos(erros, so_bloqueio=True):
    return [c for c, _ in erros if not (so_bloqueio and c.startswith("WARN"))]


class TestFornecedor(unittest.TestCase):
    def test_prefixos(self):
        self.assertEqual(fornecedor_do_sku("VIE-1066-PAI"), "Viel")
        self.assertEqual(fornecedor_do_sku("MMP_123"), "Passerini")
        self.assertEqual(fornecedor_do_sku("MDA_9"), "Terra Casa Decor")
        self.assertIsNone(fornecedor_do_sku("KOU_1"))


class TestFicha(unittest.TestCase):
    def test_viel_ok(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica Antiodor", "Lixo Quarto Escritório", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_sem_fornecedor_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Lixeira Higiênica Viel", "Quarto", DESC)
        self.assertIn("MARCA_SEM_FORNECEDOR", codigos(e))

    def test_palavra_do_titulo_repetida_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Lixeira Inox", "Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_acento_nao_engana_repeticao(self):
        e = validar_ficha("VIE-1066-PAI", "Lixeira Aço Inox 5L Pedal Cozinha Banheiro Higiênica",
                          "Viel Higienica", "Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_marca_e_modelo_nao_repetem_entre_si(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Escritório", "Escritório Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_MARCA_MODELO", codigos(e))

    def test_acima_de_30_so_avisa(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica Antiodor Escritório", "Quarto", DESC)
        self.assertEqual(codigos(e), [])
        self.assertIn("WARN_MARCA_LONGA", codigos(e, so_bloqueio=False))

    def test_vazios_bloqueiam(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "", "", DESC)
        self.assertIn("MARCA_VAZIA", codigos(e))
        self.assertIn("MODELO_VAZIO", codigos(e))

    def test_prefixo_desconhecido_bloqueia(self):
        e = validar_ficha("KOU_1", TIT, "Kou Algo", "Quarto", DESC)
        self.assertIn("FORNECEDOR_DESCONHECIDO", codigos(e))

    def test_loja_na_descricao_de_nao_mundiart_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica", "Quarto", DESC + " Terra Casa Decor.")
        self.assertIn("DESCRICAO_CITA_LOJA", codigos(e))

    def test_loja_no_titulo_sempre_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Terra Casa Decor Sala", "Terra Casa Decor", "Arte Moderna",
                          "Quadro da Terra Casa Decor.")
        self.assertIn("TITULO_CITA_LOJA", codigos(e))

    def test_mundiart_ok(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala Abstrato Grande", "Terra Casa Decor",
                          "Arte Moderna Parede", "Um quadro da marca Terra Casa Decor para sua casa.")
        self.assertEqual(codigos(e), [])

    def test_mundiart_marca_com_palavra_chave_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala", "Terra Casa Decor Arte", "Parede",
                          "Marca Terra Casa Decor.")
        self.assertIn("MARCA_MUNDIART", codigos(e))

    def test_mundiart_descricao_sem_marca_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala", "Terra Casa Decor", "Parede", "Quadro lindo.")
        self.assertIn("DESCRICAO_SEM_MARCA_PROPRIA", codigos(e))


class TestTitulo(unittest.TestCase):
    def test_usa_titulo_final_quando_existe(self):
        doc = {"titulo_final": "Escolhido Pelo Almir",
               "titles": [{"texto": "Recomendado", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "Escolhido Pelo Almir")

    def test_cai_no_recomendado(self):
        doc = {"titles": [{"texto": "A", "recomendado": False}, {"texto": "B", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "B")


if __name__ == "__main__":
    unittest.main()
