# =============================================================================
# INTERFACE STREAMLIT - SISTEMA VR/VA
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Adicionar path para imports locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from vr_system import VRAutomationSystem
    from vr_crewai import VRCrewAISystem
except ImportError:
    st.error("❌ Erro ao importar módulos do sistema. Verifique se todos os arquivos estão no diretório correto.")
    st.stop()

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
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ff6b6b;
    }
    .upload-container {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f9f9f9;
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

def inicializar_session_state():
    """Inicializa variáveis de sessão"""
    if 'vr_system' not in st.session_state:
        st.session_state.vr_system = VRAutomationSystem()
    
    if 'arquivos_carregados' not in st.session_state:
        st.session_state.arquivos_carregados = {}
    
    if 'processo_executado' not in st.session_state:
        st.session_state.processo_executado = False
    
    if 'resultado_final' not in st.session_state:
        st.session_state.resultado_final = None

def sidebar_upload():
    """Sidebar com upload de arquivos"""
    st.sidebar.header("📁 Upload de Arquivos")
    
    # Definir arquivos necessários
    arquivos_necessarios = {
        'ativos': 'Colaboradores Ativos',
        'ferias': 'Férias',
        'desligados': 'Desligados',
        'admissoes': 'Admissões do Mês',
        'valores_sindicato': 'Valores por Sindicato',
        'dias_uteis': 'Dias Úteis',
        'afastamentos': 'Afastamentos',
        'estagiarios': 'Estagiários',
        'aprendizes': 'Aprendizes',
        'exterior': 'Colaboradores Exterior'
    }
    
    # Upload de cada arquivo
    for key, label in arquivos_necessarios.items():
        st.sidebar.subheader(f"📋 {label}")
        
        uploaded_file = st.sidebar.file_uploader(
            f"Selecione o arquivo {label}",
            type=['xlsx', 'xls'],
            key=f"upload_{key}"
        )
        
        if uploaded_file is not None:
            # Carregar arquivo no sistema
            try:
                sucesso = st.session_state.vr_system.carregar_arquivo(
                    uploaded_file.name, 
                    uploaded_file.read(), 
                    key
                )
                
                if sucesso:
                    st.sidebar.success(f"✅ {label} carregado!")
                    st.session_state.arquivos_carregados[key] = uploaded_file.name
                else:
                    st.sidebar.error(f"❌ Erro ao carregar {label}")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Erro: {str(e)}")
    
    # Status dos arquivos
    st.sidebar.header("📊 Status dos Arquivos")
    
    for key, label in arquivos_necessarios.items():
        if key in st.session_state.arquivos_carregados:
            st.sidebar.write(f"✅ {label}")
        else:
            st.sidebar.write(f"⏳ {label}")
    
    # Verificar se todos os arquivos foram carregados
    arquivos_ok, faltando = st.session_state.vr_system.verificar_arquivos_necessarios()
    
    if arquivos_ok:
        st.sidebar.success("🎉 Todos os arquivos carregados!")
        return True
    else:
        st.sidebar.warning(f"⚠️ Faltam: {len(faltando)} arquivos")
        return False

def main_interface():
    """Interface principal"""
    st.title("🍽️ Sistema VR/VA - Automação Inteligente")
    st.markdown("---")
    
    # Verificar se arquivos estão carregados
    arquivos_ok = sidebar_upload()
    
    if not arquivos_ok:
        st.info("📋 **Carregue todos os arquivos necessários na barra lateral para começar.**")
        
        # Mostrar instruções
        st.header("📖 Instruções de Uso")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Como usar:")
            st.markdown("""
            1. **Upload dos Arquivos**: Carregue todos os 10 arquivos Excel necessários
            2. **Configurar Competência**: Defina o período de processamento
            3. **Executar Processo**: Clique em "Processar VR/VA"
            4. **Verificar Resultados**: Analise relatórios e métricas
            5. **Enviar Emails**: Confirme o envio automático
            """)
        
        with col2:
            st.subheader("📋 Arquivos Necessários:")
            st.markdown("""
            - **Ativos**: Lista de colaboradores ativos
            - **Férias**: Colaboradores em férias
            - **Desligados**: Funcionários desligados
            - **Admissões**: Novos funcionários do mês
            - **Valores por Sindicato**: Tabela de valores VR
            - **Dias Úteis**: Dias úteis por sindicato
            - **Afastamentos**: Licenças e afastamentos
            - **Estagiários**: Lista de estagiários
            - **Aprendizes**: Lista de aprendizes
            - **Exterior**: Colaboradores no exterior
            """)
        
        return
    
    # Interface principal quando arquivos estão carregados
    st.success("✅ **Todos os arquivos carregados! Sistema pronto para processamento.**")
    
    # Configurações
    st.header("⚙️ Configurações")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        competencia = st.text_input(
            "📅 Competência", 
            value=st.session_state.vr_system.competencia,
            help="Formato: MM/YYYY"
        )
        st.session_state.vr_system.competencia = competencia
    
    with col2:
        percentual_empresa = st.slider(
            "🏢 Percentual Empresa", 
            min_value=0.0, 
            max_value=1.0, 
            value=st.session_state.vr_system.config['percentual_empresa'],
            step=0.01,
            format="%.0f%%"
        )
        st.session_state.vr_system.config['percentual_empresa'] = percentual_empresa
        st.session_state.vr_system.config['percentual_funcionario'] = 1.0 - percentual_empresa
    
    with col3:
        dia_corte = st.number_input(
            "📆 Dia Corte Desligamento", 
            min_value=1, 
            max_value=31, 
            value=st.session_state.vr_system.config['dia_corte_desligamento']
        )
        st.session_state.vr_system.config['dia_corte_desligamento'] = dia_corte
    
    st.markdown("---")
    
    # Botões de ação
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🚀 Processar VR/VA com CrewAI", type="primary", use_container_width=True):
            processar_com_crewai()
    
    with col2:
        if st.button("📊 Processar Tradicional", use_container_width=True):
            processar_tradicional()
    
    with col3:
        if st.button("🔄 Reset Sistema", use_container_width=True):
            reset_sistema()
    
    # Mostrar resultados se processo foi executado
    if st.session_state.processo_executado and st.session_state.resultado_final is not None:
        mostrar_resultados()

def processar_com_crewai():
    """Processa VR/VA usando CrewAI"""
    try:
        with st.spinner("🤖 Processando com Agentes CrewAI..."):
            # Criar sistema CrewAI
            crew_system = VRCrewAISystem(st.session_state.vr_system)
            
            # Executar workflow
            sucesso, resultado = crew_system.execute_vr_workflow()
            
            if sucesso:
                st.success("✅ **Processamento CrewAI concluído com sucesso!**")
                
                # Armazenar resultados
                st.session_state.processo_executado = True
                st.session_state.resultado_final = st.session_state.vr_system.resultado_final
                st.session_state.resultado_crewai = resultado
                
                # Mostrar métricas principais
                metricas = resultado['metricas_finais']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "👥 Colaboradores", 
                        f"{metricas['colaboradores']:,}",
                        help="Total de colaboradores processados"
                    )
                
                with col2:
                    st.metric(
                        "💰 Valor Total VR", 
                        f"R$ {metricas['valor_total']:,.2f}",
                        help="Valor total dos vales refeição"
                    )
                
                with col3:
                    st.metric(
                        "🏢 Custo Empresa", 
                        f"R$ {metricas['custo_empresa']:,.2f}",
                        help="Custo para a empresa (80%)"
                    )
                
                with col4:
                    desconto_funcionarios = metricas['valor_total'] - metricas['custo_empresa']
                    st.metric(
                        "👤 Desconto Funcionários", 
                        f"R$ {desconto_funcionarios:,.2f}",
                        help="Desconto dos funcionários (20%)"
                    )
                
                # Mostrar análise CrewAI
                with st.expander("🤖 **Análise Detalhada dos Agentes CrewAI**", expanded=False):
                    st.markdown("### 📋 Relatório dos Agentes")
                    st.text_area(
                        "Análise CrewAI",
                        value=resultado['analise_crewai'],
                        height=400,
                        disabled=True
                    )
                
            else:
                st.error(f"❌ **Erro no processamento CrewAI:** {resultado}")
                
    except Exception as e:
        st.error(f"❌ **Erro inesperado:** {str(e)}")
        with st.expander("🔍 Detalhes do Erro"):
            import traceback
            st.code(traceback.format_exc())

