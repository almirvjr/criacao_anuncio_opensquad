#!/usr/bin/env python3
"""
Testes da trava do brief (Fase 1). Stdlib unittest (sem dependencia de pytest).

Rodar:  python -m unittest discover -s squads/ml-anuncios/pipeline/validators/tests
"""
import copy
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from validar_brief import validate_brief, parse_meclabs, evidencia_ancorada, norm  # noqa: E402


def brief_valido():
    """Brief minimo COMPLETO que deve passar (sem checagem de ancora)."""
    fotos = []
    canon = [
        (1, "CAPA_PURPLE_COW", "+m+v", None),
        (2, "ANTES_DEPOIS", "+v-a", None),
        (3, "BADGE_TAMANHO", "-f", "O tamanho serve?"),
        (4, "ANTI_ANSIEDADE_MATERIAL", "-a", "E inox de verdade?"),
        (5, "LIFESTYLE_EMOCIONAL", "+m", None),
        (6, "CLAREZA_ABSOLUTA", "-a-f", "Vem com balde?"),
        (7, "DETALHE_TECNICO", "-f+v", None),
        (8, "LIFESTYLE_USO_REAL", "+m", None),
        (9, "SOBRECORRECAO_ANSIEDADE", "-a-f", None),
        (10, "MACRO_YES_CTA_FINAL", "+i+v", None),
    ]
    for numero, funcao, meclabs, obj in canon:
        f = {
            "numero": numero, "funcao": funcao, "objetivo_meclabs": meclabs,
            "objecao_alvo": obj, "headline": f"Headline {numero}",
            "subheadline": "sub", "badge": None, "cta": None,
        }
        if numero == 9:
            f["selos_visuais"] = [{"texto": f"selo {i}"} for i in range(5)]
        if numero == 10:
            f["selos_visuais"] = [{"texto": "Envio rapido"}]
        fotos.append(f)
    return {
        "pai_sku": "VIE_TESTE", "nome_base": "Lixeira teste",
        "confianca": "media", "cor_heroi": "Branco",
        "dados_produto": {"material": {"valor": "Inox"}},
        "limitacoes": [{"texto": "Sem balde interno", "fonte": "ficha",
                        "disclosure_foto": 5}],
        "diagnostico": {
            "dor_interna_mais_forte": {"texto": "quero casa bonita",
                                       "evidencias": ["como e linda"]},
            "only_factor": {"texto": "visual sofisticado barato"},
            "ansiedades": [{"texto": "parece fragil", "familia": "F1",
                            "impacto": "alto", "evidencia": "veio amassada"}],
            "linguagem_real_cliente": ["linda"],
            "persona": {"texto": "mulher 25-49"},
        },
        "escada_e_dai": [{"feature": "inox", "logico": "resistente",
                          "emocional": "casa cuidada"}],
        "briefing_fotos": fotos,
    }


class TestBriefValido(unittest.TestCase):
    def test_brief_completo_passa(self):
        erros = [e for e in validate_brief(brief_valido()) if not e[0].startswith("WARN")]
        self.assertEqual(erros, [], f"deveria passar, mas: {erros}")

    def test_sem_raw_gera_warn(self):
        erros = validate_brief(brief_valido())
        self.assertTrue(any(c == "WARN_SEM_RAW" for c, _ in erros))


class TestSlots(unittest.TestCase):
    def test_slot_faltando(self):
        b = brief_valido()
        b["briefing_fotos"] = b["briefing_fotos"][:9]  # tira o slot 10
        self._tem(b, "SLOT_FALTANDO")

    def test_funcao_errada(self):
        b = brief_valido()
        b["briefing_fotos"][2]["funcao"] = "QUALQUER_COISA"
        self._tem(b, "SLOT_FUNCAO_ERRADA")

    def test_meclabs_proibido(self):
        b = brief_valido()
        b["briefing_fotos"][0]["objetivo_meclabs"] = "+a"  # amplificar ansiedade
        self._tem(b, "MECLABS_PROIBIDO")

    def test_objecao_obrigatoria_no_slot_4(self):
        b = brief_valido()
        b["briefing_fotos"][3]["objecao_alvo"] = None
        self._tem(b, "SLOT_SEM_OBJECAO")

    def test_foto9_selos_de_menos(self):
        b = brief_valido()
        b["briefing_fotos"][8]["selos_visuais"] = [{"texto": "x"}]
        self._tem(b, "SELOS_QTD")

    def _tem(self, brief, code):
        erros = validate_brief(brief)
        self.assertTrue(any(c == code for c, _ in erros),
                        f"esperava erro {code}; veio: {[c for c,_ in erros]}")


