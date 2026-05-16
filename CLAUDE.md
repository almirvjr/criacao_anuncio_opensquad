# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

{{DESCRICAO_DO_PROJETO}}

**Idioma:** Responda sempre em portugues (brasileiro), a menos que o usuario mude de idioma.

**Nivel tecnico:** O usuario e leigo em programacao. Ao se comunicar com ele: evite jargoes tecnicos sem explicacao, use analogias do cotidiano para explicar conceitos, prefira frases curtas e diretas. Quando precisar usar termo tecnico inevitavel, explique em parenteses o que significa. Exemplos: em vez de "endpoint", diga "endereco que recebe os dados"; em vez de "deployar", diga "publicar/ativar".

---

## n8n

| Campo | Valor |
|---|---|
| **URL** | Ver `.env` -> `N8N_URL` |
| **API Key** | Ver `.env` -> `N8N_API_KEY` |

---

## MCPs e Infraestrutura

MCPs configurados em `.mcp.json`:

- **mercadolibre**: API ML via token em `access_token_ML` do Supabase. Plugin `ml-kit` atualiza token automaticamente no SessionStart.
- **supabase**: MCP oficial Supabase para queries no banco.
- **n8n** (opcional): MCP para gerenciar workflows n8n via API.

Token ML expira em ~6h. Hook do plugin `ml-kit` puxa token fresco da tabela `access_token_ML` no SessionStart.

---

## Regras Criticas

- **Arquivos temporarios: PROIBIDO criar fora do projeto.** Sempre dentro do diretorio do projeto. Hook global `check-write-path.ps1` bloqueia violacoes.
- **HTTP em Code nodes (n8n): PROIBIDO.** Task runner bloqueia `$helpers`, `fetch()`, `require('https')`. Sempre usar HTTP Request nodes nativos. Code nodes: apenas transformacao.
- **AI Agent tools (n8n):** Sempre configurar `neverError: true` em HTTP Request Tools usadas por AI Agents. Sem isso, qualquer erro HTTP crasha o workflow.
- **Supabase nativo n8n nao suporta arrays.** Campos ARRAY falham no no `n8n-nodes-base.supabase`. Usar HTTP Request node com body JSON para inserts que incluam arrays.
- **Tabelas novas por schema de dominio.** `public` e legado; preferir schemas como `ml_tools`, `tiny`, `integracao`.
- **Validacao obrigatoria:** `validate_workflow` antes de todo `create_workflow` ou `update_workflow`.
- **Expressoes n8n:** Sempre `{{ $json.fieldName }}` - nunca omitir as chaves duplas.

---

## Progresso e Planejamento

- `PROGRESSO.md` - tarefas ativas e proximos passos. Leia apenas quando precisar de contexto historico ou planejar proximos passos. Nao leia proativamente.
- `HISTORICO.md` - tarefas concluidas. Leia apenas para contexto de decisoes passadas.
- `DECISOES.md` - decisoes tecnicas do projeto. Leia apenas ao encontrar problema similar.
- `REFERENCIA.md` - detalhes tecnicos: MCPs, tabelas, RLS, skills, workflows.

---

## Disciplina de Sessao

### Classificacao de tarefas

| Tamanho | Exemplos | Abordagem |
|---------|----------|-----------|
| **Pequena** | Corrigir campo, atualizar expressao, toggle de config | Execucao direta |
| **Media** | Adicionar 1-3 nos, modificar Code node, corrigir bug | Declarar plano em 3 linhas antes de executar |
| **Grande** | Novo workflow, reestruturar cadeia de nos, nova integracao | Usar plan mode antes de executar |

### Regras

- **Uma mudanca por vez:** atualizar -> validar -> confirmar resultado -> proxima mudanca.
- **Ler antes de adivinhar:** quando workflow falhar, verificar `get_executions` antes de qualquer hipotese.
- **Subagentes para contexto grande:** delegar parsing de JSON >30KB, pesquisa em docs ML, scripts complexos de Code nodes.
- **Prompts especificos:** incluir ID do workflow, nome do no e dado disponivel no prompt inicial.
- **`/clear` entre tarefas grandes:** libera contexto apos concluir uma unidade logica.
- **`/save` mid-session:** rodar ao concluir cada unidade logica.
