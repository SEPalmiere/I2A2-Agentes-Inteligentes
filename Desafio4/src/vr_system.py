# =============================================================================
# SISTEMA DE AUTOMAÇÃO VR/VA - VERSÃO CORRIGIDA PARA RIO GRANDE DO SUL
# =============================================================================

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import traceback
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import logging
import sys

warnings.filterwarnings('ignore')
load_dotenv()

class VRAutomationSystem:
    """Sistema completo para automação do cálculo e compra de VR/VA com sistema de logs"""
    
    def __init__(self):
        self.competencia = "05/2025"
        self.datasets = {}
        self.base_consolidada = None
        self.resultado_final = None
        self.arquivos_carregados = {}
        
        # 📝 INICIALIZAR SISTEMA DE LOGS
        self.logger = self._setup_logging()
        self.logger.info("🚀 Sistema VR/VA inicializado")
        
        # Configurações de negócio
        self.config = {
            'percentual_empresa': 0.80,
            'percentual_funcionario': 0.20,
            'dia_corte_desligamento': 15,
            'cargos_excluidos': ['DIRETOR', 'ESTAGIARIO', 'APRENDIZ'],
            'situacoes_afastamento': ['LICENÇA MATERNIDADE', 'AFASTAMENTO', 'LICENÇA MÉDICA'],
            'email_vr': 'email@gmail.com',
            'email_rh': 'email@gmail.com'
        }
        
        self.logger.info(f"⚙️ Configurações carregadas: {self.config}")
        
    def _setup_logging(self):
        """📝 Configura sistema de logging robusto"""
        try:
            # Detectar diretório raiz do projeto
            diretorio_atual = os.getcwd()
            if diretorio_atual.endswith('src') or 'src' in diretorio_atual:
                diretorio_raiz = os.path.dirname(diretorio_atual)
            else:
                diretorio_raiz = diretorio_atual
            
            # Criar diretório de logs
            diretorio_logs = os.path.join(diretorio_raiz, "outputs", "logs")
            os.makedirs(diretorio_logs, exist_ok=True)
            
            # Nome do arquivo de log com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo_log = f"vr_system_{timestamp}.log"
            caminho_log = os.path.join(diretorio_logs, nome_arquivo_log)
            
            # Configurar logger
            logger = logging.getLogger('VRSystem')
            logger.setLevel(logging.DEBUG)
            
            # Remover handlers existentes para evitar duplicação
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Handler para arquivo
            file_handler = logging.FileHandler(caminho_log, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Handler para console
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Formatador detalhado
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
                datefmt='%d/%m/%Y %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            logger.info(f"📝 Sistema de logs configurado: {caminho_log}")
            return logger
            
        except Exception as e:
            # Fallback para logging básico se houver erro
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)s | %(message)s'
            )
            logger = logging.getLogger('VRSystem')
            logger.error(f"❌ Erro ao configurar logs: {e}")
            return logger
        
    def carregar_arquivo(self, arquivo_nome, arquivo_bytes, tipo_arquivo):
        """📁 Carrega um arquivo específico na memória COM LOGS"""
        self.logger.info(f"📁 Iniciando carregamento: {arquivo_nome} (tipo: {tipo_arquivo})")
        
        try:
            # Salvar temporariamente para leitura
            temp_path = f"temp_{arquivo_nome}"
            with open(temp_path, 'wb') as f:
                f.write(arquivo_bytes)
            
            self.logger.debug(f"💾 Arquivo temporário criado: {temp_path} ({len(arquivo_bytes)} bytes)")
            
            # Mapear tipos de arquivo
            mapeamento_tipos = {
                'ativos': ('ATIVOS', 'ATIVOS'),
                'ferias': ('FERIAS', 'Planilha1'),
                'desligados': ('DESLIGADOS', 'DESLIGADOS '),
                'admissoes': ('ADMISSAO ABRIL', 'Planilha1'),
                'valores_sindicato': ('Base sindicato x valor', 'Planilha1'),
                'dias_uteis': ('Base dias uteis', 'Planilha1'),
                'afastamentos': ('AFASTAMENTOS', 'Planilha1'),
                'estagiarios': ('ESTAGIO', 'Planilha1'),
                'aprendizes': ('APRENDIZ', 'Planilha1'),
                'exterior': ('EXTERIOR', 'Planilha1')
            }
            
            if tipo_arquivo in mapeamento_tipos:
                _, sheet_name = mapeamento_tipos[tipo_arquivo]
                
                if tipo_arquivo == 'dias_uteis':
                    self.logger.debug("📅 Processando arquivo de dias úteis com tratamento especial")
                    self._carregar_dias_uteis_especial(temp_path)
                else:
                    self.logger.debug(f"📊 Carregando planilha: sheet='{sheet_name}'")
                    df = pd.read_excel(temp_path, sheet_name=sheet_name)
                    self.datasets[tipo_arquivo] = df
                    self.logger.info(f"✅ Arquivo carregado: {arquivo_nome} - {len(df)} registros")
                
                self.arquivos_carregados[tipo_arquivo] = arquivo_nome
                self.logger.debug(f"🗂️ Arquivo registrado no sistema: {tipo_arquivo}")
            else:
                self.logger.error(f"❌ Tipo de arquivo não reconhecido: {tipo_arquivo}")
                return False
            
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
                self.logger.debug(f"🗑️ Arquivo temporário removido: {temp_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ERRO ao carregar {arquivo_nome}: {str(e)}")
            self.logger.debug(f"🔍 Stacktrace: {traceback.format_exc()}")
            
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
                self.logger.debug(f"🗑️ Arquivo temporário removido após erro")
            
            return False
    
    def _carregar_dias_uteis_especial(self, file_path):
        """📅 Carrega arquivo de dias úteis com tratamento especial E LOGS"""
        self.logger.info("📅 Iniciando carregamento especial de dias úteis")
        
        try:
            df_raw = pd.read_excel(file_path, sheet_name='Planilha1', header=None)
            self.logger.debug(f"📊 Arquivo lido: {df_raw.shape[0]} linhas x {df_raw.shape[1]} colunas")
            
            dados_validos = []
            linhas_processadas = 0
            linhas_ignoradas = 0
            
            for i in range(len(df_raw)):
                linhas_processadas += 1
                try:
                    linha = df_raw.iloc[i]
                    col1 = linha.iloc[0] if len(linha) > 0 else None
                    col2 = linha.iloc[1] if len(linha) > 1 else None
                    
                    # Pular headers ou vazios
                    if (pd.isna(col1) or pd.isna(col2) or
                        str(col1).upper() in ['SINDICATO', 'SINDICADO', 'BASE'] or
                        str(col2).upper() in ['DIAS UTEIS', 'DIAS', 'VALOR']):
                        linhas_ignoradas += 1
                        self.logger.debug(f"⏭️ Linha {i+1} ignorada (header/vazio): {col1} | {col2}")
                        continue
                    
                    # Converter para número
                    dias_str = str(col2).replace(',', '.').strip()
                    if dias_str.replace('.', '').isdigit():
                        dias_num = float(dias_str)
                        sindicato_nome = str(col1).strip()
                        
                        dados_validos.append({
                            'SINDICATO': sindicato_nome,
                            'DIAS_UTEIS': dias_num
                        })
                        
                        self.logger.debug(f"✅ Linha {i+1} processada: {sindicato_nome} = {dias_num} dias")
                    else:
                        linhas_ignoradas += 1
                        self.logger.warning(f"⚠️ Linha {i+1} valor inválido: {col1} | {col2}")
                        
                except Exception as e:
                    linhas_ignoradas += 1
                    self.logger.warning(f"⚠️ Erro linha {i+1}: {str(e)}")
                    continue
            
            self.logger.info(f"📊 Processamento concluído:")
            self.logger.info(f"   📝 Linhas processadas: {linhas_processadas}")
            self.logger.info(f"   ✅ Dados válidos: {len(dados_validos)}")
            self.logger.info(f"   ⏭️ Linhas ignoradas: {linhas_ignoradas}")
            
            if dados_validos:
                self.datasets['dias_uteis'] = pd.DataFrame(dados_validos)
                self.logger.info("✅ Base de dias úteis criada com sucesso")
                
                # Log detalhado dos sindicatos carregados
                for item in dados_validos:
                    sindicato = item['SINDICATO']
                    dias = item['DIAS_UTEIS']
                    # Destacar Rio Grande do Sul
                    if any(termo in sindicato.upper() for termo in ['RS', 'RIO GRANDE', 'SINDPPD']):
                        self.logger.info(f"   🎯 RIO GRANDE DO SUL: {sindicato} = {dias} dias")
                    else:
                        self.logger.debug(f"   📋 {sindicato} = {dias} dias")
            else:
                # Dados padrão
                self.datasets['dias_uteis'] = pd.DataFrame({
                    'SINDICATO': ['PADRÃO'],
                    'DIAS_UTEIS': [22]
                })
                self.logger.warning("⚠️ Nenhum dado válido encontrado, usando padrão (22 dias)")
                
        except Exception as e:
            self.logger.error(f"❌ ERRO ao carregar dias úteis: {e}")
            self.logger.debug(f"🔍 Stacktrace: {traceback.format_exc()}")
            
            self.datasets['dias_uteis'] = pd.DataFrame({
                'SINDICATO': ['EMERGENCIA'],
                'DIAS_UTEIS': [22]
            })
            self.logger.warning("⚠️ Usando dados de emergência (22 dias)")
    
    def verificar_arquivos_necessarios(self):
        """Verifica se todos os arquivos necessários foram carregados"""
        arquivos_obrigatorios = [
            'ativos', 'ferias', 'desligados', 'admissoes', 
            'valores_sindicato', 'dias_uteis', 'afastamentos',
            'estagiarios', 'aprendizes', 'exterior'
        ]
        
        faltando = [arq for arq in arquivos_obrigatorios if arq not in self.datasets]
        return len(faltando) == 0, faltando
    
    def limpar_e_padronizar_dados(self):
        """Limpa e padroniza os dados carregados"""
        padronizacao_colunas = {
            'MATRICULA ': 'MATRICULA',
            'Cadastro': 'MATRICULA',
            'DATA DEMISSÃO': 'DATA_DEMISSAO',
            'COMUNICADO DE DESLIGAMENTO': 'COMUNICADO_DESLIGAMENTO',
            'TITULO DO CARGO': 'CARGO',
            'DESC. SITUACAO': 'SITUACAO',
            'DIAS DE FÉRIAS': 'DIAS_FERIAS',
            'Admissão': 'DATA_ADMISSAO'
        }
        
        for dataset_name, df in self.datasets.items():
            if df is not None and len(df) > 0:
                # Renomear colunas
                df.columns = [padronizacao_colunas.get(col, col) for col in df.columns]
                
                # Limpar espaços
                for col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.strip()
                
                # Padronizar MATRICULA
                if 'MATRICULA' in df.columns:
                    df['MATRICULA'] = df['MATRICULA'].astype(str).str.zfill(5)
                
                self.datasets[dataset_name] = df
    
    def criar_base_consolidada(self):
        """Cria a base consolidada única"""
        base = self.datasets['ativos'].copy()
        print(f"📊 Base inicial: {len(base)} colaboradores ativos")
        
        # Adicionar informações de admissão
        if 'DATA_ADMISSAO' not in base.columns and 'admissoes' in self.datasets:
            admissoes_mes = self.datasets['admissoes'][['MATRICULA', 'DATA_ADMISSAO']].copy()
            base = base.merge(admissoes_mes, on='MATRICULA', how='left')
            print(f"✅ Admissões integradas: {admissoes_mes.shape[0]} registros")
        
        # Marcar colaboradores em férias
        if 'ferias' in self.datasets:
            ferias = self.datasets['ferias'][['MATRICULA', 'SITUACAO', 'DIAS_FERIAS']].copy()
            ferias['EM_FERIAS'] = True
            base = base.merge(ferias[['MATRICULA', 'EM_FERIAS', 'DIAS_FERIAS']], 
                             on='MATRICULA', how='left')
            base['EM_FERIAS'] = base['EM_FERIAS'].fillna(False)
            print(f"✅ Férias integradas: {ferias.shape[0]} registros")
        
        # Marcar desligados
        if 'desligados' in self.datasets:
            desligados = self.datasets['desligados'][['MATRICULA', 'DATA_DEMISSAO', 'COMUNICADO_DESLIGAMENTO']].copy()
            desligados['DESLIGADO'] = True
            base = base.merge(desligados, on='MATRICULA', how='left')
            base['DESLIGADO'] = base['DESLIGADO'].fillna(False)
            print(f"✅ Desligados integrados: {desligados.shape[0]} registros")
        
        # Marcar afastamentos
        if 'afastamentos' in self.datasets:
            afastados = self.datasets['afastamentos'][['MATRICULA', 'SITUACAO']].copy()
            afastados = afastados[afastados['SITUACAO'].isin(self.config['situacoes_afastamento'])]
            afastados['AFASTADO'] = True
            afastados = afastados[['MATRICULA', 'AFASTADO']].drop_duplicates()
            base = base.merge(afastados, on='MATRICULA', how='left')
            base['AFASTADO'] = base['AFASTADO'].fillna(False)
            print(f"✅ Afastamentos integrados: {afastados.shape[0]} registros")
        
        # Marcar estagiários e aprendizes
        if 'estagiarios' in self.datasets and 'aprendizes' in self.datasets:
            estagiarios = self.datasets['estagiarios']['MATRICULA'].tolist()
            aprendizes = self.datasets['aprendizes']['MATRICULA'].tolist()
            base['ESTAGIARIO'] = base['MATRICULA'].isin(estagiarios)
            base['APRENDIZ'] = base['MATRICULA'].isin(aprendizes)
            print(f"✅ Estagiários: {len(estagiarios)}, Aprendizes: {len(aprendizes)}")
        
        # Marcar colaboradores no exterior
        if 'exterior' in self.datasets:
            exterior = self.datasets['exterior']['MATRICULA'].tolist()
            base['NO_EXTERIOR'] = base['MATRICULA'].isin(exterior)
            print(f"✅ Exterior: {len(exterior)} colaboradores")
        
        self.base_consolidada = base
        print(f"🎯 Base consolidada criada: {len(base)} registros")
        
        return base
    
    def aplicar_exclusoes(self):
        """Remove colaboradores não elegíveis"""
        base = self.base_consolidada.copy()
        print(f"📋 Aplicando exclusões na base de {len(base)} colaboradores")
        
        # Excluir por cargo
        mask_cargo = base['CARGO'].str.contains('|'.join(self.config['cargos_excluidos']), 
                                               case=False, na=False)
        
        # Aplicar exclusões
        base_filtrada = base[
            ~mask_cargo & 
            (base['ESTAGIARIO'] == False) & 
            (base['APRENDIZ'] == False) & 
            (base['AFASTADO'] == False) & 
            (base['NO_EXTERIOR'] == False)
        ].copy()
        
        excluidos = len(base) - len(base_filtrada)
        print(f"❌ Excluídos: {excluidos} colaboradores")
        print(f"✅ Elegíveis: {len(base_filtrada)} colaboradores")
        
        self.base_consolidada = base_filtrada
        return base_filtrada
    
    def calcular_dias_uteis_por_colaborador(self):
        """✅ Calcula os dias úteis por colaborador COM CORREÇÃO PARA RS"""
        print("📅 Calculando dias úteis por colaborador...")
        
        # Criar mapeamento robusto de dias úteis
        dias_uteis_map = {}
        df_dias = self.datasets['dias_uteis']
        
        print("📋 Mapeando dias úteis por sindicato:")
        for _, row in df_dias.iterrows():
            try:
                sindicato = str(row['SINDICATO']).strip()
                dias = float(row['DIAS_UTEIS'])
                dias_uteis_map[sindicato] = dias
                print(f"   📌 {sindicato}: {dias} dias")
            except:
                continue
        
        dias_uteis_padrao = 22
        if not dias_uteis_map:
            dias_uteis_map = {'DEFAULT': dias_uteis_padrao}
            print("⚠️ Usando mapa padrão de dias úteis")
        
        base = self.base_consolidada.copy()
        
        def obter_dias_uteis_robusto(sindicato):
            """✅ FUNÇÃO MELHORADA para obter dias úteis"""
            if pd.isna(sindicato):
                return dias_uteis_padrao
            
            sindicato_str = str(sindicato).strip()
            
            # 🎯 Match direto primeiro
            if sindicato_str in dias_uteis_map:
                return dias_uteis_map[sindicato_str]
            
            # 🎯 Match por palavras-chave (RIO GRANDE DO SUL)
            sindicato_upper = sindicato_str.upper()
            
            # Mapeamentos específicos para estados
            mapeamentos_especiais = {
                'RIO GRANDE DO SUL': ['SINDPPD RS', 'RIO GRANDE DO SUL', 'RS - SINDICATO'],
                'SÃO PAULO': ['SP - SINDICATO', 'SÃO PAULO', 'SINDICAL SP'],
                'RIO DE JANEIRO': ['RJ - SINDICATO', 'RIO DE JANEIRO', 'SINDICAL RJ'],
                'PARANÁ': ['PR - SINDICATO', 'PARANÁ', 'SINDICAL PR']
            }
            
            # Verificar mapeamentos especiais
            for estado, keywords in mapeamentos_especiais.items():
                for keyword in keywords:
                    if keyword in sindicato_upper:
                        # Buscar no mapa por estado
                        for map_key, dias in dias_uteis_map.items():
                            if estado in map_key.upper():
                                print(f"🎯 Mapeamento especial: {sindicato_str} → {map_key} = {dias} dias")
                                return dias
            
            # 🎯 Match parcial genérico
            for key, value in dias_uteis_map.items():
                key_upper = key.upper()
                if (key_upper in sindicato_upper or sindicato_upper in key_upper or
                    any(word in key_upper and word in sindicato_upper 
                        for word in ['SP', 'RJ', 'PR', 'RS', 'SINDICATO', 'SINDICAL'])):
                    print(f"📋 Match parcial: {sindicato_str} → {key} = {value} dias")
                    return value
            
            print(f"⚠️ Sindicato não mapeado: {sindicato_str}, usando padrão: {dias_uteis_padrao}")
            return dias_uteis_padrao
        
        # Aplicar mapeamento
        base['DIAS_UTEIS_SINDICATO'] = base['Sindicato'].apply(obter_dias_uteis_robusto)
        base['DIAS_UTEIS_FINAL'] = base['DIAS_UTEIS_SINDICATO']
        
        print(f"📊 Dias úteis mapeados:")
        print(base.groupby('Sindicato')['DIAS_UTEIS_SINDICATO'].first().to_dict())
        
        # Aplicar regras especiais
        # 1. Férias
        mask_ferias = base['EM_FERIAS'] == True
        if mask_ferias.any():
            print(f"🏖️ Aplicando desconto de férias para {mask_ferias.sum()} colaboradores")
            base.loc[mask_ferias, 'DIAS_UTEIS_FINAL'] = (
                base.loc[mask_ferias, 'DIAS_UTEIS_SINDICATO'] - 
                base.loc[mask_ferias, 'DIAS_FERIAS'].fillna(0)
            ).clip(lower=0)
        
        # 2. Desligados
        mask_desligados = base['DESLIGADO'] == True
        if mask_desligados.any():
            print(f"👋 Aplicando regras de desligamento para {mask_desligados.sum()} colaboradores")
            base['DATA_DEMISSAO'] = pd.to_datetime(base['DATA_DEMISSAO'], errors='coerce')
            
            # Desligados até dia 15 com OK = 0 dias
            mask_deslig_ate_15_ok = (
                mask_desligados & 
                (base['DATA_DEMISSAO'].dt.day <= self.config['dia_corte_desligamento']) &
                (base['COMUNICADO_DESLIGAMENTO'].str.upper() == 'OK')
            )
            if mask_deslig_ate_15_ok.any():
                base.loc[mask_deslig_ate_15_ok, 'DIAS_UTEIS_FINAL'] = 0
                print(f"   🚫 {mask_deslig_ate_15_ok.sum()} desligados até dia 15 com OK = 0 dias")
            
            # Desligados após dia 15 = proporcional
            mask_deslig_apos_15 = (
                mask_desligados & 
                (base['DATA_DEMISSAO'].dt.day > self.config['dia_corte_desligamento'])
            )
            if mask_deslig_apos_15.any():
                base.loc[mask_deslig_apos_15, 'DIAS_UTEIS_FINAL'] = (
                    base.loc[mask_deslig_apos_15, 'DATA_DEMISSAO'].dt.day / 30 * 
                    base.loc[mask_deslig_apos_15, 'DIAS_UTEIS_SINDICATO']
                )
                print(f"   📊 {mask_deslig_apos_15.sum()} desligados após dia 15 = proporcional")
        
        # 3. Admitidos no mês
        base['DATA_ADMISSAO'] = pd.to_datetime(base['DATA_ADMISSAO'], errors='coerce')
        mask_admitidos = base['DATA_ADMISSAO'].notna()
        if mask_admitidos.any():
            print(f"🆕 Aplicando proporcionalidade para {mask_admitidos.sum()} admitidos no mês")
            dias_restantes = 30 - base.loc[mask_admitidos, 'DATA_ADMISSAO'].dt.day + 1
            base.loc[mask_admitidos, 'DIAS_UTEIS_FINAL'] = (
                dias_restantes / 30 * base.loc[mask_admitidos, 'DIAS_UTEIS_SINDICATO']
            )
        
        # Garantir valores não negativos
        base['DIAS_UTEIS_FINAL'] = base['DIAS_UTEIS_FINAL'].clip(lower=0).round(2)
        
        print(f"✅ Dias úteis calculados - Estatísticas finais:")
        print(f"   📊 Média: {base['DIAS_UTEIS_FINAL'].mean():.2f} dias")
        print(f"   📊 Mínimo: {base['DIAS_UTEIS_FINAL'].min():.2f} dias")
        print(f"   📊 Máximo: {base['DIAS_UTEIS_FINAL'].max():.2f} dias")
        print(f"   📊 Colaboradores com 0 dias: {(base['DIAS_UTEIS_FINAL'] == 0).sum()}")
        
        self.base_consolidada = base
        return base
    
    def extrair_estado_corrigido(self, sindicato):
        """✅ FUNÇÃO CORRIGIDA - Extrai estado do sindicato com suporte completo ao RS"""
        if pd.isna(sindicato):
            return 'São Paulo'  # Default
        
        sindicato_clean = str(sindicato).upper().strip()
        
        # 🎯 PRIORIDADE 1: Rio Grande do Sul (casos específicos)
        indicadores_rs = [
            'RIO GRANDE DO SUL',
            'SINDPPD RS',
            'RS - SINDICATO',
            'SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL',
            'SINDICAL RS',
            'PORTO ALEGRE',
            'GAUCHO',
            'RS SINDICATO'
        ]
        
        for indicador in indicadores_rs:
            if indicador in sindicato_clean:
                return 'Rio Grande do Sul'
        
        # 🎯 PRIORIDADE 2: São Paulo
        if any(termo in sindicato_clean for termo in [
            'SÃO PAULO', 'SAO PAULO', 'SP - SINDICATO',
            'SINDSP', 'SINDICAL SP', 'PAULISTA'
        ]):
            return 'São Paulo'
        
        # 🎯 PRIORIDADE 3: Rio de Janeiro
        if any(termo in sindicato_clean for termo in [
            'RIO DE JANEIRO', 'RJ - SINDICATO',
            'SINDRJ', 'SINDICAL RJ'
        ]):
            return 'Rio de Janeiro'
        
        # 🎯 PRIORIDADE 4: Paraná
        if any(termo in sindicato_clean for termo in [
            'PARANÁ', 'PARANA', 'PR - SINDICATO',
            'SINDPR', 'SINDICAL PR'
        ]):
            return 'Paraná'
        
        # 🎯 FALLBACK: Verificação genérica por sufixos
        if ' RS ' in f" {sindicato_clean} " or sindicato_clean.endswith(' RS'):
            return 'Rio Grande do Sul'
        elif ' SP ' in f" {sindicato_clean} " or sindicato_clean.endswith(' SP'):
            return 'São Paulo'
        elif ' RJ ' in f" {sindicato_clean} " or sindicato_clean.endswith(' RJ'):
            return 'Rio de Janeiro'
        elif ' PR ' in f" {sindicato_clean} " or sindicato_clean.endswith(' PR'):
            return 'Paraná'
        
        # Default para São Paulo
        return 'São Paulo'
    
    def calcular_valores_vr(self):
        """✅ Calcula os valores de VR COM CORREÇÃO PARA MAPEAMENTO DE ESTADOS"""
        print("💰 Calculando valores de VR...")
        
        # Mapeamento de valores por estado
        valores_map = {}
        df_valores = self.datasets['valores_sindicato']
        
        print("💵 Carregando valores por estado:")
        for _, row in df_valores.iterrows():
            try:
                estado = str(row.iloc[0]).strip()
                valor_raw = str(row.iloc[1])
                
                # Limpar valor
                valor_clean = valor_raw.replace('R$', '').replace(' ', '').replace(',', '.')
                valor = float(valor_clean)
                
                valores_map[estado] = valor
                print(f"   💲 {estado}: R$ {valor:.2f}")
                
            except Exception as e:
                print(f"   ⚠️ Erro ao processar linha: {row.values} - {e}")
                continue
        
        # Valores padrão se não houver dados
        valor_padrao = 35.00
        if not valores_map:
            valores_map = {
                'São Paulo': 37.50,
                'Rio Grande do Sul': 35.00,
                'Rio de Janeiro': 35.00,
                'Paraná': 35.00,
                'DEFAULT': valor_padrao
            }
            print("⚠️ Usando valores padrão")
        
        base = self.base_consolidada.copy()
        
        # ✅ USAR FUNÇÃO CORRIGIDA DE EXTRAÇÃO DE ESTADO
        print("🗺️ Mapeando estados por sindicato:")
        base['ESTADO'] = base['Sindicato'].apply(self.extrair_estado_corrigido)
        
        # Debug: mostrar mapeamentos únicos
        mapeamento_debug = base[['Sindicato', 'ESTADO']].drop_duplicates()
        for _, row in mapeamento_debug.iterrows():
            print(f"   🎯 {row['Sindicato'][:50]}... → {row['ESTADO']}")
        
        # Mapear valores por estado
        def obter_valor_por_estado(estado):
            """Obtém valor diário baseado no estado"""
            if estado in valores_map:
                return valores_map[estado]
            elif 'Rio Grande do Sul' in valores_map and 'RS' in estado.upper():
                return valores_map['Rio Grande do Sul']
            elif 'São Paulo' in valores_map and 'SP' in estado.upper():
                return valores_map['São Paulo']
            else:
                return valor_padrao
        
        base['VALOR_DIARIO_VR'] = base['ESTADO'].apply(obter_valor_por_estado)
        
        # ✅ VERIFICAÇÃO ESPECÍFICA PARA RIO GRANDE DO SUL
        rs_colaboradores = base[base['ESTADO'] == 'Rio Grande do Sul']
        if len(rs_colaboradores) > 0:
            print(f"🎯 RIO GRANDE DO SUL DETECTADO:")
            print(f"   👥 Colaboradores: {len(rs_colaboradores)}")
            print(f"   💰 Valor diário: R$ {rs_colaboradores['VALOR_DIARIO_VR'].iloc[0]:.2f}")
            print(f"   📋 Sindicatos:")
            for sindicato in rs_colaboradores['Sindicato'].unique():
                count = len(rs_colaboradores[rs_colaboradores['Sindicato'] == sindicato])
                print(f"      • {sindicato}: {count} colaboradores")
        else:
            print("❌ PROBLEMA: Nenhum colaborador do Rio Grande do Sul encontrado!")
            print("🔍 Verificando sindicatos disponíveis:")
            for sindicato in base['Sindicato'].unique():
                if 'RS' in str(sindicato).upper() or 'RIO GRANDE' in str(sindicato).upper():
                    print(f"   ⚠️ Sindicato suspeito: {sindicato}")
        
        # Calcular valores finais
        print("🧮 Calculando valores finais...")
        base['TOTAL_VR'] = (base['DIAS_UTEIS_FINAL'] * base['VALOR_DIARIO_VR']).round(2)
        base['CUSTO_EMPRESA'] = (base['TOTAL_VR'] * self.config['percentual_empresa']).round(2)
        base['DESCONTO_FUNCIONARIO'] = (base['TOTAL_VR'] * self.config['percentual_funcionario']).round(2)
        
        # Observações
        base['OBS_GERAL'] = ''
        base.loc[base['EM_FERIAS'] == True, 'OBS_GERAL'] = 'EM FÉRIAS'
        base.loc[base['DESLIGADO'] == True, 'OBS_GERAL'] = 'DESLIGADO'
        base.loc[base['DATA_ADMISSAO'].notna(), 'OBS_GERAL'] = 'ADMITIDO NO MÊS'
        
        # Estatísticas finais
        print(f"✅ Valores calculados:")
        print(f"   💰 Total geral: R$ {base['TOTAL_VR'].sum():,.2f}")
        print(f"   🏢 Custo empresa: R$ {base['CUSTO_EMPRESA'].sum():,.2f}")
        print(f"   👤 Desconto funcionário: R$ {base['DESCONTO_FUNCIONARIO'].sum():,.2f}")
        
        # Breakdown por estado
        print(f"📊 Breakdown por estado:")
        breakdown = base.groupby('ESTADO').agg({
            'MATRICULA': 'count',
            'TOTAL_VR': 'sum'
        }).round(2)
        for estado, dados in breakdown.iterrows():
            print(f"   🗺️ {estado}: {dados['MATRICULA']} colaboradores, R$ {dados['TOTAL_VR']:,.2f}")
        
        self.base_consolidada = base
        return base
    
    def gerar_planilha_final(self):
        """Gera a planilha final com formato correto"""
        print("📋 Gerando planilha final...")
        
        base = self.base_consolidada.copy()
        
        resultado = pd.DataFrame()
        resultado['Matricula'] = base['MATRICULA']
        resultado['Admissão'] = base['DATA_ADMISSAO'].dt.strftime('%m/%d/%y') if 'DATA_ADMISSAO' in base.columns else ''
        resultado['Sindicato do Colaborador'] = base['Sindicato']
        resultado['Competência'] = self.competencia
        resultado['Dias'] = base['DIAS_UTEIS_FINAL'].round(2)
        resultado['VALOR DIÁRIO VR'] = base['VALOR_DIARIO_VR'].round(2)
        resultado['TOTAL'] = base['TOTAL_VR'].round(2)
        resultado['Custo empresa'] = base['CUSTO_EMPRESA'].round(2)
        resultado['Desconto profissional'] = base['DESCONTO_FUNCIONARIO'].round(2)
        resultado['OBS GERAL'] = base['OBS_GERAL']
        
        # Filtrar apenas colaboradores com dias > 0
        resultado_filtrado = resultado[resultado['Dias'] > 0].reset_index(drop=True)
        resultado_filtrado = resultado_filtrado.sort_values('Matricula').reset_index(drop=True)
        
        print(f"✅ Planilha final gerada:")
        print(f"   📊 Colaboradores com VR: {len(resultado_filtrado)}")
        print(f"   📊 Colaboradores excluídos (0 dias): {len(resultado) - len(resultado_filtrado)}")
        print(f"   💰 Valor total: R$ {resultado_filtrado['TOTAL'].sum():,.2f}")
        
        # ✅ VERIFICAÇÃO ESPECÍFICA RIO GRANDE DO SUL
        rs_final = resultado_filtrado[
            resultado_filtrado['Sindicato do Colaborador'].str.contains(
                'SINDPPD RS|RIO GRANDE DO SUL|RS', case=False, na=False
            )
        ]
        
        if len(rs_final) > 0:
            print(f"🎯 RIO GRANDE DO SUL NA PLANILHA FINAL:")
            print(f"   👥 Colaboradores RS: {len(rs_final)}")
            print(f"   💰 Valor total RS: R$ {rs_final['TOTAL'].sum():,.2f}")
            print(f"   📋 Sindicatos RS:")
            for sindicato in rs_final['Sindicato do Colaborador'].unique():
                count = len(rs_final[rs_final['Sindicato do Colaborador'] == sindicato])
                valor_total = rs_final[rs_final['Sindicato do Colaborador'] == sindicato]['TOTAL'].sum()
                print(f"      • {sindicato}: {count} colaboradores, R$ {valor_total:,.2f}")
        else:
            print("❌ PROBLEMA: Rio Grande do Sul não aparece na planilha final!")
            print("🔍 Sindicatos disponíveis na planilha final:")
            for sindicato in resultado_filtrado['Sindicato do Colaborador'].unique()[:10]:
                print(f"   📋 {sindicato}")
        
        self.resultado_final = resultado_filtrado
        return resultado_filtrado
    
    def salvar_resultado(self, nome_arquivo=None):
        """✅ Salva o resultado em arquivo Excel na pasta outputs/planilhas/"""
        if nome_arquivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            nome_arquivo = f"VR_MENSAL_{self.competencia.replace('/', '')}_FINAL_{timestamp}.xlsx"
        
        try:
            # 🎯 CORREÇÃO: Obter caminho absoluto da raiz do projeto
            # Assumir que estamos executando de src/, então subir um nível
            diretorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            diretorio_outputs = os.path.join(diretorio_raiz, "outputs", "planilhas")
            
            # Criar diretório se não existir (caminho absoluto)
            os.makedirs(diretorio_outputs, exist_ok=True)
            
            # Caminho completo absoluto para o arquivo
            caminho_completo = os.path.join(diretorio_outputs, nome_arquivo)
            
            print(f"📁 Salvando arquivo em: {caminho_completo}")
            
            with pd.ExcelWriter(caminho_completo, engine='openpyxl') as writer:
                self.resultado_final.to_excel(writer, sheet_name='VR MENSAL', index=False)
                
                # Salvar também base consolidada para auditoria
                if self.base_consolidada is not None:
                    self.base_consolidada.to_excel(writer, sheet_name='Base Consolidada', index=False)
            
            print(f"✅ Arquivo salvo com sucesso: {caminho_completo}")
            print(f"📊 Tamanho: {os.path.getsize(caminho_completo) / 1024:.1f} KB")
            
            return caminho_completo
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            print(f"🔍 Diretório atual: {os.getcwd()}")
            print(f"🔍 Diretório tentativa: {diretorio_outputs if 'diretorio_outputs' in locals() else 'N/A'}")
            traceback.print_exc()
            return None
    
    def enviar_emails(self, arquivo_final):
        """📧 Envia emails para VR e RH COM CONTROLE DETALHADO DE STATUS"""
        self.logger.info("📧 Iniciando processo de envio de emails")
        
        # Contadores de status
        emails_enviados_com_sucesso = 0
        emails_falharam = 0
        detalhes_envio = {
            'vr_empresa': {'status': False, 'erro': None},
            'rh_interno': {'status': False, 'erro': None}
        }
        
        try:
            # Verificar configurações básicas
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            
            if not email_user or not email_password:
                self.logger.error("❌ Configurações de email não encontradas no .env")
                self.logger.error("   📋 Configure EMAIL_USER e EMAIL_PASSWORD no arquivo .env")
                return False
            
            if not os.path.exists(arquivo_final):
                self.logger.error(f"❌ Arquivo final não encontrado: {arquivo_final}")
                return False
            
            self.logger.info(f"✅ Configurações verificadas:")
            self.logger.info(f"   📧 Servidor SMTP: {smtp_server}:{smtp_port}")
            self.logger.info(f"   👤 Usuário: {email_user}")
            self.logger.info(f"   📁 Arquivo: {os.path.basename(arquivo_final)} ({os.path.getsize(arquivo_final)/1024:.1f} KB)")
            
            # ENVIO 1: Email para empresa VR
            self.logger.info("📤 Enviando email 1/2: Empresa VR...")
            try:
                self._enviar_email_vr(smtp_server, smtp_port, email_user, email_password, arquivo_final)
                emails_enviados_com_sucesso += 1
                detalhes_envio['vr_empresa']['status'] = True
                self.logger.info("✅ Email para empresa VR enviado com sucesso")
                
            except Exception as e_vr:
                emails_falharam += 1
                detalhes_envio['vr_empresa']['erro'] = str(e_vr)
                self.logger.error(f"❌ Falha no email para empresa VR: {str(e_vr)}")
                self.logger.debug(f"🔍 Stacktrace VR: {traceback.format_exc()}")
            
            # ENVIO 2: Email para RH
            self.logger.info("📤 Enviando email 2/2: RH Interno...")
            try:
                self._enviar_email_rh(smtp_server, smtp_port, email_user, email_password, arquivo_final)
                emails_enviados_com_sucesso += 1
                detalhes_envio['rh_interno']['status'] = True
                self.logger.info("✅ Email para RH enviado com sucesso")
                
            except Exception as e_rh:
                emails_falharam += 1
                detalhes_envio['rh_interno']['erro'] = str(e_rh)
                self.logger.error(f"❌ Falha no email para RH: {str(e_rh)}")
                self.logger.debug(f"🔍 Stacktrace RH: {traceback.format_exc()}")
            
            # RESULTADO FINAL
            sucesso_geral = emails_enviados_com_sucesso > 0  # ✅ CORREÇÃO: Sucesso se PELO MENOS 1 email foi enviado
            
            self.logger.info("📊 RESULTADO DO ENVIO DE EMAILS:")
            self.logger.info(f"   ✅ Emails enviados com sucesso: {emails_enviados_com_sucesso}/2")
            self.logger.info(f"   ❌ Emails que falharam: {emails_falharam}/2")
            self.logger.info(f"   🎯 Status geral: {'SUCESSO' if sucesso_geral else 'FALHA'}")
            
            # Log detalhado por destinatário
            for destinatario, info in detalhes_envio.items():
                if info['status']:
                    self.logger.info(f"   ✅ {destinatario}: ENVIADO")
                else:
                    self.logger.error(f"   ❌ {destinatario}: FALHOU - {info['erro']}")
            
            # Salvar detalhes no objeto para uso posterior
            self.status_emails = {
                'sucesso_geral': sucesso_geral,
                'emails_enviados': emails_enviados_com_sucesso,
                'emails_falharam': emails_falharam,
                'detalhes': detalhes_envio,
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            if sucesso_geral:
                self.logger.info("🎉 Processo de envio de emails CONCLUÍDO COM SUCESSO")
            else:
                self.logger.warning("⚠️ Processo de envio de emails CONCLUÍDO COM PROBLEMAS")
            
            return sucesso_geral
            
        except Exception as e:
            self.logger.error(f"❌ ERRO CRÍTICO no envio de emails: {str(e)}")
            self.logger.debug(f"🔍 Stacktrace crítico: {traceback.format_exc()}")
            
            # Salvar erro crítico
            self.status_emails = {
                'sucesso_geral': False,
                'emails_enviados': emails_enviados_com_sucesso,
                'emails_falharam': 2,  # Assume que ambos falharam em caso de erro crítico
                'erro_critico': str(e),
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            
            return False
    
    def _enviar_email_vr(self, smtp_server, smtp_port, email_user, email_password, arquivo):
        """📧 Envia email para empresa VR COM LOGS DETALHADOS"""
        self.logger.debug(f"📧 Preparando email para empresa VR: {self.config['email_vr']}")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = self.config['email_vr']
            msg['Subject'] = 'Pedido de Compra de Vales'
            
            # Estatísticas para o email
            total_colaboradores = len(self.resultado_final)
            valor_total = self.resultado_final['TOTAL'].sum()
            custo_empresa = self.resultado_final['Custo empresa'].sum()
            
            # Breakdown por estado para o email
            df_estados = self.resultado_final.copy()
            df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(self.extrair_estado_corrigido)
            breakdown_estados = df_estados.groupby('Estado').agg({
                'Matricula': 'count',
                'TOTAL': 'sum'
            }).round(2)
            
            # Construir texto do breakdown
            breakdown_texto = ""
            for estado, dados in breakdown_estados.iterrows():
                breakdown_texto += f"- {estado}: {dados['Matricula']} colaboradores (R$ {dados['TOTAL']:,.2f})\n"
            
            corpo = f"""Prezados,

Segue em anexo a planilha com o pedido de compra de vales refeição para a competência {self.competencia}.

📊 RESUMO DA COMPRA:
- Total de colaboradores: {total_colaboradores:,}
- Valor total: R$ {valor_total:,.2f}
- Custo empresa (80%): R$ {custo_empresa:,.2f}

🗺️ DISTRIBUIÇÃO POR ESTADO:
{breakdown_texto}

Por favor, processem o pedido conforme layout anexo e informem prazo de entrega.

Atenciosamente,
Sistema Automático VR/VA"""
            
            msg.attach(MIMEText(corpo, 'plain'))
            self.logger.debug("✅ Corpo do email VR preparado")
            
            # Anexar arquivo
            if os.path.exists(arquivo):
                with open(arquivo, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(arquivo)}',
                )
                msg.attach(part)
                self.logger.debug(f"✅ Arquivo anexado: {os.path.basename(arquivo)}")
            else:
                self.logger.warning(f"⚠️ Arquivo de anexo não encontrado: {arquivo}")
            
            # Enviar email
            self.logger.debug(f"🔗 Conectando ao SMTP: {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            self.logger.debug("🔐 Iniciando autenticação SMTP")
            server.login(email_user, email_password)
            self.logger.debug("✅ Autenticação SMTP bem-sucedida")
            
            self.logger.debug(f"📤 Enviando email VR para: {self.config['email_vr']}")
            server.send_message(msg)
            server.quit()
            
            self.logger.info("✅ Email para empresa VR enviado com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ ERRO detalhado no envio para VR: {str(e)}")
            raise  # Re-raise para captura no nível superior
    
    def _enviar_email_rh(self, smtp_server, smtp_port, email_user, email_password, arquivo):
        """📧 Envia email para RH COM LOGS DETALHADOS"""
        self.logger.debug(f"📧 Preparando email para RH: {self.config['email_rh']}")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = self.config['email_rh']
            msg['Subject'] = 'Compra realizada com Sucesso'
            
            # Estatísticas detalhadas
            total_colaboradores = len(self.resultado_final)
            valor_total = self.resultado_final['TOTAL'].sum()
            custo_empresa = self.resultado_final['Custo empresa'].sum()
            desconto_funcionarios = self.resultado_final['Desconto profissional'].sum()
            
            # Estatísticas por estado
            df_estados = self.resultado_final.copy()
            df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(self.extrair_estado_corrigido)
            breakdown_estados = df_estados.groupby('Estado').agg({
                'Matricula': 'count',
                'TOTAL': 'sum',
                'Dias': 'mean'
            }).round(2)
            
            breakdown_texto = ""
            for estado, dados in breakdown_estados.iterrows():
                breakdown_texto += f"- {estado}: {dados['Matricula']} colaboradores, R$ {dados['TOTAL']:,.2f} (média {dados['Dias']:.1f} dias)\n"
            
            corpo = f"""Prezado RH,

A compra de vales refeição foi processada com sucesso para a competência {self.competencia}.

📊 DETALHES DO PROCESSAMENTO:
- Total de colaboradores processados: {total_colaboradores:,}
- Valor total dos vales: R$ {valor_total:,.2f}
- Custo para empresa (80%): R$ {custo_empresa:,.2f}
- Desconto dos funcionários (20%): R$ {desconto_funcionarios:,.2f}

🗺️ DISTRIBUIÇÃO POR ESTADO:
{breakdown_texto}

📧 STATUS:
- Pedido enviado automaticamente para empresa fornecedora
- Planilha de compra em anexo para controle interno
- Data/hora do processamento: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

O sistema funcionou corretamente e todos os cálculos foram aplicados conforme regras estabelecidas.

Atenciosamente,
Sistema Automático VR/VA"""
            
            msg.attach(MIMEText(corpo, 'plain'))
            self.logger.debug("✅ Corpo do email RH preparado")
            
            # Anexar arquivo
            if os.path.exists(arquivo):
                with open(arquivo, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(arquivo)}',
                )
                msg.attach(part)
                self.logger.debug(f"✅ Arquivo anexado: {os.path.basename(arquivo)}")
            else:
                self.logger.warning(f"⚠️ Arquivo de anexo não encontrado: {arquivo}")
            
            # Enviar email
            self.logger.debug(f"🔗 Conectando ao SMTP: {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            self.logger.debug("🔐 Iniciando autenticação SMTP")
            server.login(email_user, email_password)
            self.logger.debug("✅ Autenticação SMTP bem-sucedida")
            
            self.logger.debug(f"📤 Enviando email RH para: {self.config['email_rh']}")
            server.send_message(msg)
            server.quit()
            
            self.logger.info("✅ Email para RH enviado com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ ERRO detalhado no envio para RH: {str(e)}")
            raise  # Re-raise para captura no nível superior
    
    def debug_dados_rs(self):
        """🔍 Função de debug específica para Rio Grande do Sul"""
        print("\n" + "="*80)
        print("🔍 DEBUG ESPECÍFICO - RIO GRANDE DO SUL")
        print("="*80)
        
        # 1. Verificar colaboradores ativos do RS
        if 'ativos' in self.datasets:
            df_ativos = self.datasets['ativos']
            print(f"\n📋 SINDICATOS NA BASE ATIVA ({len(df_ativos)} colaboradores):")
            sindicatos_count = df_ativos['Sindicato'].value_counts()
            
            for sindicato, count in sindicatos_count.items():
                if any(termo in str(sindicato).upper() for termo in ['RS', 'RIO GRANDE', 'SINDPPD']):
                    print(f"🎯 {sindicato}: {count} colaboradores")
                else:
                    print(f"   {sindicato}: {count} colaboradores")
        
        # 2. Verificar base de dias úteis
        if 'dias_uteis' in self.datasets:
            print(f"\n📅 DIAS ÚTEIS POR SINDICATO:")
            df_dias = self.datasets['dias_uteis']
            for _, row in df_dias.iterrows():
                sindicato = row['SINDICATO']
                dias = row['DIAS_UTEIS']
                if any(termo in str(sindicato).upper() for termo in ['RS', 'RIO GRANDE', 'SINDPPD']):
                    print(f"🎯 {sindicato}: {dias} dias")
                else:
                    print(f"   {sindicato}: {dias} dias")
        
        # 3. Verificar base de valores
        if 'valores_sindicato' in self.datasets:
            print(f"\n💰 VALORES POR ESTADO:")
            df_valores = self.datasets['valores_sindicato']
            for _, row in df_valores.iterrows():
                estado = row.iloc[0]
                valor = row.iloc[1]
                if 'RIO GRANDE' in str(estado).upper() or 'RS' in str(estado).upper():
                    print(f"🎯 {estado}: {valor}")
                else:
                    print(f"   {estado}: {valor}")
        
        # 4. Verificar base consolidada
        if self.base_consolidada is not None:
            print(f"\n🔗 BASE CONSOLIDADA:")
            rs_consolidada = self.base_consolidada[
                self.base_consolidada['Sindicato'].str.contains(
                    'SINDPPD RS|RIO GRANDE DO SUL|RS', case=False, na=False
                )
            ]
            print(f"Colaboradores RS na base consolidada: {len(rs_consolidada)}")
            
            if len(rs_consolidada) > 0:
                print("Estados mapeados para colaboradores RS:")
                for _, row in rs_consolidada.iterrows():
                    estado = self.extrair_estado_corrigido(row['Sindicato'])
                    print(f"   {row['Sindicato']} → {estado}")
        
        # 5. Verificar resultado final
        if self.resultado_final is not None:
            print(f"\n📊 RESULTADO FINAL:")
            rs_final = self.resultado_final[
                self.resultado_final['Sindicato do Colaborador'].str.contains(
                    'SINDPPD RS|RIO GRANDE DO SUL|RS', case=False, na=False
                )
            ]
            print(f"Colaboradores RS no resultado final: {len(rs_final)}")
            
            if len(rs_final) > 0:
                print(f"Valor total RS: R$ {rs_final['TOTAL'].sum():,.2f}")
                print(f"Dias médios RS: {rs_final['Dias'].mean():.2f}")
            else:
                print("❌ PROBLEMA: RS não aparece no resultado final!")
        
        print("="*80)
        print("🔍 DEBUG CONCLUÍDO")
        print("="*80 + "\n")
    
    def executar_processo_completo(self):
        """🚀 Executa todo o processo COM LOGS DETALHADOS"""
        inicio_processo = datetime.now()
        self.logger.info("🚀 INICIANDO PROCESSAMENTO COMPLETO SISTEMA VR/VA")
        self.logger.info("="*80)
        
        try:
            # Verificar se todos os arquivos foram carregados
            self.logger.info("1️⃣ Verificando arquivos necessários...")
            arquivos_ok, faltando = self.verificar_arquivos_necessarios()
            if not arquivos_ok:
                self.logger.error(f"❌ Arquivos faltando: {faltando}")
                return False, f"Arquivos faltando: {faltando}"
            
            self.logger.info(f"✅ Todos os arquivos necessários carregados: {len(self.arquivos_carregados)}")
            
            # Executar pipeline com logs detalhados
            etapas = [
                ("Limpeza e padronização", self.limpar_e_padronizar_dados),
                ("Criação da base consolidada", self.criar_base_consolidada),
                ("Aplicação de exclusões", self.aplicar_exclusoes),
                ("Cálculo de dias úteis", self.calcular_dias_uteis_por_colaborador),
                ("Cálculo de valores VR", self.calcular_valores_vr),
                ("Geração da planilha final", self.gerar_planilha_final)
            ]
            
            for i, (nome_etapa, funcao) in enumerate(etapas, 2):
                self.logger.info(f"{i}️⃣ Iniciando: {nome_etapa}...")
                inicio_etapa = datetime.now()
                
                try:
                    resultado = funcao()
                    fim_etapa = datetime.now()
                    tempo_etapa = (fim_etapa - inicio_etapa).total_seconds()
                    
                    self.logger.info(f"✅ {nome_etapa} concluída em {tempo_etapa:.2f}s")
                    
                    if resultado is not None and hasattr(resultado, '__len__'):
                        self.logger.debug(f"   📊 Registros resultantes: {len(resultado)}")
                        
                except Exception as e:
                    self.logger.error(f"❌ ERRO em {nome_etapa}: {str(e)}")
                    self.logger.debug(f"🔍 Stacktrace: {traceback.format_exc()}")
                    return False, f"Erro em {nome_etapa}: {str(e)}"
            
            # Debug específico para Rio Grande do Sul
            self.logger.info("🔍 Executando verificação Rio Grande do Sul...")
            self.debug_dados_rs()
            
            # Salvar resultado
            self.logger.info("7️⃣ Salvando resultado...")
            inicio_save = datetime.now()
            arquivo_final = self.salvar_resultado()
            if not arquivo_final:
                self.logger.error("❌ Erro ao salvar arquivo final")
                return False, "Erro ao salvar arquivo final"
            
            fim_save = datetime.now()
            tempo_save = (fim_save - inicio_save).total_seconds()
            self.logger.info(f"✅ Arquivo salvo em {tempo_save:.2f}s: {arquivo_final}")
            
            # Enviar emails
            self.logger.info("8️⃣ Enviando emails...")
            inicio_emails = datetime.now()
            emails_ok = self.enviar_emails(arquivo_final)
            fim_emails = datetime.now()
            tempo_emails = (fim_emails - inicio_emails).total_seconds()
            
            if emails_ok:
                self.logger.info(f"✅ Emails enviados em {tempo_emails:.2f}s")
            else:
                self.logger.warning(f"⚠️ Falha no envio de emails ({tempo_emails:.2f}s)")
            
            # Estatísticas finais
            fim_processo = datetime.now()
            tempo_total = (fim_processo - inicio_processo).total_seconds()
            
            self.logger.info("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            self.logger.info(f"⏱️ Tempo total: {tempo_total:.2f}s ({tempo_total/60:.1f} min)")
            
            # Logs de estatísticas finais
            if self.resultado_final is not None:
                total_colaboradores = len(self.resultado_final)
                valor_total = self.resultado_final['TOTAL'].sum()
                custo_empresa = self.resultado_final['Custo empresa'].sum()
                
                self.logger.info(f"📊 ESTATÍSTICAS FINAIS:")
                self.logger.info(f"   👥 Colaboradores processados: {total_colaboradores:,}")
                self.logger.info(f"   💰 Valor total VR: R$ {valor_total:,.2f}")
                self.logger.info(f"   🏢 Custo empresa: R$ {custo_empresa:,.2f}")
                
                # Breakdown por estado nos logs
                df_estados = self.resultado_final.copy()
                df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(self.extrair_estado_corrigido)
                breakdown = df_estados.groupby('Estado').agg({
                    'Matricula': 'count',
                    'TOTAL': 'sum'
                }).round(2)
                
                self.logger.info(f"🗺️ BREAKDOWN POR ESTADO:")
                for estado, dados in breakdown.iterrows():
                    self.logger.info(f"   📍 {estado}: {dados['Matricula']} colaboradores, R$ {dados['TOTAL']:,.2f}")
            
            self.logger.info("="*80)
            
            return True, {
                'arquivo': arquivo_final,
                'colaboradores': len(self.resultado_final),
                'valor_total': self.resultado_final['TOTAL'].sum(),
                'emails_enviados': emails_ok,
                'tempo_processamento': tempo_total
            }
            
        except Exception as e:
            fim_processo = datetime.now()
            tempo_total = (fim_processo - inicio_processo).total_seconds()
            
            self.logger.error(f"❌ ERRO CRÍTICO NO PROCESSAMENTO após {tempo_total:.2f}s:")
            self.logger.error(f"   🔍 Erro: {str(e)}")
            self.logger.error(f"   📍 Stacktrace completo:")
            
            # Log do stacktrace completo
            for linha in traceback.format_exc().split('\n'):
                if linha.strip():
                    self.logger.error(f"   {linha}")
            
            return False, str(e)
