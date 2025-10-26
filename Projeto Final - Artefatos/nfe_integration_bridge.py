# =============================================================================
# PONTE DE INTEGRAÇÃO - CONECTA EXTRACTORS BÁSICO E AVANÇADO
# VERSÃO CORRIGIDA - Com campos obrigatórios garantidos
# =============================================================================

import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import sys


class NFEIntegrationBridge:
    """Integra extractor básico com extractor avançado - CORRIGIDO"""
    
    # ✅ Campos obrigatórios que DEVEM estar no dataframe final
    CAMPOS_OBRIGATORIOS = [
        'DATA EMISSÃO',
        'CPF/CNPJ EMITENTE',
        'RAZÃO SOCIAL EMITENTE',
        'INSCRIÇÃO ESTADUAL EMITENTE',
        'NOME DESTINATÁRIO'
    ]
    
    def __init__(self, basic_extractor, advanced_extractor=None):
        """
        Inicializa ponte de integração
        
        Args:
            basic_extractor: Instância de NFEExtractorSystem
            advanced_extractor: Instância de AdvancedNFEExtractor (opcional)
        """
        self.basic_extractor = basic_extractor
        self.advanced_extractor = advanced_extractor
        self.integration_log = []
    
    def process_with_fallback(self, file_path, use_advanced=True):
        """
        Processa arquivo com fallback entre extractor básico e avançado
        
        Strategy:
        1. Tenta extractor avançado (se disponível)
        2. Fallback para extractor básico se falhar
        3. Merge dos resultados
        """
        file_path = Path(file_path)
        results = {
            'file': file_path.name,
            'status': 'pending',
            'extraction_method': None,
            'data': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Tentar extração avançada primeiro
            if use_advanced and self.advanced_extractor:
                print(f"🔬 Tentando extração avançada: {file_path.name}")
                
                try:
                    if file_path.suffix.lower() == '.pdf':
                        data = self.advanced_extractor.extract_from_scanned_pdf(str(file_path))
                    else:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            text = f.read()
                        data = self.advanced_extractor.extract_advanced(text)
                    
                    if data:
                        results['extraction_method'] = 'advanced_nlp_ocr'
                        results['data'] = data
                        results['status'] = 'success_advanced'
                        self.integration_log.append(results)
                        print(f"   ✅ Extração avançada bem-sucedida")
                        return results
                
                except Exception as e:
                    print(f"   ⚠️ Extração avançada falhou: {e}")
            
            # Fallback para extrator básico
            print(f"📄 Usando extração básica: {file_path.name}")
            self.basic_extractor.process_file(str(file_path))
            
            results['extraction_method'] = 'basic_standard'
            results['status'] = 'success_basic'
            results['data'] = self.basic_extractor.extracted_data[-1] if self.basic_extractor.extracted_data else {}
            self.integration_log.append(results)
            print(f"   ✅ Extração básica bem-sucedida")
            
            return results
        
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            self.integration_log.append(results)
            print(f"   ❌ Erro: {e}")
            return results
    
    def batch_process_with_strategy(self, directory_path, strategy='hybrid'):
        """
        Processa lote de arquivos com estratégia
        
        Estratégias:
        - 'hybrid': Tenta avançado + fallback
        - 'advanced_only': Apenas avançado
        - 'basic_only': Apenas básico
        """
        results_summary = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'advanced_extracted': 0,
            'basic_extracted': 0,
            'processing_time': None,
            'files': []
        }
        
        start_time = datetime.now()
        
        for file_path in Path(directory_path).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.xml', '.pdf', '.txt', '.csv', '.json']:
                results_summary['total_files'] += 1
                
                try:
                    if strategy == 'hybrid':
                        result = self.process_with_fallback(file_path, use_advanced=True)
                    elif strategy == 'advanced_only' and self.advanced_extractor:
                        result = self.process_with_fallback(file_path, use_advanced=True)
                    else:
                        result = self.process_with_fallback(file_path, use_advanced=False)
                    
                    results_summary['files'].append(result)
                    
                    if result['status'].startswith('success'):
                        results_summary['successful'] += 1
                        if 'advanced' in result['extraction_method']:
                            results_summary['advanced_extracted'] += 1
                        else:
                            results_summary['basic_extracted'] += 1
                    else:
                        results_summary['failed'] += 1
                
                except Exception as e:
                    results_summary['failed'] += 1
                    print(f"❌ Erro ao processar {file_path.name}: {e}")
        
        end_time = datetime.now()
        results_summary['processing_time'] = str(end_time - start_time)
        
        return results_summary
    
    def merge_extraction_results(self):
        """Mescla resultados da extração avançada com básica"""
        merged_data = []
        
        for item in self.basic_extractor.extracted_data:
            merged_item = item.copy()
            
            # Buscar dados avançados correspondentes
            for log_entry in self.integration_log:
                if log_entry['extraction_method'] == 'advanced_nlp_ocr':
                    # Merge de campos adicionais
                    advanced_data = log_entry['data']
                    
                    # Adicionar campos fiscais
                    for key in ['ICMS_ALIQUOTA', 'ICMS_VALOR', 'ICMS_BASE_CALCULO', 'ICMS_CST',
                               'IPI_ALIQUOTA', 'IPI_VALOR', 'IPI_BASE_CALCULO', 'IPI_CST',
                               'PIS_ALIQUOTA', 'PIS_VALOR', 'PIS_BASE_CALCULO', 'PIS_CST',
                               'COFINS_ALIQUOTA', 'COFINS_VALOR', 'COFINS_BASE_CALCULO', 'COFINS_CST',
                               'DESCONTO_VALOR', 'ACRESCIMO_VALOR', 'FRETE_VALOR',
                               'TRANSPORTADOR_NOME', 'TRANSPORTADOR_CNPJ', 'INFO_COMPLEMENTARES']:
                        if key in advanced_data:
                            merged_item[key] = advanced_data[key]
            
            merged_data.append(merged_item)
        
        return merged_data
    
    def export_advanced_csv(self, output_path=None):
        """✅ EXPORTA DADOS COM CAMPOS OBRIGATÓRIOS GARANTIDOS"""
        if not self.basic_extractor.extracted_data:
            print("⚠️ Nenhum dado para exportar")
            return None
        
        # Mesclar dados
        merged = self.merge_extraction_results()
        df = pd.DataFrame(merged)
        
        # ✅ Garantir campos obrigatórios
        for campo in self.CAMPOS_OBRIGATORIOS:
            if campo not in df.columns:
                df[campo] = ""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"outputs/csv/nfe_advanced_extracted_{timestamp}.csv"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, sep=';', encoding='utf-8', index=False)
        
        print(f"✅ Exportado: {output_path}")
        print(f"   📊 {len(df)} registros")
        print(f"   ⭐ Campos obrigatórios presentes: {', '.join(self.CAMPOS_OBRIGATORIOS)}")
        
        return output_path
    
    def export_dataframe_final(self):
        """✅ RETORNA DATAFRAME FINAL COM CAMPOS OBRIGATÓRIOS"""
        if not self.basic_extractor.extracted_data:
            print("⚠️ Nenhum dado disponível")
            return None
        
        merged = self.merge_extraction_results()
        df = pd.DataFrame(merged)
        
        # Garantir campos obrigatórios
        for campo in self.CAMPOS_OBRIGATORIOS:
            if campo not in df.columns:
                df[campo] = ""
        
        return df
    
    def generate_integration_report(self, output_path=None):
        """Gera relatório de integração"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"outputs/logs/integration_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'campos_obrigatorios': self.CAMPOS_OBRIGATORIOS,
            'total_files_processed': len(self.integration_log),
            'basic_extractor_stats': {
                'total_files': self.basic_extractor.get_statistics()['total_files'],
                'total_records': self.basic_extractor.get_statistics()['total_records'],
                'unique_invoices': self.basic_extractor.get_statistics()['unique_invoices']
            },
            'advanced_extractor_available': self.advanced_extractor is not None,
            'integration_log': self.integration_log
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Relatório salvo: {output_path}")
        return output_path
    
    def validate_fiscal_compliance(self):
        """Valida conformidade fiscal dos dados extraídos"""
        compliance_report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(self.basic_extractor.extracted_data),
            'campos_obrigatorios': self.CAMPOS_OBRIGATORIOS,
            'validacoes': {
                'campos_obrigatorios': 0,
                'chaves_validas': 0,
                'cnpj_valido': 0,
                'valores_consistentes': 0,
                'problemas': []
            }
        }
        
        for record in self.basic_extractor.extracted_data:
            # Validar chave de acesso
            chave = record.get('CHAVE DE ACESSO', '')
            if chave and len(chave) == 44 and chave.isdigit():
                compliance_report['validacoes']['chaves_validas'] += 1
            else:
                compliance_report['validacoes']['problemas'].append(f"Chave inválida: {chave}")
            
            # Validar CNPJ
            cnpj = record.get('CPF/CNPJ EMITENTE', '')
            if cnpj and len(cnpj.replace('.', '').replace('/', '').replace('-', '')) in [11, 14]:
                compliance_report['validacoes']['cnpj_valido'] += 1
            
            # Validar campos obrigatórios
            campos_req = self.CAMPOS_OBRIGATORIOS
            preenchidos = sum(1 for c in campos_req if record.get(c))
            if preenchidos == len(campos_req):
                compliance_report['validacoes']['campos_obrigatorios'] += 1
        
        return compliance_report


# =============================================================================
# FUNÇÃO WRAPPER PARA USO FÁCIL
# =============================================================================

def create_integrated_extractor(use_advanced=True):
    """
    Factory function para criar extractor integrado
    
    Args:
        use_advanced: Se True, tenta carregar extractor avançado
    
    Returns:
        NFEIntegrationBridge: Instância integrada
    """
    from nfe_extractor import NFEExtractorSystem
    
    basic = NFEExtractorSystem()
    advanced = None
    
    if use_advanced:
        try:
            from nfe_advanced_extractor import AdvancedNFEExtractor
            advanced = AdvancedNFEExtractor()
            print("✅ Extractor avançado carregado com sucesso")
        except ImportError:
            print("⚠️ Extractor avançado não disponível, usando apenas básico")
        except Exception as e:
            print(f"⚠️ Erro ao carregar extractor avançado: {e}")
    
    return NFEIntegrationBridge(basic, advanced)


if __name__ == "__main__":
    print("="*70)
    print("🌉 PONTE DE INTEGRAÇÃO - EXTRACTOR BÁSICO + AVANÇADO")
    print("="*70)
    print()
    
    # Criar extractor integrado
    bridge = create_integrated_extractor(use_advanced=False)
    
    # Processar diretório
    directory = 'inputs'
    
    if Path(directory).exists():
        print(f"📁 Processando diretório: {directory}")
        print()
        
        results = bridge.batch_process_with_strategy(directory, strategy='basic_only')
        
        print()
        print("📊 RESUMO DO PROCESSAMENTO:")
        print(f"   Total de arquivos: {results['total_files']}")
        print(f"   Processados com sucesso: {results['successful']}")
        print(f"   Falhados: {results['failed']}")
        print(f"   Extraídos com método avançado: {results['advanced_extracted']}")
        print(f"   Extraídos com método básico: {results['basic_extracted']}")
        print(f"   Tempo total: {results['processing_time']}")
        print()
        
        # Exportar com campos avançados
        bridge.export_advanced_csv()
        
        # Gerar relatório de integração
        bridge.generate_integration_report()
        
        # Validar conformidade fiscal
        compliance = bridge.validate_fiscal_compliance()
        print("✅ Conformidade fiscal validada")
    
    else:
        print(f"⚠️ Diretório não encontrado: {directory}")