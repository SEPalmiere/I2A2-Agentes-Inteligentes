# =============================================================================
# SISTEMA AVANÇADO DE EXTRAÇÃO - OCR, NLP E CAMPOS FISCAIS
# =============================================================================

import pytesseract
from PIL import Image
import io
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
import json

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# =============================================================================
# CAMPOS FISCAIS COMPLETOS (Versão 2025)
# =============================================================================

FISCAL_FIELDS_V2025 = {
    'impostos': {
        'icms': {
            'aliquota': 'ICMS_ALIQUOTA',
            'valor': 'ICMS_VALOR',
            'base_calculo': 'ICMS_BASE_CALCULO',
            'cst': 'ICMS_CST',
            'csosn': 'ICMS_CSOSN',
            'origem_mercadoria': 'ICMS_ORIGEM'
        },
        'ipi': {
            'aliquota': 'IPI_ALIQUOTA',
            'valor': 'IPI_VALOR',
            'base_calculo': 'IPI_BASE_CALCULO',
            'cst': 'IPI_CST'
        },
        'pis': {
            'aliquota': 'PIS_ALIQUOTA',
            'valor': 'PIS_VALOR',
            'base_calculo': 'PIS_BASE_CALCULO',
            'cst': 'PIS_CST'
        },
        'cofins': {
            'aliquota': 'COFINS_ALIQUOTA',
            'valor': 'COFINS_VALOR',
            'base_calculo': 'COFINS_BASE_CALCULO',
            'cst': 'COFINS_CST'
        }
    },
    'deducoes': {
        'desconto': 'DESCONTO_VALOR',
        'desconto_percentual': 'DESCONTO_PERCENTUAL',
        'acrescimo': 'ACRESCIMO_VALOR',
        'acrescimo_percentual': 'ACRESCIMO_PERCENTUAL',
        'frete': 'FRETE_VALOR',
        'seguro': 'SEGURO_VALOR',
        'outras_deducoes': 'OUTRAS_DEDUCOES_VALOR'
    },
    'transportador': {
        'nome': 'TRANSPORTADOR_NOME',
        'cnpj': 'TRANSPORTADOR_CNPJ',
        'cpf': 'TRANSPORTADOR_CPF',
        'ie': 'TRANSPORTADOR_IE',
        'veiculo_placa': 'VEICULO_PLACA',
        'veiculo_uf': 'VEICULO_UF'
    },
    'informacoes_adicionais': {
        'informacoes_complementares': 'INFO_COMPLEMENTARES',
        'informacoes_interesse_fisco': 'INFO_INTERESSE_FISCO',
        'referencia_nf_anterior': 'REFERENCIA_NF_ANTERIOR'
    }
}

# Todos os campos padrão + campos fiscais
ALL_STANDARD_FIELDS = [
    'CHAVE DE ACESSO', 'MODELO', 'SÉRIE', 'NÚMERO',
    'NATUREZA DA OPERAÇÃO', 'DATA EMISSÃO',
    'CPF/CNPJ Emitente', 'RAZÃO SOCIAL EMITENTE',
    'INSCRIÇÃO ESTADUAL EMITENTE', 'UF EMITENTE', 'MUNICÍPIO EMITENTE',
    'CNPJ DESTINATÁRIO', 'NOME DESTINATÁRIO', 'UF DESTINATÁRIO',
    'INDICADOR IE DESTINATÁRIO', 'DESTINO DA OPERAÇÃO',
    'CONSUMIDOR FINAL', 'PRESENÇA DO COMPRADOR',
    'NÚMERO PRODUTO', 'DESCRIÇÃO DO PRODUTO/SERVIÇO',
    'CÓDIGO NCM/SH', 'NCM/SH (TIPO DE PRODUTO)', 'CFOP',
    'QUANTIDADE', 'UNIDADE', 'VALOR UNITÁRIO', 'VALOR TOTAL',
    # Novos campos fiscais
    'ICMS_ALIQUOTA', 'ICMS_VALOR', 'ICMS_BASE_CALCULO',
    'ICMS_CST', 'ICMS_CSOSN', 'ICMS_ORIGEM',
    'IPI_ALIQUOTA', 'IPI_VALOR', 'IPI_BASE_CALCULO', 'IPI_CST',
    'PIS_ALIQUOTA', 'PIS_VALOR', 'PIS_BASE_CALCULO', 'PIS_CST',
    'COFINS_ALIQUOTA', 'COFINS_VALOR', 'COFINS_BASE_CALCULO', 'COFINS_CST',
    'DESCONTO_VALOR', 'DESCONTO_PERCENTUAL',
    'ACRESCIMO_VALOR', 'ACRESCIMO_PERCENTUAL',
    'FRETE_VALOR', 'SEGURO_VALOR', 'OUTRAS_DEDUCOES_VALOR',
    'TRANSPORTADOR_NOME', 'TRANSPORTADOR_CNPJ', 'TRANSPORTADOR_CPF',
    'TRANSPORTADOR_IE', 'VEICULO_PLACA', 'VEICULO_UF',
    'INFO_COMPLEMENTARES', 'INFO_INTERESSE_FISCO', 'REFERENCIA_NF_ANTERIOR'
]

