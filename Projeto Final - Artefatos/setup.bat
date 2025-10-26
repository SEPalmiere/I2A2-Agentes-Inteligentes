@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM =============================================================================
REM SCRIPT DE INSTALAÇÃO AUTOMÁTICA - SISTEMA DE EXTRAÇÃO DE NOTAS FISCAIS
REM =============================================================================

title Sistema NFe Extractor - Instalação

echo.
echo ================================================================================
echo 📄 SISTEMA DE EXTRAÇÃO DE NOTAS FISCAIS - INSTALAÇÃO AUTOMÁTICA
echo ================================================================================
echo.

REM Verificar se Python está instalado
echo 🔍 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo 💡 AÇÃO NECESSÁRIA:
    echo 1. Baixe Python 3.10+ de: https://python.org/downloads/
    echo 2. Durante a instalação, marque "Add Python to PATH"
    echo 3. Execute este script novamente após a instalação
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% encontrado

REM Verificar versão do Python (deve ser 3.10+)
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Versão do Python muito antiga (necessário 3.10+)
    echo 💡 Atualize o Python em: https://python.org/downloads/
    pause
    exit /b 1
)

REM Criar estrutura de diretórios
echo.
echo 📁 Criando estrutura de diretórios...

set FOLDERS=venv src config inputs outputs outputs\csv outputs\logs outputs\emails temp samples

for %%f in (%FOLDERS%) do (
    if not exist "%%f" (
        mkdir "%%f"
        echo   ✅ Criado: %%f\
    ) else (
        echo   ℹ️ Já existe: %%f\
    )
)

REM Verificar se já existe ambiente virtual
if exist "venv\Scripts\activate.bat" (
    echo.
    echo 🔄 Ambiente virtual já existe. Deseja recriar? (s/N)
    set /p RECREATE_VENV=
    if /i "!RECREATE_VENV!"=="s" (
        echo 🗑️ Removendo ambiente virtual existente...
        rmdir /s /q venv
        mkdir venv
    )
)

REM Criar ambiente virtual se não existir
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo 🔧 Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual
        echo 💡 Verifique se tem permissões de escrita nesta pasta
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado
)

REM Ativar ambiente virtual
echo.
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente virtual
    pause
    exit /b 1
)

REM Atualizar pip
echo.
echo 📦 Atualizando pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo ⚠️ Aviso: Não foi possível atualizar o pip
) else (
    echo ✅ pip atualizado
)

REM Instalar dependências principais
echo.
echo 📚 Instalando dependências do Sistema NFe Extractor...
echo    Isso pode levar alguns minutos...

set PACKAGES=streamlit==1.29.0 pandas==2.1.4 numpy==1.24.3 plotly==5.17.0 python-dotenv==1.0.0 openpyxl==3.1.2 pdfplumber==0.10.3 PyPDF2==3.0.1 chardet==5.2.0 requests==2.31.0 email-validator==2.1.0

echo.
for %%p in (%PACKAGES%) do (
    echo   📥 Instalando %%p...
    pip install %%p --quiet
    if errorlevel 1 (
        echo   ❌ Erro ao instalar %%p
        set INSTALL_ERROR=1
    ) else (
        echo   ✅ %%p instalado
    )
)

REM Instalar dependências opcionais (CrewAI)
echo.
echo 🤖 Instalando CrewAI (opcional)...
pip install crewai==0.28.8 crewai-tools==0.1.6 langchain==0.1.10 langchain-community==0.0.25 pyyaml==6.0.1 --quiet
if errorlevel 1 (
    echo ⚠️ CrewAI não instalado (sistema funcionará sem análise avançada)
) else (
    echo ✅ CrewAI instalado
)

REM Instalar dependências XML avançadas (opcional)
echo.
echo 📄 Instalando processadores XML avançados...
pip install lxml==4.9.3 xmltodict==0.13.0 --quiet
if errorlevel 1 (
    echo ⚠️ Processadores XML avançados não instalados
) else (
    echo ✅ Processadores XML instalados
)

if defined INSTALL_ERROR (
    echo.
    echo ⚠️ Alguns pacotes falharam. Tentando instalação via requirements.txt...
    pip install -r requirements.txt
)

echo ✅ Dependências instaladas

