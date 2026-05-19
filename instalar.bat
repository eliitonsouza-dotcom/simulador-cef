@echo off
echo ============================================
echo  Instalando dependencias do Simulador CEF
echo ============================================
echo.
pip install flask playwright
playwright install chromium
echo.
echo ============================================
echo  Pronto! Execute "iniciar.bat" para abrir.
echo ============================================
pause
