@echo off
set PYTHON_EXE="C:\Users\IAP9978\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe"
echo ==========================================
echo   Invexa - Inicializando Sistema (Local)
echo ==========================================

echo [1/3] Verificando dependencias...
%PYTHON_EXE% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erro ao instalar dependencias. Verifique seu Python.
    pause
    exit /b
)

echo.
echo [2/3] Iniciando Banco de Dados...
:: O banco sqlite eh criado automaticamente pelo SQLAlchemy no startup se nao existir.

echo.
echo [2.5/3] Limpando processos anteriores...
%PYTHON_EXE% cleanup.py

echo.
echo [3/3] Iniciando Servidor Web...
echo Acesse no navegador: http://localhost:8000
echo Pressione CTRL+C para parar.
echo.

%PYTHON_EXE% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
