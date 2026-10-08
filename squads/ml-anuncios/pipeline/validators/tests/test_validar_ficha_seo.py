#!/usr/bin/env python3
"""Testes da regra Marca/Modelo (Almir 07/10/2026; Marca revista em 08/10). Stdlib unittest."""
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
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel", "Lixo Quarto Escritório", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_com_palavra_chave_bloqueia(self):
        # regra de 08/10: Marca = so o fornecedor (ou a marca propria), sem cauda longa
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel Higiênica Antiodor", "Quarto", DESC)
        self.assertIn("MARCA_FORA_DO_PADRAO", codigos(e))

    def test_marca_de_outro_fornecedor_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Brinox", "Quarto", DESC)
        self.assertIn("MARCA_FORA_DO_PADRAO", codigos(e))

    def test_marca_maiuscula_diferente_ok(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "VIEL", "Quarto", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_propria_em_produto_de_fornecedor_ok(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_propria_libera_loja_na_descricao(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Terra Casa Decor", "Quarto",
                          DESC + " Da marca Terra Casa Decor.")
        self.assertEqual(codigos(e), [])

    def test_palavra_do_titulo_repetida_no_modelo_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel", "Lixeira Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_acento_nao_engana_repeticao(self):
        e = validar_ficha("VIE-1066-PAI", "Lixeira Aço Inox 5L Pedal Cozinha Banheiro Higiênica",
                          "Viel", "Higienica Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_modelo_acima_de_30_so_avisa(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel", "Quarto Escritório Consultório Antiodor", DESC)
        self.assertEqual(codigos(e), [])
        self.assertIn("WARN_MODELO_LONGO", codigos(e, so_bloqueio=False))

    def test_vazios_bloqueiam(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "", "", DESC)
        self.assertIn("MARCA_VAZIA", codigos(e))
        self.assertIn("MODELO_VAZIO", codigos(e))

    def test_prefixo_desconhecido_bloqueia(self):
        e = validar_ficha("KOU_1", TIT, "Kou Algo", "Quarto", DESC)
        self.assertIn("FORNECEDOR_DESCONHECIDO", codigos(e))

    def test_loja_na_descricao_com_marca_do_fornecedor_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel", "Quarto", DESC + " Terra Casa Decor.")
        self.assertIn("DESCRICAO_CITA_LOJA", codigos(e))

    def test_loja_no_titulo_sempre_bloqueia(self):
        e = validar_ficha("MDA_9", "Quadro Terra Casa Decor Sala", "Terra Casa Decor", "Arte Moderna",
                          "Quadro da Terra Casa Decor.")
        self.assertIn("TITULO_CITA_LOJA", codigos(e))

    def test_mundiart_ok(self):
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala Abstrato Grande", "Terra Casa Decor",
                          "Arte Moderna Parede", "Um quadro da marca Terra Casa Decor para sua casa.")
        self.assertEqual(codigos(e), [])

    def test_mundiart_marca_do_fornecedor_nao_existe_so_a_propria(self):
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


class TestMarcaPropriaSemFornecedor(unittest.TestCase):
    # 08/10: com a marca propria, o nome do fornecedor nao pode sobrar no texto
    def test_marca_propria_com_fornecedor_na_descricao_bloqueia(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + "\n- Marca: Viel")
        self.assertIn("FORNECEDOR_NA_DESCRICAO", codigos(e))

    def test_marca_propria_sem_fornecedor_ok(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + "\n- Marca: Terra Casa Decor")
        self.assertEqual(codigos(e), [])

    def test_palavra_que_contem_o_nome_nao_engana(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + " Vielas e becos.")
        self.assertEqual(codigos(e), [])

    def test_marca_do_fornecedor_pode_citar_o_fornecedor(self):
        e = validar_ficha("VIE-1066-PAI", TIT, "Viel", "Quarto", DESC + "\n- Marca: Viel")
        self.assertEqual(codigos(e), [])