def processar_tradicional():
    """Processa VR/VA usando método tradicional"""
    try:
        with st.spinner("⚙️ Processando método tradicional..."):
            sucesso, resultado = st.session_state.vr_system.executar_processo_completo()
            
            if sucesso:
                st.success("✅ **Processamento tradicional concluído!**")
                
                # Armazenar resultados
                st.session_state.processo_executado = True
                st.session_state.resultado_final = st.session_state.vr_system.resultado_final
                
                # Mostrar métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("👥 Colaboradores", f"{resultado['colaboradores']:,}")
                
                with col2:
                    st.metric("💰 Valor Total", f"R$ {resultado['valor_total']:,.2f}")
                
                with col3:
                    st.metric("📧 Emails", "✅ Enviados" if resultado['emails_enviados'] else "❌ Falha")
                
            else:
                st.error(f"❌ **Erro no processamento:** {resultado}")
                
    except Exception as e:
        st.error(f"❌ **Erro inesperado:** {str(e)}")

def reset_sistema():
    """Reset do sistema"""
    st.session_state.vr_system = VRAutomationSystem()
    st.session_state.arquivos_carregados = {}
    st.session_state.processo_executado = False
    st.session_state.resultado_final = None
    st.success("🔄 **Sistema resetado com sucesso!**")

