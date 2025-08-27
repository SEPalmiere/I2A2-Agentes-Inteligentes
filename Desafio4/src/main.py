#!/usr/bin/env python3
"""
Sistema VR/VA - Arquivo Principal
Automacao completa para calculo e compra de vale refeicao/alimentacao
"""

import os
import sys
import subprocess
import socket
import webbrowser
import time
from pathlib import Path

def find_free_port(start_port=8501, max_port=8510):
    """Encontra uma porta livre para o Streamlit"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def check_requirements():
    """Verifica se as dependencias estao instaladas"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'openpyxl',
        'dotenv'  # Corrigido: era 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                # Caso especial para python-dotenv
                from dotenv import load_dotenv
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_ollama():
    """Verifica se o Ollama esta rodando"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Ollama conectado"
        else:
            return False, "Ollama nao esta respondendo"
    except Exception as e:
        return False, f"Erro ao conectar com Ollama: {str(e)}"

def check_python_files():
    """Verifica se os arquivos Python necessarios existem"""
    required_files = [
        'app.py',
        'vr_system.py',
        'vr_crewai.py'
    ]
    
    missing_files = []
    current_dir = Path(__file__).parent
    
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def kill_existing_streamlit():
    """Mata processos existentes do Streamlit"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/f', '/im', 'streamlit.exe'], 
                         capture_output=True, text=True)
        else:  # Linux/Mac
            subprocess.run(['pkill', '-f', 'streamlit'], 
                         capture_output=True, text=True)
        print("Processos anteriores do Streamlit finalizados")
    except Exception:
        pass  # Nao e critico se falhar

def create_log_directory():
    """Cria diretorio de logs se nao existir"""
    try:
        log_dir = Path(__file__).parent.parent / "outputs" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Aviso: Nao foi possivel criar diretorio de logs: {e}")
        return False

def run_streamlit():
    """Executa o Streamlit"""
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print("ERRO: Arquivo app.py nao encontrado!")
        print("Certifique-se de que app.py esta na pasta src/")
        return False
    
    # Tentar encontrar uma porta livre
    port = find_free_port()
    if not port:
        print("ERRO: Nenhuma porta disponivel encontrada (8501-8510)")
        print("Tente fechar outras aplicacoes Streamlit")
        return False
    
    print(f"Iniciando interface web na porta {port}...")
    print(f"URL: http://localhost:{port}")
    print("Aguarde a inicializacao...")
    print()
    print("Para parar o sistema: Pressione Ctrl+C")
    print("=" * 60)
    
    try:
        # Executar Streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", str(port),
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--server.headless", "true"
        ], check=False)
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\nSistema interrompido pelo usuario")
        return True
    except Exception as e:
        print(f"ERRO ao executar Streamlit: {e}")
        return False

def print_system_info():
    """Exibe informacoes do sistema"""
    print("SISTEMA VR/VA - AUTOMACAO INTELIGENTE")
    print("=" * 60)
    print("Funcionalidades:")
    print("  * Upload de 10 arquivos Excel de RH")
    print("  * Processamento com 6 agentes CrewAI")
    print("  * Dashboard executivo interativo")
    print("  * Emails automaticos para fornecedor e RH")
    print("  * Relatorios detalhados por sindicato/estado")
    print("  * Validacoes automaticas de qualidade")
    print()

