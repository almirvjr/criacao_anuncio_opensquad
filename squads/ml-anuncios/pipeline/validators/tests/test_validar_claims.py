#!/usr/bin/env python3
"""Testes da guarda anti-claim-falso (Fase 2). Stdlib unittest."""
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from validar_claims import (  # noqa: E402
    validar_claims, derivar_termo_policiado, afirmado, declarado,
)


def brief_base():
    """Brief com a limitacao 'sem balde interno' declarada na foto 9."""
    return {
        "dados_produto": {"caracteristicas": {"valor": ["Acionamento por pedal", "Corpo em aco inox"]}},
        "limitacoes": [
            {"texto": "Modelo sem balde interno (usa saco comum)", "fonte": "ficha", "disclosure_foto": 9},
        ],
        "briefing_fotos": [
            {"numero": 9, "funcao": "SOBRECORRECAO_ANSIEDADE", "headline": "Compra sem surpresas",
             "selos_visuais": [
                 {"texto": "Corpo em aco inox"},
                 {"texto": "Compativel com saco comum"},
                 {"texto": "Modelo sem balde interno"},
                 {"texto": "Pedal pratico"},
             ]},
        ],
    }


class TestDerivacao(unittest.TestCase):
    def test_deriva_ausencia(self):
        termo, eh_aus = derivar_termo_policiado("Modelo sem balde interno (usa saco comum)")
        self.assertEqual(termo, "balde interno")
        self.assertTrue(eh_aus)

    def test_nao_vem_com(self):
        termo, eh_aus = derivar_termo_policiado("Nao vem com balde")
        self.assertEqual(termo, "balde")
        self.assertTrue(eh_aus)

    def test_sem_negacao(self):
        termo, eh_aus = derivar_termo_policiado("Haste do pedal em nylon")
        self.assertFalse(eh_aus)


class TestAfirmadoNegado(unittest.TestCase):
    def test_afirmado(self):
        self.assertTrue(afirmado("balde interno", "lixeira com balde interno removivel"))

    def test_negado_nao_e_afirmado(self):
        self.assertFalse(afirmado("balde interno", "modelo sem balde interno"))

    def test_declarado(self):
        self.assertTrue(declarado("balde interno", "modelo sem balde interno"))
        self.assertFalse(declarado("balde interno", "com balde interno"))


class TestGuarda(unittest.TestCase):
    def test_brief_correto_passa(self):
        blocks, _ = validar_claims(brief_base())
        self.assertEqual(blocks, [], f"deveria passar: {blocks}")

    def test_claim_falso_bloqueia(self):
        b = brief_base()
        # foto 6 afirma o balde que o produto NAO tem
        b["briefing_fotos"].append(
            {"numero": 7, "funcao": "DETALHE_TECNICO", "headline": "Vem com balde interno removivel"})
        blocks, _ = validar_claims(b)
        self.assertTrue(any(c == "CLAIM_FALSO" for c, _ in blocks),
                        f"esperava CLAIM_FALSO; veio {[c for c,_ in blocks]}")

    def test_limitacao_nao_declarada_bloqueia(self):
        b = brief_base()
        # remove o selo de transparencia -> foto 9 nao declara mais a limitacao
        b["briefing_fotos"][0]["selos_visuais"] = [
            {"texto": "Corpo em aco inox"}, {"texto": "Pedal pratico"},
        ]
        blocks, _ = validar_claims(b)
        self.assertTrue(any(c == "LIMITACAO_NAO_DECLARADA" for c, _ in blocks))

    def test_feature_alto_risco_gera_warn(self):
        b = brief_base()
        # afirma 'sensor' que nao consta em caracteristicas nem em limitacoes
        b["briefing_fotos"].append(
            {"numero": 5, "funcao": "CLAREZA_ABSOLUTA", "headline": "Abertura com sensor automatico"})
        blocks, warns = validar_claims(b)
        self.assertTrue(any(c == "CLAIM_RISCO_NAO_CONFIRMADO" for c, _ in warns))

    def test_disclosure_negado_conta_como_declarado(self):
        # a propria frase "sem balde interno" no selo declara a limitacao (nao e claim)
        blocks, _ = validar_claims(brief_base())
        self.assertFalse(any(c == "CLAIM_FALSO" for c, _ in blocks))


if __name__ == "__main__":
    unittest.main(verbosity=2)
