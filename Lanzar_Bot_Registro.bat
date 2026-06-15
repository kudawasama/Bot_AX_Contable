@echo off
title Bot AX Contable - Lanzador Registro
:: Cambiar a la unidad H si es necesario
h: 2>nul
:: Entrar a la carpeta del proyecto
pushd "%~dp0"
set "VENV_PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if exist "%~dp0bot_ax_registro.py" (
	if exist "%VENV_PYTHONW%" (
		start "Bot AX Registro" "%VENV_PYTHONW%" "%~dp0bot_ax_registro.py"
	) else (
		where pythonw >nul 2>&1
		if %ERRORLEVEL%==0 (
			start "Bot AX Registro" pythonw "%~dp0bot_ax_registro.py"
		) else (
			where python >nul 2>&1
			if %ERRORLEVEL%==0 (
				start "Bot AX Registro" python "%~dp0bot_ax_registro.py"
			) else (
				echo Error: no se encontró python/pythonw en PATH.
			)
		)
	)
) else (
	echo Error: no se encontró bot_ax_registro.py en %~dp0
)
popd
exit /b
exit
