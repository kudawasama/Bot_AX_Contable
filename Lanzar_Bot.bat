@echo off
title Bot AX Contable - Lanzador
:: Cambiar al directorio del script y ejecutar la GUI (usa pythonw si está disponible)
pushd "%~dp0"
set "VENV_PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if exist "%~dp0app_gui_qt.py" (
	if exist "%VENV_PYTHONW%" (
		start "Bot AX GUI" "%VENV_PYTHONW%" "%~dp0app_gui_qt.py"
	) else (
		where pythonw >nul 2>&1
		if %ERRORLEVEL%==0 (
			start "Bot AX GUI" pythonw "%~dp0app_gui_qt.py"
		) else (
			where python >nul 2>&1
			if %ERRORLEVEL%==0 (
				start "Bot AX GUI" python "%~dp0app_gui_qt.py"
			) else (
				echo Error: no se encontró python/pythonw en PATH.
			)
		)
	)
) else (
	if exist "%~dp0app_gui.py" (
		if exist "%VENV_PYTHONW%" (
			start "Bot AX GUI" "%VENV_PYTHONW%" "%~dp0app_gui.py"
		) else (
			where pythonw >nul 2>&1
			if %ERRORLEVEL%==0 (
				start "Bot AX GUI" pythonw "%~dp0app_gui.py"
			) else (
				where python >nul 2>&1
				if %ERRORLEVEL%==0 (
					start "Bot AX GUI" python "%~dp0app_gui.py"
				) else (
					echo Error: no se encontró python/pythonw en PATH.
				)
			)
		)
	) else (
		echo Error: no se encontró app_gui_qt.py ni app_gui.py en %~dp0
	)
)
popd
exit /b
