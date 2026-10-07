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


class TestCopyDaRenata(unittest.TestCase):
    """A guarda cobria SO o overlay das fotos — titulo e descricao da Renata
    passavam sem trava nenhuma (achado da higiene de prompts, 2026-07-19).
    O comprador le a descricao antes de comprar: claim falso ali gera devolucao
    igual (ou pior) que na foto.
    """

    def copy_base(self):
        return {
            "titles": [
                {"texto": "Lixeira Inox 12L Pedal Antiodor Cozinha", "recomendado": True},
            ],
            "description": {
                "bloco_1_abertura": "Tem detalhes que mudam a sensacao da casa.",
                "bloco_2_specs": "- Material: aco inox\n- Capacidade: 12 litros",
                "bloco_3_features_beneficios": "- Pedal silencioso: mais higiene no dia a dia",
            },
        }

    def test_claim_falso_na_descricao_bloqueia(self):
        copy = self.copy_base()
        copy["description"]["bloco_2_specs"] += "\n- Acompanha balde interno removivel"
        blocks, _ = validar_claims(brief_base(), copy_doc=copy)
        self.assertTrue(any(c.startswith("CLAIM_FALSO") for c, _ in blocks),
                        f"deveria bloquear claim falso na descricao; veio {blocks}")

    def test_claim_falso_no_titulo_bloqueia(self):
        copy = self.copy_base()
        copy["titles"].append({"texto": "Lixeira Inox 12L com Balde Interno", "recomendado": False})
        blocks, _ = validar_claims(brief_base(), copy_doc=copy)
        self.assertTrue(any(c.startswith("CLAIM_FALSO") for c, _ in blocks),
                        f"deveria bloquear claim falso no titulo; veio {blocks}")

    def test_limitacao_declarada_na_descricao_passa(self):
        """'nao vem com balde interno' e transparencia, nao claim — nao pode bloquear."""
        copy = self.copy_base()
        copy["description"]["bloco_3_features_beneficios"] += (
            "\n\nEste modelo nao vem com balde interno removivel."
        )
        blocks, _ = validar_claims(brief_base(), copy_doc=copy)
        self.assertEqual([], [b for b in blocks if b[0].startswith("CLAIM_FALSO")],
                         f"disclosure honesto nao pode bloquear; veio {blocks}")

    def test_copy_limpa_passa(self):
        blocks, _ = validar_claims(brief_base(), copy_doc=self.copy_base())
        self.assertEqual([], [b for b in blocks if "COPY" in b[0]])

    def test_sem_copy_continua_funcionando(self):
        """Retrocompatibilidade: chamar sem copy_doc nao pode mudar nada."""
        blocks, warns = validar_claims(brief_base())
        self.assertEqual([], blocks)
