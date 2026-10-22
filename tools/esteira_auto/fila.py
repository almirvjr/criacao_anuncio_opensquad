"""Fila de pedidos de anuncio do hub (Supabase). A esteira entra com usuario proprio (hub_esteira), que so
consegue: pegar o proximo pedido, anotar o andamento, gravar o resultado e terminar. Nao le tabela, nao publica.
Senha so do cofre do Windows (item hub_esteira-postgres, posto pelo senha_esteira.py do projeto hub_canais);
o projeto vem do .env. Nunca imprime senha nem texto cru de erro (o repositorio e publico)."""
import json
import socket
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOST = "aws-0-us-west-2.pooler.supabase.com"
SERVICO = "hub_esteira-postgres"


class SemAcesso(Exception):
    """Nao conseguiu entrar no banco (mensagem fixa, sem detalhe)."""


def maquina():
    return socket.gethostname()


def _projeto():
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("SUPABASE_PROJECT_ID="):
            return linha.split("=", 1)[1].strip().strip('"')
    raise SemAcesso("falta SUPABASE_PROJECT_ID no .env")


def conectar():
    import keyring
    import pg8000
    usuario = "hub_esteira." + _projeto()
    senha = keyring.get_password(SERVICO, usuario)
    if not senha:
        raise SemAcesso("a senha da esteira nao esta no cofre do Windows (rode o senha_esteira.py do hub)")
    try:
        conn = pg8000.connect(host=HOST, port=6543, user=usuario, password=senha, database="postgres",
                              ssl_context=True, timeout=30)
    except Exception:  # noqa: BLE001
        raise SemAcesso("o banco do hub nao abriu com a senha da esteira") from None
    conn.autocommit = True
    return conn


class Fila:
    """As 4 portas da esteira no banco. Cada chamada e um comando so (sem transacao aberta)."""

    def __init__(self, conectar=conectar, nome_maquina=None):
        self._conectar = conectar
        self._conn = None
        self.maquina = nome_maquina or maquina()

    def _um(self, sql, args):
        for tentativa in (1, 2):  # conexao parada cai (porteiro do banco): reabre uma vez
            try:
                if self._conn is None:
                    self._conn = self._conectar()
                cur = self._conn.cursor()
                cur.execute(sql, args)
                return cur.fetchone()[0]
            except SemAcesso:
                raise
            except Exception:  # noqa: BLE001
                self._conn = None
                if tentativa == 2:
                    raise SemAcesso("o banco do hub nao respondeu") from None

    def pegar(self):
        r = self._um("select esteira.pegar_pedido(%s)", (self.maquina,))
        return json.loads(r) if isinstance(r, str) else r

    def anotar(self, pedido_id, etapa, texto, lote=None):
        return bool(self._um("select esteira.anotar_andamento(%s, %s, %s, %s, %s)",
                             (pedido_id, self.maquina, etapa, texto, lote)))

    def gravar_resultado(self, pedido_id, resultado):
        return bool(self._um("select esteira.gravar_resultado(%s, %s, %s::text::jsonb)",
                             (pedido_id, self.maquina, json.dumps(resultado, ensure_ascii=False))))

    def terminar(self, pedido_id, erro=None):
        return bool(self._um("select esteira.terminar_pedido(%s, %s, %s)", (pedido_id, self.maquina, erro)))
