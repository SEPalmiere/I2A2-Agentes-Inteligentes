# =============================================================================
# GERENCIADOR DE LOGS - SISTEMA VR/VA
# =============================================================================

import os
import glob
from datetime import datetime
import pandas as pd
import json

class LogManager:
    """📝 Gerenciador centralizado de logs do sistema VR/VA"""
    
    def __init__(self):
        # Detectar diretório de logs
        diretorio_atual = os.getcwd()
        if diretorio_atual.endswith('src'):
            diretorio_raiz = os.path.dirname(diretorio_atual)
        else:
            diretorio_raiz = diretorio_atual
        
        self.diretorio_logs = os.path.join(diretorio_raiz, "outputs", "logs")
        os.makedirs(self.diretorio_logs, exist_ok=True)
    
    def gerar_resumo_logs(self):
        """📊 Gera resumo de todos os logs disponíveis"""
        try:
            logs_encontrados = glob.glob(os.path.join(self.diretorio_logs, "*.log"))
            
            if not logs_encontrados:
                return self._criar_log_vazio("Nenhum arquivo de log encontrado")
            
            resumo = {
                'timestamp_resumo': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'total_arquivos_log': len(logs_encontrados),
                'arquivos_log': [],
                'estatisticas_gerais': {
                    'total_linhas': 0,
                    'total_erros': 0,
                    'total_warnings': 0,
                    'total_infos': 0,
                    'processamentos_concluidos': 0,
                    'processamentos_falharam': 0
                }
            }
            
            for arquivo_log in logs_encontrados:
                info_arquivo = self._analisar_arquivo_log(arquivo_log)
                resumo['arquivos_log'].append(info_arquivo)
                
                # Somar estatísticas
                est = resumo['estatisticas_gerais']
                est['total_linhas'] += info_arquivo['total_linhas']
                est['total_erros'] += info_arquivo['erros']
                est['total_warnings'] += info_arquivo['warnings']
                est['total_infos'] += info_arquivo['infos']
                
                if info_arquivo['processamento_concluido']:
                    est['processamentos_concluidos'] += 1
                else:
                    est['processamentos_falharam'] += 1
            
            # Salvar resumo
            arquivo_resumo = os.path.join(self.diretorio_logs, f"resumo_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(arquivo_resumo, 'w', encoding='utf-8') as f:
                json.dump(resumo, f, indent=2, ensure_ascii=False)
            
            # Criar também um arquivo texto legível
            self._criar_resumo_texto(resumo)
            
            return resumo
            
        except Exception as e:
            return self._criar_log_vazio(f"Erro ao gerar resumo: {str(e)}")
    
    def _analisar_arquivo_log(self, caminho_arquivo):
        """🔍 Analisa um arquivo de log específico"""
        try:
            nome_arquivo = os.path.basename(caminho_arquivo)
            tamanho_kb = os.path.getsize(caminho_arquivo) / 1024
            data_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho_arquivo))
            
            info = {
                'nome_arquivo': nome_arquivo,
                'caminho_completo': caminho_arquivo,
                'tamanho_kb': round(tamanho_kb, 2),
                'data_modificacao': data_modificacao.strftime("%d/%m/%Y %H:%M:%S"),
                'total_linhas': 0,
                'erros': 0,
                'warnings': 0,
                'infos': 0,
                'debugs': 0,
                'processamento_concluido': False,
                'tempo_processamento': None,
                'colaboradores_processados': 0,
                'valor_total_processado': 0.0,
                'primeiras_linhas': [],
                'ultimas_linhas': [],
                'erros_encontrados': []
            }
            
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            info['total_linhas'] = len(linhas)
            
            # Analisar cada linha
            for i, linha in enumerate(linhas):
                linha_clean = linha.strip()
                
                # Contar por nível
                if '| ERROR   |' in linha:
                    info['erros'] += 1
                    if len(info['erros_encontrados']) < 10:  # Limitar a 10 erros
                        info['erros_encontrados'].append(linha_clean)
                elif '| WARNING |' in linha:
                    info['warnings'] += 1
                elif '| INFO    |' in linha:
                    info['infos'] += 1
                elif '| DEBUG   |' in linha:
                    info['debugs'] += 1
                
                # Verificar conclusão
                if 'PROCESSAMENTO CONCLUÍDO COM SUCESSO' in linha:
                    info['processamento_concluido'] = True
                
                # Extrair métricas
                # Extrair métricas
                if 'Colaboradores processados:' in linha:
                    try:
                        numero = linha.split('Colaboradores processados:')[1].strip().replace(',', '')
                        info['colaboradores_processados'] = int(numero)
                    except:
                        pass
                
                if 'Valor total VR: R
                 in linha:
                    try:
                        valor = linha.split('Valor total VR: R
                )[1].strip().replace(',', '').replace('.', '')
                        info['valor_total_processado'] = float(valor) / 100
                    except:
                        pass
                
                if 'Tempo total:' in linha and 's (' in linha:
                    try:
                        tempo = linha.split('Tempo total:')[1].split('s (')[0].strip()
                        info['tempo_processamento'] = float(tempo)
                    except:
                        pass
            
            # Capturar primeiras e últimas linhas
            info['primeiras_linhas'] = [linha.strip() for linha in linhas[:5]]
            info['ultimas_linhas'] = [linha.strip() for linha in linhas[-5:]]
            
            return info
            
        except Exception as e:
            return {
                'nome_arquivo': os.path.basename(caminho_arquivo),
                'erro_analise': str(e),
                'total_linhas': 0,
                'erros': 0,
                'warnings': 0,
                'infos': 0
            }
    
    def _criar_resumo_texto(self, resumo):
        """📄 Cria resumo em formato texto legível"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_texto = os.path.join(self.diretorio_logs, f"RESUMO_LOGS_{timestamp}.txt")
        
        try:
            with open(arquivo_texto, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("📝 RESUMO GERAL DOS LOGS - SISTEMA VR/VA\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"🕐 Data/Hora: {resumo['timestamp_resumo']}\n")
                f.write(f"📁 Total de arquivos de log: {resumo['total_arquivos_log']}\n\n")
                
                # Estatísticas gerais
                est = resumo['estatisticas_gerais']
                f.write("📊 ESTATÍSTICAS GERAIS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"📝 Total de linhas de log: {est['total_linhas']:,}\n")
                f.write(f"❌ Total de erros: {est['total_erros']:,}\n")
                f.write(f"⚠️ Total de warnings: {est['total_warnings']:,}\n")
                f.write(f"ℹ️ Total de infos: {est['total_infos']:,}\n")
                f.write(f"✅ Processamentos concluídos: {est['processamentos_concluidos']}\n")
                f.write(f"❌ Processamentos falharam: {est['processamentos_falharam']}\n\n")
                
                # Detalhes por arquivo
                f.write("📋 DETALHES POR ARQUIVO:\n")
                f.write("="*80 + "\n")
                
                for i, arquivo in enumerate(resumo['arquivos_log'], 1):
                    f.write(f"\n{i}. 📄 {arquivo['nome_arquivo']}\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"📅 Data: {arquivo['data_modificacao']}\n")
                    f.write(f"💾 Tamanho: {arquivo['tamanho_kb']} KB\n")
                    f.write(f"📝 Linhas: {arquivo['total_linhas']:,}\n")
                    f.write(f"❌ Erros: {arquivo['erros']}\n")
                    f.write(f"⚠️ Warnings: {arquivo['warnings']}\n")
                    f.write(f"ℹ️ Infos: {arquivo['infos']}\n")
                    
                    if arquivo.get('processamento_concluido'):
                        f.write("✅ Status: CONCLUÍDO COM SUCESSO\n")
                    else:
                        f.write("❌ Status: FALHOU OU INCOMPLETO\n")
                    
                    if arquivo.get('tempo_processamento'):
                        tempo = arquivo['tempo_processamento']
                        f.write(f"⏱️ Tempo: {tempo:.2f}s ({tempo/60:.1f} min)\n")
                    
                    if arquivo.get('colaboradores_processados', 0) > 0:
                        f.write(f"👥 Colaboradores: {arquivo['colaboradores_processados']:,}\n")
                    
                    if arquivo.get('valor_total_processado', 0) > 0:
                        f.write(f"💰 Valor total: R$ {arquivo['valor_total_processado']:,.2f}\n")
                    
                    # Mostrar erros se houver
                    if arquivo.get('erros_encontrados'):
                        f.write(f"\n🚨 PRINCIPAIS ERROS ENCONTRADOS:\n")
                        for j, erro in enumerate(arquivo['erros_encontrados'][:5], 1):
                            f.write(f"   {j}. {erro}\n")
                    
                    f.write("\n")
                
                f.write("="*80 + "\n")
                f.write("📝 Resumo gerado automaticamente pelo Sistema VR/VA\n")
                f.write("="*80 + "\n")
            
            print(f"📄 Resumo texto criado: {arquivo_texto}")
            
        except Exception as e:
            print(f"❌ Erro ao criar resumo texto: {e}")
    
    def _criar_log_vazio(self, mensagem):
        """📝 Cria estrutura de log vazia para casos de erro"""
        return {
            'timestamp_resumo': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_arquivos_log': 0,
            'mensagem': mensagem,
            'estatisticas_gerais': {
                'total_linhas': 0,
                'total_erros': 0,
                'total_warnings': 0,
                'total_infos': 0,
                'processamentos_concluidos': 0,
                'processamentos_falharam': 0
            }
        }
    
    def limpar_logs_antigos(self, dias_manter=7):
        """🗑️ Remove logs mais antigos que X dias"""
        try:
            logs_encontrados = glob.glob(os.path.join(self.diretorio_logs, "*.log"))
            agora = datetime.now()
            removidos = 0
            
            for arquivo_log in logs_encontrados:
                data_arquivo = datetime.fromtimestamp(os.path.getmtime(arquivo_log))
                dias_diferenca = (agora - data_arquivo).days
                
                if dias_diferenca > dias_manter:
                    os.remove(arquivo_log)
                    removidos += 1
                    print(f"🗑️ Log removido: {os.path.basename(arquivo_log)} ({dias_diferenca} dias)")
            
            print(f"✅ Limpeza concluída: {removidos} arquivos removidos")
            return removidos
            
        except Exception as e:
            print(f"❌ Erro na limpeza de logs: {e}")
            return 0
    
    def exportar_logs_excel(self):
        """📊 Exporta resumo dos logs para Excel"""
        try:
            resumo = self.gerar_resumo_logs()
            
            if resumo['total_arquivos_log'] == 0:
                print("⚠️ Nenhum log encontrado para exportar")
                return None
            
            # Criar DataFrame com informações dos arquivos
            dados_arquivos = []
            for arquivo in resumo['arquivos_log']:
                dados_arquivos.append({
                    'Nome do Arquivo': arquivo['nome_arquivo'],
                    'Data Modificação': arquivo['data_modificacao'],
                    'Tamanho (KB)': arquivo['tamanho_kb'],
                    'Total Linhas': arquivo['total_linhas'],
                    'Erros': arquivo['erros'],
                    'Warnings': arquivo['warnings'],
                    'Infos': arquivo['infos'],
                    'Status': 'CONCLUÍDO' if arquivo.get('processamento_concluido') else 'FALHOU',
                    'Tempo (s)': arquivo.get('tempo_processamento', ''),
                    'Colaboradores': arquivo.get('colaboradores_processados', ''),
                    'Valor Total (R$)': arquivo.get('valor_total_processado', '')
                })
            
            df_arquivos = pd.DataFrame(dados_arquivos)
            
            # Criar DataFrame com estatísticas gerais
            est = resumo['estatisticas_gerais']
            dados_estatisticas = [
                ['Total de Arquivos Log', resumo['total_arquivos_log']],
                ['Total de Linhas', est['total_linhas']],
                ['Total de Erros', est['total_erros']],
                ['Total de Warnings', est['total_warnings']],
                ['Total de Infos', est['total_infos']],
                ['Processamentos Concluídos', est['processamentos_concluidos']],
                ['Processamentos Falharam', est['processamentos_falharam']]
            ]
            
            df_estatisticas = pd.DataFrame(dados_estatisticas, columns=['Métrica', 'Valor'])
            
            # Salvar Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_excel = os.path.join(self.diretorio_logs, f"analise_logs_{timestamp}.xlsx")
            
            with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
                df_estatisticas.to_excel(writer, sheet_name='Estatísticas Gerais', index=False)
                df_arquivos.to_excel(writer, sheet_name='Detalhes por Arquivo', index=False)
            
            print(f"📊 Análise Excel criada: {arquivo_excel}")
            return arquivo_excel
            
        except Exception as e:
            print(f"❌ Erro ao exportar para Excel: {e}")
            return None

def main():
    """🚀 Função principal para execução standalone"""
    print("📝 GERENCIADOR DE LOGS - SISTEMA VR/VA")
    print("="*50)
    
    log_manager = LogManager()
    
    print("1. Gerando resumo dos logs...")
    resumo = log_manager.gerar_resumo_logs()
    
    print("2. Exportando para Excel...")
    arquivo_excel = log_manager.exportar_logs_excel()
    
    print("3. Limpando logs antigos (>7 dias)...")
    removidos = log_manager.limpar_logs_antigos(7)
    
    print("\n✅ OPERAÇÕES CONCLUÍDAS:")
    print(f"   📝 Logs analisados: {resumo['total_arquivos_log']}")
    print(f"   📊 Excel gerado: {'✅' if arquivo_excel else '❌'}")
    print(f"   🗑️ Logs removidos: {removidos}")
    print(f"   📁 Diretório: {log_manager.diretorio_logs}")

if __name__ == "__main__":
    main()
                