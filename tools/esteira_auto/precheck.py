"""Etapa 'entrada': planilha do Olist -> anuncios-entrada.json do lote, com peso e caixa da
cubagem. Falta peso/caixa = para ja, dizendo o SKU (o frete do ML sairia errado)."""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tools"))
from esteira.payload_builder import atributos_embalagem  # noqa: E402

CUBAGEM = Path(r"G:\Meu Drive\TERRA CASA DECOR\ESTOQUE\CUBAGEM DOS PRODUTOS.xlsx")


def faltas_de_caixa(entrada):
    return [f"{a['pai_sku']}: sem peso ou medida da caixa — confira a linha dele na cubagem"
            for a in entrada.get("anuncios", []) if not atributos_embalagem(a)]


def ler_planilha(planilha, lote, cubagem=CUBAGEM, rodar=subprocess.run):
    saida = Path(lote) / "anuncios-entrada.json"
    cmd = [sys.executable, str(RAIZ / "tools" / "tiny_to_esteira.py"), str(planilha), str(saida),
           "--cubagem", str(cubagem)]
    r = rodar(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not saida.is_file():
        return ["nao consegui ler a planilha: ela e o export de produtos do Olist (.xls ou .xlsx)?"]
    entrada = json.loads(saida.read_text(encoding="utf-8"))
    if not entrada.get("anuncios"):
        return ["a planilha nao tem nenhum produto (so o cabecalho?)"]
    return faltas_de_caixa(entrada)
