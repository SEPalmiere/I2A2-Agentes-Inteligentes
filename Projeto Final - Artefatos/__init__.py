"""
Sistema de Extração de Notas Fiscais - Multi-formato
Versão 2.0.0

Sistema completo para extração automatizada de dados de notas fiscais
de múltiplos formatos (XML, PDF, TXT, CSV, JSON) utilizando 6 agentes
CrewAI especializados e interface Streamlit moderna.

Módulos principais:
- nfe_extractor: Sistema de extração multi-formato com padronização
- nfe_agents: Sistema de agentes CrewAI para análise inteligente
- app: Interface Streamlit para interação do usuário
- main: Orquestrador principal do sistema

Funcionalidades:
- Extração de dados de XML, PDF, TXT, CSV e JSON
- Padronização automática para formato 2025
- Consolidação em lista única CSV
- Validação de qualidade e contagem
- Dashboard analítico interativo
- Envio automático por email
- Relatórios detalhados de processamento
"""

__version__ = "2.0.0"
__author__ = "Sistema NFe Extractor"
__description__ = "Extração inteligente multi-formato de Notas Fiscais"
__license__ = "MIT"

# Importações principais (com tratamento de erro)
try:
    from .nfe_extractor import NFEExtractorSystem
    __all__ = ['NFEExtractorSystem']
except ImportError:
    __all__ = []

try:
    from .nfe_agents import NFECrewAISystem
    __all__.append('NFECrewAISystem')
except ImportError:
    pass

# Configurações do sistema
SYSTEM_CONFIG = {
    'version': __version__,
    'supported_formats': [
        'XML',      # Notas fiscais eletrônicas
        'PDF',      # Documentos digitalizados
        'TXT',      # Arquivos delimitados
        'CSV',      # Planilhas texto
        'JSON'      # Dados estruturados
    ],
    'agents': [
        'Data Extraction Specialist',
        'Field Standardization Specialist', 
        'Data Consolidation Specialist',
        'Quality Assurance Specialist',
        'Record Counting Specialist',
        'Communication and Reporting Specialist'
    ],
    'standard_fields_2025': [
        'CHAVE DE ACESSO',
        'MODELO',
        'SÉRIE',
        'NÚMERO',
        'NATUREZA DA OPERAÇÃO',
        'DATA EMISSÃO',
        'CPF/CNPJ Emitente',
        'RAZÃO SOCIAL EMITENTE',
        'INSCRIÇÃO ESTADUAL EMITENTE',
        'UF EMITENTE',
        'MUNICÍPIO EMITENTE',
        'CNPJ DESTINATÁRIO',
        'NOME DESTINATÁRIO',
        'UF DESTINATÁRIO',
        'INDICADOR IE DESTINATÁRIO',
        'DESTINO DA OPERAÇÃO',
        'CONSUMIDOR FINAL',
        'PRESENÇA DO COMPRADOR',
        'NÚMERO PRODUTO',
        'DESCRIÇÃO DO PRODUTO/SERVIÇO',
        'CÓDIGO NCM/SH',
        'NCM/SH (TIPO DE PRODUTO)',
        'CFOP',
        'QUANTIDADE',
        'UNIDADE',
        'VALOR UNITÁRIO',
        'VALOR TOTAL'
    ],
    'validation_rules': {
        'chave_acesso_length': 44,
        'cnpj_length': 14,
        'cpf_length': 11,
        'ncm_length': 8,
        'cfop_valid_starts': ['5', '6', '7'],
        'date_formats': ['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S'],
        'decimal_separator': ',',
        'thousands_separator': '.'
    },
    'default_config': {
        'output_format': 'CSV',
        'delimiter': ';',
        'encoding': 'utf-8',
        'save_inputs': True,
        'validate_quality': True,
        'check_count': True,
        'send_email': False
    }
}