# =============================================================================
# PADRÕES REGEX PARA EXTRAÇÃO
# =============================================================================

FISCAL_PATTERNS = {
    'chave_acesso': r'\d{44}',
    'cnpj': r'\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}',
    'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
    'data': r'\d{1,2}[/\-]\d{1,2}[/\-]\d{4}',
    'hora': r'\d{2}:\d{2}:\d{2}',
    'cst': r'(?:CST|CSOSN)[:\s]*(\d{3})',
    'aliquota': r'(?:alíquota|aliq|tx)[:\s]*(\d+[.,]\d{2})\s*%',
    'valor': r'(?:valor|vl|r\$)[:\s]*(\d+[.,]\d{2})',
    'icms': r'(?:icms|imposto\s+circulação)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'ipi': r'(?:ipi|imposto\s+sobre\s+produto)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'pis': r'(?:pis|prog\.?\s+integração\s+social)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'cofins': r'(?:cofins|contrib\.?\s+social)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'desconto': r'(?:desconto|desc\.?)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'acrescimo': r'(?:acréscimo|acr\.?)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
    'frete': r'(?:frete|transporte)[:\s]*r?\$?\s*(\d+[.,]\d{2})',
}

# =============================================================================
# CLASSE PARA OCR EM PDFs SCANEADOS
# =============================================================================

