# =============================================================================
# DASHBOARD MODULE - SISTEMA VR/VA (VERSÃO MELHORADA)
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

def formatar_moeda_br(valor):
    """💰 Formata valores monetários no padrão brasileiro"""
    try:
        if pd.isna(valor) or valor in [None, '', 0]:
            return "R$ 0,00"
        
        if isinstance(valor, str):
            valor = float(valor.replace('R$', '').replace('.', '').replace(',', '.'))
        
        # Formatação brasileira: 1.234.567,89
        valor_str = f"{float(valor):,.2f}"
        valor_br = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_br}"
        
    except Exception as e:
        return f"R$ {valor}"

def extrair_estado_corrigido(sindicato):
    """✅ Extrai estado baseado no sindicato"""
    if pd.isna(sindicato):
        return 'Não Identificado'
    
    sindicato_clean = str(sindicato).upper().strip()
    
    # 🎯 PRIORIDADE 1: Rio Grande do Sul
    indicadores_rs = [
        'RIO GRANDE DO SUL', 'SINDPPD RS', 'RS - SINDICATO',
        'SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL',
        'SINDICAL RS', 'PORTO ALEGRE'
    ]
    
    for indicador in indicadores_rs:
        if indicador in sindicato_clean:
            return 'Rio Grande do Sul'
    
    # São Paulo
    if any(termo in sindicato_clean for termo in [
        'SÃO PAULO', 'SAO PAULO', 'SP - SINDICATO',
        'SINDSP', 'SINDICAL SP'
    ]):
        return 'São Paulo'
    
    # Rio de Janeiro
    if any(termo in sindicato_clean for termo in [
        'RIO DE JANEIRO', 'RJ - SINDICATO',
        'SINDRJ', 'SINDICAL RJ'
    ]):
        return 'Rio de Janeiro'
    
    # Paraná
    if any(termo in sindicato_clean for termo in [
        'PARANÁ', 'PARANA', 'PR - SINDICATO',
        'SINDPR', 'SINDICAL PR'
    ]):
        return 'Paraná'
    
    # FALLBACK genérico
    if ' RS ' in f" {sindicato_clean} " or sindicato_clean.endswith(' RS'):
        return 'Rio Grande do Sul'
    elif ' SP ' in f" {sindicato_clean} " or sindicato_clean.endswith(' SP'):
        return 'São Paulo'
    elif ' RJ ' in f" {sindicato_clean} " or sindicato_clean.endswith(' RJ'):
        return 'Rio de Janeiro'
    elif ' PR ' in f" {sindicato_clean} " or sindicato_clean.endswith(' PR'):
        return 'Paraná'
    
    return 'Outros'