def main():
    """Funcao principal"""
    try:
        print_system_info()
        
        # Verificar se estamos na pasta correta
        current_dir = Path(__file__).parent
        if not current_dir.name == 'src':
            print("Aviso: Executando fora da pasta src/")
        
        # Criar diretorio de logs
        create_log_directory()
        
        # Verificar dependencias Python
        print("Verificando dependencias Python...")
        deps_ok, missing_deps = check_requirements()
        
        if not deps_ok:
            print("ERRO: Dependencias faltando:")
            for dep in missing_deps:
                print(f"   * {dep}")
            print()
            print("SOLUCAO:")
            print("   1. Volte para pasta principal: cd ..")
            print("   2. Execute: setup.bat")
            print("   3. Tente novamente apos a instalacao")
            return False
        
        print("Dependencias Python OK")
        
        # Verificar arquivos Python
        print("Verificando arquivos Python...")
        files_ok, missing_files = check_python_files()
        
        if not files_ok:
            print("ERRO: Arquivos Python faltando:")
            for file in missing_files:
                print(f"   * {file}")
            print()
            print("SOLUCAO:")
            print("   Certifique-se de que todos os arquivos Python estao na pasta src/")
            return False
        
        print("Arquivos Python OK")
        
        # Verificar Ollama (opcional)
        print("Verificando Ollama...")
        ollama_ok, ollama_msg = check_ollama()
        
        if ollama_ok:
            print(f"Ollama: {ollama_msg}")
            print("CrewAI disponivel para analise avancada")
        else:
            print(f"Ollama: {ollama_msg}")
            print("Sistema funcionara no modo tradicional")
            print("   Para usar CrewAI:")
            print("   1. Execute em outro terminal: ollama serve")
            print("   2. Execute: ollama pull llama3.2:3b")
        
        print()
        print("INICIANDO SISTEMA...")
        print()
        
        # Finalizar processos anteriores
        kill_existing_streamlit()
        
        # Executar Streamlit
        success = run_streamlit()
        
        if success:
            print("\nSistema encerrado normalmente")
        else:
            print("\nSistema encerrado com erros")
            
        return success
        
    except KeyboardInterrupt:
        print("\nSistema interrompido pelo usuario")
        return True
    except Exception as e:
        print(f"\nERRO inesperado: {e}")
        print("\nInformacoes para debug:")
        print(f"   * Pasta atual: {Path.cwd()}")
        print(f"   * Pasta do script: {Path(__file__).parent}")
        print(f"   * Python: {sys.version}")
        
        import traceback
        print("\nStack trace:")
        traceback.print_exc()
        
        return False

def show_help():
    """Mostra informacoes de ajuda"""
    print("SISTEMA VR/VA - AJUDA")
    print("=" * 40)
    print()
    print("COMO USAR:")
    print("   python main.py              # Executar sistema completo")
    print("   python main.py --help       # Mostrar esta ajuda")
    print("   python main.py --check      # Apenas verificar sistema")
    print()
    print("RESOLUCAO DE PROBLEMAS:")
    print("   * Dependencias: Execute setup.bat na pasta principal")
    print("   * Ollama: Execute 'ollama serve' em outro terminal")
    print("   * Arquivos: Certifique-se que estao na pasta src/")
    print("   * Porta: Feche outros aplicativos Streamlit")
    print()
    print("ESTRUTURA ESPERADA:")
    print("   src/")
    print("   ├── main.py           # Este arquivo")
    print("   ├── app.py            # Interface Streamlit")
    print("   ├── vr_system.py      # Sistema VR tradicional")
    print("   ├── vr_crewai.py      # Agentes CrewAI")
    print("   └── __init__.py       # Inicializacao")
    print()

def check_system():
    """Executa apenas verificacoes do sistema"""
    print("VERIFICACAO COMPLETA DO SISTEMA")
    print("=" * 50)
    
    all_ok = True
    
    # Verificar Python
    print(f"Python: {sys.version}")
    
    # Verificar dependencias
    deps_ok, missing_deps = check_requirements()
    if deps_ok:
        print("Dependencias Python: OK")
    else:
        print("Dependencias Python: FALTANDO")
        for dep in missing_deps:
            print(f"   * {dep}")
        all_ok = False
    
    # Verificar arquivos
    files_ok, missing_files = check_python_files()
    if files_ok:
        print("Arquivos Python: OK")
    else:
        print("Arquivos Python: FALTANDO")
        for file in missing_files:
            print(f"   * {file}")
        all_ok = False
    
    # Verificar Ollama
    ollama_ok, ollama_msg = check_ollama()
    if ollama_ok:
        print(f"Ollama: {ollama_msg}")
    else:
        print(f"Ollama: {ollama_msg}")
    
    # Verificar porta
    port = find_free_port()
    if port:
        print(f"Porta disponivel: {port}")
    else:
        print("Nenhuma porta livre encontrada (8501-8510)")
    
    # Verificar logs
    if create_log_directory():
        print("Diretorio de logs: OK")
    else:
        print("Diretorio de logs: PROBLEMA")
    
    print("\n" + "=" * 50)
    if all_ok:
        print("SISTEMA TOTALMENTE FUNCIONAL!")
        print("Pronto para execucao")
    else:
        print("SISTEMA COM PROBLEMAS")
        print("Corrija os itens marcados antes de prosseguir")
    
    return all_ok

if __name__ == "__main__":
    # Verificar argumentos da linha de comando
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            sys.exit(0)
        elif sys.argv[1] in ['--check', '-c', 'check']:
            success = check_system()
            sys.exit(0 if success else 1)
        else:
            print(f"Argumento desconhecido: {sys.argv[1]}")
            print("Use: python main.py --help")
            sys.exit(1)
    
    # Executar sistema normalmente
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\nERRO critico: {e}")
        sys.exit(1)