class OCRExtractor:
    """Extrator com OCR para PDFs scaneados e imagens"""
    
    def __init__(self, language='por'):
        """Inicializa OCR com idioma português"""
        self.language = language
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self):
        """Verifica se Tesseract está instalado"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def extract_from_pdf_scanned(self, file_path):
        """Extrai texto de PDF com OCR"""
        if not self.tesseract_available:
            print("⚠️ Tesseract não instalado. Instale com: pip install pytesseract")
            return None
        
        try:
            import pdf2image
            
            images = pdf2image.convert_from_path(file_path, dpi=300)
            extracted_text = ""
            
            for page_num, image in enumerate(images):
                print(f"   📄 Processando página {page_num + 1}/{len(images)} com OCR...")
                text = pytesseract.image_to_string(image, lang=self.language)
                extracted_text += f"\n--- PÁGINA {page_num + 1} ---\n{text}"
            
            return extracted_text
        
        except ImportError:
            print("⚠️ pdf2image não instalado. Instale com: pip install pdf2image")
            return None
        except Exception as e:
            print(f"❌ Erro ao processar OCR: {e}")
            return None
    
    def extract_from_image(self, image_path):
        """Extrai texto de imagem com OCR"""
        if not self.tesseract_available:
            return None
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.language)
            return text
        except Exception as e:
            print(f"❌ Erro ao processar imagem: {e}")
            return None

# =============================================================================
# CLASSE PARA NLP - EXTRAÇÃO SEMÂNTICA
# =============================================================================

class NLPExtractor:
    """Extrator com NLP para compreensão semântica"""
    
    def __init__(self):
        """Inicializa modelo spaCy"""
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo spaCy"""
        if not SPACY_AVAILABLE:
            print("⚠️ spaCy não instalado. Instale com: pip install spacy")
            print("   Depois execute: python -m spacy download pt_core_news_sm")
            return
        
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except OSError:
            print("⚠️ Modelo PT não encontrado. Baixando...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "pt_core_news_sm"])
            self.nlp = spacy.load("pt_core_news_news_sm")
    
    def extract_entities(self, text):
        """Extrai entidades nomeadas do texto"""
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            label = ent.label_
            if label not in entities:
                entities[label] = []
            entities[label].append(ent.text)
        
        return entities
    
    def extract_impostos_nlp(self, text):
        """Extrai informações de impostos usando análise semântica"""
        impostos = {}
        
        # Buscar padrões de impostos
        for imposto, pattern in FISCAL_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                impostos[imposto] = match.group(0)
        
        return impostos
    
    def extract_monetary_values(self, text):
        """Extrai valores monetários do texto"""
        valores = {}
        
        # Padrão: R$ 1.234,56
        pattern = r'r?\$?\s*(\d+[\.,]\d+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for i, match in enumerate(matches):
            valor = match.group(1).replace('.', '').replace(',', '.')
            valores[f'valor_{i}'] = float(valor)
        
        return valores

# =============================================================================
# CLASSE PARA RECONHECIMENTO DE LAYOUTS
# =============================================================================

class LayoutRecognizer:
    """Identifica e se adapta a diferentes layouts de documentos"""
    
    LAYOUTS = {
        'nfe_padrao': {
            'indicadores': ['chave de acesso', 'nota fiscal eletrônica', 'nfe'],
            'campos_obrigatorios': ['emitente', 'destinatário', 'itens', 'total']
        },
        'nfe_simplificada': {
            'indicadores': ['nfs-e', 'nota fiscal de serviço'],
            'campos_obrigatorios': ['tomador', 'prestador', 'valor', 'serviço']
        },
        'cupom_fiscal': {
            'indicadores': ['cupom', 'ecf', 'extrato'],
            'campos_obrigatorios': ['itens', 'total', 'data']
        },
        'invoice_internacional': {
            'indicadores': ['invoice', 'commercial invoice'],
            'campos_obrigatorios': ['exporter', 'importer', 'items', 'amount']
        }
    }
    
    def identify_layout(self, text):
        """Identifica o layout do documento"""
        text_lower = text.lower()
        scores = {}
        
        for layout_name, layout_config in self.LAYOUTS.items():
            score = 0
            for indicator in layout_config['indicadores']:
                if indicator in text_lower:
                    score += 1
            scores[layout_name] = score
        
        best_layout = max(scores, key=scores.get)
        return best_layout, scores[best_layout]
    
    def adapt_extraction(self, text, layout_type):
        """Adapta extração baseado no tipo de layout"""
        if layout_type == 'nfe_padrao':
            return self._extract_nfe_padrao(text)
        elif layout_type == 'nfe_simplificada':
            return self._extract_nfe_simplificada(text)
        elif layout_type == 'cupom_fiscal':
            return self._extract_cupom(text)
        elif layout_type == 'invoice_internacional':
            return self._extract_invoice(text)
        return {}
    
    def _extract_nfe_padrao(self, text):
        """Extração específica para NF-e padrão"""
        data = {}
        # Buscar chave de acesso
        chave_match = re.search(FISCAL_PATTERNS['chave_acesso'], text)
        if chave_match:
            data['CHAVE DE ACESSO'] = chave_match.group(0)
        return data
    
    def _extract_nfe_simplificada(self, text):
        """Extração específica para NF-e simplificada"""
        return {}
    
    def _extract_cupom(self, text):
        """Extração específica para cupom fiscal"""
        return {}
    
    def _extract_invoice(self, text):
        """Extração específica para invoice internacional"""
        return {}

# =============================================================================
# CLASSE PARA CONTROLE DE VERSÃO FISCAL
# =============================================================================

class FiscalVersionControl:
    """Sistema de versionamento para adaptação a mudanças legais"""
    
    def __init__(self, config_path='fiscal_versions.json'):
        """Inicializa controle de versão"""
        self.config_path = config_path
        self.versions = self._load_versions()
        self.current_version = self._get_current_version()
    
    def _load_versions(self):
        """Carrega arquivo de versões"""
        default_versions = {
            '2024': {
                'data_inicio': '2024-01-01',
                'data_fim': '2024-12-31',
                'campos_obrigatorios': ALL_STANDARD_FIELDS,
                'novas_regras': [],
                'campos_descontinuados': []
            },
            '2025': {
                'data_inicio': '2025-01-01',
                'data_fim': '2025-12-31',
                'campos_obrigatorios': ALL_STANDARD_FIELDS,
                'novas_regras': [
                    'ICMS_ORIGEM obrigatório em operações interestaduais',
                    'CST em todos os itens obrigatório'
                ],
                'campos_descontinuados': [],
                'novos_campos': [
                    'INFORMACOES_ADICIONAIS',
                    'CHAVE_ACESSO_NFE_ANTERIOR'
                ]
            }
        }
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_versions
    
    def _get_current_version(self):
        """Retorna versão fiscal atual"""
        today = datetime.now().date()
        for version, config in self.versions.items():
            data_inicio = datetime.strptime(config['data_inicio'], '%Y-%m-%d').date()
            data_fim = datetime.strptime(config['data_fim'], '%Y-%m-%d').date()
            if data_inicio <= today <= data_fim:
                return version
        return max(self.versions.keys())
    
    def get_validation_rules(self):
        """Retorna regras de validação da versão atual"""
        version_config = self.versions.get(self.current_version, {})
        return {
            'campos_obrigatorios': version_config.get('campos_obrigatorios', []),
            'novas_regras': version_config.get('novas_regras', []),
            'campos_descontinuados': version_config.get('campos_descontinuados', [])
        }
    
    def validate_with_version(self, data, version=None):
        """Valida dados conforme versão fiscal"""
        if version is None:
            version = self.current_version
        
        rules = self.versions.get(version, {})
        erros = []
        avisos = []
        
        # Validar campos obrigatórios
        for campo in rules.get('campos_obrigatorios', []):
            if campo not in data or not data[campo]:
                erros.append(f"Campo obrigatório ausente: {campo}")
        
        # Validar campos descontinuados
        for campo in rules.get('campos_descontinuados', []):
            if campo in data:
                avisos.append(f"Campo descontinuado: {campo}")
        
        return {
            'valido': len(erros) == 0,
            'erros': erros,
            'avisos': avisos,
            'versao': version
        }
    
    def save_version_config(self):
        """Salva configuração de versões em arquivo"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.versions, f, ensure_ascii=False, indent=2)

# =============================================================================
# CLASSE INTEGRADA - ADVANCED EXTRACTOR
# =============================================================================

class AdvancedNFEExtractor:
    """Extrator avançado com OCR, NLP e campos fiscais"""
    
    def __init__(self):
        self.ocr = OCRExtractor()
        self.nlp = NLPExtractor()
        self.layout_recognizer = LayoutRecognizer()
        self.fiscal_version = FiscalVersionControl()
        self.extracted_data = []
    
    def extract_advanced(self, text, file_type='pdf'):
        """Extração avançada com múltiplas técnicas"""
        data = {}
        
        # 1. Identificar layout
        layout_type, score = self.layout_recognizer.identify_layout(text)
        print(f"📋 Layout identificado: {layout_type} (score: {score})")
        
        # 2. Extração por padrões regex
        for pattern_name, pattern in FISCAL_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                data[pattern_name] = match.group(0)
        
        # 3. Extração de entidades com NLP
        if self.nlp.nlp:
            entities = self.nlp.extract_entities(text)
            data['entidades_nlp'] = entities
        
        # 4. Extração de valores monetários
        valores = self.nlp.extract_monetary_values(text)
        data.update(valores)
        
        # 5. Extração específica por layout
        layout_data = self.layout_recognizer.adapt_extraction(text, layout_type)
        data.update(layout_data)
        
        # 6. Validar com versão fiscal
        validation = self.fiscal_version.validate_with_version(data)
        data['validacao_fiscal'] = validation
        
        return data
    
    def extract_from_scanned_pdf(self, file_path):
        """Extração completa de PDF scaneado"""
        print(f"🔍 Processando PDF scaneado: {file_path}")
        
        # 1. OCR
        text = self.ocr.extract_from_pdf_scanned(file_path)
        if not text:
            return None
        
        # 2. Extração avançada
        data = self.extract_advanced(text, 'pdf')
        
        # Preencher campos padrão
        resultado = {field: data.get(field, '') for field in ALL_STANDARD_FIELDS}
        
        return resultado


if __name__ == "__main__":
    print("="*70)
    print("🔍 EXTRATOR AVANÇADO COM OCR, NLP E CAMPOS FISCAIS")
    print("="*70)
    print()
    
    # Exemplo de uso
    extractor = AdvancedNFEExtractor()
    
    # Teste com texto simples
    texto_exemplo = """
    CHAVE DE ACESSO: 41240106267630001509550010035101291224888487
    NOTA FISCAL ELETRÔNICA
    
    EMITENTE:
    CNPJ: 06.267.630/0001-09
    RAZÃO SOCIAL: COMPANHIA BRASILEIRA DE EDUC. E SIST. DE ENS. S.A - PR OP
    
    DESTINATÁRIO:
    CNPJ: 39.4429.021/9651
    NOME: COMANDO DA AERONAUTICA
    
    ITEM 1:
    DESCRIÇÃO: COLECAO SPE EF1 4ANO VOL 1 AL
    NCM: 49019900
    QUANTIDADE: 1
    VALOR UNITÁRIO: 522,50
    
    IMPOSTOS:
    ICMS: R$ 0,00
    IPI: R$ 0,00
    PIS: R$ 0,00
    COFINS: R$ 0,00
    CST: 41
    
    VALOR TOTAL: R$ 522,50
    """
    
    resultado = extractor.extract_advanced(texto_exemplo)
    
    print("📊 DADOS EXTRAÍDOS:")
    for chave, valor in resultado.items():
        if valor:
            print(f"  {chave}: {valor}")
    
    print()
    print("✅ Extração avançada concluída!")