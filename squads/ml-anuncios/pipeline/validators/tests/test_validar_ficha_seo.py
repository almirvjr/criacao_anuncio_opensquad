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
        self.assertEqual(fornecedor_do_sku("BEL-4006-PAI"), "Bellagio")

    def test_bellagio_nem_zanotti_no_titulo(self):
        tit = "Tigela de Melamina Funda 800ml para Servir"
        self.assertEqual(codigos(validar_ficha("BEL-4006-PAI", tit, "Terra Casa Decor", "Bowl Sopa Cereal", DESC)), [])
        for t in (tit + " Bellagio", tit + " Zanotti"):
            self.assertIn("TITULO_CITA_MARCA", codigos(validar_ficha("BEL-4006-PAI", t, "Terra Casa Decor", "Bowl", DESC)))


class TestFicha(unittest.TestCase):
    def test_viel_ok(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount", "Lixo Quarto Escritório", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_com_palavra_chave_bloqueia(self):
        # regra de 08/10: Marca = so o fornecedor (ou a marca propria), sem cauda longa
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount Higiênica Antiodor", "Quarto", DESC)
        self.assertIn("MARCA_FORA_DO_PADRAO", codigos(e))

    def test_marca_de_outro_fornecedor_bloqueia(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Brinox", "Quarto", DESC)
        self.assertIn("MARCA_FORA_DO_PADRAO", codigos(e))

    def test_marca_maiuscula_diferente_ok(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "PARAMOUNT", "Quarto", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_propria_em_produto_de_fornecedor_ok(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC)
        self.assertEqual(codigos(e), [])

    def test_marca_propria_libera_loja_na_descricao(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Terra Casa Decor", "Quarto",
                          DESC + " Da marca Terra Casa Decor.")
        self.assertEqual(codigos(e), [])

    def test_palavra_do_titulo_repetida_no_modelo_bloqueia(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount", "Lixeira Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_acento_nao_engana_repeticao(self):
        e = validar_ficha("PAR-1066-PAI", "Lixeira Aço Inox 5L Pedal Cozinha Banheiro Higiênica",
                          "Paramount", "Higienica Quarto", DESC)
        self.assertIn("PALAVRA_REPETIDA_TITULO", codigos(e))

    def test_modelo_acima_de_30_so_avisa(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount", "Quarto Escritório Consultório Antiodor", DESC)
        self.assertEqual(codigos(e), [])
        self.assertIn("WARN_MODELO_LONGO", codigos(e, so_bloqueio=False))

    def test_vazios_bloqueiam(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "", "", DESC)
        self.assertIn("MARCA_VAZIA", codigos(e))
        self.assertIn("MODELO_VAZIO", codigos(e))

    def test_prefixo_desconhecido_bloqueia(self):
        e = validar_ficha("KOU_1", TIT, "Kou Algo", "Quarto", DESC)
        self.assertIn("FORNECEDOR_DESCONHECIDO", codigos(e))

    def test_loja_na_descricao_liberada_mesmo_com_marca_do_fornecedor(self):
        # Almir 02/11/2026: a descricao pode citar a Terra Casa Decor em qualquer produto
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount", "Quarto", DESC + " Terra Casa Decor.")
        self.assertNotIn("DESCRICAO_CITA_LOJA", codigos(e))
        self.assertEqual([c for c in codigos(e) if not c.startswith("WARN")], [])

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
        self.assertIn("MARCA_TEM_QUE_SER_PROPRIA", codigos(e))

    def test_mundiart_descricao_nao_precisa_citar_a_marca(self):
        # 02/11/2026: a exigencia de apresentar como Terra Casa Decor caiu; a descricao pode citar, nao precisa
        e = validar_ficha("MDA_9", "Quadro Decorativo Sala", "Terra Casa Decor", "Parede", "Quadro lindo.")
        self.assertEqual(codigos(e), [])


class TestTitulo(unittest.TestCase):
    def test_usa_titulo_final_quando_existe(self):
        doc = {"titulo_final": "Escolhido Pelo Almir",
               "titles": [{"texto": "Recomendado", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "Escolhido Pelo Almir")

    def test_cai_no_recomendado(self):
        doc = {"titles": [{"texto": "A", "recomendado": False}, {"texto": "B", "recomendado": True}]}
        self.assertEqual(titulo_do_copy(doc), "B")


class TestMarcaPropriaSemFornecedor(unittest.TestCase):
    # 08/10: com a marca propria, o nome do fornecedor nao pode sobrar no texto
    def test_marca_propria_com_fornecedor_na_descricao_bloqueia(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + "\n- Marca: Paramount")
        self.assertIn("FORNECEDOR_NA_DESCRICAO", codigos(e))

    def test_marca_propria_sem_fornecedor_ok(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + "\n- Marca: Terra Casa Decor")
        self.assertEqual(codigos(e), [])

    def test_palavra_que_contem_o_nome_nao_engana(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Terra Casa Decor", "Quarto", DESC + " Paramountes e becos.")
        self.assertEqual(codigos(e), [])

    def test_marca_do_fornecedor_pode_citar_o_fornecedor(self):
        e = validar_ficha("PAR-1066-PAI", TIT, "Paramount", "Quarto", DESC + "\n- Marca: Paramount")
        self.assertEqual(codigos(e), [])


class TestRegras23Out(unittest.TestCase):
    # Almir 23/10: titulo sem marca/fornecedor; Material e Linha = palavras de busca novas; bloco com titulo
    COZY = "Prato Raso Refeição Plástico 25,7 cm Borda Alta Micro-ondas"

    def test_titulo_com_fornecedor_bloqueia(self):
        e = validar_ficha("PAR-1066-PAI", "Lixeira Paramount Inox 5L com Pedal", "Paramount", "Quarto", DESC)
        self.assertIn("TITULO_CITA_MARCA", codigos(e))

    def test_titulo_longo_com_submarca_bloqueia(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC,
                          outros_titulos=["Prato Raso Plástico Coza 25,7 cm Vendido por Unidade"])
        self.assertIn("TITULO_CITA_MARCA", codigos(e))

    def test_marca_propria_nao_barra_casa_no_titulo(self):
        e = validar_ficha("MDA-1-PAI", "Vaso Decorativo Cerâmica Casa Sala", "Terra Casa Decor", "Quarto",
                          DESC + " Da marca Terra Casa Decor.")
        self.assertNotIn("TITULO_CITA_MARCA", codigos(e))

    def test_material_e_linha_repetindo_titulo_bloqueia(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC,
                          material="Polipropileno Plástico", linha="Borda Alta")
        self.assertEqual(codigos(e).count("PALAVRA_REPETIDA_TITULO"), 2)

    def test_material_e_linha_novos_ok(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC,
                          material="Polipropileno Reciclável", linha="Cozy Infantil Área Gourmet")
        self.assertEqual(codigos(e), [])

    def test_material_real_igual_ao_titulo_na_1a_palavra_ok(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC, material="Plástico Reciclável")
        self.assertEqual(codigos(e), [])

    def test_nome_da_linha_no_titulo_bloqueia(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC, linha="Cozy Infantil",
                          outros_titulos=["Prato Raso Plástico Cozy 25,7 cm Vendido por Unidade"])
        self.assertIn("TITULO_CITA_LINHA", codigos(e))

    def test_nao_se_aplica_passa(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC, linha="não se aplica")
        self.assertEqual(codigos(e), [])

    def test_repeticao_entre_campos_so_avisa(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC, linha="Mesa Infantil")
        self.assertIn("WARN_REPETIDA_ENTRE_CAMPOS", codigos(e, so_bloqueio=False))
        self.assertEqual(codigos(e), [])

    def test_bloco_sem_titulo_bloqueia(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC,
                          blocos={"bloco_2_specs": "- Material: polipropileno\n- Diâmetro: 25,7 cm"})
        self.assertIn("BLOCO_SEM_TITULO", codigos(e))

    def test_bloco_com_titulo_ok(self):
        e = validar_ficha("BRI-coza18-PAI", self.COZY, "Brinox", "Mesa Posta", DESC,
                          blocos={"bloco_2_specs": "Especificações técnicas\n- Material: polipropileno"})
        self.assertEqual(codigos(e), [])


class TestRegraMarca02Nov(unittest.TestCase):
    # Almir 02/11/2026: BEL/MDA/VIE ou kit = Marca Terra Casa Decor e fornecedor some de tudo
    T = "Tigela de Melamina Funda 800ml para Servir"
    KIT = ["BRI-coza27-20641_3009-KTMASTER"]

    def test_bel_com_marca_bellagio_bloqueia(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Bellagio", "Bowl", DESC)
        self.assertIn("MARCA_TEM_QUE_SER_PROPRIA", codigos(e))

    def test_bel_tcd_com_bellagio_na_descricao_bloqueia(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC + " Linha Bellagio.")
        self.assertIn("FORNECEDOR_CITADO", codigos(e))
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC + " Zanotti Presentes.")
        self.assertIn("FORNECEDOR_CITADO", codigos(e))

    def test_bel_tcd_descricao_citando_a_loja_ok(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC + " Da Terra Casa Decor.")
        self.assertEqual(codigos(e), [])

    def test_bel_com_bellagio_no_modelo_ou_valor_da_ficha_bloqueia(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bellagio Bowl", DESC)
        self.assertIn("FORNECEDOR_CITADO", codigos(e))
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC,
                          valores={"por_variacao": "Bellagio Oceano"})
        self.assertIn("FORNECEDOR_CITADO", codigos(e))
        self.assertIn("por_variacao", [m for c, m in e if c == "FORNECEDOR_CITADO"][0])

    def test_acento_e_maiuscula_nao_enganam(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC + " BELLAGIO!")
        self.assertIn("FORNECEDOR_CITADO", codigos(e))

    def test_kit_de_brinox_com_marca_coza_bloqueia(self):
        e = validar_ficha("BRI-coza27-PAI", TIT, "Coza", "Mesa Posta", DESC, skus=self.KIT)
        self.assertIn("MARCA_TEM_QUE_SER_PROPRIA", codigos(e))

    def test_kit_de_brinox_tcd_com_brinox_no_texto_bloqueia(self):
        e = validar_ficha("BRI-coza27-PAI", TIT, "Terra Casa Decor", "Mesa Posta", DESC + " Brinox.", skus=self.KIT)
        self.assertIn("FORNECEDOR_CITADO", codigos(e))
        e = validar_ficha("BRI-coza27-PAI", TIT, "Terra Casa Decor", "Mesa Posta", DESC + " Coza.", skus=self.KIT)
        self.assertIn("FORNECEDOR_CITADO", codigos(e))

    def test_kit_de_brinox_tcd_limpo_ok(self):
        e = validar_ficha("BRI-coza27-PAI", TIT, "Terra Casa Decor", "Mesa Posta", DESC, skus=self.KIT)
        self.assertEqual(codigos(e), [])

    def test_brinox_sem_kit_marca_brinox_ok(self):
        e = validar_ficha("BRI-coza27-PAI", TIT, "Brinox", "Mesa Posta", DESC, skus=["BRI-coza27-20641_3009-BR"])
        self.assertEqual(codigos(e), [])

    def test_kit_e_detectado_no_pai_tambem(self):
        e = validar_ficha("BRI-x-KT2", TIT, "Brinox", "Mesa Posta", DESC)
        self.assertIn("MARCA_TEM_QUE_SER_PROPRIA", codigos(e))

    def test_titulo_com_tcd_continua_bloqueado(self):
        e = validar_ficha("BEL-4006-PAI", "Tigela Terra Casa Decor Servir", "Terra Casa Decor", "Bowl", DESC)
        self.assertIn("TITULO_CITA_LOJA", codigos(e))

    def test_proibidas_extras_do_hub(self):
        e = validar_ficha("BEL-4006-PAI", self.T, "Terra Casa Decor", "Bowl", DESC + " Fulano.",
                          proibidas_extra=["Fulano"])
        self.assertIn("FORNECEDOR_CITADO", codigos(e))


class TestMainYaml(unittest.TestCase):
    def test_valores_e_skus_do_yaml(self):
        from validar_ficha_seo import skus_do_copy, valores_da_ficha
        doc = {"pai_sku": "BRI-coza27-PAI", "attributes": {"MODEL": "Coza"},
               "por_variacao": {"BRI-coza27-20641_3009-KTMASTER": {"attributes": {"LINE": "Brinox"}}},
               "ficha_magalu": [{"nome": "Marca", "valor": "Viel"}]}
        self.assertIn("BRI-coza27-20641_3009-KTMASTER", skus_do_copy(doc))
        v = valores_da_ficha(doc)
        self.assertIn("Brinox", v["por_variacao"])
        self.assertIn("Viel", v["ficha_magalu"])



if __name__ == "__main__":
    unittest.main()