def mostrar_resultados():
    """Mostra resultados detalhados"""
    st.markdown("---")
    st.header("📊 Resultados Detalhados")
    
    df_resultado = st.session_state.resultado_final
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Planilha Final", 
        "📈 Dashboard", 
        "🗺️ Análise Geográfica", 
        "💼 Por Sindicato",
        "📤 Downloads"
    ])
    
    with tab1:
        st.subheader("📋 Planilha Final de VR/VA")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sindicatos = ['Todos'] + list(df_resultado['Sindicato do Colaborador'].unique())
            sindicato_filter = st.selectbox("🏛️ Filtrar por Sindicato", sindicatos)
        
        with col2:
            valor_min = st.number_input("💰 Valor Mínimo", min_value=0.0, value=0.0)
        
        with col3:
            valor_max = st.number_input("💰 Valor Máximo", min_value=0.0, value=float(df_resultado['TOTAL'].max()))
        
        # Aplicar filtros
        df_filtrado = df_resultado.copy()
        
        if sindicato_filter != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Sindicato do Colaborador'] == sindicato_filter]
        
        df_filtrado = df_filtrado[
            (df_filtrado['TOTAL'] >= valor_min) & 
            (df_filtrado['TOTAL'] <= valor_max)
        ]
        
        # Mostrar estatísticas do filtro
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Registros", f"{len(df_filtrado):,}")
        
        with col2:
            st.metric("💰 Total Filtrado", f"R$ {df_filtrado['TOTAL'].sum():,.2f}")
        
        with col3:
            st.metric("📈 Valor Médio", f"R$ {df_filtrado['TOTAL'].mean():,.2f}")
        
        with col4:
            st.metric("⏱️ Dias Médios", f"{df_filtrado['Dias'].mean():.1f}")
        
        # Mostrar tabela
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )
    
    with tab2:
        st.subheader("📈 Dashboard Executivo")
        
        # KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👥 Total Colaboradores",
                f"{len(df_resultado):,}",
                help="Número total de colaboradores processados"
            )
        
        with col2:
            st.metric(
                "💰 Valor Total VR",
                f"R$ {df_resultado['TOTAL'].sum():,.2f}",
                help="Valor total dos vales refeição"
            )
        
        with col3:
            st.metric(
                "🏢 Custo Empresa",
                f"R$ {df_resultado['Custo empresa'].sum():,.2f}",
                help="Custo total para a empresa"
            )
        
        with col4:
            st.metric(
                "👤 Desconto Funcionários",
                f"R$ {df_resultado['Desconto profissional'].sum():,.2f}",
                help="Total de descontos dos funcionários"
            )
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de valores
            fig_hist = px.histogram(
                df_resultado,
                x='TOTAL',
                nbins=30,
                title="📊 Distribuição de Valores de VR",
                labels={'TOTAL': 'Valor VR (R$)', 'count': 'Frequência'}
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Top 10 maiores valores
            top_10 = df_resultado.nlargest(10, 'TOTAL')
            fig_bar = px.bar(
                top_10,
                x='Matricula',
                y='TOTAL',
                title="🏆 Top 10 Maiores Valores VR",
                labels={'TOTAL': 'Valor VR (R$)', 'Matricula': 'Matrícula'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Análise temporal
        if 'Admissão' in df_resultado.columns and df_resultado['Admissão'].notna().any():
            st.subheader("📅 Análise de Admissões")
            
            # Converter datas de admissão
            df_admissoes = df_resultado[df_resultado['Admissão'].notna()].copy()
            if len(df_admissoes) > 0:
                try:
                    df_admissoes['Data_Admissao'] = pd.to_datetime(df_admissoes['Admissão'], format='%m/%d/%y')
                    admissoes_por_dia = df_admissoes.groupby('Data_Admissao').size().reset_index(name='Quantidade')
                    
                    fig_line = px.line(
                        admissoes_por_dia,
                        x='Data_Admissao',
                        y='Quantidade',
                        title="📈 Admissões por Data",
                        labels={'Data_Admissao': 'Data de Admissão', 'Quantidade': 'Número de Admissões'}
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                except:
                    st.info("📝 Não foi possível processar as datas de admissão")
    
    with tab3:
        st.subheader("🗺️ Análise Geográfica")
        
        # Extrair estado do sindicato
        def extrair_estado_grafico(sindicato):
            if pd.isna(sindicato):
                return 'Não Identificado'
            
            sindicato_upper = str(sindicato).upper()
            if 'SP' in sindicato_upper:
                return 'São Paulo'
            elif 'RJ' in sindicato_upper:
                return 'Rio de Janeiro'
            elif 'PR' in sindicato_upper:
                return 'Paraná'
            elif 'RS' in sindicato_upper:
                return 'Rio Grande do Sul'
            else:
                return 'Outros'
        
        df_resultado['Estado'] = df_resultado['Sindicato do Colaborador'].apply(extrair_estado_grafico)
        
        # Análise por estado
        analise_estado = df_resultado.groupby('Estado').agg({
            'Matricula': 'count',
            'TOTAL': 'sum',
            'VALOR DIÁRIO VR': 'mean',
            'Dias': 'mean'
        }).round(2)
        
        analise_estado.columns = ['Colaboradores', 'Valor Total (R$)', 'Valor Médio Diário (R$)', 'Dias Médios']
        analise_estado = analise_estado.sort_values('Valor Total (R$)', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Resumo por Estado:**")
            st.dataframe(analise_estado, use_container_width=True)
        
        with col2:
            # Gráfico pizza
            fig_pie = px.pie(
                values=analise_estado['Valor Total (R$)'],
                names=analise_estado.index,
                title="🥧 Distribuição de Valores por Estado"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfico de barras por estado
        fig_bar_estado = px.bar(
            x=analise_estado.index,
            y=analise_estado['Colaboradores'],
            title="👥 Colaboradores por Estado",
            labels={'x': 'Estado', 'y': 'Número de Colaboradores'}
        )
        st.plotly_chart(fig_bar_estado, use_container_width=True)
    
    with tab4:
        st.subheader("💼 Análise por Sindicato")
        
        # Análise detalhada por sindicato
        analise_sindicato = df_resultado.groupby('Sindicato do Colaborador').agg({
            'Matricula': 'count',
            'TOTAL': ['sum', 'mean'],
            'Dias': 'mean',
            'VALOR DIÁRIO VR': 'first'
        }).round(2)
        
        # Achatar colunas
        analise_sindicato.columns = [
            'Colaboradores', 
            'Valor Total (R$)', 
            'Valor Médio por Pessoa (R$)',
            'Dias Médios',
            'Valor Diário (R$)'
        ]
        
        analise_sindicato = analise_sindicato.sort_values('Valor Total (R$)', ascending=False)
        
        st.write("**📋 Detalhamento por Sindicato:**")
        st.dataframe(analise_sindicato, use_container_width=True)
        
        # Gráfico comparativo
        fig_comparison = px.bar(
            x=analise_sindicato.index,
            y=analise_sindicato['Valor Total (R$)'],
            title="💰 Valor Total por Sindicato",
            labels={'x': 'Sindicato', 'y': 'Valor Total (R$)'}
        )
        fig_comparison.update_xaxes(tickangle=45)
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Eficiência por sindicato
        st.subheader("📈 Eficiência por Sindicato")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_dias = px.bar(
                x=analise_sindicato.index,
                y=analise_sindicato['Dias Médios'],
                title="⏱️ Dias Médios por Sindicato",
                labels={'x': 'Sindicato', 'y': 'Dias Médios'}
            )
            fig_dias.update_xaxes(tickangle=45)
            st.plotly_chart(fig_dias, use_container_width=True)
        
        with col2:
            fig_valor_diario = px.bar(
                x=analise_sindicato.index,
                y=analise_sindicato['Valor Diário (R$)'],
                title="💵 Valor Diário por Sindicato",
                labels={'x': 'Sindicato', 'y': 'Valor Diário (R$)'}
            )
            fig_valor_diario.update_xaxes(tickangle=45)
            st.plotly_chart(fig_valor_diario, use_container_width=True)
    
    with tab5:
        st.subheader("📤 Downloads e Relatórios")
        
        # Preparar dados para download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 Planilha Principal:**")
            
            # Converter DataFrame para CSV
            csv_principal = df_resultado.to_csv(index=False)
            
            st.download_button(
                label="💾 Download Planilha VR (CSV)",
                data=csv_principal,
                file_name=f"VR_Mensal_{st.session_state.vr_system.competencia.replace('/', '')}_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Estatísticas resumidas
            st.write("**📈 Resumo Executivo:**")
            resumo = {
                'Métrica': [
                    'Total de Colaboradores',
                    'Valor Total VR (R$)',
                    'Custo Empresa (R$)',
                    'Desconto Funcionários (R$)',
                    'Valor Médio por Pessoa (R$)',
                    'Dias Médios de Trabalho'
                ],
                'Valor': [
                    f"{len(df_resultado):,}",
                    f"{df_resultado['TOTAL'].sum():,.2f}",
                    f"{df_resultado['Custo empresa'].sum():,.2f}",
                    f"{df_resultado['Desconto profissional'].sum():,.2f}",
                    f"{df_resultado['TOTAL'].mean():,.2f}",
                    f"{df_resultado['Dias'].mean():.2f}"
                ]
            }
            
            df_resumo = pd.DataFrame(resumo)
            csv_resumo = df_resumo.to_csv(index=False)
            
            st.download_button(
                label="📋 Download Resumo Executivo (CSV)",
                data=csv_resumo,
                file_name=f"Resumo_VR_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.write("**🗺️ Análises por Estado:**")
            
            csv_estado = analise_estado.to_csv()
            
            st.download_button(
                label="🗺️ Download Análise por Estado (CSV)",
                data=csv_estado,
                file_name=f"Analise_Estado_VR_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.write("**💼 Análises por Sindicato:**")
            
            csv_sindicato = analise_sindicato.to_csv()
            
            st.download_button(
                label="💼 Download Análise por Sindicato (CSV)",
                data=csv_sindicato,
                file_name=f"Analise_Sindicato_VR_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Informações do processamento
        st.markdown("---")
        st.subheader("ℹ️ Informações do Processamento")
        
        info_processamento = {
            'Competência': st.session_state.vr_system.competencia,
            'Data/Hora Processamento': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'Percentual Empresa': f"{st.session_state.vr_system.config['percentual_empresa']*100:.0f}%",
            'Percentual Funcionário': f"{st.session_state.vr_system.config['percentual_funcionario']*100:.0f}%",
            'Dia Corte Desligamento': st.session_state.vr_system.config['dia_corte_desligamento'],
            'Total de Arquivos Processados': len(st.session_state.arquivos_carregados)
        }
        
        for key, value in info_processamento.items():
            st.write(f"**{key}:** {value}")

def main():
    """Função principal"""
    try:
        # Inicializar session state
        inicializar_session_state()
        
        # Interface principal
        main_interface()
        
    except Exception as e:
        st.error(f"❌ **Erro crítico na aplicação:** {str(e)}")
        
        with st.expander("🔍 Detalhes Técnicos"):
            import traceback
            st.code(traceback.format_exc())
        
        st.info("🔄 **Tente recarregar a página ou entre em contato com o suporte técnico.**")

if __name__ == "__main__":
    main()