REM Criar requirements.txt
echo.
echo 📄 Criando requirements.txt...
(
echo # Sistema de Extração de Notas Fiscais
echo streamlit==1.29.0
echo pandas==2.1.4
echo numpy==1.24.3
echo python-dotenv==1.0.0
echo pdfplumber==0.10.3
echo PyPDF2==3.0.1
echo chardet==5.2.0
echo openpyxl==3.1.2
echo plotly==5.17.0
echo requests==2.31.0
echo email-validator==2.1.0
echo # CrewAI (opcional)
echo crewai==0.28.8
echo crewai-tools==0.1.6
echo langchain==0.1.10
echo langchain-community==0.0.25
echo pyyaml==6.0.1
echo # XML avançado (opcional)
echo lxml==4.9.3
echo xmltodict==0.13.0
) > requirements.txt
echo ✅ requirements.txt criado

REM Criar arquivo .env se não existir
if not exist ".env" (
    echo.
    echo ⚙️ Criando arquivo de configuração .env...
    (
    echo # =============================================================================
    echo # CONFIGURAÇÕES DO SISTEMA DE EXTRAÇÃO NFe
    echo # =============================================================================
    echo.
    echo # Configurações do Ollama
    echo OLLAMA_BASE_URL=http://localhost:11434
    echo OLLAMA_MODEL=llama3.2:3b
    echo.
    echo # Configurações de Email
    echo SMTP_SERVER=smtp.gmail.com
    echo SMTP_PORT=587
    echo EMAIL_USER=seu_email@gmail.com
    echo EMAIL_PASSWORD=sua_senha_de_app_do_gmail
    echo EMAIL_DESTINATARIO=fiscal@empresa.com
    echo.
    echo # Configurações do CrewAI
    echo CREWAI_VERBOSE=false
    echo CREWAI_LOG_LEVEL=ERROR
    echo.
    echo # Configurações gerais
    echo DEBUG=True
    echo.
    echo # Configurações de Extração
    echo MAX_FILE_SIZE_MB=100
    echo ALLOWED_EXTENSIONS=xml,pdf,txt,csv,json
    echo.
    echo # Configurações de Validação
    echo VALIDATE_CNPJ=true
    echo VALIDATE_CPF=true
    echo VALIDATE_NFE_KEY=true
    ) > .env
    echo ✅ Arquivo .env criado
    echo ⚠️ IMPORTANTE: Edite o arquivo .env com suas credenciais
) else (
    echo ✅ Arquivo .env já existe
)

REM Criar script de inicialização
echo.
echo 🚀 Criando script de inicialização...
(
echo @echo off
echo chcp 65001 ^>nul
echo title Sistema NFe Extractor - Executando
echo.
echo echo ================================================================================
echo echo 📄 SISTEMA DE EXTRAÇÃO DE NOTAS FISCAIS - INICIANDO...
echo echo ================================================================================
echo echo.
echo.
echo REM Ativar ambiente virtual
echo if not exist "venv\Scripts\activate.bat" ^(
echo     echo ❌ Ambiente virtual não encontrado!
echo     echo 💡 Execute setup.bat primeiro
echo     pause
echo     exit /b 1
echo ^)
echo.
echo call venv\Scripts\activate.bat
echo.
echo REM Verificar se arquivos Python existem
echo if not exist "src\main.py" ^(
echo     echo ⚠️ Arquivos Python não encontrados na pasta src/
echo     echo.
echo     echo 📋 ARQUIVOS NECESSÁRIOS:
echo     echo - src\main.py
echo     echo - src\app.py  
echo     echo - src\nfe_extractor.py
echo     echo - src\nfe_agents.py
echo     echo - src\__init__.py
echo     echo.
echo     echo 💡 Copie os arquivos Python para a pasta src/
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ✅ Iniciando Sistema NFe Extractor...
echo cd src
echo python main.py
echo.
echo if errorlevel 1 ^(
echo     echo.
echo     echo ❌ Erro ao executar o sistema
echo     echo 💡 Verifique os logs em outputs\logs\
echo     pause
echo ^)
) > iniciar_nfe.bat
echo ✅ iniciar_nfe.bat criado

REM Criar script para Streamlit direto
echo.
echo 🌐 Criando script para interface web...
(
echo @echo off
echo chcp 65001 ^>nul
echo title Sistema NFe - Interface Web
echo.
echo call venv\Scripts\activate.bat
echo cd src
echo echo 🌐 Iniciando interface web...
echo streamlit run app.py --server.port 8501 --server.address localhost
echo pause
) > interface_web.bat
echo ✅ interface_web.bat criado

REM Verificar Ollama
echo.
echo 🤖 Verificando Ollama...
curl -s -m 5 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Ollama não está rodando ou não está instalado
    echo.
    echo 📋 CONFIGURAÇÃO DO OLLAMA (Opcional):
    echo 1. Baixe de: https://ollama.ai/download
    echo 2. Instale o Ollama
    echo 3. Abra um novo terminal como Administrador
    echo 4. Execute: ollama serve
    echo 5. Em outro terminal execute: ollama pull llama3.2:3b
    echo.
    echo 💡 O sistema funcionará sem CrewAI se o Ollama não estiver disponível
) else (
    echo ✅ Ollama está rodando
    
    REM Verificar modelo
    curl -s http://localhost:11434/api/tags | findstr "llama3.2:3b" >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ Modelo llama3.2:3b não encontrado
        echo 📥 Execute em outro terminal: ollama pull llama3.2:3b
    ) else (
        echo ✅ Modelo llama3.2:3b disponível
    )
)

