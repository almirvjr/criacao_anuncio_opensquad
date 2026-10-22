# rodar_fila.ps1 - tarefa agendada "Esteira - fila do hub" (de 5 em 5 min, escondida pelo run-hidden.vbs do hub-meta).
# Faz UM pedido de anuncio da fila do hub por vez (maestro.py --fila). Sem pedido = sai na hora.
# Registro em squads/ml-anuncios/output/lotes/fila.log (so o que o maestro imprime: nunca senha).
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8  # sem isso o acento chega quebrado no fila.log
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent (Split-Path -Parent $aqui)
$lotes = Join-Path $raiz 'squads\ml-anuncios\output\lotes'
New-Item -ItemType Directory -Force $lotes | Out-Null
$log = Join-Path $lotes 'fila.log'
$saida = & python (Join-Path $aqui 'maestro.py') --fila 2>&1 | Out-String
$codigo = $LASTEXITCODE
if ($saida.Trim() -ne 'Nenhum pedido na fila do hub.' -and $saida.Trim() -ne 'Outra rodada da fila esta trabalhando.') {
    Add-Content -Path $log -Encoding utf8 -Value ("=== {0:yyyy-MM-dd HH:mm} (saida {1})`r`n{2}" -f (Get-Date), $codigo, $saida.Trim())
}
exit $codigo
