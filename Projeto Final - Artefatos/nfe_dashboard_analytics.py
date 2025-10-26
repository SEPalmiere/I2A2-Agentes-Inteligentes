# =============================================================================
# MÓDULO DE DASHBOARD E ANÁLISES - nfe_dashboard_analytics.py
# Gráficos e análises interativas para dados de Notas Fiscais
# =============================================================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st


class NFEDashboardAnalytics:
    """Gerador de gráficos e análises para dados de Notas Fiscais"""
    
    def __init__(self, dataframe):
        """
        Inicializa com DataFrame de notas fiscais processadas
        
        Parâmetros:
        -----------
        dataframe : pd.DataFrame
            DataFrame com dados extraídos e normalizados
        """
        self.df = dataframe
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepara dados para análises"""
        # Converter valor total para float
        if 'VALOR TOTAL' in self.df.columns:
            self.df['VALOR_TOTAL_NUM'] = self.df['VALOR TOTAL'].apply(
                lambda x: float(str(x).replace(',', '.')) if pd.notna(x) else 0
            )
        
        # Converter data emissão
        if 'DATA EMISSÃO' in self.df.columns:
            self.df['DATA_EMISSAO'] = pd.to_datetime(
                self.df['DATA EMISSÃO'], 
                format='%d/%m/%Y %H:%M:%S',
                errors='coerce'
            )
            self.df['MES'] = self.df['DATA_EMISSAO'].dt.to_period('M')
            self.df['DIA_SEMANA'] = self.df['DATA_EMISSAO'].dt.day_name()
        
        # Converter quantidade
        if 'QUANTIDADE' in self.df.columns:
            self.df['QTD_NUM'] = pd.to_numeric(
                self.df['QUANTIDADE'], 
                errors='coerce'
            ).fillna(0)
        
        # Converter valor unitário
        if 'VALOR UNITÁRIO' in self.df.columns:
            self.df['VALOR_UNIT_NUM'] = self.df['VALOR UNITÁRIO'].apply(
                lambda x: float(str(x).replace(',', '.')) if pd.notna(x) else 0
            )
    
    # =========================================================================
    # KPIS
    # =========================================================================
    
    def gerar_kpis(self):
        """Gera KPIs principais"""
        kpis = {
            'total_notas': len(self.df),
            'valor_total': self.df['VALOR_TOTAL_NUM'].sum(),
            'valor_medio': self.df['VALOR_TOTAL_NUM'].mean(),
            'notas_unicas': self.df['CHAVE DE ACESSO'].nunique() if 'CHAVE DE ACESSO' in self.df.columns else 0,
            'maior_emitente': self._get_maior_emitente(),
            'maior_destinatario': self._get_maior_destinatario(),
            'uf_principal': self._get_uf_principal(),
            'produto_principal': self._get_produto_principal(),
            'data_inicio': self.df['DATA_EMISSAO'].min() if 'DATA_EMISSAO' in self.df.columns else None,
            'data_fim': self.df['DATA_EMISSAO'].max() if 'DATA_EMISSAO' in self.df.columns else None,
            'num_emitentes': self.df['CPF/CNPJ Emitente'].nunique() if 'CPF/CNPJ Emitente' in self.df.columns else 0,
            'num_estados': self.df['UF EMITENTE'].nunique() if 'UF EMITENTE' in self.df.columns else 0
        }
        return kpis
    
    def _get_maior_emitente(self):
        """Identifica maior emitente por valor"""
        if 'CPF/CNPJ Emitente' not in self.df.columns:
            return None
        emitente = self.df.groupby('CPF/CNPJ Emitente')['VALOR_TOTAL_NUM'].sum().idxmax()
        return emitente
    
    def _get_maior_destinatario(self):
        """Identifica maior destinatário por quantidade de notas"""
        if 'NOME DESTINATÁRIO' not in self.df.columns:
            return None
        destinatario = self.df['NOME DESTINATÁRIO'].value_counts().idxmax()
        return destinatario
    
    def _get_uf_principal(self):
        """Identifica UF com mais notas"""
        if 'UF EMITENTE' not in self.df.columns:
            return None
        uf = self.df['UF EMITENTE'].value_counts().idxmax()
        return uf
    
    def _get_produto_principal(self):
        """Identifica produto mais movimentado"""
        if 'DESCRIÇÃO DO PRODUTO/SERVIÇO' not in self.df.columns:
            return None
        produto = self.df.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['VALOR_TOTAL_NUM'].sum().idxmax()
        return produto
    
    # =========================================================================
    # GRÁFICO 1: SÉRIE TEMPORAL
    # =========================================================================
    
    def gerar_grafico_serie_temporal(self):
        """Gráfico 1: Evolução de notas ao longo do tempo"""
        if 'MES' not in self.df.columns:
            return None
        
        # Agrupamento por mês
        series_mes = self.df.groupby('MES').agg({
            'CHAVE DE ACESSO': 'count',
            'VALOR_TOTAL_NUM': 'sum'
        }).reset_index()
        
        series_mes['MES'] = series_mes['MES'].astype(str)
        series_mes.rename(columns={'CHAVE DE ACESSO': 'Quantidade'}, inplace=True)
        
        fig = px.line(
            series_mes,
            x='MES',
            y=['Quantidade', 'VALOR_TOTAL_NUM'],
            title='📈 Evolução de Notas Fiscais por Período',
            labels={
                'MES': 'Período',
                'Quantidade': 'Quantidade de Notas',
                'VALOR_TOTAL_NUM': 'Valor Total (R$)'
            },
            markers=True,
            line_shape='linear'
        )
        
        fig.update_layout(
            hovermode='x unified',
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 2: TOP EMITENTES
    # =========================================================================
    
    def gerar_grafico_top_emitentes(self, top_n=10):
        """Gráfico 2: Top N emitentes por valor"""
        if 'CPF/CNPJ Emitente' not in self.df.columns:
            return None
        
        top_emitentes = self.df.groupby('CPF/CNPJ Emitente').agg({
            'CHAVE DE ACESSO': 'count',
            'VALOR_TOTAL_NUM': 'sum',
            'RAZÃO SOCIAL EMITENTE': 'first'
        }).sort_values('VALOR_TOTAL_NUM', ascending=False).head(top_n).reset_index()
        
        top_emitentes.rename(columns={
            'CHAVE DE ACESSO': 'Quantidade',
            'RAZÃO SOCIAL EMITENTE': 'Emitente'
        }, inplace=True)
        
        fig = px.bar(
            top_emitentes,
            y='Emitente',
            x='VALOR_TOTAL_NUM',
            orientation='h',
            title=f'🏆 Top {top_n} Emitentes por Valor',
            labels={'VALOR_TOTAL_NUM': 'Valor Total (R$)', 'Emitente': 'Emitente'},
            color='VALOR_TOTAL_NUM',
            color_continuous_scale='Blues',
            text='Quantidade',
            hover_data={'Quantidade': True}
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        fig.update_traces(textposition='outside')
        
        return fig
    
    # =========================================================================
    # GRÁFICO 3: DISTRIBUIÇÃO DE VALORES
    # =========================================================================
    
    def gerar_grafico_distribuicao_valores(self):
        """Gráfico 3: Distribuição de valores (Histograma)"""
        fig = px.histogram(
            self.df,
            x='VALOR_TOTAL_NUM',
            nbins=20,
            title='💰 Distribuição de Valores de Notas Fiscais',
            labels={'VALOR_TOTAL_NUM': 'Valor Total (R$)', 'count': 'Quantidade'},
            color_discrete_sequence=['#667eea']
        )
        
        # Adicionar estatísticas
        media = self.df['VALOR_TOTAL_NUM'].mean()
        mediana = self.df['VALOR_TOTAL_NUM'].median()
        
        fig.add_vline(
            media,
            line_dash='dash',
            line_color='red',
            annotation_text=f'Média: R$ {media:.2f}',
            annotation_position='top left'
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 4: PRODUTOS MAIS MOVIMENTADOS
    # =========================================================================
    
    def gerar_grafico_produtos(self):
        """Gráfico 4: Produtos mais movimentados (Pizza)"""
        if 'DESCRIÇÃO DO PRODUTO/SERVIÇO' not in self.df.columns:
            return None
        
        produtos = self.df.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO').agg({
            'VALOR_TOTAL_NUM': 'sum',
            'CHAVE DE ACESSO': 'count'
        }).sort_values('VALOR_TOTAL_NUM', ascending=False).head(10).reset_index()
        
        produtos.rename(columns={
            'DESCRIÇÃO DO PRODUTO/SERVIÇO': 'Produto',
            'CHAVE DE ACESSO': 'Quantidade'
        }, inplace=True)
        
        fig = px.pie(
            produtos,
            values='VALOR_TOTAL_NUM',
            names='Produto',
            title='📦 Produtos Mais Movimentados',
            hole=0.3
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 5: FLUXO ENTRE UFS
    # =========================================================================
    
    def gerar_grafico_fluxo_ufs(self):
        """Gráfico 5: Fluxo de notas entre UFs"""
        if 'UF EMITENTE' not in self.df.columns or 'UF DESTINATÁRIO' not in self.df.columns:
            return None
        
        fluxo = self.df.groupby(['UF EMITENTE', 'UF DESTINATÁRIO']).size().reset_index(name='Quantidade')
        fluxo = fluxo.sort_values('Quantidade', ascending=False).head(20)
        
        fluxo['Rota'] = fluxo['UF EMITENTE'] + ' → ' + fluxo['UF DESTINATÁRIO']
        
        fig = px.bar(
            fluxo,
            y='Rota',
            x='Quantidade',
            orientation='h',
            title='🌍 Fluxo de Notas entre UFs (Top 20)',
            labels={'Quantidade': 'Quantidade de Notas', 'Rota': 'Rota'},
            color='Quantidade',
            color_continuous_scale='Greens'
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 6: PADRÃO SEMANAL
    # =========================================================================
    
    def gerar_grafico_padrao_semanal(self):
        """Gráfico 6: Padrão de emissões por dia da semana"""
        if 'DIA_SEMANA' not in self.df.columns:
            return None
        
        ordem_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        nomes_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        padrao = self.df['DIA_SEMANA'].value_counts().reindex(ordem_dias).reset_index()
        padrao.columns = ['Dia', 'Quantidade']
        padrao['Dia'] = padrao['Dia'].map(dict(zip(ordem_dias, nomes_dias)))
        
        fig = px.bar(
            padrao,
            x='Dia',
            y='Quantidade',
            title='📅 Padrão de Emissões por Dia da Semana',
            labels={'Quantidade': 'Quantidade de Notas', 'Dia': 'Dia da Semana'},
            color='Quantidade',
            color_continuous_scale='Purples'
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 7: TOP DESTINATÁRIOS
    # =========================================================================
    
    def gerar_grafico_top_destinatarios(self, top_n=10):
        """Gráfico 7: Top N destinatários"""
        if 'NOME DESTINATÁRIO' not in self.df.columns:
            return None
        
        top_dest = self.df.groupby('NOME DESTINATÁRIO').agg({
            'CHAVE DE ACESSO': 'count',
            'VALOR_TOTAL_NUM': 'sum'
        }).sort_values('CHAVE DE ACESSO', ascending=False).head(top_n).reset_index()
        
        top_dest.rename(columns={
            'CHAVE DE ACESSO': 'Quantidade',
            'NOME DESTINATÁRIO': 'Destinatário'
        }, inplace=True)
        
        fig = px.bar(
            top_dest,
            y='Destinatário',
            x='Quantidade',
            orientation='h',
            title=f'🎯 Top {top_n} Destinatários',
            labels={'Quantidade': 'Quantidade de Notas', 'Destinatário': 'Destinatário'},
            color='Quantidade',
            color_continuous_scale='Oranges'
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    # =========================================================================
    # GRÁFICO 8: CORRELAÇÃO QUANTIDADE X VALOR
    # =========================================================================
    
    def gerar_grafico_correlacao(self):
        """Gráfico 8: Correlação entre Quantidade e Valor Unitário"""
        if 'QTD_NUM' not in self.df.columns or 'VALOR_UNIT_NUM' not in self.df.columns:
            return None
        
        df_filtro = self.df[(self.df['QTD_NUM'] > 0) & (self.df['VALOR_UNIT_NUM'] > 0)].copy()
        
        fig = px.scatter(
            df_filtro,
            x='QTD_NUM',
            y='VALOR_UNIT_NUM',
            size='VALOR_TOTAL_NUM',
            title='📊 Correlação: Quantidade vs Valor Unitário',
            labels={
                'QTD_NUM': 'Quantidade',
                'VALOR_UNIT_NUM': 'Valor Unitário (R$)'
            },
            color='VALOR_TOTAL_NUM',
            color_continuous_scale='Viridis',
            hover_data={
                'QTD_NUM': ':.2f',
                'VALOR_UNIT_NUM': ':.2f',
                'VALOR_TOTAL_NUM': ':.2f'
            }
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    # =========================================================================
    # MÉTODO PRINCIPAL: RENDERIZAR DASHBOARD
    # =========================================================================
    
    def render_dashboard(self):
        """Renderiza dashboard completo no Streamlit"""
        st.subheader("📊 Dashboard Analítico")
        
        # KPIs
        kpis = self.gerar_kpis()
        self._render_kpis(kpis)
        
        st.divider()
        
        # Gráficos em grid 2x2
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = self.gerar_grafico_serie_temporal()
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = self.gerar_grafico_top_emitentes()
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig3 = self.gerar_grafico_distribuicao_valores()
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            fig4 = self.gerar_grafico_produtos()
            if fig4:
                st.plotly_chart(fig4, use_container_width=True)
        
        col5, col6 = st.columns(2)
        
        with col5:
            fig5 = self.gerar_grafico_fluxo_ufs()
            if fig5:
                st.plotly_chart(fig5, use_container_width=True)
        
        with col6:
            fig6 = self.gerar_grafico_padrao_semanal()
            if fig6:
                st.plotly_chart(fig6, use_container_width=True)
        
        # Gráficos adicionais em grid 2x2
        col7, col8 = st.columns(2)
        
        with col7:
            fig7 = self.gerar_grafico_top_destinatarios()
            if fig7:
                st.plotly_chart(fig7, use_container_width=True)
        
        with col8:
            fig8 = self.gerar_grafico_correlacao()
            if fig8:
                st.plotly_chart(fig8, use_container_width=True)
    
    def _render_kpis(self, kpis):
        """Renderiza KPIs em cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Total de Notas",
                f"{kpis['total_notas']:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                "💰 Valor Total",
                f"R$ {kpis['valor_total']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                "📈 Valor Médio",
                f"R$ {kpis['valor_medio']:,.2f}",
                delta=None
            )
        
        with col4:
            st.metric(
                "🔄 Notas Únicas",
                f"{kpis['notas_unicas']:,}",
                delta=None
            )
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                "🏆 Maior Emitente",
                str(kpis['maior_emitente'])[:30] + '...' if len(str(kpis['maior_emitente'])) > 30 else str(kpis['maior_emitente']),
                delta=None
            )
        
        with col6:
            st.metric(
                "🎯 Maior Destinatário",
                str(kpis['maior_destinatario'])[:30] + '...' if len(str(kpis['maior_destinatario'])) > 30 else str(kpis['maior_destinatario']),
                delta=None
            )
        
        with col7:
            st.metric(
                "🌍 UF Principal",
                str(kpis['uf_principal']),
                delta=None
            )
        
        with col8:
            st.metric(
                "📦 Produto Principal",
                str(kpis['produto_principal'])[:30] + '...' if kpis['produto_principal'] and len(str(kpis['produto_principal'])) > 30 else str(kpis['produto_principal']),
                delta=None
            )

