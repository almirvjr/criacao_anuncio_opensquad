"""Chama o Claude sem conversa (claude -p) para uma etapa da esteira.

Permissoes fechadas: pode ler/escrever arquivos de dados, rodar SO os validadores e o tiny_to_esteira,
buscar no Cloudinary e usar o navegador escondido da Helena. NAO pode publicar: o disparo
e o 2o envio sao negados, assim como ler o .env, python -c, curl e o MCP do n8n.
Nunca devolve texto cru de erro (pode carregar segredo)."""
import json
import subprocess
from pathlib import Path

PERMITIDAS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task", "WebSearch", "WebFetch",
    # so os programas que ja existem e foram revisados; nunca "python *" (o Claude poderia
    # escrever um .py proprio que le o .env e chama o webhook)
    "Bash(python squads/ml-anuncios/pipeline/validators/*)", "Bash(python tools/tiny_to_esteira.py*)",
    "Bash(ls *)", "Bash(mkdir *)",
    "mcp__cloudinary__search-assets", "mcp__playwright", "mcp__mercadolibre",
]
NEGADAS = [
    "Bash(*disparar_publicacao*)", "Bash(*completar_anuncio*)", "Bash(*.env*)", "Bash(*..*)",
    "Bash(python -c*)", "Bash(curl*)", "Read(./.env)", "Read(**/.env)", "mcp__n8n",
    # nao cria nem altera programa: o que roda e so o que ja foi revisado
    "Write(**/*.py)", "Edit(**/*.py)", "Write(tools/**)", "Edit(tools/**)",
    "Write(squads/ml-anuncios/pipeline/**)", "Edit(squads/ml-anuncios/pipeline/**)",
]


def montar_comando(instrucao):
    return ["claude", "-p", instrucao, "--output-format", "json",
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
