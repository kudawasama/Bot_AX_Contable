@echo off
title Bot AX Registro - Lanzador Gemini Engine
:: Cambiar a la unidad H si es necesario
h: 2>nul
:: Entrar a la carpeta del proyecto
cd /d "h:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
:: Ejecutar la interfaz gráfica de Registro sin ventana de consola
start pythonw bot_ax_registro.py
exit