def mostrar_kpis_principais(df):
    """📊 KPIs principais do dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Colaboradores", f"{len(df):,}")
    
    with col2:
        total_vr = df['TOTAL'].sum()
        st.metric("💰 Total VR", formatar_moeda_br(total_vr))
    
    with col3:
        custo_empresa = df['Custo empresa'].sum()
        st.metric("🏢 Custo Empresa", formatar_moeda_br(custo_empresa))
    
    with col4:
        desconto = df['Desconto profissional'].sum()
        st.metric("👤 Desconto", formatar_moeda_br(desconto))

def mostrar_distribuicao_valores_melhorada(df):
    """📊 Gráfico de distribuição de valores MELHORADO"""
    st.subheader("📊 Análise de Distribuição")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 📊 HISTOGRAMA MELHORADO - Mostra valor total por faixa
        df_hist = df.copy()
        df_hist['Faixa_VR'] = pd.cut(df_hist['TOTAL'], bins=10, precision=0)
        
        # Agregar por faixa mostrando VALOR TOTAL
        faixas_agregadas = df_hist.groupby('Faixa_VR', observed=True).agg({
            'TOTAL': 'sum',
            'Matricula': 'count'
        }).reset_index()
        
        # Formatar labels das faixas
        faixas_agregadas['Faixa_Label'] = faixas_agregadas['Faixa_VR'].apply(
            lambda x: f"R$ {x.left:.0f} - R$ {x.right:.0f}"
        )
        
        fig_hist = px.bar(
            faixas_agregadas, 
            x='Faixa_Label', 
            y='TOTAL',
            title="💰 Valor Total por Faixa de VR",
            labels={'TOTAL': 'Valor Total (R$)', 'Faixa_Label': 'Faixa de Valores'},
            color='TOTAL',
            color_continuous_scale='viridis'
        )
        
        # Formatação melhorada
        fig_hist.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                         "Valor Total: R$ %{y:,.2f}<br>" +
                         "<extra></extra>"
        )
        fig_hist.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # 📊 ANÁLISE POR ESTADO
        df_estados = df.copy()
        df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
        
        analise_estado = df_estados.groupby('Estado').agg({
            'Matricula': 'count',
            'TOTAL': 'sum'
        }).reset_index()
        
        fig_estados = px.pie(
            analise_estado,
            values='TOTAL',
            names='Estado',
            title="🗺️ Distribuição de Valores por Estado",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig_estados.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>" +
                         "Valor: R$ %{value:,.2f}<br>" +
                         "Percentual: %{percent}<br>" +
                         "<extra></extra>"
        )
        fig_estados.update_layout(height=400)
        st.plotly_chart(fig_estados, use_container_width=True)

def mostrar_top_10_melhorado(df):
    """🏆 Top 10 maiores valores MELHORADO com dados dos funcionários"""
    st.subheader("🏆 Top 10 Maiores Valores - Análise Detalhada")
    
    # Preparar dados do Top 10 com informações adicionais
    top_10 = df.nlargest(10, 'TOTAL').copy()
    top_10['Estado'] = top_10['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
    top_10['Valor_Formatado'] = top_10['TOTAL'].apply(formatar_moeda_br)
    top_10['Ranking'] = range(1, len(top_10) + 1)
    
    # Extrair informações adicionais
    top_10['Sindicato_Resumido'] = top_10['Sindicato do Colaborador'].apply(
        lambda x: str(x)[:30] + "..." if len(str(x)) > 30 else str(x)
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 📊 GRÁFICO DE BARRAS MELHORADO
        fig_top10 = px.bar(
            top_10,
            x='Matricula',
            y='TOTAL',
            title="💰 Top 10 - Valores por Colaborador",
            labels={'TOTAL': 'Valor VR (R$)', 'Matricula': 'Matrícula'},
            color='Estado',
            text='TOTAL',
            hover_data={
                'Estado': True,
                'Dias': True,
                'VALOR DIÁRIO VR': True,
                'Sindicato_Resumido': True
            }
        )
        
        # Customização do hover e texto
        fig_top10.update_traces(
            texttemplate='R$ %{text:,.0f}',
            textposition='outside',
            hovertemplate="<b>Matrícula: %{x}</b><br>" +
                         "Valor VR: R$ %{y:,.2f}<br>" +
                         "Estado: %{color}<br>" +
                         "Dias: %{customdata[1]}<br>" +
                         "Valor Diário: R$ %{customdata[2]:,.2f}<br>" +
                         "Sindicato: %{customdata[3]}<br>" +
                         "<extra></extra>"
        )
        
        fig_top10.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_top10, use_container_width=True)
    
    with col2:
        # 📋 TABELA DETALHADA DO TOP 10
        st.write("**📋 Detalhes dos Top 10:**")
        
        # Selecionar e renomear colunas para exibição
        colunas_exibir = {
            'Ranking': '🏆',
            'Matricula': '👤 Matrícula',
            'Valor_Formatado': '💰 Valor VR',
            'Estado': '🗺️ Estado',
            'Dias': '📅 Dias',
            'VALOR DIÁRIO VR': '💵 Valor/Dia',
            'Sindicato_Resumido': '🏛️ Sindicato'
        }
        
        # Preparar DataFrame para exibição
        top_10_display = top_10[list(colunas_exibir.keys())].copy()
        top_10_display.columns = list(colunas_exibir.values())
        top_10_display['💵 Valor/Dia'] = top_10_display['💵 Valor/Dia'].apply(
            lambda x: f"R$ {x:.2f}"
        )
        top_10_display['📅 Dias'] = top_10_display['📅 Dias'].round(1)
        
        st.dataframe(
            top_10_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                '🏆': st.column_config.NumberColumn(width="small"),
                '👤 Matrícula': st.column_config.TextColumn(width="medium"),
                '💰 Valor VR': st.column_config.TextColumn(width="medium"),
                '🗺️ Estado': st.column_config.TextColumn(width="medium"),
                '📅 Dias': st.column_config.NumberColumn(width="small"),
                '💵 Valor/Dia': st.column_config.TextColumn(width="medium"),
                '🏛️ Sindicato': st.column_config.TextColumn(width="large")
            }
        )

def mostrar_analises_avancadas(df):
    """📈 Análises avançadas melhoradas"""
    st.subheader("📈 Análises Avançadas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 📅 ANÁLISE POR FAIXA DE DIAS
        st.write("**📅 Distribuição por Dias Úteis**")
        
        df_temp = df.copy()
        df_temp['Faixa_Dias'] = pd.cut(df_temp['Dias'], 
                                 bins=[0, 10, 15, 20, 25, 30], 
                                 labels=['1-10', '11-15', '16-20', '21-25', '26-30'],
                                 right=False)
        
        dias_analise = df_temp.groupby('Faixa_Dias', observed=True).agg({
            'Matricula': 'count',
            'TOTAL': 'sum'
        }).reset_index()
        
        fig_dias = px.bar(
            dias_analise,
            x='Faixa_Dias',
            y='Matricula',
            title="👥 Colaboradores por Faixa de Dias",
            color='TOTAL',
            color_continuous_scale='blues',
            hover_data={'TOTAL': ':,.2f'}
        )
        fig_dias.update_traces(
            hovertemplate="<b>Faixa: %{x} dias</b><br>" +
                         "Colaboradores: %{y}<br>" +
                         "Valor Total: R$ %{color:,.2f}<br>" +
                         "<extra></extra>"
        )
        fig_dias.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_dias, use_container_width=True)
    
    with col2:
        # 📊 ESTATÍSTICAS RESUMIDAS
        st.write("**📊 Estatísticas Resumidas**")
        
        stats = {
            'Métrica': [
                '💰 Valor Médio',
                '📈 Valor Mediano',
                '⬆️ Valor Máximo', 
                '⬇️ Valor Mínimo',
                '📏 Desvio Padrão',
                '📅 Dias Médios'
            ],
            'Valor': [
                formatar_moeda_br(df['TOTAL'].mean()),
                formatar_moeda_br(df['TOTAL'].median()),
                formatar_moeda_br(df['TOTAL'].max()),
                formatar_moeda_br(df['TOTAL'].min()),
                formatar_moeda_br(df['TOTAL'].std()),
                f"{df['Dias'].mean():.1f} dias"
            ]
        }
        
        df_stats = pd.DataFrame(stats)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    
    with col3:
        # 🎯 ANÁLISE DE CONCENTRAÇÃO
        st.write("**🎯 Análise de Concentração**")
        
        # Top 10% dos colaboradores
        top_10_percent = int(len(df) * 0.1)
        top_10p_valor = df.nlargest(top_10_percent, 'TOTAL')['TOTAL'].sum()
        concentracao_10p = (top_10p_valor / df['TOTAL'].sum()) * 100
        
        # Top 20% dos colaboradores  
        top_20_percent = int(len(df) * 0.2)
        top_20p_valor = df.nlargest(top_20_percent, 'TOTAL')['TOTAL'].sum()
        concentracao_20p = (top_20p_valor / df['TOTAL'].sum()) * 100
        
        fig_concentracao = px.pie(
            values=[concentracao_10p, concentracao_20p - concentracao_10p, 100 - concentracao_20p],
            names=['Top 10%', 'Top 11-20%', 'Restante 80%'],
            title="🎯 Concentração de Valores",
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
        )
        fig_concentracao.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>" +
                         "Percentual: %{percent}<br>" +
                         "<extra></extra>"
        )
        fig_concentracao.update_layout(height=300)
        st.plotly_chart(fig_concentracao, use_container_width=True)

def mostrar_insights_automaticos(df):
    """🧠 Insights automáticos melhorados"""
    st.subheader("🧠 Insights Automáticos")
    
    # Preparar dados para insights
    df_estados = df.copy()
    df_estados['Estado'] = df_estados['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**💡 Insights Descobertos:**")
        
        # Calcular insights automáticos
        valor_medio = df['TOTAL'].mean()
        acima_media = len(df[df['TOTAL'] > valor_medio])
        percentual_acima = (acima_media / len(df)) * 100
        
        estado_maior = df_estados.groupby('Estado')['TOTAL'].sum().idxmax()
        valor_maior_estado = df_estados.groupby('Estado')['TOTAL'].sum().max()
        
        # Top 10 para análise
        top_10 = df.nlargest(10, 'TOTAL')
        
        st.write(f"• **{percentual_acima:.1f}%** dos colaboradores estão acima da média")
        st.write(f"• **{estado_maior}** concentra o maior valor: {formatar_moeda_br(valor_maior_estado)}")
        st.write(f"• **Top 10** representa **{(top_10['TOTAL'].sum()/df['TOTAL'].sum()*100):.1f}%** do valor total")
        st.write(f"• Amplitude de valores: **{formatar_moeda_br(df['TOTAL'].max() - df['TOTAL'].min())}**")
        
        # Insight sobre dias úteis
        dias_zero = len(df[df['Dias'] == 0])
        dias_parciais = len(df[(df['Dias'] > 0) & (df['Dias'] < 22)])
        st.write(f"• **{dias_parciais}** colaboradores com dias parciais (< 22 dias)")
        
        # Insight sobre sindicatos
        sindicatos_unicos = df['Sindicato do Colaborador'].nunique()
        maior_sindicato = df.groupby('Sindicato do Colaborador')['Matricula'].count().idxmax()
        qtd_maior_sindicato = df.groupby('Sindicato do Colaborador')['Matricula'].count().max()
        st.write(f"• **{sindicatos_unicos}** sindicatos diferentes processados")
        st.write(f"• Maior sindicato: **{qtd_maior_sindicato}** colaboradores")
    
    with col2:
        st.success("**✅ Qualidade dos Dados:**")
        
        # Verificações de qualidade
        valores_zero = len(df[df['TOTAL'] == 0])
        dias_zero = len(df[df['Dias'] == 0])
        sindicatos_unicos = df['Sindicato do Colaborador'].nunique()
        estados_unicos = df_estados['Estado'].nunique()
        
        # Verificar consistência
        valor_total_calculado = df['Custo empresa'].sum() + df['Desconto profissional'].sum()
        valor_total_real = df['TOTAL'].sum()
        diferenca = abs(valor_total_calculado - valor_total_real)
        percentual_diferenca = (diferenca / valor_total_real) * 100 if valor_total_real > 0 else 0
        
        st.write(f"• **{len(df):,}** colaboradores processados")
        st.write(f"• **{valores_zero}** com valor zero")
        st.write(f"• **{sindicatos_unicos}** sindicatos diferentes")
        st.write(f"• **{estados_unicos}** estados mapeados")
        
        if valores_zero == 0 and dias_zero == 0 and percentual_diferenca < 0.01:
            st.write("• ✅ **Dados 100% consistentes**")
        else:
            problemas = valores_zero + dias_zero
            st.write(f"• ⚠️ **{problemas}** registros com problemas")
            if percentual_diferenca >= 0.01:
                st.write(f"• ⚠️ **Diferença nos cálculos: {percentual_diferenca:.2f}%**")
        
        # Insight sobre distribuição geográfica
        breakdown_estados = df_estados.groupby('Estado')['TOTAL'].sum().sort_values(ascending=False)
        st.write(f"• **Estados processados:** {', '.join(breakdown_estados.index[:3])}")

def mostrar_analise_geografica(df):
    """🗺️ Análise geográfica melhorada"""
    st.subheader("🗺️ Análise Geográfica")
    
    # Usar função corrigida
    df_geo = df.copy()
    df_geo['Estado'] = df_geo['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
    
    # 🔍 DEBUG específico para Rio Grande do Sul
    with st.expander("🔍 DEBUG - Verificação Rio Grande do Sul"):
        df_rs_debug = df[df['Sindicato do Colaborador'].str.contains(
            'SINDPPD RS|RIO GRANDE DO SUL|RS', case=False, na=False
        )]
        
        if len(df_rs_debug) > 0:
            st.success(f"✅ Encontrados {len(df_rs_debug)} colaboradores com sindicatos do RS")
            st.write("**Sindicatos do RS detectados:**")
            st.dataframe(df_rs_debug[['Matricula', 'Sindicato do Colaborador', 'TOTAL']].head(10))
        else:
            st.error("❌ Nenhum colaborador do RS encontrado")
        
        st.write("**Mapeamento de Estados (amostra):**")
        sindicatos_sample = df['Sindicato do Colaborador'].unique()[:10]
        for sindicato in sindicatos_sample:
            estado_mapeado = extrair_estado_corrigido(sindicato)
            emoji = "🎯" if estado_mapeado == 'Rio Grande do Sul' else "  "
            st.write(f"{emoji} {sindicato} → {estado_mapeado}")
    
    # Análise por estado
    analise_estado = df_geo.groupby('Estado').agg({
        'Matricula': 'count',
        'TOTAL': 'sum',
        'VALOR DIÁRIO VR': 'mean',
        'Dias': 'mean'
    }).round(2)
    
    analise_estado.columns = ['Colaboradores', 'Valor Total', 'Valor Diario', 'Dias Medios']
    analise_estado = analise_estado.sort_values('Valor Total', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Resumo por Estado:**")
        
        # Formatar valores para exibição
        analise_display = analise_estado.copy()
        analise_display['Valor Total'] = analise_display['Valor Total'].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        analise_display['Valor Diario'] = analise_display['Valor Diario'].apply(
            lambda x: f"R$ {x:.2f}".replace('.', ',')
        )
        analise_display['Dias Medios'] = analise_display['Dias Medios'].apply(
            lambda x: f"{x:.1f}"
        )
        
        st.dataframe(analise_display, use_container_width=True)
    
    with col2:
        # Gráfico pizza melhorado
        fig_pie = px.pie(
            values=analise_estado['Valor Total'],
            names=analise_estado.index,
            title="🥧 Distribuição por Estado",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>" +
                         "Valor: R$ %{value:,.2f}<br>" +
                         "Percentual: %{percent}<br>" +
                         "<extra></extra>"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico de barras por estado
    fig_bar_estado = px.bar(
        x=analise_estado.index,
        y=analise_estado['Colaboradores'],
        title="👥 Colaboradores por Estado",
        labels={'x': 'Estado', 'y': 'Número de Colaboradores'},
        color=analise_estado['Valor Total'],
        color_continuous_scale='viridis'
    )
    fig_bar_estado.update_traces(
        hovertemplate="<b>%{x}</b><br>" +
                     "Colaboradores: %{y}<br>" +
                     "Valor Total: R$ %{color:,.2f}<br>" +
                     "<extra></extra>"
    )
    fig_bar_estado.update_layout(showlegend=False)
    st.plotly_chart(fig_bar_estado, use_container_width=True)
    
    # ✅ VERIFICAÇÃO FINAL
    if 'Rio Grande do Sul' in analise_estado.index:
        rs_dados = analise_estado.loc['Rio Grande do Sul']
        st.success(f"✅ **RIO GRANDE DO SUL DETECTADO:** {rs_dados['Colaboradores']} colaboradores, R$ {rs_dados['Valor Total']:,.2f}")
    else:
        st.error("❌ **PROBLEMA:** Rio Grande do Sul não aparece nos resultados")

def mostrar_dashboard_executivo(df):
    """📈 Dashboard executivo completo"""
    st.subheader("📈 Dashboard Executivo")
    
    # KPIs principais
    mostrar_kpis_principais(df)
    
    st.markdown("---")
    
    # Distribuição de valores
    mostrar_distribuicao_valores_melhorada(df)
    
    st.markdown("---")
    
    # Top 10 melhorado
    mostrar_top_10_melhorado(df)
    
    st.markdown("---")
    
    # Análises avançadas
    mostrar_analises_avancadas(df)
    
    st.markdown("---")
    
    # Insights automáticos
    mostrar_insights_automaticos(df)

def mostrar_downloads(df, vr_system):
    """📤 Seção de downloads"""
    st.subheader("📤 Downloads")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Planilha Principal:**")
        
        # Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='VR MENSAL', index=False)
        
        st.download_button(
            label="💾 Download Excel",
            data=buffer.getvalue(),
            file_name=f"VR_Mensal_{vr_system.competencia.replace('/', '')}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"VR_Mensal_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        st.write("**📈 Resumo Executivo:**")
        
        # Resumo com formatação monetária corrigida
        resumo = {
            'Metrica': [
                'Total Colaboradores',
                'Valor Total VR',
                'Custo Empresa', 
                'Desconto Funcionarios',
                'Valor Medio',
                'Dias Medios'
            ],
            'Valor': [
                f"{len(df):,}",
                formatar_moeda_br(df['TOTAL'].sum()),
                formatar_moeda_br(df['Custo empresa'].sum()),
                formatar_moeda_br(df['Desconto profissional'].sum()),
                formatar_moeda_br(df['TOTAL'].mean()),
                f"{df['Dias'].mean():.2f}"
            ]
        }
        
        df_resumo = pd.DataFrame(resumo)
        csv_resumo = df_resumo.to_csv(index=False)
        
        st.download_button(
            label="📋 Download Resumo",
            data=csv_resumo,
            file_name=f"Resumo_VR_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.dataframe(df_resumo, use_container_width=True, hide_index=True)
    
    # Informações do processamento
    st.markdown("---")
    st.subheader("ℹ️ Informacoes do Processamento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**📅 Competencia:** {vr_system.competencia}")
        st.info(f"**⏰ Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    with col2:
        st.info(f"**🏢 % Empresa:** {vr_system.config['percentual_empresa']*100:.0f}%")
        st.info(f"**👤 % Funcionario:** {vr_system.config['percentual_funcionario']*100:.0f}%")
    
    with col3:
        st.info(f"**📅 Dia Corte:** {vr_system.config['dia_corte_desligamento']}")
        st.info(f"**📁 Arquivos:** {len(st.session_state.arquivos_carregados) if 'arquivos_carregados' in st.session_state else 0}")

def mostrar_analise_sindicatos(df):
    """💼 Análise detalhada por sindicatos"""
    st.subheader("💼 Análise por Sindicato")
    
    # Análise detalhada por sindicato
    analise_sindicato = df.groupby('Sindicato do Colaborador').agg({
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
    
    # Adicionar coluna de eficiência
    analise_sindicato['Eficiência (%)'] = (
        (analise_sindicato['Dias Médios'] / analise_sindicato['Dias Médios'].max()) * 100
    ).round(1)
    
    st.write("**📋 Detalhamento por Sindicato:**")
    
    # Filtros para a tabela
    col1, col2 = st.columns(2)
    
    with col1:
        min_colaboradores = st.slider(
            "Mínimo de colaboradores por sindicato",
            min_value=1,
            max_value=int(analise_sindicato['Colaboradores'].max()),
            value=1
        )
    
    with col2:
        ordenar_por = st.selectbox(
            "Ordenar por",
            ['Valor Total (R$)', 'Colaboradores', 'Valor Médio por Pessoa (R$)', 'Dias Médios']
        )
    
    # Aplicar filtros
    analise_filtrada = analise_sindicato[
        analise_sindicato['Colaboradores'] >= min_colaboradores
    ].sort_values(ordenar_por, ascending=False)
    
    st.dataframe(analise_filtrada, use_container_width=True)
    
    # Gráficos comparativos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por valor total
        fig_comparison = px.bar(
            x=analise_filtrada.index[:10],  # Top 10 sindicatos
            y=analise_filtrada['Valor Total (R$)'][:10],
            title="💰 Top 10 Sindicatos - Valor Total",
            labels={'x': 'Sindicato', 'y': 'Valor Total (R$)'},
            color=analise_filtrada['Colaboradores'][:10],
            color_continuous_scale='viridis'
        )
        fig_comparison.update_xaxes(tickangle=45)
        fig_comparison.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                         "Valor Total: R$ %{y:,.2f}<br>" +
                         "Colaboradores: %{color}<br>" +
                         "<extra></extra>"
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    with col2:
        # Gráfico de dispersão: Colaboradores vs Valor Médio
        fig_scatter = px.scatter(
            analise_filtrada,
            x='Colaboradores',
            y='Valor Médio por Pessoa (R$)',
            title="👥 Colaboradores vs Valor Médio por Pessoa",
            hover_name=analise_filtrada.index,
            size='Valor Total (R$)',
            color='Dias Médios',
            color_continuous_scale='RdYlBu_r'
        )
        fig_scatter.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>" +
                         "Colaboradores: %{x}<br>" +
                         "Valor Médio: R$ %{y:,.2f}<br>" +
                         "Dias Médios: %{color:.1f}<br>" +
                         "<extra></extra>"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Análise de eficiência
    st.subheader("📈 Análise de Eficiência por Sindicato")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Dias médios por sindicato
        fig_dias = px.bar(
            x=analise_filtrada.index[:10],
            y=analise_filtrada['Dias Médios'][:10],
            title="⏱️ Dias Médios - Top 10 Sindicatos",
            labels={'x': 'Sindicato', 'y': 'Dias Médios'},
            color=analise_filtrada['Dias Médios'][:10],
            color_continuous_scale='Blues'
        )
        fig_dias.update_xaxes(tickangle=45)
        fig_dias.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                         "Dias Médios: %{y:.1f}<br>" +
                         "<extra></extra>"
        )
        st.plotly_chart(fig_dias, use_container_width=True)
    
    with col2:
        # Valor diário por sindicato
        fig_valor_diario = px.bar(
            x=analise_filtrada.index[:10],
            y=analise_filtrada['Valor Diário (R$)'][:10],
            title="💵 Valor Diário - Top 10 Sindicatos",
            labels={'x': 'Sindicato', 'y': 'Valor Diário (R$)'},
            color=analise_filtrada['Valor Diário (R$)'][:10],
            color_continuous_scale='Greens'
        )
        fig_valor_diario.update_xaxes(tickangle=45)
        fig_valor_diario.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                         "Valor Diário: R$ %{y:.2f}<br>" +
                         "<extra></extra>"
        )
        st.plotly_chart(fig_valor_diario, use_container_width=True)

def mostrar_planilha_final_melhorada(df):
    """📋 Planilha final com filtros avançados"""
    st.subheader("📋 Planilha Final de VR/VA")
    
    # Filtros avançados
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sindicatos = ['Todos'] + list(df['Sindicato do Colaborador'].unique())
        sindicato_filter = st.selectbox("🏛️ Sindicato", sindicatos)
    
    with col2:
        # Filtro por estado
        df_temp = df.copy()
        df_temp['Estado'] = df_temp['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
        estados = ['Todos'] + list(df_temp['Estado'].unique())
        estado_filter = st.selectbox("🗺️ Estado", estados)
    
    with col3:
        valor_min = st.number_input("💰 Valor Mínimo", min_value=0.0, value=0.0)
    
    with col4:
        valor_max = st.number_input("💰 Valor Máximo", min_value=0.0, value=float(df['TOTAL'].max()))
    
    # Filtros adicionais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dias_min = st.number_input("📅 Dias Mínimos", min_value=0.0, value=0.0, step=0.1)
    
    with col2:
        dias_max = st.number_input("📅 Dias Máximos", min_value=0.0, value=float(df['Dias'].max()), step=0.1)
    
    with col3:
        # Filtro por observações
        obs_filter = st.multiselect(
            "📝 Observações",
            options=df['OBS GERAL'].unique(),
            default=[]
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    df_filtrado['Estado'] = df_filtrado['Sindicato do Colaborador'].apply(extrair_estado_corrigido)
    
    if sindicato_filter != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Sindicato do Colaborador'] == sindicato_filter]
    
    if estado_filter != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_filter]
    
    df_filtrado = df_filtrado[
        (df_filtrado['TOTAL'] >= valor_min) & 
        (df_filtrado['TOTAL'] <= valor_max) &
        (df_filtrado['Dias'] >= dias_min) &
        (df_filtrado['Dias'] <= dias_max)
    ]
    
    if obs_filter:
        df_filtrado = df_filtrado[df_filtrado['OBS GERAL'].isin(obs_filter)]
    
    # Mostrar estatísticas do filtro
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Registros", f"{len(df_filtrado):,}")
    
    with col2:
        st.metric("💰 Total Filtrado", formatar_moeda_br(df_filtrado['TOTAL'].sum()))
    
    with col3:
        st.metric("📈 Valor Médio", formatar_moeda_br(df_filtrado['TOTAL'].mean()))
    
    with col4:
        st.metric("⏱️ Dias Médios", f"{df_filtrado['Dias'].mean():.1f}")
    
    # Opções de exibição
    st.markdown("**⚙️ Opções de Exibição:**")
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_todas_colunas = st.checkbox("Mostrar todas as colunas", value=False)
    
    with col2:
        registros_por_pagina = st.selectbox(
            "Registros por página",
            [50, 100, 200, 500, "Todos"],
            index=1
        )
    
    # Selecionar colunas para exibição
    if mostrar_todas_colunas:
        colunas_exibir = df_filtrado.columns.tolist()
    else:
        colunas_exibir = [
            'Matricula', 'Sindicato do Colaborador', 'Estado',
            'Dias', 'VALOR DIÁRIO VR', 'TOTAL',
            'Custo empresa', 'Desconto profissional', 'OBS GERAL'
        ]
    
    # Paginar resultados
    if registros_por_pagina != "Todos":
        total_pages = len(df_filtrado) // registros_por_pagina + (1 if len(df_filtrado) % registros_por_pagina > 0 else 0)
        
        if total_pages > 1:
            page_number = st.number_input(
                f"Página (1 a {total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1
            )
            
            start_idx = (page_number - 1) * registros_por_pagina
            end_idx = start_idx + registros_por_pagina
            df_exibir = df_filtrado[colunas_exibir].iloc[start_idx:end_idx]
        else:
            df_exibir = df_filtrado[colunas_exibir]
    else:
        df_exibir = df_filtrado[colunas_exibir]
    
    # Mostrar tabela
    st.dataframe(
        df_exibir,
        use_container_width=True,
        hide_index=True,
        column_config={
            'TOTAL': st.column_config.NumberColumn(
                'Valor Total',
                format="R$ %.2f"
            ),
            'Custo empresa': st.column_config.NumberColumn(
                'Custo Empresa',
                format="R$ %.2f"
            ),
            'Desconto profissional': st.column_config.NumberColumn(
                'Desconto Funcionário',
                format="R$ %.2f"
            ),
            'VALOR DIÁRIO VR': st.column_config.NumberColumn(
                'Valor Diário',
                format="R$ %.2f"
            ),
            'Dias': st.column_config.NumberColumn(
                'Dias Úteis',
                format="%.1f"
            )
        }
    )
    
    # Resumo dos filtros aplicados
    if len(df_filtrado) < len(df):
        filtros_aplicados = []
        if sindicato_filter != 'Todos':
            filtros_aplicados.append(f"Sindicato: {sindicato_filter}")
        if estado_filter != 'Todos':
            filtros_aplicados.append(f"Estado: {estado_filter}")
        if valor_min > 0:
            filtros_aplicados.append(f"Valor mín: R$ {valor_min:.2f}")
        if valor_max < df['TOTAL'].max():
            filtros_aplicados.append(f"Valor máx: R$ {valor_max:.2f}")
        if dias_min > 0:
            filtros_aplicados.append(f"Dias mín: {dias_min}")
        if dias_max < df['Dias'].max():
            filtros_aplicados.append(f"Dias máx: {dias_max}")
        if obs_filter:
            filtros_aplicados.append(f"Observações: {', '.join(obs_filter)}")
        
        st.info(f"**Filtros aplicados:** {' | '.join(filtros_aplicados)}")
        
        # Botão para limpar filtros
        if st.button("🔄 Limpar Filtros"):
            st.rerun()