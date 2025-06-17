#!/usr/bin/env python3
"""
Arquivo principal para executar o Agente Fiscal
"""

import os
import sys
import subprocess
import socket
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
    """Verifica se as dependências estão instaladas"""
    try:
        import streamlit
        import crewai
        import pandas
        print("✅ Todas as dependências estão instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        return False

def check_ollama():
    """Verifica se o Ollama está rodando"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama está rodando")
            return True
        else:
            print("❌ Ollama não está respondendo")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Ollama: {e}")
        return False

def check_csv_files():
    """Verifica se os arquivos CSV existem"""
    base_path = Path(__file__).parent.parent
    csv_path = base_path / "knowledge"
    
    cabecalho_file = csv_path / "202401_NFs_Cabecalho.csv"
    itens_file = csv_path / "202401_NFs_Itens.csv"
    
    if cabecalho_file.exists() and itens_file.exists():
        print("✅ Arquivos CSV encontrados")
        # Configurar variáveis de ambiente
        os.environ["CSV_CABECALHO_PATH"] = str(cabecalho_file)
        os.environ["CSV_ITENS_PATH"] = str(itens_file)
        return True
    else:
        print("❌ Arquivos CSV não encontrados")
        print(f"Procurando em: {csv_path}")
        return False

def install_requirements():
    """Instala as dependências do requirements.txt"""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    if requirements_path.exists():
        print("📦 Instalando dependências...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        return True
    else:
        print("❌ Arquivo requirements.txt não encontrado")
        return False

def kill_existing_streamlit():
    """Mata processos existentes do Streamlit na porta 8501"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/f', '/im', 'streamlit.exe'], 
                         capture_output=True, text=True)
        else:  # Linux/Mac
            subprocess.run(['pkill', '-f', 'streamlit'], 
                         capture_output=True, text=True)
        print("🔄 Processos anteriores finalizados")
    except:
        pass

def run_streamlit():
    """Executa o Streamlit"""
    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print("❌ Arquivo app.py não encontrado")
        return
    
    # Tentar encontrar uma porta livre
    port = find_free_port()
    if not port:
        print("❌ Nenhuma porta disponível encontrada")
        print("💡 Tente fechar outras aplicações Streamlit")
        return
    
    print(f"🌐 Iniciando Streamlit na porta {port}...")
    print(f"📱 Acesse: http://localhost:{port}")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", str(port),
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar Streamlit: {e}")

def main():
    """Função principal"""
    print("🤖 Agente Fiscal - Inicializando...")
    print("=" * 50)
    
    # Verificar dependências
    if not check_requirements():
        print("\n📦 Instalando dependências...")
        if not install_requirements():
            print("❌ Falha na instalação das dependências")
            input("Pressione Enter para sair...")
            return
        
        if not check_requirements():
            print("❌ Ainda há dependências faltando")
            input("Pressione Enter para sair...")
            return
    
    # Verificar Ollama
    if not check_ollama():
        print("\n⚠️  ATENÇÃO: Certifique-se de que o Ollama está rodando:")
        print("   1. Abra um novo terminal")
        print("   2. Execute: ollama serve")
        print("   3. Execute: ollama pull llama3.2:3b")
        input("Pressione Enter depois de configurar o Ollama...")
        
        # Verificar novamente
        if not check_ollama():
            print("❌ Ollama ainda não está disponível")
            input("Pressione Enter para sair...")
            return
    
    # Verificar arquivos CSV
    if not check_csv_files():
        print("\n⚠️  ATENÇÃO: Coloque os arquivos CSV na pasta 'knowledge/':")
        print("   - 202401_NFs_Cabecalho.csv")
        print("   - 202401_NFs_Itens.csv")
        input("Pressione Enter depois de adicionar os arquivos...")
        
        if not check_csv_files():
            print("❌ Arquivos CSV ainda não encontrados")
            input("Pressione Enter para sair...")
            return
    
    print("\n✅ Todos os pré-requisitos atendidos!")
    
    # Finalizar processos anteriores
    kill_existing_streamlit()
    
    # Executar Streamlit
    run_streamlit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Execução interrompida")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        input("Pressione Enter para sair...")