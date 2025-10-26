#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar todas as bibliotecas instaladas no venv
Retorna nome e versão de cada pacote
"""

import pkg_resources
import sys
from pathlib import Path
from datetime import datetime
import json

def get_installed_packages():
    """Retorna lista de todos os pacotes instalados com versões"""
    packages = []
    for dist in pkg_resources.working_set:
        packages.append({
            'nome': dist.project_name,
            'versao': dist.version,
            'localizacao': dist.location
        })
    return sorted(packages, key=lambda x: x['nome'].lower())

def print_table(packages):
    """Imprime tabela formatada"""
    print("\n" + "="*100)
    print(f"{'BIBLIOTECA':<50} {'VERSÃO':<30} {'LOCALIZAÇÃO'}")
    print("="*100)
    
    for pkg in packages:
        nome = pkg['nome'][:49]
        versao = pkg['versao'][:29]
        localizacao = pkg['localizacao'][-15:] if len(pkg['localizacao']) > 15 else pkg['localizacao']
        print(f"{nome:<50} {versao:<30} {localizacao}")
    
    print("="*100)
    print(f"Total de pacotes: {len(packages)}\n")

def save_to_csv(packages, filename="bibliotecas_instaladas.csv"):
    """Salva em arquivo CSV"""
    import csv
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['nome', 'versao', 'localizacao'])
        writer.writeheader()
        writer.writerows(packages)
    print(f"✅ Arquivo salvo: {filename}\n")

def save_to_json(packages, filename="bibliotecas_instaladas.json"):
    """Salva em arquivo JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(packages, f, ensure_ascii=False, indent=2)
    print(f"✅ Arquivo salvo: {filename}\n")

def save_to_txt(packages, filename="bibliotecas_instaladas.txt"):
    """Salva em arquivo TXT formatado"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write(f"RELATÓRIO DE BIBLIOTECAS INSTALADAS\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Interpretador: {sys.executable}\n")
        f.write("="*100 + "\n\n")
        
        f.write(f"{'BIBLIOTECA':<50} {'VERSÃO':<30}\n")
        f.write("-"*100 + "\n")
        
        for pkg in packages:
            nome = pkg['nome']
            versao = pkg['versao']
            f.write(f"{nome:<50} {versao:<30}\n")
        
        f.write("\n" + "="*100 + "\n")
        f.write(f"Total de pacotes instalados: {len(packages)}\n")
        f.write("="*100 + "\n")
    print(f"✅ Arquivo salvo: {filename}\n")

def main():
    print("\n" + "🔍 ANALISANDO BIBLIOTECAS DO VENV".center(100))
    print(f"Python: {sys.version.split()[0]}")
    print(f"Interpretador: {sys.executable}\n")
    
    # Obter pacotes
    packages = get_installed_packages()
    
    # Imprimir tabela
    print_table(packages)
    
    # Salvar em diferentes formatos
    print("📁 Salvando em diferentes formatos...\n")
    save_to_csv(packages)
    save_to_json(packages)
    save_to_txt(packages)
    
    # Estatísticas
    print("📊 ESTATÍSTICAS")
    print("="*50)
    print(f"Total de pacotes: {len(packages)}")
    print(f"Diretório do venv: {Path(sys.executable).parent.parent}")
    print(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*50 + "\n")
    
    # Listar pacotes críticos do projeto
    print("🎯 PACOTES CRÍTICOS DO PROJETO")
    print("="*50)
    criticos = ['streamlit', 'pandas', 'numpy', 'plotly', 'pdfplumber', 
                'langchain', 'crewai', 'pydantic', 'tenacity', 'chardet']
    
    for critico in criticos:
        for pkg in packages:
            if pkg['nome'].lower() == critico.lower():
                print(f"✅ {pkg['nome']:<40} v{pkg['versao']}")
                break
        else:
            print(f"❌ {critico:<40} NÃO INSTALADO")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
    