REM Criar arquivo de amostras
echo.
echo 📄 Criando arquivo de exemplo...
(
echo "CHAVE DE ACESSO";"NUMERO";"EMITENTE";"VALOR"
echo "12345678901234567890123456789012345678901234";"001";"EMPRESA EXEMPLO";"100,00"
) > samples\exemplo_nfe.csv
echo ✅ Arquivo de exemplo criado em samples\

REM Criar arquivo de instruções
echo.
echo 📚 Criando guia de uso rápido...
(
echo # 📄 SISTEMA DE EXTRAÇÃO NFe - GUIA RÁPIDO
echo.
echo ## 🚀 Como Executar
echo.
echo ### Opção 1: Sistema Completo
echo ```
echo iniciar_nfe.bat
echo ```
echo.
echo ### Opção 2: Apenas Interface Web  
echo ```
echo interface_web.bat
echo ```
echo.
echo ## 📁 Arquivos Necessários
echo.
echo Coloque na pasta `src/`:
echo - main.py
echo - app.py
echo - nfe_extractor.py
echo - nfe_agents.py
echo - __init__.py
echo.
echo ## ⚙️ Configuração
echo.
echo 1. Edite `.env` com suas credenciais
echo 2. (Opcional) Configure Ollama para CrewAI
echo 3. Coloque os arquivos Python nas pastas corretas
echo.
echo ## 📊 Como Usar
echo.
echo 1. Execute `iniciar_nfe.bat`
echo 2. Acesse http://localhost:8501
echo 3. Selecione arquivos NFe ou pasta
echo 4. Clique em "Processar Arquivos"
echo 5. Visualize dados extraídos
echo 6. Baixe CSV consolidado
echo 7. Envie por email (opcional)
echo.
echo ## 📄 Formatos Suportados
echo.
echo - **XML**: NFe padrão nacional
echo - **PDF**: Documentos fiscais digitalizados
echo - **TXT**: Arquivos delimitados
echo - **CSV**: Planilhas texto
echo - **JSON**: Dados estruturados
echo.
echo ## 🔧 Solução de Problemas
echo.
echo - **Ollama**: Opcional para análise CrewAI
echo - **Python**: Use versão 3.10 ou superior  
echo - **Permissões**: Execute como Administrador se necessário
echo - **Encoding**: Sistema detecta automaticamente
) > GUIA_NFE.md
echo ✅ GUIA_NFE.md criado

echo.
echo ================================================================================
echo ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ================================================================================
echo.
echo 📋 PRÓXIMOS PASSOS:
echo.
echo 1. 📧 Edite o arquivo .env com suas credenciais de email
echo 2. 🤖 (Opcional) Configure o Ollama para análise avançada
echo 3. 📁 Coloque os arquivos Python na pasta src/
echo 4. 🚀 Execute: iniciar_nfe.bat
echo.
echo 📂 ESTRUTURA CRIADA:
echo ├── 🔧 setup.bat              (este arquivo)
echo ├── 🚀 iniciar_nfe.bat        (executar sistema)
echo ├── 🌐 interface_web.bat      (apenas interface)
echo ├── ⚙️ .env                   (configurações)
echo ├── 📦 requirements.txt       (dependências)
echo ├── 📚 GUIA_NFE.md           (instruções)
echo ├── 🗂️ src/                   (código Python)
echo ├── 🎛️ config/                (configurações)
echo ├── 📥 inputs/                (arquivos originais)
echo ├── 📤 outputs/               (resultados)
echo ├── 📁 samples/               (exemplos)
echo └── 🐍 venv/                  (ambiente Python)
echo.
echo 💡 DICAS IMPORTANTES:
echo - Sistema funciona SEM Ollama (modo básico)
echo - Configure email no .env para envios automáticos
echo - Suporta XML, PDF, TXT, CSV e JSON
echo - Interface web em http://localhost:8501
echo - Consulte GUIA_NFE.md para instruções detalhadas
echo.

pause