def get_system_info():
    """
    Retorna informações detalhadas do sistema
    
    Returns:
        dict: Informações do sistema incluindo versão, módulos e configurações
    """
    import sys
    import os
    from pathlib import Path
    
    return {
        'version': __version__,
        'python_version': sys.version,
        'platform': sys.platform,
        'modules_available': __all__,
        'config': SYSTEM_CONFIG,
        'installation_path': Path(__file__).parent,
        'directories': {
            'inputs': 'inputs/',
            'outputs': 'outputs/csv/',
            'logs': 'outputs/logs/',
            'temp': 'temp/'
        }
    }

def check_dependencies():
    """
    Verifica se todas as dependências estão instaladas
    
    Returns:
        dict: Status das dependências e lista de pacotes faltando
    """
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'openpyxl',
        'python-dotenv',
        'numpy',
        'requests',
        'chardet',
        'pdfplumber'
    ]
    
    optional_packages = [
        'crewai',
        'langchain',
        'langchain-community',
        'pyyaml',
        'lxml',
        'pytesseract',
        'xmltodict'
    ]
    
    missing_required = []
    missing_optional = []
    
    # Verificar pacotes obrigatórios
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_required.append(package)
    
    # Verificar pacotes opcionais
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    return {
        'success': len(missing_required) == 0,
        'missing_required': missing_required,
        'missing_optional': missing_optional,
        'crewai_available': 'crewai' not in missing_optional,
        'pdf_advanced': 'pdfplumber' not in missing_required,
        'xml_advanced': 'lxml' not in missing_optional
    }

def validate_file_format(file_path):
    """
    Valida se o arquivo é de um formato suportado
    
    Args:
        file_path (str): Caminho do arquivo
        
    Returns:
        tuple: (bool, str) - (válido, formato detectado)
    """
    from pathlib import Path
    
    supported_extensions = ['.xml', '.pdf', '.txt', '.csv', '.json']
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext in supported_extensions:
        return True, file_ext.upper().replace('.', '')
    
    # Verificar se é TXT delimitado
    if file_ext == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if ';' in first_line:
                    return True, 'TXT_DELIMITED'
                elif ',' in first_line:
                    return True, 'CSV'
        except:
            pass
    
    return False, 'UNKNOWN'

def detect_encoding(file_path):
    """
    Detecta o encoding de um arquivo
    
    Args:
        file_path (str): Caminho do arquivo
        
    Returns:
        str: Encoding detectado
    """
    try:
        import chardet
        
        with open(file_path, 'rb') as f:
            raw = f.read(10000)
            result = chardet.detect(raw)
            return result['encoding'] or 'utf-8'
    except:
        return 'utf-8'

def validate_cnpj(cnpj):
    """
    Valida CNPJ usando algoritmo oficial
    
    Args:
        cnpj (str): CNPJ a validar
        
    Returns:
        bool: True se válido
    """
    import re
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', str(cnpj))
    
    if len(cnpj) != 14:
        return False
    
    # Validação do primeiro dígito
    sum_val = 0
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(12):
        sum_val += int(cnpj[i]) * weights[i]
    
    remainder = sum_val % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    
    if int(cnpj[12]) != digit1:
        return False
    
    # Validação do segundo dígito
    sum_val = 0
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(13):
        sum_val += int(cnpj[i]) * weights[i]
    
    remainder = sum_val % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    
    return int(cnpj[13]) == digit2

def validate_cpf(cpf):
    """
    Valida CPF usando algoritmo oficial
    
    Args:
        cpf (str): CPF a validar
        
    Returns:
        bool: True se válido
    """
    import re
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', str(cpf))
    
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False
    
    # Validação do primeiro dígito
    sum_val = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = (sum_val * 10) % 11
    if digit1 == 10:
        digit1 = 0
    
    if int(cpf[9]) != digit1:
        return False
    
    # Validação do segundo dígito
    sum_val = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = (sum_val * 10) % 11
    if digit2 == 10:
        digit2 = 0
    
    return int(cpf[10]) == digit2

