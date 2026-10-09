"""Chama o Claude sem conversa (claude -p) para uma etapa da esteira.

Permissoes fechadas: grava so na pasta dos lotes, roda SO os validadores e o tiny_to_esteira,
buscar no Cloudinary e usar o navegador escondido da Helena. NAO pode publicar: o disparo
e o 2o envio sao negados, assim como ler o .env, python -c, curl e o MCP do n8n.
Nunca devolve texto cru de erro (pode carregar segredo)."""
import json
import subprocess
from pathlib import Path

# Liberar o minimo, em vez de listar o proibido: no Windows maiuscula/minuscula dao no mesmo
# arquivo, entao uma lista de proibidos sempre deixa furo (ex.: gravar VALIDADOR.PY por cima
# de um programa liberado). Programa: so estes, pelo nome exato. Gravar: so na pasta dos lotes.
PROGRAMAS = [
    "squads/ml-anuncios/pipeline/validators/validar_brief.py",
    "squads/ml-anuncios/pipeline/validators/validar_claims.py",
    "squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py",
    "squads/ml-anuncios/pipeline/validators/capas.py",
    "tools/tiny_to_esteira.py",
]
PERMITIDAS = [
    "Read", "Glob", "Grep", "Agent", "Task", "WebSearch", "WebFetch",
    "Edit(squads/ml-anuncios/output/lotes/**)", "Write(squads/ml-anuncios/output/lotes/**)",
    *[f"Bash(python {s} *)" for s in PROGRAMAS],
    "Bash(ls *)", "Bash(mkdir *)",
    "mcp__cloudinary__search-assets", "mcp__playwright", "mcp__mercadolibre",
]
NEGADAS = [
    "Bash(*disparar_publicacao*)", "Bash(*completar_anuncio*)", "Bash(*.env*)", "Bash(*..*)",
    "Bash(python -c*)", "Bash(curl*)", "mcp__n8n",
    # o .env tem o endereco de publicar e a chave do ML: bloqueado em toda combinacao de caixa
    *[f"Read(**/.{a}{b}{c})" for a in "eE" for b in "nN" for c in "vV"],
    # navegador sem rodar codigo (daria para mandar dados para fora pela pagina)
    "mcp__playwright__browser_evaluate", "mcp__playwright__browser_run_code",
]


def montar_comando(instrucao):
    # dontAsk: o que nao esta liberado e negado. Sem isso o claude -p herda o modo "auto" do
    # settings.json do hub, e o classificador aprova escrita fora da lista (sondado 09/10/2026).
    return ["claude", "-p", instrucao, "--output-format", "json", "--permission-mode", "dontAsk",
            "--allowedTools", ",".join(PERMITIDAS), "--disallowedTools", ",".join(NEGADAS)]


def chamar(instrucao, raiz, timeout_s=2400, rodar=subprocess.run):
    try:
        r = rodar(montar_comando(instrucao), cwd=str(Path(raiz)), capture_output=True,
                  text=True, encoding="utf-8", errors="replace", timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return False, f"passou do tempo ({timeout_s // 60} min)"
    except FileNotFoundError:
        return False, "nao achei o programa do Claude neste computador"
    try:
        d = json.loads(r.stdout or "")
    except ValueError:
        return False, f"o Claude terminou sem resposta legivel (codigo {r.returncode})"
    if r.returncode != 0 or d.get("is_error"):
        return False, f"o Claude terminou com erro (codigo {r.returncode})"
    return True, str(d.get("result") or "")[:500]
