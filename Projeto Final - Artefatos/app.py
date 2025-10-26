import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import sys
from pathlib import Path
import shutil
import logging
import io

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nfe_extractor import NFEExtractorSystem
from nfe_agents import NFECrewAISystem, OllamaConnectionError
from nfe_dashboard_analytics import NFEDashboardAnalytics
# from nfe_advanced_extractor import NFEAdvancedExtractor
from nfe_integration_bridge import NFEIntegrationBridge
from app_utils import (
    setup_logging,
    setup_page_config,
    init_session_state,
    reset_system,
    process_files_from_path,
    send_email_results
)

NOTAS_FISCAIS_PATH = Path(__file__).parent.parent / "NotasFiscais"
NOTAS_FISCAIS_PATH.mkdir(exist_ok=True)

LOGS_PATH = Path(__file__).parent / "outputs" / "logs"
LOGS_PATH.mkdir(parents=True, exist_ok=True)

CSV_OUTPUT_PATH = Path(__file__).parent / "outputs" / "csv"

logger, log_file, stream_capture = setup_logging(LOGS_PATH)

setup_page_config()
init_session_state()

st.markdown("""
<div class="main-header">
    <h1>📊 Sistema de Extração de Notas Fiscais</h1>
    <p style="font-size: 1.1em; margin: 0;">Extração inteligente multi-formato com CrewAI obrigatório</p>
    <p style="font-size: 0.9em; margin-top: 0.5em; opacity: 0.9;">
        XML | PDF | TXT | CSV | JSON (Suporta arquivos >200MB)
    </p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Opções de Processamento")
    
    modo = st.radio(
        "Escolha o modo de entrada:",
        ["Pasta Padrão (NotasFiscais)", "Upload de Arquivos"]
    )
    
    st.markdown("---")
    
    if st.session_state.processed and st.session_state.results:
        st.header("📊 Estatísticas")
        stats = st.session_state.results
        
        st.metric("📊 Arquivos", stats['total_files'])
        st.metric("✅ Sucesso", stats['successful_files'])
        st.metric("📊 Registros", stats['total_records'])
        st.metric("📑 NFes Únicas", stats['unique_invoices'])
        
        success_rate = (stats['successful_files'] / max(stats['total_files'], 1) * 100)
        st.progress(success_rate / 100)
        st.caption(f"Taxa de sucesso: {success_rate:.1f}%")
    
    st.markdown("---")
    
    col_reset = st.columns(1)
    
    with col_reset[0]:
        if st.button("🗑️ Reset", use_container_width=True):
            reset_system(logger, stream_capture)

if st.session_state.processed:
    tabs_list = st.tabs([
        "📄 Processar",
        "📋 Dados Completos",
        "📊 Dashboard",
        "📈 Relatório",
        "📧 Email",
        "📝 Logs"
    ])
    tab_processar, tab_dados, tab_dashboard, tab_relatorio, tab_email, tab_logs = tabs_list
else:
    tabs_list = st.tabs([
        "📄 Processar",
        "📊 Dashboard"
    ])
    tab_processar, tab_dashboard = tabs_list
    tab_dados = None
    tab_relatorio = None
    tab_email = None
    tab_logs = None

with tab_processar:
    st.header("Processar Arquivos NFe")
    
    if modo == "Pasta Padrão (NotasFiscais)":
        st.markdown(f"""
        <div class="info-box">
            <strong>📊 Pasta Padrão:</strong> {str(NOTAS_FISCAIS_PATH)}<br>
            <strong>Como usar:</strong> Coloque seus arquivos de nota fiscal nesta pasta e clique em "Processar"
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🚀 Processar com CrewAI", type="primary", use_container_width=True):
                arquivos = list(NOTAS_FISCAIS_PATH.glob('*.csv')) + \
                          list(NOTAS_FISCAIS_PATH.glob('*.txt')) + \
                          list(NOTAS_FISCAIS_PATH.glob('*.xml')) + \
                          list(NOTAS_FISCAIS_PATH.glob('*.json')) + \
                          list(NOTAS_FISCAIS_PATH.glob('*.pdf'))
                
                if arquivos:
                    process_files_from_path(str(NOTAS_FISCAIS_PATH), logger, stream_capture)
                else:
                    logger.warning("Nenhum arquivo encontrado em NotasFiscais")
                    stream_capture.add_log("Nenhum arquivo encontrado em NotasFiscais", "WARNING")
                    st.error(f"❌ Nenhum arquivo encontrado em {NOTAS_FISCAIS_PATH}")
    
    else:
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ ATENÇÃO:</strong> Upload de Arquivos suporta apenas arquivos com menos de 200 MB por arquivo.<br>
            Para arquivos maiores, use a opção "Pasta Padrão" e coloque os arquivos em NotasFiscais.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("upload_form"):
            uploaded_files = st.file_uploader(
                "Selecione os arquivos de NFe (máximo 200MB por arquivo)",
                type=['xml', 'pdf', 'txt', 'csv', 'json'],
                accept_multiple_files=True
            )
            
            submitted = st.form_submit_button("🚀 Processar com CrewAI")
            
            if submitted and uploaded_files and not st.session_state.processing:
                temp_dir = Path('temp')
                temp_dir.mkdir(exist_ok=True)
                
                logger.info(f"Upload de {len(uploaded_files)} arquivo(s)")
                stream_capture.add_log(f"Upload de {len(uploaded_files)} arquivo(s)", "INFO")
                
                for file in uploaded_files:
                    temp_path = temp_dir / file.name
                    with open(temp_path, 'wb') as f:
                        f.write(file.getbuffer())
                    logger.info(f"Arquivo salvo: {file.name}")
                    stream_capture.add_log(f"Arquivo salvo: {file.name}", "INFO")
                
                process_files_from_path(str(temp_dir), logger, stream_capture)
    
    if st.session_state.processed and st.session_state.results:
        st.divider()
        st.subheader("📈 Resumo do Processamento")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Arquivos", st.session_state.results['total_files'])
        
        with col2:
            st.metric("Arquivos com Sucesso", st.session_state.results['successful_files'])
        
        with col3:
            st.metric("Total de Registros", st.session_state.results['total_records'])
        
        with col4:
            st.metric("NFes Únicas", st.session_state.results['unique_invoices'])

if st.session_state.processed and tab_dados is not None:
    with tab_dados:
        st.header("📋 Lista Completa de Notas Fiscais")
        
        if st.session_state.dataframe is not None and len(st.session_state.dataframe) > 0:
            df = st.session_state.dataframe.copy()
            
            if 'DATA EMISSO' in df.columns:
                df['ANO'] = pd.to_datetime(df['DATA EMISSO'], format='%d/%m/%Y %H:%M:%S', errors='coerce').dt.year
            
            st.subheader("📄 Filtros")
            
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            col_filter4, col_filter5, col_filter6 = st.columns(3)
            
            with col_filter1:
                ufs = ['Todos'] + sorted(df['UF EMITENTE'].unique().tolist()) if 'UF EMITENTE' in df.columns else ['Todos']
                uf_filter = st.selectbox("Estado (Emitente)", ufs, key="dados_uf")
            
            with col_filter2:
                anos = ['Todos'] + sorted([str(int(x)) for x in df['ANO'].dropna().unique()]) if 'ANO' in df.columns else ['Todos']
                ano_filter = st.selectbox("Ano", anos, key="dados_ano")
            
            with col_filter3:
                naturezas = ['Todos'] + sorted(df['NATUREZA DA OPERAÇO'].unique().tolist())[:30] if 'NATUREZA DA OPERAÇO' in df.columns else ['Todos']
                natureza_filter = st.selectbox("Natureza Operação", naturezas, key="dados_natureza")
            
            with col_filter4:
                emitentes = ['Todos'] + sorted(df['RAZO SOCIAL EMITENTE'].unique().tolist())[:50] if 'RAZO SOCIAL EMITENTE' in df.columns else ['Todos']
                emitente_filter = st.selectbox("Emitente", emitentes, key="dados_emitente")
            
            with col_filter5:
                municipios = ['Todos'] + sorted(df['MUNICÍPIO EMITENTE'].unique().tolist())[:50] if 'MUNICÍPIO EMITENTE' in df.columns else ['Todos']
                municipio_filter = st.selectbox("Município", municipios, key="dados_municipio")
            
            with col_filter6:
                ufs_dest = ['Todos'] + sorted(df['UF Destinatário'].unique().tolist()) if 'UF Destinatário' in df.columns else ['Todos']
                uf_dest_filter = st.selectbox("UF Destinatário", ufs_dest, key="dados_uf_dest")
            
            df_filtrado = df.copy()
            
            if uf_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['UF EMITENTE'] == uf_filter]
            if ano_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['ANO'] == int(ano_filter)]
            if natureza_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['NATUREZA DA OPERAÇO'] == natureza_filter]
            if emitente_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['RAZO SOCIAL EMITENTE'] == emitente_filter]
            if municipio_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['MUNICÍPIO EMITENTE'] == municipio_filter]
            if uf_dest_filter != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['UF Destinatário'] == uf_dest_filter]
            
            st.info(f"📝Mostrando {len(df_filtrado)} de {len(df)} registros")
            
            st.subheader("Dados com Paginação")
            
            records_per_page = 100
            total_records = len(df_filtrado)
            total_pages = (total_records + records_per_page - 1) // records_per_page
            
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            
            with col_pag1:
                if st.button("⬅️ Anterior"):
                    if st.session_state.page_number > 0:
                        st.session_state.page_number -= 1
                    st.rerun()
            
            with col_pag2:
                page_input = st.number_input(
                    "Página",
                    min_value=1,
                    max_value=max(1, total_pages),
                    value=st.session_state.page_number + 1,
                    step=1
                )
                st.session_state.page_number = page_input - 1
            
            with col_pag3:
                if st.button("Próximo ➡️"):
                    if st.session_state.page_number < total_pages - 1:
                        st.session_state.page_number += 1
                    st.rerun()
            
            start_idx = st.session_state.page_number * records_per_page
            end_idx = start_idx + records_per_page
            
            df_page = df_filtrado.iloc[start_idx:end_idx]
            
            st.caption(f"Página {st.session_state.page_number + 1} de {total_pages}")
            
            display_cols = [
                'CHAVE DE ACESSO',
                'MODELO',
                'S‰RIE',
                'NšMERO',
                'NATUREZA DA OPERAÇO',
                'DATA EMISSO',
                'CPF/CNPJ Emitente',
                'RAZO SOCIAL EMITENTE',
                'INSCRI‡ƒO ESTADUAL EMITENTE',
                'UF EMITENTE',
                'MUNICÍPIO EMITENTE',
                'CNPJ Destinatário',
                'NOME Destinatário',
                'UF Destinatário',
                'INDICADOR IE Destinatário',
                'DESTINO DA OPERAÇO',
                'CONSUMIDOR FINAL',
                'PRESEN‡A DO COMPRADOR',
                'NšMERO PRODUTO',
                'DESCRI‡ƒO DO PRODUTO/SERVI‡O',
                'C“DIGO NCM/SH',
                'NCM/SH (TIPO DE PRODUTO)',
                'CFOP',
                'QUANTIDADE',
                'UNIDADE',
                'VALOR UNITRIO',
                'VALOR TOTAL'
            ]
            
            cols_existentes = [col for col in display_cols if col in df_page.columns]
            
            st.dataframe(
                df_page[cols_existentes],
                use_container_width=True,
                height=400
            )
            
            st.subheader("📊 Download")
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                csv_filtrado = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8')
                st.download_button(
                    label="📊 Baixar Dados Filtrados (CSV)",
                    data=csv_filtrado,
                    file_name=f"nfe_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_down2:
                if st.session_state.csv_file:
                    with open(st.session_state.csv_file, 'r', encoding='utf-8') as f:
                        csv_completo = f.read()
                    st.download_button(
                        label="📊 Baixar Lista Completa (CSV)",
                        data=csv_completo,
                        file_name=f"nfe_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            st.subheader("📝Estatísticas dos Dados Filtrados")
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("Total de Registros", len(df_filtrado))
            
            with stat_col2:
                notas_unicas = df_filtrado['CHAVE DE ACESSO'].nunique() if 'CHAVE DE ACESSO' in df_filtrado.columns else 0
                st.metric("Notas Únicas", notas_unicas)
            
            with stat_col3:
                if 'VALOR TOTAL' in df_filtrado.columns:
                    total_valor = df_filtrado['VALOR TOTAL'].astype(str).str.replace(',', '.').astype(float).sum()
                    st.metric("Valor Total", f"R$ {total_valor:,.2f}")
                else:
                    st.metric("Valor Total", "N/A")
            
            with stat_col4:
                if 'QUANTIDADE' in df_filtrado.columns:
                    qtd_total = df_filtrado['QUANTIDADE'].astype(str).str.replace(',', '.').astype(float).sum()
                    st.metric("Quantidade Total", f"{qtd_total:,.2f}")
                else:
                    st.metric("Quantidade Total", "N/A")
        
        else:
            st.info("Nenhum dado disponível. Processe arquivos primeiro.")

with tab_dashboard:
    st.header("📝Dashboard Anal­tico")
    
    if st.session_state.processed and st.session_state.dataframe is not None and len(st.session_state.dataframe) > 0:
        try:
            logger.info("Gerando dashboard")
            stream_capture.add_log("Gerando dashboard", "INFO")
            
            df = st.session_state.dataframe.copy()
            
            st.subheader("📄 Filtros Din¢micos")
            
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            col_filt4, col_filt5, col_filt6 = st.columns(3)
            
            with col_filt1:
                estados = ['Todos'] + sorted(df['UF EMITENTE'].unique().tolist()) if 'UF EMITENTE' in df.columns else ['Todos']
                estado_dash = st.selectbox("Estado (Emitente)", estados, key="dash_estado")
            
            with col_filt2:
                if 'DATA EMISSO' in df.columns:
                    df['ANO'] = pd.to_datetime(df['DATA EMISSO'], format='%d/%m/%Y %H:%M:%S', errors='coerce').dt.year
                    anos = ['Todos'] + sorted([str(int(x)) for x in df['ANO'].dropna().unique()])
                else:
                    anos = ['Todos']
                ano_dash = st.selectbox("Ano", anos, key="dash_ano")
            
            with col_filt3:
                naturezas = ['Todos'] + sorted(df['NATUREZA DA OPERAÇO'].unique().tolist())[:30] if 'NATUREZA DA OPERAÇO' in df.columns else ['Todos']
                natureza_dash = st.selectbox("Natureza Operação", naturezas, key="dash_natureza")
            
            with col_filt4:
                emitentes = ['Todos'] + sorted(df['RAZO SOCIAL EMITENTE'].unique().tolist())[:50] if 'RAZO SOCIAL EMITENTE' in df.columns else ['Todos']
                emitente_dash = st.selectbox("Emitente", emitentes, key="dash_emitente")
            
            with col_filt5:
                municipios = ['Todos'] + sorted(df['MUNICÍPIO EMITENTE'].unique().tolist())[:50] if 'MUNICÍPIO EMITENTE' in df.columns else ['Todos']
                municipio_dash = st.selectbox("Município", municipios, key="dash_municipio")
            
            with col_filt6:
                ufs_dest = ['Todos'] + sorted(df['UF DESTINATÁRIO'].unique().tolist()) if 'UF Destinatário' in df.columns else ['Todos']
                uf_dest_dash = st.selectbox("UF Destinatário", ufs_dest, key="dash_uf_dest")
            
            df_dashboard = df.copy()
            
            if estado_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['UF EMITENTE'] == estado_dash]
            if ano_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['ANO'] == int(ano_dash)]
            if natureza_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['NATUREZA DA OPERAÇO'] == natureza_dash]
            if emitente_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['RAZO SOCIAL EMITENTE'] == emitente_dash]
            if municipio_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['MUNICÍPIO EMITENTE'] == municipio_dash]
            if uf_dest_dash != 'Todos':
                df_dashboard = df_dashboard[df_dashboard['UF DESTINATÁRIO'] == uf_dest_dash]
            
            st.info(f"Registros com filtros: {len(df_dashboard)} de {len(df)}")
            
            st.divider()
            
            st.subheader("📋 Soma de Valores por Estado")
            valor_por_estado = df_dashboard.groupby('UF EMITENTE')['VALOR TOTAL'].apply(
                lambda x: x.astype(str).str.replace(',', '.').astype(float).sum()
            ).reset_index().sort_values('VALOR TOTAL', ascending=False)
            valor_por_estado.columns = ['Estado', 'Valor Total']
            
            fig_valor = px.bar(
                valor_por_estado,
                x='Estado',
                y='Valor Total',
                title='Soma de Valores das Notas Fiscais por Estado',
                labels={'Estado': 'Estado', 'Valor Total': 'Valor (R$)'},
                color='Valor Total',
                color_continuous_scale='Viridis',
                text='Valor Total'
            )
            fig_valor.update_traces(texttemplate='R$ %{text:.0f}', textposition='outside')
            fig_valor.update_layout(height=400, template='plotly_white', showlegend=False)
            st.plotly_chart(fig_valor, use_container_width=True)
            
            st.divider()
            
            dashboard = NFEDashboardAnalytics(df_dashboard)
            dashboard.render_dashboard()
            
            st.divider()
            
            st.subheader("📊 Exportar Dados do Dashboard")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                kpis = dashboard.gerar_kpis()
                relatorio_texto = f"""RELATÓRIO DE ANÁLISE - NOTAS FISCAIS
====================================

Data do Relatório: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

RESUMO EXECUTIVO
----------------
Total de Notas Fiscais: {kpis['total_notas']}
Valor Total Movimentado: R$ {kpis['valor_total']:,.2f}
Valor M©dio por Nota: R$ {kpis['valor_medio']:,.2f}
Notas Únicas (por CHAVE): {kpis['notas_unicas']}

PRINCIPAIS INDICADORES
----------------------
Maior Emitente: {kpis['maior_emitente']}
Maior Destinatário: {kpis['maior_destinatario']}
UF Principal (Emitente): {kpis['uf_principal']}
Produto Principal: {kpis['produto_principal']}

PERODO
-------
Data Inicial: {kpis['data_inicio'].strftime('%d/%m/%Y') if kpis['data_inicio'] else 'N/A'}
Data Final: {kpis['data_fim'].strftime('%d/%m/%Y') if kpis['data_fim'] else 'N/A'}

DISTRIBUI‡ƒO
------------
Quantidade de Emitentes: {kpis['num_emitentes']}
Quantidade de Estados: {kpis['num_estados']}
"""
                
                st.download_button(
                    label="📄 Download Relatório (TXT)",
                    data=relatorio_texto,
                    file_name=f"relatorio_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                resumo_dados = {
                    'M©trica': [
                        'Total de Notas',
                        'Valor Total (R$)',
                        'Valor Médio (R$)',
                        'Notas Únicas',
                        'Emitentes',
                        'Estados',
                        'Data Inicial',
                        'Data Final'
                    ],
                    'Valor': [
                        kpis['total_notas'],
                        f"{kpis['valor_total']:.2f}",
                        f"{kpis['valor_medio']:.2f}",
                        kpis['notas_unicas'],
                        kpis['num_emitentes'],
                        kpis['num_estados'],
                        kpis['data_inicio'].strftime('%d/%m/%Y') if kpis['data_inicio'] else 'N/A',
                        kpis['data_fim'].strftime('%d/%m/%Y') if kpis['data_fim'] else 'N/A'
                    ]
                }
                
                df_resumo = pd.DataFrame(resumo_dados)
                csv_resumo = df_resumo.to_csv(index=False, sep=';', encoding='utf-8')
                
                st.download_button(
                    label="📝Download KPIs (CSV)",
                    data=csv_resumo,
                    file_name=f"kpis_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                if st.session_state.dataframe is not None:
                    csv_data = st.session_state.dataframe.to_csv(index=False, sep=';', encoding='utf-8')
                    st.download_button(
                        label="📋 Download Dados (CSV)",
                        data=csv_data,
                        file_name=f"dados_nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            logger.info("Dashboard gerado com sucesso")
            stream_capture.add_log("Dashboard gerado com sucesso", "INFO")
        
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard: {e}", exc_info=True)
            stream_capture.add_log(f"Erro ao gerar dashboard: {e}", "ERROR")
            st.error(f"⚠️ Œ Erro ao gerar dashboard: {e}")
    
    else:
        st.info("""
        ⚠️ ³ **Dashboard ser¡ exibido aqui ap³s o processamento dos arquivos.**
        
        **Passos:**
        1. V¡ para a aba "📄 Processar"
        2. Selecione os arquivos ou pasta
        3. Clique em ">🚀 Processar com CrewAI"
        4. Aguarde o processamento (pode levar alguns minutos)
        5. Volte aqui para ver a análise completa com gr¡ficos e KPIs
        """)

if st.session_state.processed and tab_relatorio is not None:
    with tab_relatorio:
        st.header("📈 Relatório T©cnico de Processamento")
        
        st.info("""
        >ℹ️ Este relatório cont©m a análise detalhada dos 6 agentes CrewAI 
        executados durante o processamento das notas fiscais.
        """)
        
        if st.session_state.crew_analysis:
            st.subheader("📋 Análise dos Agentes CrewAI")
            
            import html
            texto_limpo = html.unescape(st.session_state.crew_analysis)
            
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; max-height: 600px; overflow-y: auto; line-height: 1.6;">
                <div style="white-space: pre-wrap; word-wrap: break-word; font-size: 14px;">""" + 
                texto_limpo + 
                """</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("📊 Download")
            
            col_rel1, col_rel2 = st.columns(2)
            
            with col_rel1:
                st.download_button(
                    label="📄 Download Relatório (TXT)",
                    data=st.session_state.crew_analysis,
                    file_name=f"relatorio_crews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_rel2:
                relatorio_email = f"""
RELAT“RIO DE PROCESSAMENTO NFe - ANLISE DOS AGENTES CREWAI
============================================================

Data do Relatório: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

ESTATSTICAS DO PROCESSAMENTO
-----------------------------
Total de Arquivos: {st.session_state.results['total_files']}
Arquivos Processados com Sucesso: {st.session_state.results['successful_files']}
Total de Registros Extra­dos: {st.session_state.results['total_records']}
Notas Fiscais Únicas: {st.session_state.results['unique_invoices']}
Taxa de Sucesso: {(st.session_state.results['successful_files']/max(st.session_state.results['total_files'],1)*100):.1f}%

ANLISE DETALHADA DOS AGENTES CREWAI
====================================

{st.session_state.crew_analysis}

FIM DO RELAT“RIO
"""
                
                st.download_button(
                    label="📧 Download para Email (TXT)",
                    data=relatorio_email,
                    file_name=f"relatorio_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            st.divider()
            
            st.subheader("📝Resumo das Etapas")
            
            etapas = [
                (">🟡 Agente 1", "Data Extraction Specialist", "Extração de dados de múltiplos formatos"),
                (">🟡 Agente 2", "Field Standardization Specialist", "Padronizaço de campos"),
                (">🟢 Agente 3", "Data Consolidation Specialist", "Consolidaço em lista ºnica"),
                (">🔵 Agente 4", "Quality Assurance Specialist", "Validação de qualidade"),
                (">🟣 Agente 5", "Record Counting Specialist", "Verificaço de contagem"),
                (">🟤 Agente 6", "Communication & Reporting Specialist", "Geraço de relat³rios")
            ]
            
            for emoji, nome, descricao in etapas:
                st.write(f"{emoji} **{nome}**")
                st.write(f"{descricao}")
        
        else:
            st.warning("⚠️ Nenhuma análise disponível. Processe arquivos primeiro.")

if st.session_state.processed and tab_email is not None:
    with tab_email:
        st.header("📧 Enviar Relatório por Email")
        
        st.info("""
        >ℹ️ Clique no bot£o abaixo para enviar todos os documentos processados 
        para o email do respons¡vel configurado no arquivo .env
        """)
        
        email_destinatario = os.getenv('EMAIL_DESTINATARIO', 'fiscal@empresa.com')
        
        st.markdown(f"""
        <div class="info-box">
            <strong>📧 Email de Destino:</strong> {email_destinatario}<br>
            <strong>📊 Será incluí­do:</strong><br>
            >• Lista completa de notas fiscais (CSV)<br>
            >• Logs detalhados do processamento<br>
            <strong>📊 Mensagem:</strong><br>
            "Notas Fiscais processadas com sucesso, em anexo est¡ a lista completa das notas fiscais encontradas"
        </div>
        """, unsafe_allow_html=True)
        
        col_email1, col_email2, col_email3 = st.columns([1, 1, 1])
        
        with col_email2:
            if st.button("📧 ENVIAR EMAIL COM DOCUMENTOS", type="primary", use_container_width=True, key="send_email_btn"):
                send_email_results(logger, stream_capture, log_file)
        
        st.divider()
        
        st.subheader("📄 Documentos que serão enviados")
        
        doc_col1, doc_col2 = st.columns(2)
        
        with doc_col1:
            st.markdown("#### 📋 Arquivo CSV")
            if st.session_state.csv_file and Path(st.session_state.csv_file).exists():
                file_size = Path(st.session_state.csv_file).stat().st_size / 1024
                st.write(f"✅ {Path(st.session_state.csv_file).name}")
                st.write(f"📝Tamanho: {file_size:.2f} KB")
                st.write(f"📊 Registros: {st.session_state.results['total_records']}")
            else:
                st.write("⚠️ Arquivo não disponível")
        
        with doc_col2:
            st.markdown("#### 📊 Arquivo de LOG")
            if log_file and Path(log_file).exists():
                file_size = Path(log_file).stat().st_size / 1024
                st.write(f"✅ {Path(log_file).name}")
                st.write(f"📝Tamanho: {file_size:.2f} KB")
                st.write(f"⚠️ Criado em: {datetime.fromtimestamp(Path(log_file).stat().st_mtime).strftime('%d/%m/%Y %H:%M:%S')}")
            else:
                st.write("⚠️ Arquivo não disponível")
        
        st.divider()
        
        st.subheader(">ℹ️ Configuração de Email")
        
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.write("**SMTP Server:** " + os.getenv('SMTP_SERVER', 'N£o configurado'))
            st.write("**SMTP Port:** " + os.getenv('SMTP_PORT', 'N£o configurado'))
        
        with config_col2:
            st.write("**Email Remetente:** " + ('✅ Configurado' if os.getenv('EMAIL_USER') else '⚠️ Œ N£o configurado'))
            st.write("**Senha Configurada:** " + ('✅ Sim' if os.getenv('EMAIL_PASSWORD') else '⚠️ Œ N£o'))
        
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Nota:</strong> As credenciais de email devem estar configuradas no arquivo .env para que o envio funcione.
        </div>
        """, unsafe_allow_html=True)

if st.session_state.processed and tab_logs is not None:
    with tab_logs:
        st.header("📊 Logs do Processamento")
        
        st.info("""
        >ℹ️ Abaixo está o histórico completo de logs do processamento.
        Os logs tamb©m s£o salvos automaticamente em: `outputs/logs/`
        """)
        
        if st.session_state.logs_text:
            st.subheader("📋 Logs Detalhados")
            
            st.markdown("""
            <div style="background-color: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 8px; max-height: 600px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.6;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">""" + 
                st.session_state.logs_text.replace('<', '&lt;').replace('>', '&gt;') + 
                """</pre>
            </div>
            """, unsafe_allow_html=True)
            
            col_log1, col_log2, col_log3 = st.columns(3)
            
            with col_log1:
                st.download_button(
                    label="📊 Baixar Logs (TXT)",
                    data=st.session_state.logs_text,
                    file_name=f"logs_nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_log2:
                if st.button("📄 Atualizar Logs", use_container_width=True):
                    st.session_state.logs_text = stream_capture.get_logs()
                    st.rerun()
            
            with col_log3:
                if st.button("🚀 Limpar Exibiço", use_container_width=True):
                    st.session_state.logs_text = ""
                    st.rerun()
            
            st.divider()
            
            st.subheader("📊 Arquivo de Log Salvo")
            
            if log_file and Path(log_file).exists():
                st.success(f"✅ Arquivo salvo em: `{log_file}`")
                
                log_stats_col1, log_stats_col2, log_stats_col3 = st.columns(3)
                
                with log_stats_col1:
                    file_size = Path(log_file).stat().st_size / 1024
                    st.metric("Tamanho do Arquivo", f"{file_size:.2f} KB")
                
                with log_stats_col2:
                    created_time = datetime.fromtimestamp(Path(log_file).stat().st_ctime)
                    st.metric("Data de Criação", created_time.strftime('%d/%m/%Y'))
                
                with log_stats_col3:
                    modified_time = datetime.fromtimestamp(Path(log_file).stat().st_mtime)
                    st.metric("última Modificação", modified_time.strftime('%H:%M:%S'))
                
                st.subheader("📈 Preview do Arquivo Salvo")
                with open(log_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                if file_content:
                    st.markdown("""
                    <div style="background-color: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 8px; max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 12px; line-height: 1.6;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">""" + 
                        file_content.replace('<', '&lt;').replace('>', '&gt;') + 
                        """</pre>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Arquivo de log vazio. Os logs podem estar sendo salvos apenas em memória.")
            else:
                st.error("⚠️ Arquivo de log não encontrado")
        
        else:
            st.info(">ℹ️ Nenhum log disponível no momento. Processe arquivos para gerar logs.")

logger.info("Aplicação Streamlit iniciada")
stream_capture.add_log("Aplicação Streamlit iniciada", "INFO")