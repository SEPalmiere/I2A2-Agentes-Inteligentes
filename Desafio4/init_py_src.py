"""
Sistema VR/VA - Automação Inteligente
Versão 1.0.0

Sistema completo para automação do cálculo e compra de vale refeição/alimentação
utilizando 6 agentes CrewAI especializados e interface Streamlit moderna.

Módulos principais:
- vr_system: Sistema VR tradicional com toda a lógica de negócio
- vr_crewai: Sistema de agentes CrewAI para análise inteligente
- app: Interface Streamlit para interação do usuário
- main: Orquestrador principal do sistema

Funcionalidades:
- Upload de 10 arquivos Excel de RH
- Consolidação automática de dados
- Aplicação de regras trabalhistas
- Cálculos precisos de VR/VA
- Validações de qualidade
- Dashboard executivo interativo
- Emails automáticos para fornecedor e RH
- Relatórios detalhados por sindicato/estado
"""

__version__ = "1.0.0"
__author__ = "Sistema VR/VA"
__description__ = "Automação inteligente para cálculo e compra de vale refeição/alimentação"
__license__ = "MIT"

# Importações principais (com tratamento de erro)
try:
    from .vr_system import VRAutomationSystem
    __all__ = ['VRAutomationSystem']
except ImportError:
    __all__ = []

try:
    from .vr_crewai import VRCrewAISystem
    __all__.append('VRCrewAISystem')
except ImportError:
    pass

# Configurações do sistema
SYSTEM_CONFIG = {
    'version': __version__,
    'required_files': [
        'ATIVOS.xlsx',
        'FERIAS.xlsx', 
        'DESLIGADOS.xlsx',
        'ADMISSAO ABRIL.xlsx',
        'Base sindicato x valor.xlsx',
        'Base dias uteis.xlsx',
        'AFASTAMENTOS.xlsx',
        'ESTAGIO.xlsx',
        'APRENDIZ.xlsx',
        'EXTERIOR.xlsx'
    ],
    'agents': [
        'Data Consolidator',
        'Business Rules Engine',
        'VR Calculator',
        'Quality Assurance',
        'Purchase Manager',
        'Communication Hub'
    ],
    'supported_formats': ['.xlsx', '.xls'],
    'default_config': {
        'percentual_empresa': 0.80,
        'percentual_funcionario': 0.20,
        'dia_corte_desligamento': 15,
        'competencia_padrao': '05/2025'
    }
}

def get_system_info():
    """
    Retorna informações do sistema
    
    Returns:
        dict: Informações detalhadas do sistema
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
        'installation_path': Path(__file__).parent
    }

def check_dependencies():
    """
    Verifica se todas as dependências estão instaladas
    
    Returns:
        tuple: (bool, list) - (sucesso, lista de dependências faltando)
    """
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly',
        'openpyxl',
        'python-dotenv',
        'numpy',
        'requests'
    ]
    
    optional_packages = [
        'crewai',
        'langchain',
        'langchain-community',
        'pyyaml'
    ]
    
    missing_required = []
    missing_optional = []
    
    # Verificar pacotes obrigatórios
    for package in required_packages:
        try:
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
        'crewai_available': 'crewai' not in missing_optional
    }

def validate_files(files_dict):
    """
    Valida se todos os arquivos necessários estão presentes
    
    Args:
        files_dict (dict): Dicionário com arquivos carregados
        
    Returns:
        tuple: (bool, list) - (válido, lista de arquivos faltando)
    """
    required_keys = [
        'ativos', 'ferias', 'desligados', 'admissoes',
        'valores_sindicato', 'dias_uteis', 'afastamentos',
        'estagiarios', 'aprendizes', 'exterior'
    ]
    
    missing = [key for key in required_keys if key not in files_dict]
    
    return len(missing) == 0, missing

# Mensagens de status do sistema
STATUS_MESSAGES = {
    'system_ready': '✅ Sistema VR/VA pronto para uso',
    'files_missing': '⚠️ Arquivos obrigatórios faltando',
    'dependencies_missing': '❌ Dependências Python faltando',
    'crewai_unavailable': '⚠️ CrewAI indisponível (modo tradicional apenas)',
    'ollama_disconnected': '⚠️ Ollama desconectado (CrewAI limitado)',
    'processing_started': '🚀 Processamento iniciado',
    'processing_completed': '✅ Processamento concluído com sucesso',
    'processing_failed': '❌ Erro no processamento',
    'emails_sent': '📧 Emails enviados com sucesso',
    'emails_failed': '❌ Falha no envio de emails'
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
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler se especificado
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
    Inicializa o sistema VR/VA
    
    Returns:
        dict: Status da inicialização
    """
    try:
        # Verificar dependências
        deps_status = check_dependencies()
        
        # Configurar logging
        setup_logging()
        
        # Log de inicialização
        logger = logging.getLogger(__name__)
        logger.info(f"Inicializando Sistema VR/VA v{__version__}")
        
        if not deps_status['success']:
            logger.warning(f"Dependências faltando: {deps_status['missing_required']}")
        
        if not deps_status['crewai_available']:
            logger.warning("CrewAI não disponível - modo tradicional apenas")
        
        return {
            'success': deps_status['success'],
            'version': __version__,
            'dependencies': deps_status,
            'modules_loaded': __all__
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'version': __version__
        }

# Banner de boas-vindas
WELCOME_BANNER = f"""
🍽️ Sistema VR/VA v{__version__}
Automação Inteligente para Vale Refeição/Alimentação

Funcionalidades:
• 6 Agentes CrewAI especializados
• Interface Streamlit moderna
• Dashboard executivo interativo
• Emails automáticos
• Relatórios detalhados
• Validações de qualidade

Desenvolvido com CrewAI, Streamlit e Ollama
"""

def print_welcome():
    """Exibe banner de boas-vindas"""
    print("=" * 60)
    print(WELCOME_BANNER)
    print("=" * 60)