def validate_nfe_key(key):
    """
    Valida chave de acesso da NFe (44 dígitos)
    
    Args:
        key (str): Chave de acesso
        
    Returns:
        bool: True se válida
    """
    import re
    
    # Remove caracteres não numéricos
    key = re.sub(r'\D', '', str(key))
    
    if len(key) != 44:
        return False
    
    # Cálculo do dígito verificador
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    weight_index = 0
    sum_val = 0
    
    for i in range(43):
        sum_val += int(key[i]) * weights[weight_index]
        weight_index = (weight_index + 1) % 8
    
    remainder = sum_val % 11
    digit = 0 if remainder in [0, 1] else 11 - remainder
    
    return int(key[43]) == digit

# Mensagens de status do sistema
STATUS_MESSAGES = {
    'system_ready': '✅ Sistema de Extração NFe pronto para uso',
    'files_missing': '⚠️ Nenhum arquivo selecionado',
    'extraction_started': '🚀 Extração iniciada',
    'extraction_completed': '✅ Extração concluída com sucesso',
    'extraction_failed': '❌ Erro na extração',
    'validation_passed': '✅ Validação de qualidade aprovada',
    'validation_failed': '⚠️ Validação com alertas',
    'count_match': '✅ Contagem de registros corresponde',
    'count_mismatch': '⚠️ Divergência na contagem de registros',
    'email_sent': '📧 Email enviado com sucesso',
    'email_failed': '❌ Falha no envio de email'
}

def get_status_message(key):
    """
    Retorna mensagem de status formatada
    
    Args:
        key (str): Chave da mensagem
        
    Returns:
        str: Mensagem formatada
    """
    return STATUS_MESSAGES.get(key, f'Status desconhecido: {key}')

# Logging configuration
import logging

def setup_logging(level=logging.INFO, log_file=None):
    """
    Configura sistema de logging
    
    Args:
        level: Nível de logging (default: INFO)
        log_file: Arquivo de log (opcional)
    """
    from datetime import datetime
    
    # Criar diretório de logs se não existir
    if log_file:
        from pathlib import Path
        Path('outputs/logs').mkdir(parents=True, exist_ok=True)
        
        if not log_file.startswith('outputs/logs/'):
            log_file = f'outputs/logs/{log_file}'
    else:
        log_file = f'outputs/logs/nfe_extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Função de inicialização
def initialize_system():
    """
    Inicializa o sistema de extração NFe
    
    Returns:
        dict: Status da inicialização
    """
    try:
        from pathlib import Path
        
        # Verificar dependências
        deps_status = check_dependencies()
        
        # Configurar logging
        setup_logging()
        
        # Log de inicialização
        logger = logging.getLogger(__name__)
        logger.info(f"Inicializando Sistema NFe Extractor v{__version__}")
        
        # Criar diretórios necessários
        directories = ['inputs', 'outputs/csv', 'outputs/logs', 'outputs/emails', 'temp']
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        if not deps_status['success']:
            logger.warning(f"Dependências faltando: {deps_status['missing_required']}")
        
        if not deps_status['crewai_available']:
            logger.warning("CrewAI não disponível - análise limitada")
        
        return {
            'success': deps_status['success'],
            'version': __version__,
            'dependencies': deps_status,
            'modules_loaded': __all__,
            'supported_formats': SYSTEM_CONFIG['supported_formats']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'version': __version__
        }

# Banner de boas-vindas
WELCOME_BANNER = f"""
🔍 Sistema de Extração NFe v{__version__}
Extração Inteligente Multi-formato de Notas Fiscais

Funcionalidades:
- Extração de XML, PDF, TXT, CSV e JSON
- Padronização automática de campos
- 6 Agentes CrewAI especializados
- Validação de qualidade e contagem
- Dashboard analítico interativo
- Envio automático por email

Desenvolvido com CrewAI, Streamlit e Ollama
"""

def print_welcome():
    """Exibe banner de boas-vindas"""
    print("=" * 60)
    print(WELCOME_BANNER)
    print("=" * 60)