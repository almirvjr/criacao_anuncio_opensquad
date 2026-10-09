@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Criar anuncios do ML
echo Esteira de anuncios. Pode deixar esta janela aberta e fazer outra coisa:
echo a tela de aprovacao abre sozinha quando o texto estiver pronto.
echo.
python "%~dp0maestro.py"
if errorlevel 9009 (
  echo Python nao encontrado neste computador. Chame o Claude.
  pause
  exit /b 9009
)
echo.
pause
