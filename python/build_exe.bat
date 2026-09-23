@echo off
REM ---------------------------------------------------------------
REM  Genera dist\CalculadoraSupervivencia.exe (un único fichero)
REM  Ejecutar desde la carpeta del proyecto, con el entorno activado.
REM ---------------------------------------------------------------
cd /d "%~dp0"
python -m pip install -r requirements.txt || goto :error
python -m PyInstaller --noconfirm --clean calculadora.spec || goto :error
echo.
echo Listo: dist\CalculadoraSupervivencia.exe
pause
exit /b 0
:error
echo.
echo Ha fallado la generacion del ejecutable. Revisa los mensajes anteriores.
pause
exit /b 1
