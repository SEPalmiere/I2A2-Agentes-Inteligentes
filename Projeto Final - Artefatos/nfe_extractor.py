# =============================================================================
# SISTEMA DE EXTRAÇÃO DE NOTAS FISCAIS - MULTI-FORMATO COM LIMPEZA E NORMALIZAÇÃO
# VERSÃO CORRIGIDA - Campos obrigatórios garantidos
# =============================================================================

import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
import xml.etree.ElementTree as ET
import pdfplumber
import chardet
import csv
import re
import shutil
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO
# =============================================================================

def detect_encoding(path, nbytes=100000):
    """Detecta o encoding de um arquivo."""
    with open(path, 'rb') as f:
        raw = f.read(nbytes)
    enc = chardet.detect(raw)
    return enc['encoding'] or 'utf-8'


def detect_delimiter(path, encoding):
    """Detecta o delimitador de um arquivo CSV."""
    with open(path, 'r', encoding=encoding, errors='replace') as f:
        sample = ''.join([next(f) for _ in range(10)])
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
        return dialect.delimiter
    except Exception:
        counts = {d: sample.count(d) for d in [',', ';', '\t', '|']}
        return max(counts, key=counts.get)


def limpar_colunas(df):
    """Limpa nomes das colunas: remove espaços e converte para MAIÚSCULO."""
    df.columns = df.columns.str.strip().str.upper()
    return df


def _format_date(valor):
    """Formata data para padrão DD/MM/YYYY HH:MM:SS"""
    if pd.isna(valor) or valor == '':
        return ''
    
    valor_str = str(valor)[:19]
    
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', 
                '%d/%m/%Y', '%Y%m%d']:
        try:
            dt = datetime.strptime(valor_str[:10], fmt[:10])
            return dt.strftime('%d/%m/%Y 00:00:00')
        except:
            continue
    
    return valor_str


def _format_currency(valor):
    """Formata valor monetário com vírgula como separador decimal"""
    if pd.isna(valor) or valor == '':
        return '0,00'
    
    try:
        valor_str = str(valor).strip()
        if ',' in valor_str:
            v_float = float(valor_str.replace(',', '.'))
        else:
            v_float = float(valor_str)
        return f"{v_float:.2f}".replace('.', ',')
    except:
        return str(valor)


def normalizar_valores(df):
    """
    Normaliza valores dos dados:
    - Datas em formato DD/MM/YYYY HH:MM:SS
    - Valores monetários com vírgula como separador
    - Remove espaços extras de strings
    - Converte strings para MAIÚSCULO
    """
    # Datas
    colunas_data = [col for col in df.columns if 'DATA' in col or 'EMISSÃO' in col]
    for col in colunas_data:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _format_date(x))
    
    # Valores monetários
    colunas_valor = [col for col in df.columns if 'VALOR' in col]
    for col in colunas_valor:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _format_currency(x))
    
    # Remove espaços extras e converte para MAIÚSCULO
    string_cols = df.select_dtypes(include=['object']).columns
    for col in string_cols:
        if not any(keyword in col.upper() for keyword in ['DATA', 'EMISSÃO', 'VALOR']):
            df[col] = df[col].str.strip().str.upper()
        else:
            df[col] = df[col].str.strip()
    
    return df


def ler_csv_seguro(path, try_on_bad_lines='skip', nrows=None):
    """
    Lê CSV detectando encoding e delimitador.
    Limpa e padroniza nomes das colunas.
    Normaliza valores.
    ✅ CORREÇÃO: Preserva zeros em CNPJ/CPF usando dtype=str
    """
    encoding = detect_encoding(path)
    delimiter = detect_delimiter(path, encoding)
    
    # ✅ CORREÇÃO: Usar dtype=str para preservar zeros
    df = pd.read_csv(path, encoding=encoding, delimiter=delimiter, 
                     on_bad_lines=try_on_bad_lines, dtype=str, nrows=nrows)
    
    df = limpar_colunas(df)
    df = normalizar_valores(df)
    
    return df


# =============================================================================
# CLASSE NFEExtractorSystem - CORRIGIDA
# =============================================================================

