# Template de projeto n8n

Ponto de partida para novos projetos de automacao n8n + Mercado Libre + Supabase.

## Setup manual

1. Copiar `.env.example` para `.env` e preencher credenciais
2. Abrir Claude Code dentro da pasta com o plugin ml-kit carregado:

   ```bash
   claude --plugin-dir C:\Users\Almir\claude-plugins\ml-kit
   ```

3. Editar `CLAUDE.md` substituindo `{{DESCRICAO_DO_PROJETO}}` pela descricao real.
4. Primeiro commit:

   ```bash
   git init
   git add .
   git commit -m "chore: bootstrap from project-template-n8n"
   ```

## Setup automatico

Usar o script `new-proj.ps1`:

```powershell
new-proj meu-projeto
```

O script: cria repo no GitHub via template, clona local, copia `.env.example` -> `.env`, abre editor.

## Estrutura

| Arquivo | Proposito |
|---------|-----------|
| `CLAUDE.md` | Instrucoes de alto nivel para Claude Code |
| `REFERENCIA.md` | Detalhes tecnicos (MCPs, tabelas, workflows) |
| `PROGRESSO.md` | Tarefas ativas |
| `HISTORICO.md` | Tarefas concluidas |
| `DECISOES.md` | Decisoes tecnicas registradas |
| `.env.example` | Template de variaveis de ambiente |
| `.mcp.json` | MCP servers (ML token preenchido pelo plugin ml-kit) |