class TestProvaSocial(unittest.TestCase):
    def _foto11(self):
        return {"numero": 11, "funcao": "PROVA_SOCIAL", "objetivo_meclabs": "+v-a",
                "headline": "Quem compra aprova", "subheadline": None,
                "badge": None, "cta": None,
                "selos_visuais": [{"texto": "Bem avaliado"}]}

    def test_prova_social_sem_review_real_reprova(self):
        b = brief_valido()
        b["briefing_fotos"].append(self._foto11())
        erros = validate_brief(b)
        self.assertTrue(any(c == "PROVA_SOCIAL_SEM_REVIEW" for c, _ in erros))

    def test_prova_social_com_flag_passa(self):
        b = brief_valido()
        b["briefing_fotos"].append(self._foto11())
        b["reviews_proprios_confirmados"] = True
        erros = [e for e in validate_brief(b) if not e[0].startswith("WARN")]
        self.assertEqual(erros, [], f"deveria passar: {erros}")

    def test_sem_foto11_continua_valido(self):
        # ausencia do slot opcional NAO reprova
        erros = [e for e in validate_brief(brief_valido()) if not e[0].startswith("WARN")]
        self.assertEqual(erros, [])

    def test_slot_12_e_extra(self):
        b = brief_valido()
        b["briefing_fotos"].append({"numero": 12, "funcao": "X", "objetivo_meclabs": "+m",
                                    "headline": "h"})
        erros = validate_brief(b)
        self.assertTrue(any(c == "SLOT_EXTRA" for c, _ in erros))


class TestLimitacoes(unittest.TestCase):
    def test_limitacoes_ausente_reprova(self):
        b = brief_valido()
        del b["limitacoes"]
        erros = validate_brief(b)
        self.assertTrue(any(c == "FALTA_CAMPO" for c, _ in erros))

    def test_limitacoes_vazia_sem_nota_reprova(self):
        b = brief_valido()
        b["limitacoes"] = []
        erros = validate_brief(b)
        self.assertTrue(any(c == "LIMITACOES_VAZIA" for c, _ in erros))

    def test_limitacoes_vazia_com_nota_passa(self):
        b = brief_valido()
        b["limitacoes"] = []
        b["limitacoes_nota"] = "Produto sem limitacao relevante: ficha completa, sem ponto fraco em reviews."
        erros = [e for e in validate_brief(b) if not e[0].startswith("WARN")]
        self.assertEqual(erros, [])


class TestEvidencia(unittest.TestCase):
    def test_ansiedade_sem_evidencia(self):
        b = brief_valido()
        b["diagnostico"]["ansiedades"][0]["evidencia"] = None
        erros = validate_brief(b)
        self.assertTrue(any(c == "ANSIEDADE_SEM_EVIDENCIA" for c, _ in erros))

    def test_ancora_pega_review_inventado(self):
        # raw_dir temporario com um review real; brief cita frase inventada.
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "MLB1.json"), "w", encoding="utf-8") as fh:
                fh.write('{"reviews":["a lixeira e muito linda fiel ao anuncio"]}')
            b = brief_valido()
            b["diagnostico"]["dor_interna_mais_forte"]["evidencias"] = ["frase totalmente inventada que nao existe"]
            erros = validate_brief(b, raw_dir=d)
            self.assertTrue(any(c == "EVIDENCIA_INVENTADA" for c, _ in erros))

    def test_ancora_aceita_review_real(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "MLB1.json"), "w", encoding="utf-8") as fh:
                fh.write('{"reviews":["a lixeira e muito linda, fiel ao anuncio"]}')
            b = brief_valido()
            b["diagnostico"]["dor_interna_mais_forte"]["evidencias"] = ["a lixeira e muito linda"]
            b["diagnostico"]["ansiedades"][0]["evidencia"] = "fiel ao anuncio"
            erros = [e for e in validate_brief(b, raw_dir=d) if not e[0].startswith("WARN")]
            self.assertEqual(erros, [], f"deveria passar: {erros}")


class TestUnidades(unittest.TestCase):
    def test_parse_meclabs(self):
        self.assertEqual(parse_meclabs("+v-a"), ["+v", "-a"])
        self.assertEqual(parse_meclabs("-a-f"), ["-a", "-f"])
        self.assertIsNone(parse_meclabs("+v xyz"))

    def test_ancora_split_reticencias(self):
        blob = norm("trecho um do meio trecho dois do fim")
        self.assertTrue(evidencia_ancorada("trecho um ... trecho dois", blob))
        self.assertFalse(evidencia_ancorada("trecho um ... nao existe", blob))


if __name__ == "__main__":
    unittest.main(verbosity=2)