class NFEExtractorSystem:
    """Sistema universal para extração de dados de Notas Fiscais"""
    
    # ✅ CAMPOS OBRIGATÓRIOS - GARANTIDOS NO RESULTADO FINAL
    CAMPOS_OBRIGATORIOS = [
        'DATA EMISSÃO',
        'CPF/CNPJ EMITENTE',
        'RAZÃO SOCIAL EMITENTE',
        'INSCRIÇÃO ESTADUAL EMITENTE',
        'NOME DESTINATÁRIO'
    ]
    
    STANDARD_FIELDS = [
        'CHAVE DE ACESSO', 'MODELO', 'SÉRIE', 'NÚMERO',
        'NATUREZA DA OPERAÇÃO', 'DATA EMISSÃO',
        'CPF/CNPJ EMITENTE', 'RAZÃO SOCIAL EMITENTE',
        'INSCRIÇÃO ESTADUAL EMITENTE', 'UF EMITENTE', 'MUNICÍPIO EMITENTE',
        'CNPJ DESTINATÁRIO', 'NOME DESTINATÁRIO', 'UF DESTINATÁRIO',
        'INDICADOR IE DESTINATÁRIO', 'DESTINO DA OPERAÇÃO',
        'CONSUMIDOR FINAL', 'PRESENÇA DO COMPRADOR',
        'NÚMERO PRODUTO', 'DESCRIÇÃO DO PRODUTO/SERVIÇO',
        'CÓDIGO NCM/SH', 'NCM/SH (TIPO DE PRODUTO)', 'CFOP',
        'QUANTIDADE', 'UNIDADE', 'VALOR UNITÁRIO', 'VALOR TOTAL'
    ]
    
    FIELD_MAPPING = {
        'chave': ['CHAVE DE ACESSO', 'CHAVE', 'chNFe', 'chave_acesso', 'key', 'accessKey', 'NFe'],
        'modelo': ['MODELO', 'mod', 'modelo_nf', 'model', 'MOD'],
        'serie': ['SÉRIE', 'SERIE', 'serie', 'series', 'SER'],
        'numero': ['NÚMERO', 'NUMERO', 'nNF', 'numero_nf', 'number', 'NUM'],
        'natureza': ['NATUREZA DA OPERAÇÃO', 'NATUREZA', 'natOp', 'natureza_operacao', 'NAT_OP'],
        'emissao': ['DATA EMISSÃO', 'DATA EMISSAO', 'dhEmi', 'dataEmissao', 'emission_date', 'DT_EMIS'],
        'cnpj_emitente': ['CPF/CNPJ EMITENTE', 'CNPJ_EMIT', 'CNPJ', 'emit_cnpj', 'CNPJ EMITENTE', 'CPF/CNPJ Emitente'],
        'razao_emitente': ['RAZÃO SOCIAL EMITENTE', 'RAZAO SOCIAL', 'xNome', 'emit_nome', 'RAZAO_SOCIAL'],
        'ie_emitente': ['INSCRIÇÃO ESTADUAL EMITENTE', 'IE', 'IE_EMIT', 'IE EMITENTE', 'INSCRIÇÃO ESTADUAL'],
        'uf_emitente': ['UF EMITENTE', 'UF_EMIT', 'emit_uf', 'UF'],
        'municipio_emitente': ['MUNICÍPIO EMITENTE', 'MUNICIPIO_EMIT', 'emit_municipio', 'MUNICIPIO'],
        'cnpj_dest': ['CNPJ DESTINATÁRIO', 'CNPJ_DEST', 'dest_cnpj', 'CNPJ DEST'],
        'nome_dest': ['NOME DESTINATÁRIO', 'NOME_DEST', 'dest_nome', 'NOME DEST'],
        'uf_dest': ['UF DESTINATÁRIO', 'UF_DEST', 'dest_uf', 'UF DEST'],
        'ie_dest': ['INDICADOR IE DESTINATÁRIO', 'IE_DEST', 'dest_ie_indicador', 'IE DEST'],
        'destino_operacao': ['DESTINO DA OPERAÇÃO', 'DESTINO', 'idDest', 'DEST_OPERACAO'],
        'consumidor_final': ['CONSUMIDOR FINAL', 'indFinal', 'CONS_FINAL'],
        'presenca': ['PRESENÇA DO COMPRADOR', 'PRESENCA DO COMPRADOR', 'indPres'],
        'num_produto': ['NÚMERO PRODUTO', 'NUMERO PRODUTO', 'ITEM', 'nItem', 'NUM_PROD'],
        'descricao': ['DESCRIÇÃO DO PRODUTO/SERVIÇO', 'DESCRICAO', 'xProd', 'DESC_PRODUTO'],
        'ncm': ['CÓDIGO NCM/SH', 'CODIGO NCM', 'NCM', 'NCM_SH'],
        'ncm_tipo': ['NCM/SH (TIPO DE PRODUTO)', 'NCM (TIPO DE PRODUTO)', 'tipo_produto'],
        'cfop': ['CFOP', 'cfop', 'CFOP_CODIGO'],
        'quantidade': ['QUANTIDADE', 'QTD', 'qCom', 'QTDE', 'QTD_PRODUTO'],
        'unidade': ['UNIDADE', 'UN', 'uCom', 'UNIDADE_MEDIDA'],
        'valor_unit': ['VALOR UNITÁRIO', 'VALOR UNITARIO', 'VL_UNIT', 'vUnCom'],
        'valor_total': ['VALOR TOTAL', 'VL_TOTAL', 'vProd', 'VL_PRODUTO']
    }
    
    def __init__(self):
        self.extracted_data = []
        self.processed_files = []
        self.field_mapping = self._initialize_field_mapping()
        self.standard_columns = self._get_standard_columns()
        self.setup_directories()
    
    def _initialize_field_mapping(self):
        """Inicializa mapeamento de campos"""
        return self.FIELD_MAPPING
    
    def _get_standard_columns(self):
        """Retorna colunas padrão"""
        return self.STANDARD_FIELDS
    
    def setup_directories(self):
        """Cria diretórios necessários"""
        for dir_path in ['inputs', 'outputs/csv', 'outputs/logs', 'outputs/json']:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def detect_file_format(self, file_path):
        """Detecta o formato do arquivo"""
        ext = Path(file_path).suffix.upper()
        if ext == '.XML':
            return 'XML'
        elif ext == '.PDF':
            return 'PDF'
        elif ext == '.JSON':
            return 'JSON'
        elif ext in ['.CSV', '.TXT', '.TSV']:
            return 'CSV'
        else:
            return 'UNKNOWN'
    
    def _find_field_in_dict(self, data, field_key):
        """Procura um campo em um dicionário usando mapeamento"""
        possivel_nomes = self.field_mapping.get(field_key, [field_key])
        
        for nome in possivel_nomes:
            if nome in data:
                return data[nome]
            for chave in data.keys():
                if chave.upper() == nome.upper():
                    return data[chave]
        
        return ''
    
    def _standardize_record(self, record):
        """Padroniza um registro para o formato padrão"""
        if not isinstance(record, dict):
            return {}
        
        standardized = {}
        for standard_field in self.STANDARD_FIELDS:
            for field_key, possible_names in self.field_mapping.items():
                if standard_field in possible_names:
                    value = self._find_field_in_dict(record, field_key)
                    standardized[standard_field] = value if value else ''
                    break
            else:
                standardized[standard_field] = ''
        
        return standardized
    
    def _standardize_list(self, data_list):
        """Padroniza uma lista de registros"""
        return [self._standardize_record(item) for item in data_list if isinstance(item, dict)]
    
    def extract_from_csv(self, file_path):
        """Extrai dados de arquivo CSV/TXT"""
        try:
            df = ler_csv_seguro(file_path)
            return df.to_dict('records')
        except Exception as e:
            print(f"❌ Erro ao extrair CSV: {e}")
            return []
    
    def extract_from_xml(self, file_path):
        """Extrai dados de arquivo XML (NFe)"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            extracted = []
            
            for nfe_element in root.findall('.//nfe:NFe', ns) or root.findall('.//NFe'):
                base_data = {}
                
                info_nfe = nfe_element.find('nfe:infNFe', ns) or nfe_element.find('infNFe')
                if info_nfe is None:
                    continue
                
                ide = info_nfe.find('nfe:ide', ns) or info_nfe.find('ide')
                if ide is not None:
                    base_data['CHAVE DE ACESSO'] = info_nfe.get('Id', '').replace('NFe', '')
                    base_data['MODELO'] = ide.findtext('nfe:mod', '', ns) or ide.findtext('mod', '')
                    base_data['SÉRIE'] = ide.findtext('nfe:serie', '', ns) or ide.findtext('serie', '')
                    base_data['NÚMERO'] = ide.findtext('nfe:nNF', '', ns) or ide.findtext('nNF', '')
                    base_data['NATUREZA DA OPERAÇÃO'] = ide.findtext('nfe:natOp', '', ns) or ide.findtext('natOp', '')
                    base_data['DATA EMISSÃO'] = _format_date(ide.findtext('nfe:dhEmi', '', ns) or ide.findtext('dhEmi', ''))
                
                emit = info_nfe.find('nfe:emit', ns) or info_nfe.find('emit')
                if emit is not None:
                    base_data['CPF/CNPJ EMITENTE'] = emit.findtext('nfe:CNPJ', '', ns) or emit.findtext('CNPJ', '')
                    base_data['RAZÃO SOCIAL EMITENTE'] = emit.findtext('nfe:xNome', '', ns) or emit.findtext('xNome', '')
                    base_data['INSCRIÇÃO ESTADUAL EMITENTE'] = emit.findtext('nfe:IE', '', ns) or emit.findtext('IE', '')
                    base_data['UF EMITENTE'] = emit.findtext('nfe:UF', '', ns) or emit.findtext('UF', '')
                    base_data['MUNICÍPIO EMITENTE'] = emit.findtext('nfe:xMun', '', ns) or emit.findtext('xMun', '')
                
                dest = info_nfe.find('nfe:dest', ns) or info_nfe.find('dest')
                if dest is not None:
                    base_data['CNPJ DESTINATÁRIO'] = dest.findtext('nfe:CNPJ', '', ns) or dest.findtext('CNPJ', '')
                    base_data['NOME DESTINATÁRIO'] = dest.findtext('nfe:xNome', '', ns) or dest.findtext('xNome', '')
                
                for det in nfe_element.findall('nfe:det', ns) or nfe_element.findall('det'):
                    item_data = base_data.copy()
                    item_data['NÚMERO PRODUTO'] = det.get('nItem', '')
                    
                    prod = det.find('nfe:prod', ns) or det.find('prod')
                    if prod is not None:
                        item_data['DESCRIÇÃO DO PRODUTO/SERVIÇO'] = prod.findtext('nfe:xProd', '', ns) or prod.findtext('xProd', '')
                        item_data['CÓDIGO NCM/SH'] = prod.findtext('nfe:NCM', '', ns) or prod.findtext('NCM', '')
                        item_data['CFOP'] = prod.findtext('nfe:CFOP', '', ns) or prod.findtext('CFOP', '')
                        item_data['QUANTIDADE'] = prod.findtext('nfe:qCom', '', ns) or prod.findtext('qCom', '')
                        item_data['UNIDADE'] = prod.findtext('nfe:uCom', '', ns) or prod.findtext('uCom', '')
                        item_data['VALOR UNITÁRIO'] = _format_currency(prod.findtext('nfe:vUnCom', '', ns) or prod.findtext('vUnCom', ''))
                        item_data['VALOR TOTAL'] = _format_currency(prod.findtext('nfe:vProd', '', ns) or prod.findtext('vProd', ''))
                    
                    extracted.append(item_data)
            
            df = pd.DataFrame(extracted)
            if not df.empty:
                df = normalizar_valores(df)
                return df.to_dict('records')
            return extracted
        
        except Exception as e:
            print(f"❌ Erro ao extrair XML: {e}")
            return []
    
    def extract_from_pdf(self, file_path):
        """Extrai dados de PDF"""
        try:
            extracted = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    chaves = re.findall(r'\d{44}', text)
                    
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if table and len(table) > 1:
                                headers = table[0]
                                for row in table[1:]:
                                    if len(row) == len(headers):
                                        item = dict(zip(headers, row))
                                        extracted.append(item)
            
            return self._standardize_list(extracted) if extracted else []
        
        except Exception as e:
            print(f"❌ Erro ao extrair PDF: {e}")
            return []
    
    def extract_from_json(self, file_path):
        """Extrai dados de arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return self._standardize_list(data)
            elif isinstance(data, dict):
                if 'nfe' in data:
                    return self._standardize_list([data['nfe']])
                elif 'items' in data:
                    return self._standardize_list(data['items'])
                else:
                    return self._standardize_list([data])
            
            return []
        
        except Exception as e:
            print(f"❌ Erro ao extrair JSON: {e}")
            return []
    
    def process_file(self, file_path):
        """Processa um único arquivo"""
        try:
            input_path = Path('inputs') / Path(file_path).name
            shutil.copy2(file_path, input_path)
            
            file_format = self.detect_file_format(file_path)
            
            if file_format in ['CSV', 'TXT']:
                data = self.extract_from_csv(file_path)
            elif file_format == 'XML':
                data = self.extract_from_xml(file_path)
            elif file_format == 'PDF':
                data = self.extract_from_pdf(file_path)
            elif file_format == 'JSON':
                data = self.extract_from_json(file_path)
            else:
                data = []
            
            if data:
                self.extracted_data.extend(data)
                self.processed_files.append({
                    'file': Path(file_path).name,
                    'format': file_format,
                    'records': len(data),
                    'status': 'success'
                })
            
            return len(data)
        
        except Exception as e:
            self.processed_files.append({
                'file': Path(file_path).name,
                'status': 'error',
                'error': str(e)
            })
            return 0
    
    def process_directory(self, directory_path):
        """Processa todos os arquivos de um diretório"""
        total = 0
        for file_path in Path(directory_path).rglob('*'):
            if file_path.is_file():
                total += self.process_file(str(file_path))
        return total
    
    def export_to_csv(self, output_path=None):
        """✅ EXPORTA COM CAMPOS OBRIGATÓRIOS GARANTIDOS"""
        if not self.extracted_data:
            print("⚠️ Nenhum dado para exportar")
            return None, None
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"outputs/csv/nfe_extracted_{timestamp}.csv"
        
        df = pd.DataFrame(self.extracted_data)
        
        # ✅ GARANTIR TODOS OS CAMPOS PADRÃO
        for field in self.STANDARD_FIELDS:
            if field not in df.columns:
                df[field] = ""
        
        # ✅ EXPORTAR NA ORDEM PADRÃO
        df = df[self.STANDARD_FIELDS]
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, sep=';', encoding='utf-8', index=False)
        
        print(f"✅ Exportado: {output_path}")
        print(f"   📊 {len(df)} registros, {len(self.STANDARD_FIELDS)} campos padrão")
        print(f"   ⭐ Campos obrigatórios: {', '.join(self.CAMPOS_OBRIGATORIOS)}")
        
        return output_path, df
    
    def export_dataframe(self):
        """✅ RETORNA DATAFRAME FINAL COM CAMPOS OBRIGATÓRIOS"""
        if not self.extracted_data:
            print("⚠️ Nenhum dado para exportar")
            return None
        
        df = pd.DataFrame(self.extracted_data)
        
        # Garantir todos os campos
        for field in self.STANDARD_FIELDS:
            if field not in df.columns:
                df[field] = ""
        
        df = df[self.STANDARD_FIELDS]
        return df
    
    def save_to_csv(self):
        """Alias para export_to_csv (compatibilidade)"""
        return self.export_to_csv()
    
    def get_statistics(self):
        """Retorna estatísticas do processamento"""
        return {
            'total_files': len(self.processed_files),
            'successful_files': sum(1 for f in self.processed_files if f.get('status') == 'success'),
            'failed_files': sum(1 for f in self.processed_files if f.get('status') == 'error'),
            'total_records': len(self.extracted_data),
            'unique_invoices': len(set(item.get('CHAVE DE ACESSO', '') for item in self.extracted_data if item.get('CHAVE DE ACESSO'))),
            'standard_fields': len(self.STANDARD_FIELDS),
            'files_processed': self.processed_files
        }
    
    def clear_memory(self):
        """Limpa memória"""
        self.extracted_data = []
        self.processed_files = []


if __name__ == "__main__":
    extractor = NFEExtractorSystem()
    
    files = [
        '202401_NFs_Cabecalho.csv',
        '202401_NFs_Itens.csv',
        '202505_NFe_NotaFiscal.csv'
    ]
    
    print("="*60)
    print("🔍 EXTRATOR UNIVERSAL DE NOTAS FISCAIS - CORRIGIDO")
    print("="*60)
    print()
    
    for file in files:
        try:
            extractor.process_file(file)
            print(f"✅ Processado: {file}")
        except FileNotFoundError:
            print(f"⚠️ Arquivo não encontrado: {file}")
    
    print()
    stats = extractor.get_statistics()
    print(f"📋 Total: {stats['total_records']} registros em {stats['total_files']} arquivos")
    print()
    
    if extractor.extracted_data:
        output, df = extractor.export_to_csv()
        print()
        print("📊 AMOSTRA DOS DADOS:")
        print(df.head(3))