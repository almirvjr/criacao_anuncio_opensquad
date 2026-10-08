@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Aprovar anuncios do ML
python "%~dp0aprovacao.py" %*
if errorlevel 9009 (
  echo Python nao encontrado neste computador. Chame o Claude.
  pause
)
