# =============================================================================
# SOLUÇÃO PARA ERRO DE IMPORT - 3 OPÇÕES
# =============================================================================

# 🚨 ERRO ATUAL: ModuleNotFoundError: No module named 'utils'

# ✅ SOLUÇÃO 1: ADICIONAR FUNÇÕES DIRETAMENTE NO APP.PY (MAIS SIMPLES)
# Adicione estas funções no app.py, APÓS os imports existentes e ANTES de inicializar_session_state():

def formatar_moeda_br(valor):
    """💰 Formata valores monetários no padrão brasileiro"""
    try:
        import pandas as pd
        
        if pd.isna(valor) or valor in [None, '', 0]:
            return "R$ 0,00"
        
        # Converter para float se necessário
        if isinstance(valor, str):
            valor = float(valor.replace('R$', '').replace('.', '').replace(',', '.'))
        
        # Formatação brasileira: 1.234.567,89
        valor_str = f"{float(valor):,.2f}"
        valor_br = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_br}"
        
    except Exception as e:
        return f"R$ {valor}"

def verificar_status_email(vr_system, resultado=None):
    """📧 Verifica status real do envio de emails"""
    try:
        # Verificar se o sistema tem status detalhado
        if hasattr(vr_system, 'status_emails'):
            status = vr_system.status_emails
            return status.get('sucesso_geral', False), status
        
        # Verificar no resultado direto
        if isinstance(resultado, dict):
            return resultado.get('emails_enviados', False), {'emails_enviados': resultado.get('emails_enviados', False)}
        
        # Se chegou até aqui sem erro e há resultado final, assumir sucesso
        if hasattr(vr_system, 'resultado_final') and vr_system.resultado_final is not None:
            return True, {'assumido': True}
        
        return False, {'erro': 'Status não disponível'}
        
    except Exception as e:
        return False, {'erro': str(e)}

# =============================================================================
# OU SOLUÇÃO 2: CORRIGIR O IMPORT (SE QUISER MANTER ARQUIVO SEPARADO)
# =============================================================================

# No app.py, SUBSTITUA:
# from utils import formatar_moeda_br, StatusManager

# POR ESTE CÓDIGO (com tratamento de erro):
try:
    from utils import formatar_moeda_br, StatusManager
except ImportError as e:
    print(f"Aviso: Não foi possível importar utils: {e}")
    
    # Definir funções localmente como fallback
    def formatar_moeda_br(valor):
        """💰 Formata valores monetários no padrão brasileiro"""
        try:
            import pandas as pd
            
            if pd.isna(valor) or valor in [None, '', 0]:
                return "R$ 0,00"
            
            if isinstance(valor, str):
                valor = float(valor.replace('R$', '').replace('.', '').replace(',', '.'))
            
            valor_str = f"{float(valor):,.2f}"
            valor_br = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
            return f"R$ {valor_br}"
            
        except Exception as e:
            return f"R$ {valor}"
    
    class StatusManager:
        def __init__(self):
            self.status_cache = {}

# =============================================================================
# OU SOLUÇÃO 3: VERIFICAR SE ARQUIVO utils.py EXISTE E ESTÁ CORRETO
# =============================================================================

# Verificar se existe o arquivo src/utils.py
# Se não existir, criar com este conteúdo:

"""
# Conteúdo para src/utils.py (arquivo completo)
import pandas as pd
from datetime import datetime
import os

def formatar_moeda_br(valor):
    \"\"\"💰 Formata valores monetários no padrão brasileiro\"\"\"
    try:
        if pd.isna(valor) or valor in [None, '', 0]:
            return "R$ 0,00"
        
        if isinstance(valor, str):
            valor = float(valor.replace('R$', '').replace('.', '').replace(',', '.'))
        
        valor_str = f"{float(valor):,.2f}"
        valor_br = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_br}"
        
    except Exception as e:
        return f"R$ {valor}"

class StatusManager:
    def __init__(self):
        self.status_cache = {}
        self.historico = []
    
    def atualizar_status_email(self, resultado_envio, detalhes=None):
        timestamp = datetime.now()
        status = {
            'sucesso': resultado_envio,
            'timestamp': timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            'detalhes': detalhes or {}
        }
        self.status_cache['email'] = status
        return status
    
    def obter_status_email(self):
        return self.status_cache.get('email', {
            'sucesso': False,
            'timestamp': 'N/A',
            'detalhes': {}
        })
"""