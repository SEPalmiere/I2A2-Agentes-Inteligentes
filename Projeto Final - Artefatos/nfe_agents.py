# =============================================================================
# AGENTES CREWAI PARA EXTRAÇÃO DE NOTAS FISCAIS - MODO OBRIGATÓRIO
# Com captura de logs melhorada
# =============================================================================

from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
import logging
from pathlib import Path

load_dotenv()

# Criar diretório de logs se não existir
logs_dir = Path(__file__).parent / "outputs" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Configurar logging com captura completa
log_file = logs_dir / f"nfe_agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Formato detalhado para capturar tudo
log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Configurar logger root
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[]
)

# Stream handler (terminal)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# File handler (arquivo)
file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# Adicionar handlers ao logger root
root_logger = logging.getLogger()
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Configurar logging das bibliotecas externas
logging.getLogger('crewai').setLevel(logging.DEBUG)
logging.getLogger('langchain').setLevel(logging.DEBUG)
logging.getLogger('langchain_community').setLevel(logging.DEBUG)

class OllamaConnectionError(Exception):
    """Exceção para erro de conexão com Ollama"""
    pass

class NFECrewAISystem:
    """Sistema obrigatório de agentes CrewAI para extração de Notas Fiscais"""
    
    def __init__(self, extractor_system):
        self.extractor = extractor_system
        self.validation_results = {}
        
        logger.info("Inicializando NFECrewAISystem")
        
        # Validar Ollama antes de criar qualquer coisa
        self._validate_ollama()
        
        # Inicializar LLM após validação
        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        
        logger.info("LLM Ollama inicializado com sucesso")
    
    def _validate_ollama(self):
        """Valida se Ollama está rodando e modelo está disponível"""
        try:
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
            
            logger.info(f"Validando Ollama em {ollama_url}")
            
            # Testar conexão com Ollama
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            
            if response.status_code != 200:
                raise OllamaConnectionError(
                    f"Ollama não está respondendo. Status: {response.status_code}"
                )
            
            # Verificar se modelo está disponível
            models_data = response.json()
            available_models = [m.get('name', '').split(':')[0] for m in models_data.get('models', [])]
            
            model_base = model_name.split(':')[0]
            
            if model_base not in available_models:
                raise OllamaConnectionError(
                    f"Modelo '{model_name}' não encontrado. Modelos disponíveis: {available_models}. "
                    f"Execute: ollama pull {model_name}"
                )
            
            logger.info(f"✓ Ollama validado - Modelo {model_name} disponível")
            
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                "ERRO: Ollama não está rodando! "
                "Execute em outro terminal: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise OllamaConnectionError(
                "ERRO: Ollama não respondeu no tempo limite. "
                "Verifique se está rodando em http://localhost:11434"
            )
        except OllamaConnectionError:
            raise
        except Exception as e:
            raise OllamaConnectionError(f"ERRO ao validar Ollama: {str(e)}")
    
    def create_extraction_agent(self):
        """Agente 1: Especialista em Extração Multi-formato"""
        return Agent(
            role="Data Extraction Specialist",
            goal="Extrair dados de notas fiscais de múltiplos formatos com máxima precisão",
            backstory="""Especialista em extração de dados com 15+ anos de experiência em documentos fiscais.
            Expertise: Parsing XML, extração de PDFs, processamento de arquivos delimitados, 
            detecção automática de formatos, tratamento de encodings múltiplos.
            Garante que nenhum dado seja perdido durante a extração.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_standardization_agent(self):
        """Agente 2: Especialista em Padronização de Campos"""
        return Agent(
            role="Field Standardization Specialist",
            goal="Padronizar nomenclaturas de campos variados para formato único 2025",
            backstory="""Especialista em padronização de dados fiscais com conhecimento de normas brasileiras.
            Expertise: Mapeamento inteligente de campos, identificação por padrões (44 chars = chave, 14 dígitos = CNPJ),
            normalização de formatos, aplicação consistente de nomenclatura 2025.
            Preserva integridade dos dados durante transformações.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_consolidation_agent(self):
        """Agente 3: Especialista em Consolidação de Dados"""
        return Agent(
            role="Data Consolidation Specialist",
            goal="Consolidar todos os dados extraídos em lista única padronizada em CSV",
            backstory="""Especialista em consolidação de dados com expertise em estruturação de informações.
            Habilidades: Unificação de múltiplas fontes, criação de estruturas tabulares,
            aplicação de cabeçalhos padrão, ordenação lógica, eliminação de duplicatas,
            geração de CSVs bem estruturados com encoding UTF-8.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_quality_agent(self):
        """Agente 4: Especialista em Validação de Qualidade"""
        return Agent(
            role="Quality Assurance Specialist",
            goal="Validar qualidade e integridade dos dados extraídos e consolidados",
            backstory="""Auditor especializado em qualidade de dados fiscais com certificações em compliance.
            Expertise: Validação de chaves de acesso (44 dígitos e verificador), verificação de CNPJs/CPFs,
            conferência de NCM/CFOP, detecção de valores inconsistentes, identificação de campos obrigatórios faltantes,
            análise de coerência entre quantidade x valor.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_counting_agent(self):
        """Agente 5: Especialista em Verificação de Contagem"""
        return Agent(
            role="Record Counting Specialist",
            goal="Verificar se quantidade de registros extraídos corresponde ao esperado",
            backstory="""Especialista em auditoria de contagem e reconciliação de dados.
            Competências: Contagem precisa de itens em documentos fonte, comparação entre 
            registros esperados vs extraídos, identificação de perdas durante processamento,
            análise de completude, validação de totalizadores.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_communication_agent(self):
        """Agente 6: Especialista em Comunicação e Relatórios"""
        return Agent(
            role="Communication and Reporting Specialist",
            goal="Gerar relatórios executivos e enviar comunicações com resultados",
            backstory="""Especialista em comunicação corporativa e geração de relatórios executivos.
            Habilidades: Criação de relatórios claros, formatação profissional de emails,
            anexação segura de arquivos, comunicação de métricas, alertas sobre problemas,
            follow-up automático quando necessário.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_extraction_task(self, agent):
        """Tarefa 1: Extração de Dados"""
        files_info = "\n".join([f"- {f['file']} ({f['format']}): {f['records']} registros" 
                                for f in self.extractor.processed_files])
        
        return Task(
            description=f"""
            EXTRAIR DADOS DE NOTAS FISCAIS MULTI-FORMATO
            
            Arquivos processados:
            {files_info if files_info else 'Aguardando processamento...'}
            
            OBJETIVOS:
            1. Identificar e extrair todos os campos relevantes
            2. Preservar integridade dos dados
            3. Tratar diferentes encodings (UTF-8, CP1252, ISO-8859-1)
            4. Capturar cabeçalhos e itens
            5. Manter rastreabilidade do arquivo origem
            
            VALIDAÇÕES:
            - Chave de acesso: 44 caracteres numéricos
            - CNPJ/CPF: validar formato e dígitos
            - Datas: converter para padrão DD/MM/YYYY HH:MM:SS
            - Valores: preservar precisão decimal
            """,
            expected_output="Dados extraídos com sucesso de todos os arquivos, mantendo integridade",
            agent=agent
        )
    
    def create_standardization_task(self, agent):
        """Tarefa 2: Padronização de Campos"""
        return Task(
            description=f"""
            PADRONIZAR NOMENCLATURA DE CAMPOS PARA FORMATO 2025
            
            Total de registros a padronizar: {len(self.extractor.extracted_data)}
            
            MAPEAMENTOS CRÍTICOS:
            - Chave NFe → "CHAVE DE ACESSO"
            - CNPJ/CPF → "CPF/CNPJ Emitente" ou "CNPJ DESTINATÁRIO"
            - Data Emissão → "DATA EMISSÃO" (formato: DD/MM/YYYY HH:MM:SS)
            - Valores → Formato decimal com vírgula (ex: "150,66")
            
            REGRAS DE IDENTIFICAÇÃO:
            - 44 caracteres numéricos = Chave de Acesso
            - 14 dígitos = CNPJ
            - 11 dígitos = CPF
            - Padrão NCM = 8 dígitos
            - CFOP = 4 dígitos iniciando com 5, 6 ou 7
            """,
            expected_output="Todos os campos padronizados conforme nomenclatura 2025, com tipos corretos",
            agent=agent
        )
    
    def create_consolidation_task(self, agent):
        """Tarefa 3: Consolidação em Lista"""
        return Task(
            description=f"""
            CONSOLIDAR DADOS EM LISTA ÚNICA FORMATO CSV
            
            ESTRUTURA REQUERIDA:
            - Cabeçalho com nomes padrão 2025
            - Delimitador: ponto-e-vírgula (;)
            - Encoding: UTF-8
            - Decimais: vírgula como separador
            
            ORDENAÇÃO:
            1. Por data de emissão (mais recente primeiro)
            2. Por número da nota fiscal
            3. Por item dentro da nota
            
            TOTALIZADORES A CALCULAR:
            - Total de notas únicas
            - Soma de valores totais
            - Quantidade de itens
            - Média de valores
            
            FORMATO SAÍDA: outputs/csv/nfe_extracted_YYYYMMDD_HHMMSS.csv
            """,
            expected_output="Lista consolidada em CSV com todos os registros, ordenada e totalizada",
            agent=agent
        )
    
    def create_quality_task(self, agent):
        """Tarefa 4: Validação de Qualidade"""
        stats = self.extractor.get_statistics()
        
        return Task(
            description=f"""
            VALIDAR QUALIDADE DOS DADOS EXTRAÍDOS
            
            ESTATÍSTICAS ATUAIS:
            - Arquivos processados: {stats['total_files']}
            - Registros extraídos: {stats['total_records']}
            - Notas únicas: {stats['unique_invoices']}
            
            VALIDAÇÕES OBRIGATÓRIAS:
            
            1. CHAVE DE ACESSO:
               - Exatos 44 dígitos
               - Validar dígito verificador
               - Sem duplicatas
            
            2. CNPJ/CPF:
               - Validar algoritmo oficial
               - Formatar com zeros à esquerda
            
            3. VALORES:
               - Quantidade × Valor Unit = Total (tolerância 0.01)
               - Valores não negativos
               - Máximo 2 casas decimais
            
            4. DATAS:
               - Formato válido
               - Não futuras
               - Coerência temporal
            
            5. NCM/CFOP:
               - NCM: 8 dígitos válidos
               - CFOP: códigos existentes
            
            CRITÉRIOS APROVAÇÃO:
            - Mínimo 95% campos obrigatórios preenchidos
            - Zero chaves duplicadas
            - Máximo 5% registros com alertas
            """,
            expected_output="Relatório de qualidade com % aprovação, lista de problemas e recomendações",
            agent=agent
        )
    
    def create_counting_task(self, agent):
        """Tarefa 5: Verificação de Contagem"""
        expected_count = sum(f['records'] for f in self.extractor.processed_files)
        actual_count = len(self.extractor.extracted_data)
        
        return Task(
            description=f"""
            VERIFICAR CORRESPONDÊNCIA DE CONTAGEM
            
            CONTAGENS A VERIFICAR:
            1. Total de arquivos processados: {len(self.extractor.processed_files)}
            2. Registros por arquivo:
            {chr(10).join([f"   - {f['file']}: {f['records']} registros" 
                          for f in self.extractor.processed_files])}
            3. Total geral esperado: {expected_count}
            4. Total extraído: {actual_count}
            
            ANÁLISE DE DISCREPÂNCIAS:
            - Identificar registros perdidos
            - Localizar duplicações não intencionais
            - Verificar se todos os itens foram capturados
            - Conferir totalizadores
            
            TOLERÂNCIA: 0% para contagem de registros
            
            AÇÃO SE DIVERGENTE:
            - Gerar alerta vermelho na interface
            - Detalhar onde está a diferença
            - Sugerir reprocessamento se necessário
            """,
            expected_output="Confirmação se contagens correspondem ou relatório detalhado de divergências",
            agent=agent
        )
    
    def create_communication_task(self, agent):
        """Tarefa 6: Comunicação e Relatórios"""
        stats = self.extractor.get_statistics()
        
        return Task(
            description=f"""
            GERAR RELATÓRIO E ENVIAR EMAIL COM RESULTADOS
            
            DESTINATÁRIO: {os.getenv('EMAIL_DESTINATARIO', 'fiscal@empresa.com')}
            
            CONTEÚDO DO EMAIL:
            - Resumo executivo do processamento
            - Total de arquivos: {stats['total_files']}
            - Total de registros: {stats['total_records']}
            - Taxa de sucesso: {(stats['successful_files']/max(stats['total_files'],1)*100):.1f}%
            - Alertas de qualidade (se houver)
            - Anexo: arquivo CSV gerado
            
            FORMATAÇÃO:
            - Email HTML profissional
            - Tabelas para estatísticas
            - Destaques para alertas
            - Call-to-action claro
            
            CONFIRMAÇÃO:
            - Registrar envio com timestamp
            - Salvar cópia em outputs/emails/
            """,
            expected_output="Email enviado com sucesso, confirmação de entrega e cópia arquivada",
            agent=agent
        )
    
    def execute_extraction_workflow(self, directory_path):
        """Executa workflow completo de extração com CrewAI obrigatório"""
        try:
            logger.info("=" * 70)
            logger.info("🔧 INICIANDO WORKFLOW DE EXTRAÇÃO COM CREWAI (OBRIGATÓRIO)")
            logger.info("=" * 70)
            
            # Validar Ollama novamente
            self._validate_ollama()
            
            # Processar arquivos
            logger.info("📂 Processando arquivos do diretório...")
            total_records = self.extractor.process_directory(directory_path)
            
            if total_records == 0:
                logger.error("✗ Nenhum registro extraído dos arquivos")
                return False, "✗ Nenhum registro extraído dos arquivos"
            
            logger.info(f"✓ {total_records} registros extraídos dos documentos")
            
            # Criar agentes
            logger.info("🔧 Criando agentes especializados...")
            extraction_agent = self.create_extraction_agent()
            standardization_agent = self.create_standardization_agent()
            consolidation_agent = self.create_consolidation_agent()
            quality_agent = self.create_quality_agent()
            counting_agent = self.create_counting_agent()
            communication_agent = self.create_communication_agent()
            
            logger.info("✓ Agentes criados com sucesso")
            
            # Criar tarefas
            logger.info("📝 Definindo tarefas...")
            task1 = self.create_extraction_task(extraction_agent)
            task2 = self.create_standardization_task(standardization_agent)
            task3 = self.create_consolidation_task(consolidation_agent)
            task4 = self.create_quality_task(quality_agent)
            task5 = self.create_counting_task(counting_agent)
            task6 = self.create_communication_task(communication_agent)
            
            logger.info("✓ Tarefas definidas")
            
            # Criar crew
            logger.info("🤥 Montando equipe CrewAI...")
            crew = Crew(
                agents=[
                    extraction_agent,
                    standardization_agent,
                    consolidation_agent,
                    quality_agent,
                    counting_agent,
                    communication_agent
                ],
                tasks=[task1, task2, task3, task4, task5, task6],
                verbose=True
            )
            
            logger.info("✓ Equipe CrewAI montada")
            
            # Executar workflow
            logger.info("🎉 Executando análise com agentes CrewAI...")
            logger.debug("Iniciando crew.kickoff() - aguarde...")
            crew_result = crew.kickoff()
            
            logger.info("✓ Análise CrewAI concluída")
            logger.debug(f"Resultado do Crew capturado com sucesso")
            
            # Salvar CSV
            logger.info("🎾 Salvando lista consolidada...")
            csv_file, df = self.extractor.save_to_csv()
            
            logger.info(f"✓ CSV salvo em: {csv_file}")
            
            # Verificar contagem
            stats = self.extractor.get_statistics()
            count_match = stats['total_records'] == total_records
            
            if count_match:
                logger.info("✓ Contagem de registros corresponde!")
            else:
                logger.warning(f"⚠ Divergência na contagem! Esperado: {total_records}, Extraído: {stats['total_records']}")
            
            # Enviar email
            if csv_file:
                logger.info("📧 Preparando envio de email...")
                self._send_email_with_results(csv_file, stats)
            
            self.validation_results = {
                'success': True,
                'csv_file': csv_file,
                'statistics': stats,
                'count_match': count_match,
                'expected_records': total_records,
                'extracted_records': stats['total_records'],
                'crew_analysis': str(crew_result),
                'dataframe': df
            }
            
            logger.info("=" * 70)
            logger.info("✓ WORKFLOW CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 70)
            
            return True, self.validation_results
            
        except OllamaConnectionError as e:
            error_msg = f"✗ ERRO CRÍTICO: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"✗ Erro no workflow CrewAI: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _send_email_with_results(self, csv_file, stats):
        """Envia email com resultados - otimizado para evitar erro 552"""
        try:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            email_to = os.getenv("EMAIL_DESTINATARIO", "fiscal@empresa.com")
            
            if not email_user or not email_password:
                logger.warning("⚠ Credenciais de email não configuradas")
                return False
            
            logger.info(f"Preparando envio de email para: {email_to}")
            logger.debug(f"Arquivo anexo: {os.path.basename(csv_file)}")
            
            msg = MIMEMultipart('alternative')
            msg['From'] = email_user
            msg['To'] = email_to
            msg['Subject'] = f"Extração NFe - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            # HTML minimalista para reduzir tamanho e evitar erro 552
            html_body = f"""<html><body style="font-family:Arial,sans-serif;">
<h2>Extração de Notas Fiscais</h2>
<p><strong>Arquivos:</strong> {stats['total_files']} | <strong>Registros:</strong> {stats['total_records']} | <strong>Sucesso:</strong> {(stats['successful_files']/max(stats['total_files'],1)*100):.1f}%</p>
<p>Arquivo anexo: {os.path.basename(csv_file)}</p>
<p>Processado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
</body></html>"""
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Verificar tamanho do arquivo antes de anexar
            try:
                file_size = os.path.getsize(csv_file)
                if file_size > 20000000:
                    logger.warning(f"Arquivo muito grande ({file_size} bytes). Enviando sem anexo")
                else:
                    with open(csv_file, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(csv_file)}')
                    msg.attach(part)
                    logger.debug(f"Arquivo anexado com sucesso")
            except Exception as attach_error:
                logger.warning(f"Não foi possível anexar arquivo: {attach_error}")
            
            # Enviar email com timeout
            logger.info(f"Conectando ao servidor SMTP {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado com sucesso para {email_to}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Erro autenticação SMTP: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"Desconexão SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Erro SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}", exc_info=True)
            return False