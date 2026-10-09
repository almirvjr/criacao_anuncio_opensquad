#!/usr/bin/env python3
"""Testes do montador de capas (esteira sem fotos, 07/10/2026)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from capas import url_ml, montar  # noqa: E402

BASE = "https://res.cloudinary.com/wa5lvi98/image/upload/"
TR = "c_pad,w_1200,h_1200,b_white,q_auto"


def res(pid, tags, ext="png", criado="2026-10-07T18:52:19+00:00"):
    return {"asset_id": pid, "public_id": pid, "tags": tags, "created_at": criado,
            "width": 1254, "height": 1254, "secure_url": f"{BASE}v1791399139/{pid}.{ext}"}


def anuncio(pai, skus):
    return {"pai_sku": pai, "variacoes": [{"sku": s, "cor": s[-2:]} for s in skus]}


class TestUrl(unittest.TestCase):
    def test_url_ml_jpg(self):
        self.assertEqual(url_ml(f"{BASE}v1/foto.jpg"), f"{BASE}{TR}/v1/foto.jpg")

    def test_url_ml_png_com_acento(self):
        u = f"{BASE}v1791386078/3405_Lixeira_Corpo_em_A%C3%A7o_Inox.png"
        self.assertEqual(url_ml(u), f"{BASE}{TR}/v1791386078/3405_Lixeira_Corpo_em_A%C3%A7o_Inox.jpg")

    def test_url_ml_idempotente(self):
        u = url_ml(f"{BASE}v1/foto.jpg")
        self.assertEqual(url_ml(u), u)

    def test_url_de_outra_nuvem_recusa(self):
        with self.assertRaises(ValueError):
            url_ml("https://res.cloudinary.com/outra/image/upload/v1/x.jpg")


class TestMontar(unittest.TestCase):
    def test_uma_capa_por_cor(self):
        rs = [res("a", ["capa-anuncio", "VIE-1066-3402-BR"]), res("b", ["VIE-1066-3405-PT", "capa-anuncio"])]
        capas, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])])
        self.assertEqual(erros, [])
        pv = capas["VIE-1066-PAI"]["picture_ids_por_variacao"]
        self.assertEqual([p["sku_variacao"] for p in pv], ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])
        self.assertEqual(pv[0]["picture_ids"], [f"{BASE}{TR}/v1791399139/a.jpg"])

    def test_sem_etiqueta_capa_ignora(self):
        rs = [res("a", ["VIE-1066-3402-BR"])]
        _, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR"])])
        self.assertTrue(any("VIE-1066-3402-BR" in e for e in erros))

    def test_sku_com_underscore_nao_casa_e_avisa_qual_falta(self):
        rs = [res("a", ["capa-anuncio", "VIE_1066_3402_BR"]), res("b", ["capa-anuncio", "VIE-1066-3405-PT"])]
        _, erros = montar(rs, [anuncio("VIE-1066-PAI", ["VIE-1066-3402-BR", "VIE-1066-3405-PT"])])
        self.assertEqual(len(erros), 1)
        self.assertIn("VIE-1066-3402-BR", erros[0])

    def test_mais_antiga_primeiro_e_teto_10(self):
        rs = [res(f"f{i:02d}", ["capa-anuncio", "S-1"], criado=f"2026-10-07T10:{i:02d}:00+00:00")
              for i in range(11, -1, -1)]
        capas, erros = montar(rs, [anuncio("P", ["S-1"])])
        self.assertTrue(any("mais de 10" in e for e in erros))
        self.assertTrue(capas["P"]["picture_ids_por_variacao"][0]["picture_ids"][0].endswith("/f00.jpg"))


class TestFotosExtras(unittest.TestCase):
    """Almir 09/10/2026: alem da capa, as outras fotos com a etiqueta do SKU tambem vao (capa primeiro)."""

    def test_capa_primeiro_depois_as_outras_do_sku(self):
        rs = [res("site_01", ["S-1"], criado="2026-10-09T19:56:08+00:00"),
              res("site_02", ["S-1"], criado="2026-10-09T19:56:09+00:00"),
              res("capa_01", ["S-1", "capa-anuncio"], criado="2026-10-09T20:20:41+00:00"),
              res("outro", ["S-2"])]
        capas, erros = montar(rs, [anuncio("P", ["S-1"])])
        self.assertEqual(erros, [])
        ids = capas["P"]["picture_ids_por_variacao"][0]["picture_ids"]
        self.assertEqual([u.rsplit("/", 1)[1] for u in ids], ["capa_01.jpg", "site_01.jpg", "site_02.jpg"])

    def test_sem_capa_continua_faltando_mesmo_com_outras_fotos(self):
        rs = [res("site_01", ["S-1"])]
        _, erros = montar(rs, [anuncio("P", ["S-1"])])
        self.assertTrue(any("falta capa" in e for e in erros))

    def test_extras_cortadas_em_10_sem_erro(self):
        rs = [res("capa", ["S-1", "capa-anuncio"])] + [
            res(f"x{i:02d}", ["S-1"], criado=f"2026-10-07T10:{i:02d}:00+00:00") for i in range(12)]
        capas, erros = montar(rs, [anuncio("P", ["S-1"])])
        self.assertEqual(erros, [])
        ids = capas["P"]["picture_ids_por_variacao"][0]["picture_ids"]
        self.assertEqual(len(ids), 10)
        self.assertTrue(ids[0].endswith("/capa.jpg"))


if __name__ == "__main__":
    unittest.main()
