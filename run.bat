@echo off
setlocal

echo ==========================================
echo   Invexa Invest - Inicializando Sistema (Local)
echo ==========================================

:: 1. Verifica se a virtualenv .venv existe; se nao existir, cria automaticamente
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Ambiente virtual .venv nao encontrado. Criando .venv...
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python -m venv --system-site-packages .venv
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            py -m venv --system-site-packages .venv
        ) else (
            echo [ERRO] Python nao encontrado no PATH para criar o ambiente virtual .venv.
            echo Por favor, instale o Python e adicione ao PATH.
            pause
            exit /b 1
        )
    )
)

set "PYTHON_CMD=.venv\Scripts\python.exe"

echo [Ambiente Ativo]: .venv (%PYTHON_CMD%)
echo.

echo [1/3] Verificando dependencias...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [AVISO] Falha ou alerta ao verificar dependencias. Prosseguindo com a inicializacao...
)

echo.
echo [2/3] Iniciando Banco de Dados...
:: O banco sqlite eh criado automaticamente pelo SQLAlchemy no startup se nao existir.

echo.
echo [2.5/3] Limpando processos anteriores...
%PYTHON_CMD% scripts\cleanup.py

echo.
echo [3/3] Iniciando Servidor Web...
echo Acesse no navegador: http://localhost:8000
echo Pressione CTRL+C para parar.
echo.

%PYTHON_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause