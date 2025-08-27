# =============================================================================
# INTERFACE STREAMLIT - SISTEMA VR/VA (VERSÃO CORRIGIDA)
# =============================================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
import traceback
import logging

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports do sistema
try:
    from vr_system import VRAutomationSystem
    SYSTEM_AVAILABLE = True
    print("✅ vr_system importado com sucesso")
except ImportError as e:
    st.error(f"❌ ERRO ao importar vr_system: {e}")
    SYSTEM_AVAILABLE = False

try:
    from vr_crewai import VRCrewAISystem
    CREWAI_AVAILABLE = True
    print("✅ vr_crewai importado com sucesso")
except ImportError as e:
    st.warning(f"⚠️ CrewAI não disponível: {e}")
    CREWAI_AVAILABLE = False

# Import do módulo dashboard
try:
    from dashboard import (
        mostrar_dashboard_executivo, 
        mostrar_analise_geografica,
        mostrar_analise_sindicatos,
        mostrar_planilha_final_melhorada,
        mostrar_downloads,
        formatar_moeda_br
    )
    DASHBOARD_AVAILABLE = True
    print("✅ dashboard importado com sucesso")
except ImportError as e:
    st.error(f"❌ ERRO ao importar dashboard: {e}")
    DASHBOARD_AVAILABLE = False

# Configuração da página
st.set_page_config(
    page_title="Sistema VR/VA - Automação Inteligente",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ff6b6b;
        margin: 0.5rem 0;
    }
    .success-container {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def setup_streamlit_logging():
    """🔍 Configura logs específicos para Streamlit"""
    try:
        diretorio_atual = os.getcwd()
        if diretorio_atual.endswith('src'):
            diretorio_raiz = os.path.dirname(diretorio_atual)
        else:
            diretorio_raiz = diretorio_atual
        
        diretorio_logs = os.path.join(diretorio_raiz, "outputs", "logs")
        os.makedirs(diretorio_logs, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(diretorio_logs, f"streamlit_interface_{timestamp}.log")
        
        logger = logging.getLogger('StreamlitApp')
        logger.setLevel(logging.DEBUG)
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"🌐 Sistema de logs Streamlit configurado: {log_file}")
        return logger
        
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('StreamlitApp')
        logger.error(f"❌ Erro configurar logs Streamlit: {e}")
        return logger

# Inicializar logger global
streamlit_logger = setup_streamlit_logging()

def verificar_status_email(vr_system, resultado=None):
    """📧 Verifica status real do envio de emails"""
    try:
        if hasattr(vr_system, 'status_emails'):
            status = vr_system.status_emails
            return status.get('sucesso_geral', False), status
        
        if isinstance(resultado, dict):
            return resultado.get('emails_enviados', False), {}
        
        if hasattr(vr_system, 'resultado_final') and vr_system.resultado_final is not None:
            return True, {'assumido': True}
        
        return False, {'erro': 'Status não disponível'}
        
    except Exception as e:
        return False, {'erro': str(e)}

def inicializar_session_state():
    """🔧 Inicializa variáveis de sessão COM LOGS"""
    streamlit_logger.info("🔧 Inicializando session state")
    
    if 'vr_system' not in st.session_state:
        if SYSTEM_AVAILABLE:
            st.session_state.vr_system = VRAutomationSystem()
            streamlit_logger.info("✅ VRAutomationSystem inicializado")
        else:
            st.session_state.vr_system = None
            streamlit_logger.error("❌ VRAutomationSystem não disponível")
    
    if 'arquivos_carregados' not in st.session_state:
        st.session_state.arquivos_carregados = {}
        streamlit_logger.debug("📋 arquivos_carregados inicializado")
    
    if 'processo_executado' not in st.session_state:
        st.session_state.processo_executado = False
        streamlit_logger.debug("⚙️ processo_executado inicializado")
    
    if 'resultado_final' not in st.session_state:
        st.session_state.resultado_final = None
        streamlit_logger.debug("📊 resultado_final inicializado")

def sidebar_upload():
    """Sidebar com upload de arquivos"""
    st.sidebar.header("📁 Upload de Arquivos")
    
    if not SYSTEM_AVAILABLE or st.session_state.vr_system is None:
        st.sidebar.error("Sistema não disponível")
        return False
    
    # Definir arquivos necessários
    arquivos_necessarios = {
        'ativos': 'Colaboradores Ativos',
        'ferias': 'Funcionários em Férias',
        'desligados': 'Desligamentos',
        'admissoes': 'Admissões do Mês',
        'valores_sindicato': 'Valores por Estado',
        'dias_uteis': 'Dias Úteis',
        'afastamentos': 'Afastamentos',
        'estagiarios': 'Estagiários',
        'aprendizes': 'Aprendizes',
        'exterior': 'Colaboradores Exterior'
    }
    
    # Upload de cada arquivo
    for key, label in arquivos_necessarios.items():
        st.sidebar.subheader(f"{label}")
        
        uploaded_file = st.sidebar.file_uploader(
            f"Selecione {label}",
            type=['xlsx', 'xls'],
            key=f"upload_{key}",
            help=f"Arquivo: {label}.xlsx"
        )
        
        if uploaded_file is not None:
            try:
                sucesso = st.session_state.vr_system.carregar_arquivo(
                    uploaded_file.name, 
                    uploaded_file.read(), 
                    key
                )
                
                if sucesso:
                    st.sidebar.success(f"✅ {label}")
                    st.session_state.arquivos_carregados[key] = uploaded_file.name
                else:
                    st.sidebar.error(f"❌ {label}")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Erro: {str(e)}")
    
    # Status dos arquivos
    st.sidebar.header("📊 Status dos Arquivos")
    
    for key, label in arquivos_necessarios.items():
        if key in st.session_state.arquivos_carregados:
            st.sidebar.write(f"✅ {label}")
        else:
            st.sidebar.write(f"⭕ {label}")
    
    # Verificar se todos os arquivos foram carregados
    arquivos_ok, faltando = st.session_state.vr_system.verificar_arquivos_necessarios()
    
    if arquivos_ok:
        st.sidebar.success("🎉 Todos os arquivos carregados!")
        return True
    else:
        st.sidebar.warning(f"⚠️ Faltam: {len(faltando)} arquivos")
        return False

def mostrar_instrucoes():
    """Mostra instruções quando arquivos não estão carregados"""
    st.info("📋 Carregue todos os 10 arquivos Excel na barra lateral para começar.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Como usar:")
        st.markdown("""
        1. **Upload**: Carregue os 10 arquivos Excel na sidebar
        2. **Configure**: Defina competência e percentuais
        3. **Processe**: Escolha CrewAI ou tradicional
        4. **Analise**: Use dashboard e relatórios
        5. **Download**: Baixe resultados finais
        """)
    
    with col2:
        st.subheader("📋 Arquivos Necessários:")
        st.markdown("""
        - **ATIVOS.xlsx** - Colaboradores ativos
        - **FERIAS.xlsx** - Funcionários em férias
        - **DESLIGADOS.xlsx** - Desligamentos
        - **ADMISSAO ABRIL.xlsx** - Admissões
        - **Base sindicato x valor.xlsx** - Valores VR
        - **Base dias uteis.xlsx** - Dias úteis
        - **AFASTAMENTOS.xlsx** - Licenças
        - **ESTAGIO.xlsx** - Estagiários
        - **APRENDIZ.xlsx** - Aprendizes
        - **EXTERIOR.xlsx** - Colaboradores exterior
        """)

def mostrar_configuracoes():
    """✅ Interface de configurações CORRIGIDA"""
    st.header("⚙️ Configurações")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        competencia = st.text_input(
            "📅 Competência", 
            value=st.session_state.vr_system.competencia,
            help="Formato: MM/YYYY"
        )
        st.session_state.vr_system.competencia = competencia
    
    with col2:
        # ✅ CORREÇÃO: Slider de 0-100% ao invés de 0.0-1.0
        percentual_empresa_pct = st.slider(
            "🏢 % Empresa", 
            min_value=0,        # 0 ao invés de 0.0
            max_value=100,      # 100 ao invés de 1.0
            value=int(st.session_state.vr_system.config['percentual_empresa'] * 100),  # Converter para %
            step=1,             # 1% ao invés de 0.01
            format="%d%%"       # %d para inteiro
        )
        
        # Converter de volta para decimal para o sistema
        percentual_empresa = percentual_empresa_pct / 100.0
        st.session_state.vr_system.config['percentual_empresa'] = percentual_empresa
        st.session_state.vr_system.config['percentual_funcionario'] = 1.0 - percentual_empresa
    
    with col3:
        dia_corte = st.number_input(
            "📅 Dia Corte", 
            min_value=1, 
            max_value=31, 
            value=st.session_state.vr_system.config['dia_corte_desligamento']
        )
        st.session_state.vr_system.config['dia_corte_desligamento'] = dia_corte
    
    with col4:
        total_ativos = len(st.session_state.vr_system.datasets.get('ativos', []))
        st.metric("👥 Colaboradores", f"{total_ativos:,}")

def mostrar_botoes_processamento():
    """Botões de processamento"""
    st.header("🚀 Processamento")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🤖 Processar com CrewAI", type="primary", use_container_width=True):
            processar_com_crewai()
    
    with col2:
        if st.button("⚙️ Processar Tradicional", use_container_width=True):
            processar_tradicional()
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            reset_sistema()

def processar_com_crewai():
    """🤖 Processa VR/VA usando CrewAI - VERSÃO CORRIGIDA"""
    streamlit_logger.info("🤖 Iniciando processamento CrewAI")
    
    try:
        if not CREWAI_AVAILABLE:
            streamlit_logger.error("❌ CrewAI não disponível")
            st.error("CrewAI não disponível. Use processamento tradicional.")
            return
        
        streamlit_logger.info("⚙️ Verificando arquivos necessários...")
        arquivos_ok, faltando = st.session_state.vr_system.verificar_arquivos_necessarios()
        if not arquivos_ok:
            streamlit_logger.error(f"❌ Arquivos faltando para CrewAI: {faltando}")
            st.error(f"Arquivos faltando: {faltando}")
            return
        
        streamlit_logger.info(f"✅ Todos os arquivos OK: {len(st.session_state.arquivos_carregados)}")
        
        # ✅ CORREÇÃO: Apenas spinner, sem progress bar confusa
        with st.spinner("🤖 Processando com CrewAI... Isso pode levar alguns minutos."):
            streamlit_logger.info("👥 Criando sistema CrewAI")
            crew_system = VRCrewAISystem(st.session_state.vr_system)
            streamlit_logger.info("✅ Sistema CrewAI criado")
            
            streamlit_logger.info("⚡ Executando workflow CrewAI")
            inicio_processamento = datetime.now()
            sucesso, resultado = crew_system.execute_vr_workflow()
            fim_processamento = datetime.now()
            tempo_processamento = (fim_processamento - inicio_processamento).total_seconds()
        
        if sucesso:
            streamlit_logger.info(f"✅ CrewAI concluído em {tempo_processamento:.2f}s")
            st.success("✅ CrewAI concluído com sucesso!")
            
            st.session_state.processo_executado = True
            st.session_state.resultado_final = st.session_state.vr_system.resultado_final
            
            # Log das métricas
            metricas = resultado['metricas_finais']
            streamlit_logger.info(f"📊 Métricas CrewAI:")
            streamlit_logger.info(f"   👥 Colaboradores: {metricas['colaboradores']:,}")
            streamlit_logger.info(f"   💰 Valor total: R$ {metricas['valor_total']:,.2f}")
            streamlit_logger.info(f"   🏢 Custo empresa: R$ {metricas['custo_empresa']:,.2f}")
            
            # ✅ CORREÇÃO: Métricas com formatação monetária corrigida
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Colaboradores", f"{metricas['colaboradores']:,}")
            
            with col2:
                # ✅ CORREÇÃO: Valor total formatado corretamente
                valor_total_formatado = f"R$ {metricas['valor_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.metric("💰 Total VR", valor_total_formatado)
            
            with col3:
                # ✅ CORREÇÃO: Custo empresa formatado corretamente  
                custo_empresa_formatado = f"R$ {metricas['custo_empresa']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.metric("🏢 Custo Empresa", custo_empresa_formatado)
            
            with col4:
                # ✅ CORREÇÃO: Status de email mais claro
                email_ok, email_status = verificar_status_email(st.session_state.vr_system, resultado)
                if email_ok:
                    st.metric("📧 Emails", "Enviado com Sucesso!", delta="✅", delta_color="normal")
                else:
                    st.metric("📧 Emails", "Falha no Envio", delta="❌ Verificar config", delta_color="inverse")
            
        else:
            streamlit_logger.error(f"❌ Erro CrewAI após {tempo_processamento:.2f}s: {resultado}")
            st.error(f"❌ Erro: {resultado}")
            
    except Exception as e:
        streamlit_logger.error(f"❌ Erro inesperado no CrewAI: {str(e)}")
        streamlit_logger.debug(f"🔍 Stacktrace CrewAI: {traceback.format_exc()}")
        st.error(f"❌ Erro inesperado: {str(e)}")

def processar_tradicional():
    """⚙️ Processa VR/VA usando método tradicional - VERSÃO CORRIGIDA"""
    streamlit_logger.info("⚙️ Iniciando processamento tradicional")
    
    try:
        streamlit_logger.info("🔍 Verificando arquivos necessários...")
        arquivos_ok, faltando = st.session_state.vr_system.verificar_arquivos_necessarios()
        if not arquivos_ok:
            streamlit_logger.error(f"❌ Arquivos faltando para tradicional: {faltando}")
            st.error(f"Arquivos faltando: {faltando}")
            return
            
        streamlit_logger.info(f"✅ Arquivos verificados: {len(st.session_state.arquivos_carregados)}")
        
        # ✅ CORREÇÃO: Apenas spinner, sem progress bar confusa
        with st.spinner("⚙️ Processando dados... Aguarde alguns instantes."):
            streamlit_logger.info("🚀 Executando processo tradicional completo")
            inicio_processamento = datetime.now()
            sucesso, resultado = st.session_state.vr_system.executar_processo_completo()
            fim_processamento = datetime.now()
            tempo_processamento = (fim_processamento - inicio_processamento).total_seconds()
        
        if sucesso:
            streamlit_logger.info(f"✅ Processamento tradicional concluído em {tempo_processamento:.2f}s")
            st.success("✅ Processamento concluído!")
            
            st.session_state.processo_executado = True
            st.session_state.resultado_final = st.session_state.vr_system.resultado_final
            
            # Log das métricas
            streamlit_logger.info(f"📊 Métricas tradicional:")
            streamlit_logger.info(f"   👥 Colaboradores: {resultado['colaboradores']:,}")
            streamlit_logger.info(f"   💰 Valor total: R$ {resultado['valor_total']:,.2f}")
            streamlit_logger.info(f"   📧 Emails: {'✅' if resultado['emails_enviados'] else '❌'}")
            
            # ✅ CORREÇÃO: Métricas com formatação monetária corrigida
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Colaboradores", f"{resultado['colaboradores']:,}")
            
            with col2:
                # ✅ CORREÇÃO: Valor total formatado corretamente
                valor_total_formatado = f"R$ {resultado['valor_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.metric("💰 Valor Total", valor_total_formatado)
            
            with col3:
                # ✅ CORREÇÃO: Status de email mais claro
                email_ok, email_status = verificar_status_email(st.session_state.vr_system, resultado)
                if email_ok:
                    st.metric("📧 Emails", "Enviado com Sucesso!", delta="✅", delta_color="normal")
                else:
                    detalhes = email_status.get('erro', 'Verificar logs')
                    st.metric("📧 Emails", "Falha no Envio", delta=f"❌ {detalhes[:15]}", delta_color="inverse")
            
        else:
            streamlit_logger.error(f"❌ Erro tradicional após {tempo_processamento:.2f}s: {resultado}")
            st.error(f"❌ Erro: {resultado}")
            
    except Exception as e:
        streamlit_logger.error(f"❌ Erro inesperado no tradicional: {str(e)}")
        streamlit_logger.debug(f"🔍 Stacktrace tradicional: {traceback.format_exc()}")
        st.error(f"❌ Erro inesperado: {str(e)}")

def reset_sistema():
    """🔄 Reset do sistema COM LOGS"""
    streamlit_logger.info("🔄 Executando reset do sistema")
    
    try:
        if SYSTEM_AVAILABLE:
            st.session_state.vr_system = VRAutomationSystem()
            streamlit_logger.info("✅ VRAutomationSystem resetado")
        
        st.session_state.arquivos_carregados = {}
        st.session_state.processo_executado = False
        st.session_state.resultado_final = None
        
        streamlit_logger.info("✅ Session state limpo")
        st.success("🔄 Sistema resetado!")
        st.rerun()
        
    except Exception as e:
        streamlit_logger.error(f"❌ Erro no reset: {str(e)}")
        st.error(f"❌ Erro no reset: {str(e)}")

def mostrar_resultados():
    """Mostra resultados detalhados usando módulo dashboard"""
    if not DASHBOARD_AVAILABLE:
        st.error("❌ Módulo dashboard não disponível")
        return
    
    st.header("📊 Resultados")
    
    df = st.session_state.resultado_final
    
    if df is None or df.empty:
        st.error("Nenhum resultado disponível")
        return
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Planilha", "📈 Dashboard", "🗺️ Geografia", "💼 Sindicatos", "📤 Downloads"
    ])
    
    with tab1:
        mostrar_planilha_final_melhorada(df)
    
    with tab2:
        mostrar_dashboard_executivo(df)
    
    with tab3:
        mostrar_analise_geografica(df)
    
    with tab4:
        mostrar_analise_sindicatos(df)
    
    with tab5:
        mostrar_downloads(df, st.session_state.vr_system)

def main_interface():
    """Interface principal"""
    st.markdown("""
    <div class="main-header">
        <h1>🍽️ Sistema VR/VA - Automação Inteligente</h1>
        <p>Processamento automatizado com 6 agentes CrewAI especializados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar se arquivos estão carregados
    arquivos_ok = sidebar_upload()
    
    if not arquivos_ok:
        mostrar_instrucoes()
        return
    
    # Interface quando arquivos estão carregados
    st.success("✅ Todos os arquivos carregados! Sistema pronto para processamento.")
    
    # Configurações
    mostrar_configuracoes()
    
    st.markdown("---")
    
    # Botões de processamento
    mostrar_botoes_processamento()
    
    # Mostrar resultados se disponível
    if st.session_state.processo_executado and st.session_state.resultado_final is not None:
        st.markdown("---")
        mostrar_resultados()

def main():
    """🌐 Função principal COM LOGS COMPLETOS"""
    streamlit_logger.info("🌐 Iniciando aplicação Streamlit")
    
    try:
        # Inicializar session state
        inicializar_session_state()
        
        # Verificar sistema
        if not SYSTEM_AVAILABLE:
            streamlit_logger.error("❌ Sistema VR não disponível")
            st.error("❌ Sistema VR não disponível")
            st.markdown("""
            ### 🔧 Soluções:
            1. Execute `setup.bat` na pasta principal
            2. Certifique-se que `vr_system.py` está em `src/`
            3. Ative o ambiente virtual
            4. Recarregue a página
            """)
            return
        
        if not DASHBOARD_AVAILABLE:
            streamlit_logger.error("❌ Módulo dashboard não disponível")
            st.error("❌ Módulo dashboard não disponível")
            st.markdown("""
            ### 🔧 Soluções:
            1. Certifique-se que `dashboard.py` está em `src/`
            2. Verifique as dependências do dashboard
            3. Recarregue a página
            """)
            return
        
        streamlit_logger.info("✅ Sistema VR e Dashboard disponíveis e inicializados")
        
        # Interface principal
        main_interface()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: gray; padding: 20px;'>
            <b>🍽️ Sistema VR/VA v2.1 (CORRIGIDO + DASHBOARD MELHORADO)</b><br>
            ✅ CrewAI + Streamlit + Ollama + Dashboard Modular
        </div>
        """, unsafe_allow_html=True)
        
        streamlit_logger.info("✅ Interface renderizada com sucesso")
        
    except Exception as e:
        streamlit_logger.error(f"❌ Erro crítico na aplicação: {str(e)}")
        streamlit_logger.debug(f"🔍 Stacktrace main: {traceback.format_exc()}")
        
        st.error(f"❌ Erro crítico: {str(e)}")
        
        with st.expander("🔍 Detalhes"):
            st.code(traceback.format_exc())
            
        # Log adicional para troubleshooting
        streamlit_logger.error("🔍 Informações de troubleshooting:")
        streamlit_logger.error(f"   🐍 Python: {sys.version}")
        streamlit_logger.error(f"   📁 Working dir: {os.getcwd()}")
        streamlit_logger.error(f"   📂 Files in dir: {os.listdir('.')}")

if __name__ == "__main__":
    main()