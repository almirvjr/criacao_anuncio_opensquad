"""Chama o Claude sem conversa (claude -p) para uma etapa da esteira.

Permissoes fechadas: le so dentro do projeto (sem os arquivos de chave), grava so na pasta dos lotes, roda SO os validadores,
buscar no Cloudinary e usar o navegador escondido da Helena. NAO pode publicar: o disparo
e o 2o envio sao negados, assim como ler o .env, python -c, curl e o MCP do n8n.
Nunca devolve texto cru de erro (pode carregar segredo)."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from esteira_auto import vaga as vaga_mod  # noqa: E402

# Liberar o minimo, em vez de listar o proibido (revisoes de 09/10/2026):
# - sem "Read/Glob/Grep" gerais: no modo dontAsk o Claude so le DENTRO do projeto; fora (outros
#   projetos, ~/.claude.json) e negado. Dentro, os arquivos com chave sao negados abaixo (a regra
#   ignora maiuscula/minuscula, sondado).
# - gravar: so na pasta dos lotes. Programa: so os validadores, pelo nome exato (eles so leem);
#   tiny_to_esteira e capas.py gravam onde o argumento mandar, entao quem roda e o maestro.
# - internet: so paginas do ML. Sem o MCP do ML (pode ter ferramenta que mexe em anuncio).
#   Navegador sem digitar/preencher/rodar codigo (o perfil pode estar logado).
PROGRAMAS = [
    "squads/ml-anuncios/pipeline/validators/validar_brief.py",
    "squads/ml-anuncios/pipeline/validators/validar_claims.py",
    "squads/ml-anuncios/pipeline/validators/validar_ficha_seo.py",
    "squads/ml-anuncios/pipeline/validators/validar_ficha_nsa.py",
]
PERMITIDAS = [
    "Agent", "Task", "WebSearch",
    "WebFetch(domain:mercadolivre.com.br)", "WebFetch(domain:www.mercadolivre.com.br)",
    "WebFetch(domain:produto.mercadolivre.com.br)", "WebFetch(domain:api.mercadolibre.com)",
    "Edit(squads/ml-anuncios/output/lotes/**)", "Write(squads/ml-anuncios/output/lotes/**)",
    *[f"Bash(python {s} *)" for s in PROGRAMAS],
    "mcp__cloudinary__search-assets", "mcp__playwright",
]
NEGADAS = [
    "Bash(*disparar_publicacao*)", "Bash(*completar_anuncio*)", "Bash(*.env*)", "Bash(*..*)",
    "Bash(python -c*)", "Bash(curl*)", "mcp__n8n", "mcp__mercadolibre",
    "Read(**/.mcp.json)", "Read(**/.env*)", "Read(_opensquad/_browser_profile/**)",
    *[f"Read({vaga_mod.perfil_navegador_rel(v)}/**)" for v in range(2, vaga_mod.MAXIMO + 1)],
    "Read(.playwright-mcp/**)", "Read(.git/**)", "Read(.claude/**)",
    *[f"Read(**/.{a}{b}{c})" for a in "eE" for b in "nN" for c in "vV"],
    "mcp__playwright__browser_evaluate", "mcp__playwright__browser_run_code",
    "mcp__playwright__browser_type", "mcp__playwright__browser_fill_form", "mcp__playwright__browser_file_upload",
]


def montar_comando(instrucao):
    # dontAsk: o que nao esta liberado e negado. Sem isso o claude -p herda o modo "auto" do
    # settings.json do hub, e o classificador aprova escrita fora da lista (sondado 09/10/2026).
    return ["claude", "-p", instrucao, "--output-format", "json", "--permission-mode", "dontAsk",
            "--allowedTools", ",".join(PERMITIDAS), "--disallowedTools", ",".join(NEGADAS)]


def chamar(instrucao, raiz, timeout_s=2400, rodar=subprocess.run):
    # vaga 2: o navegador do MCP playwright abre no perfil da vaga (o persistente so aceita um navegador por vez).
    # Vaga 1 nao passa `env` (igual antes).
    extra = {} if (env := vaga_mod.env_claude()) is None else {"env": env}
    try:
        r = rodar(montar_comando(instrucao), cwd=str(Path(raiz)), capture_output=True,
                  text=True, encoding="utf-8", errors="replace", timeout=timeout_s, **extra)
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
