"""
app_utils.py - Utilitários e funçíµes auxiliares para app.py
Contém classes, configuraçõess e funçíµes de suporte
"""

import streamlit as st
import pandas as pd
import logging
import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# CLASSE: StreamCapture
# ============================================================================

class StreamCapture:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.file_handler = None
        self.setup_file_handler()
    
    def setup_file_handler(self):
        self.file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
    
    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        formatted_msg = f"[{timestamp}] {level}: {message}"
        self.logs.append(formatted_msg)
        
        if self.file_handler:
            record = logging.LogRecord(
                name="NFE_SYSTEM",
                level=getattr(logging, level),
                pathname="",
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            self.file_handler.emit(record)
    
    def get_logs(self):
        return "\n".join(self.logs)
    
    def clear_logs(self):
        self.logs = []

# ============================================================================
# FUNÇÃO: Configuração de Logging
# ============================================================================

def setup_logging(logs_path):
    log_file = logs_path / f"nfe_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__), log_file, StreamCapture(log_file)

# ============================================================================
# FUNÇÃO: Configuração de Página Streamlit
# ============================================================================

def setup_page_config():
    st.set_page_config(
        page_title="Sistema de Extracao NFe - Multi-formato",
        page_icon="📥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .info-box {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .success-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .ollama-error {
            background: #f8d7da;
            border: 2px solid #721c24;
            padding: 1rem;
            border-radius: 5px;
            color: #721c24;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNÇÃO: Inicialização do Estado da Sessão
# ============================================================================

def init_session_state():
    if 'extractor' not in st.session_state:
        from nfe_extractor import NFEExtractorSystem
        st.session_state.extractor = NFEExtractorSystem()
    if 'crew_system' not in st.session_state:
        st.session_state.crew_system = None
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'dataframe' not in st.session_state:
        st.session_state.dataframe = None
    if 'csv_file' not in st.session_state:
        st.session_state.csv_file = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'logs_text' not in st.session_state:
        st.session_state.logs_text = ""
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    if 'crew_analysis' not in st.session_state:
        st.session_state.crew_analysis = ""

# ============================================================================
# FUNÇÃO: Reset do Sistema
# ============================================================================

def reset_system(logger, stream_capture):
    logger.info("Reset do sistema iniciado")
    stream_capture.add_log("Reset do sistema iniciado", "INFO")
    
    if st.session_state.extractor:
        st.session_state.extractor.clear_memory()
        from nfe_extractor import NFEExtractorSystem
        st.session_state.extractor = NFEExtractorSystem()
    
    st.session_state.crew_system = None
    st.session_state.processed = False
    st.session_state.dataframe = None
    st.session_state.csv_file = None
    st.session_state.processing = False
    st.session_state.error_message = None
    st.session_state.results = None
    
    logger.info("Reset completado")
    stream_capture.add_log("Reset completado", "INFO")
    st.success("Sistema reiniciado - Pronto para novo processamento")
    st.rerun()

# ============================================================================
# FUNÇÃO: Processamento de Arquivos
# ============================================================================

def process_files_from_path(directory_path, logger, stream_capture):
    if not directory_path or not Path(directory_path).exists():
        logger.error(f"Caminho inválido: {directory_path}")
        stream_capture.add_log(f"Caminho inválido: {directory_path}", "ERROR")
        st.error("Caminho não existe ou inválido")
        return False
    
    try:
        from nfe_agents import NFECrewAISystem, OllamaConnectionError
        
        st.session_state.processing = True
        logger.info(f"Iniciando processamento de: {directory_path}")
        stream_capture.add_log(f"Iniciando processamento de: {directory_path}", "INFO")
        
        try:
            st.session_state.crew_system = NFECrewAISystem(st.session_state.extractor)
            logger.info("CrewAI System criado com sucesso")
            stream_capture.add_log("CrewAI System criado com sucesso", "INFO")
        except OllamaConnectionError as e:
            logger.error(f"Erro de conexão Ollama: {e}")
            stream_capture.add_log(f"Erro de conexão Ollama: {e}", "ERROR")
            st.markdown(f"""
            <div class="ollama-error">
                 ERRO CRíTICO: Ollama não está disponí­vel<br><br>
                {str(e)}<br><br>
                <strong>Ações necessárias:</strong><br>
                1. Abra um novo terminal<br>
                2. Execute: ollama serve<br>
                3. Em outro terminal: ollama pull llama3.2:3b<br>
                4. Retorne aqui e tente novamente
            </div>
            """, unsafe_allow_html=True)
            st.session_state.error_message = str(e)
            st.session_state.processing = False
            return False
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(" Iniciando pipeline CrewAI...")
        logger.info("Pipeline CrewAI iniciado")
        stream_capture.add_log("Pipeline CrewAI iniciado", "INFO")
        
        success, resultado = st.session_state.crew_system.execute_extraction_workflow(directory_path)
        
        if success:
            status_text.text("Processamento concluí­do com sucesso!")
            logger.info("Processamento concluí­do com sucesso")
            stream_capture.add_log("Processamento concluí­do com sucesso", "INFO")
            
            st.session_state.csv_file = resultado['csv_file']
            st.session_state.dataframe = resultado['dataframe']
            st.session_state.processed = True
            st.session_state.results = resultado['statistics']
            st.session_state.crew_analysis = resultado.get('crew_analysis', '')
            st.session_state.error_message = None
            
            logger.info(f"Processamento concluí­do. Registros: {len(st.session_state.dataframe) if st.session_state.dataframe is not None else 0}")
            stream_capture.add_log(f"Total de registros processados: {len(st.session_state.dataframe) if st.session_state.dataframe is not None else 0}", "INFO")
            
            st.session_state.logs_text = stream_capture.get_logs()
            
            progress_bar.progress(1.0)
            
            import time
            time.sleep(1)
            
            st.rerun()
        else:
            logger.error(f"Erro no processamento: {resultado}")
            stream_capture.add_log(f"Erro no processamento: {resultado}", "ERROR")
            st.error(f"Erro no processamento: {resultado}")
            st.session_state.error_message = resultado
            return False
            
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        stream_capture.add_log(f"Erro inesperado: {e}", "ERROR")
        st.error(f"Erro inesperado: {str(e)}")
        st.session_state.error_message = str(e)
        return False
    
    finally:
        st.session_state.processing = False

# ============================================================================
# FUNÇÃO: Envio de Email
# ============================================================================

def send_email_with_attachments(smtp_config, email_to, csv_file, stats, log_file, logger, stream_capture):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    
    try:
        smtp_server = smtp_config['smtp_server']
        smtp_port = smtp_config['smtp_port']
        email_user = smtp_config['email_user']
        email_password = smtp_config['email_password']
        
        if not email_user or not email_password:
            st.warning("Credenciais de email nao configuradas")
            logger.warning("Credenciais de email nao configuradas")
            stream_capture.add_log("Credenciais de email nao configuradas", "WARNING")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = email_to
        msg['Subject'] = f"Notas Fiscais Processadas - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # HTML minimalista para evitar erro 552 (tamanho excessivo)
        html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2>Notas Fiscais Processadas</h2>
<p>Arquivos: {stats['total_files']} | Registros: {stats['total_records']} | Taxa: {(stats['successful_files']/max(stats['total_files'],1)*100):.1f}%</p>
<p>Processado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
</body></html>"""
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Anexar CSV com validacao de tamanho (max 20MB)
        if csv_file and Path(csv_file).exists():
            file_size = os.path.getsize(csv_file)
            if file_size > 20000000:
                logger.warning(f"CSV muito grande ({file_size} bytes). Enviando sem anexo")
                stream_capture.add_log(f"CSV muito grande ({file_size} bytes). Enviando sem anexo", "WARNING")
            else:
                try:
                    with open(csv_file, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={Path(csv_file).name}')
                    msg.attach(part)
                    logger.info(f"CSV anexado: {csv_file}")
                    stream_capture.add_log(f"CSV anexado: {csv_file}", "INFO")
                except Exception as e:
                    logger.warning(f"Erro ao anexar CSV: {e}")
                    stream_capture.add_log(f"Erro ao anexar CSV: {e}", "WARNING")
        
        # Anexar log com validacao de tamanho (max 10MB)
        if log_file and Path(log_file).exists():
            file_size = os.path.getsize(log_file)
            if file_size > 10000000:
                logger.warning(f"Log muito grande ({file_size} bytes). Enviando sem anexo")
                stream_capture.add_log(f"Log muito grande ({file_size} bytes). Enviando sem anexo", "WARNING")
            else:
                try:
                    with open(log_file, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={Path(log_file).name}')
                    msg.attach(part)
                    logger.info(f"Log anexado: {log_file}")
                    stream_capture.add_log(f"Log anexado: {log_file}", "INFO")
                except Exception as e:
                    logger.warning(f"Erro ao anexar log: {e}")
                    stream_capture.add_log(f"Erro ao anexar log: {e}", "WARNING")
        
        # Enviar email com timeout 30s
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        
        logger.info("Email enviado com sucesso")
        stream_capture.add_log("Email enviado com sucesso", "INFO")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro autenticacao SMTP: {e}")
        stream_capture.add_log(f"Erro autenticacao SMTP: {e}", "ERROR")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"Desconexao SMTP: {e}")
        stream_capture.add_log(f"Desconexao SMTP: {e}", "ERROR")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Erro SMTP: {e}")
        stream_capture.add_log(f"Erro SMTP: {e}", "ERROR")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}", exc_info=True)
        stream_capture.add_log(f"Erro ao enviar email: {e}", "ERROR")
        return False

def send_email_results(logger, stream_capture, log_file):
    if not st.session_state.crew_system:
        st.error("Sistema não inicializado")
        logger.error("Tentativa de enviar email com sistema não inicializado")
        stream_capture.add_log("Tentativa de enviar email com sistema não inicializado", "ERROR")
        return
    
    try:
        with st.spinner("Enviando email com documentos..."):
            logger.info("Iniciando envio de email")
            stream_capture.add_log("Iniciando envio de email", "INFO")
            
            smtp_config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'email_user': os.getenv('EMAIL_USER'),
                'email_password': os.getenv('EMAIL_PASSWORD')
            }
            
            success = send_email_with_attachments(
                smtp_config,
                os.getenv('EMAIL_DESTINATARIO', 'fiscal@empresa.com'),
                st.session_state.csv_file,
                st.session_state.results,
                str(log_file),
                logger,
                stream_capture
            )
            
            if success:
                st.success("Email enviado com sucesso!")
                logger.info("Email enviado com sucesso")
                stream_capture.add_log("Email enviado com sucesso", "INFO")
            else:
                st.warning("Email não pôde ser enviado. Verifique configuraçõess SMTP.")
                logger.warning("Email não enviado - verificar configuraçõess")
                stream_capture.add_log("Email não enviado - verificar configuraçõess", "WARNING")
                
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}", exc_info=True)
        stream_capture.add_log(f"Erro ao enviar email: {e}", "ERROR")
        st.error(f"Erro ao enviar email: {str(e)}")