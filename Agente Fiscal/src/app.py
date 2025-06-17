# VERSAO 3 - INTERFACE OTIMIZADA
import streamlit as st
import os
from crew import FiscalCrew

st.set_page_config(
    page_title="Agente Fiscal - Análise Avançada",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("🧾 Agente Fiscal - Análise Avançada de Notas Fiscais")
    st.markdown("---")
    
    # Sidebar otimizada
    with st.sidebar:
        st.header("🎯 Status & Métricas")
        
        try:
            crew = FiscalCrew()
            data_info = crew.get_data_info()
            
            st.success("✅ Sistema Ativo")
            st.code(f"Modelo: {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}")
            
            if 'cabecalho' in data_info:
                st.metric("📄 Notas Fiscais", data_info['cabecalho']['registros'])
            
            if 'itens' in data_info:
                st.metric("📦 Itens", data_info['itens']['registros'])
                
            # Quick stats
            if crew.df_cabecalho is not None:
                valor_total = crew.df_cabecalho['VALOR NOTA FISCAL'].sum()
                st.metric("💰 Valor Total", f"R$ {valor_total:,.0f}")
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            st.stop()
    
    # Interface principal
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("💬 Consultas & Relatórios")
        
        # Abas para diferentes tipos de consulta
        tab1, tab2 = st.tabs(["🔍 Consulta Rápida", "📊 Relatório Completo"])
        
        with tab1:
            st.subheader("Perguntas Específicas")
            exemplos_rapidos = [
                "Qual o valor total das notas fiscais?",
                "Quais são os principais fornecedores?",
                "Qual a distribuição por UF?",
                "Quais produtos têm maior valor?",
                "Qual o valor médio por nota fiscal?"
            ]
            
            pergunta_rapida = st.selectbox(
                "Exemplos de consultas:",
                [""] + exemplos_rapidos,
                index=0
            )
            
            pergunta_custom = st.text_input(
                "Ou digite sua pergunta:",
                value=pergunta_rapida,
                placeholder="Ex: Quantas notas fiscais temos do PR?"
            )
            
            if st.button("🔍 Consultar", type="primary", key="consulta"):
                if pergunta_custom.strip():
                    with st.spinner("🤖 Analisando..."):
                        try:
                            crew = FiscalCrew()
                            resposta = crew.run(pergunta_custom)
                            st.success("✅ Consulta realizada!")
                            with st.expander("📋 Resultado", expanded=True):
                                st.markdown(resposta)
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                else:
                    st.warning("⚠️ Digite ou selecione uma pergunta.")
        
        with tab2:
            st.subheader("Relatório Fiscal Completo")
            st.info("📈 Gera análise completa com todas as métricas fiscais importantes")
            
            tipo_relatorio = st.selectbox(
                "Tipo de relatório:",
                [
                    "Relatório fiscal completo",
                    "Análise completa de fornecedores", 
                    "Relatório de conformidade fiscal",
                    "Análise geográfica completa"
                ]
            )
            
            if st.button("📊 Gerar Relatório", type="primary", key="relatorio"):
                with st.spinner("📝 Gerando relatório completo..."):
                    try:
                        crew = FiscalCrew()
                        resposta = crew.run(tipo_relatorio)
                        st.success("✅ Relatório gerado!")
                        
                        # Opção de download (simulada)
                        st.download_button(
                            label="💾 Download Relatório",
                            data=resposta,
                            file_name=f"relatorio_fiscal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
                        
                        with st.expander("📊 Relatório Completo", expanded=True):
                            st.markdown(resposta)
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    with col2:
        st.header("📈 Dashboard Executivo")
        
        try:
            crew = FiscalCrew()
            
            if crew.df_cabecalho is not None:
                # Métricas principais
                valor_total = crew.df_cabecalho['VALOR NOTA FISCAL'].sum()
                qtd_notas = len(crew.df_cabecalho)
                valor_medio = crew.df_cabecalho['VALOR NOTA FISCAL'].mean()
                qtd_fornecedores = crew.df_cabecalho['RAZÃO SOCIAL EMITENTE'].nunique()
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("💰 Valor Total", f"R$ {valor_total:,.0f}")
                    st.metric("📄 Total NFs", f"{qtd_notas:,}")
                with col_b:
                    st.metric("📊 Valor Médio", f"R$ {valor_medio:,.0f}")
                    st.metric("🏢 Fornecedores", f"{qtd_fornecedores}")
                
                # Top fornecedores visual
                st.subheader("🏆 Top 5 Fornecedores")
                top_fornecedores = crew.df_cabecalho.groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum().sort_values(ascending=False).head(5)
                
                for i, (fornecedor, valor) in enumerate(top_fornecedores.items(), 1):
                    pct = (valor / valor_total) * 100
                    st.write(f"**{i}.** {fornecedor[:25]}...")
                    st.progress(pct/100)
                    st.caption(f"R$ {valor:,.0f} ({pct:.1f}%)")
                
                # Distribuição geográfica
                st.subheader("🗺️ Por Estado")
                por_uf = crew.df_cabecalho.groupby('UF EMITENTE')['VALOR NOTA FISCAL'].sum().sort_values(ascending=False)
                
                for uf, valor in por_uf.head(5).items():
                    pct = (valor / valor_total) * 100
                    col_uf1, col_uf2 = st.columns([1, 2])
                    with col_uf1:
                        st.write(f"**{uf}**")
                    with col_uf2:
                        st.progress(pct/100)
                        st.caption(f"R$ {valor:,.0f}")
                        
        except Exception as e:
            st.error(f"Erro no dashboard: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>🤖 Agente Fiscal v3.0 - CrewAI & Ollama</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    import pandas as pd
    main()
