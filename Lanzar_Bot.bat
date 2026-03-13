@echo off
title Bot AX Contable - Lanzador
:: Cambiar a la unidad H si es necesario
h: 2>nul
:: Entrar a la carpeta del proyecto
cd /d "h:\Mi unidad\Desarrollo y Proyectos\GitHub\Bot_AX_Contable"
:: Ejecutar la interfaz gráfica sin ventana de consola
start pythonw app_gui.py
exit
