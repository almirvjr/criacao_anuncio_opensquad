#!/usr/bin/env python3
"""Testes da trava de prompts (Fase 3). Stdlib unittest."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from validar_prompts import validar_prompts  # noqa: E402
from validar_brief import SLOTS_CANONICOS  # noqa: E402


def escrever_set_completo(pasta, override=None, extra=None):
    """Escreve foto-01..10.json validos. override={numero: dict_patch}."""
    override = override or {}
    for numero, (funcao, _) in SLOTS_CANONICOS.items():
        d = {"imagem": numero, "nome": funcao, "objetivo_meclabs": "+m",
             "prompt": {"instrucao_principal": "USE A IMAGEM ANEXADA"}}
        d.update(override.get(numero, {}))
        with open(os.path.join(pasta, f"foto-{numero:02d}.json"), "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
    if extra:
        for fname, conteudo in extra.items():
            with open(os.path.join(pasta, fname), "w", encoding="utf-8") as fh:
                fh.write(conteudo)


class TestPrompts(unittest.TestCase):
    def test_set_completo_passa(self):
        with tempfile.TemporaryDirectory() as d:
            escrever_set_completo(d)
            self.assertEqual(validar_prompts(d), [])

    def test_placeholder_nao_preenchido(self):
        with tempfile.TemporaryDirectory() as d:
            escrever_set_completo(d)
            # corrompe o foto-05 com um placeholder
            with open(os.path.join(d, "foto-05.json"), "w", encoding="utf-8") as fh:
                json.dump({"imagem": 5, "nome": "LIFESTYLE_EMOCIONAL",
                           "headline": "{{headline_emocional}}"}, fh)
            erros = validar_prompts(d)
            self.assertTrue(any(c == "PLACEHOLDER_NAO_PREENCHIDO" for c, _ in erros))

    def test_funcao_errada(self):
        with tempfile.TemporaryDirectory() as d:
            escrever_set_completo(d, override={7: {"nome": "DETALHE_TECNICO_1"}})
            erros = validar_prompts(d)
            self.assertTrue(any(c == "PROMPT_FUNCAO_ERRADA" for c, _ in erros))

    def test_slot_faltando(self):
        with tempfile.TemporaryDirectory() as d:
            escrever_set_completo(d)
            os.remove(os.path.join(d, "foto-10.json"))
            erros = validar_prompts(d)
            self.assertTrue(any(c == "PROMPT_SLOT_FALTANDO" for c, _ in erros))

    def test_ficha_auxiliar_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d:
            escrever_set_completo(d, extra={
                "foto-ficha.json": json.dumps({"nome": "FICHA_TECNICA_DIMENSOES", "imagem": 99})})
            self.assertEqual(validar_prompts(d), [])

    def test_pasta_vazia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(any(c == "SEM_PROMPTS" for c, _ in validar_prompts(d)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
