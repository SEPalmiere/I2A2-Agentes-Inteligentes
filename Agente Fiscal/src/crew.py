# VERSAO 4 - CORRIGIDA PARA RELATÓRIOS FISCAIS
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
from datetime import datetime
import traceback

load_dotenv()

class FiscalCrew:
    def __init__(self):
        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.df_cabecalho = None
        self.df_itens = None
        self._load_data()
        
    def _load_data(self):
        """Carrega os dados dos arquivos CSV"""
        try:
            cabecalho_path = os.getenv("CSV_CABECALHO_PATH", "knowledge/202401_NFs_Cabecalho.csv")
            itens_path = os.getenv("CSV_ITENS_PATH", "knowledge/202401_NFs_Itens.csv")
            
            print(f"🔍 Tentando carregar: {cabecalho_path}")
            print(f"🔍 Tentando carregar: {itens_path}")
            
            # Carregar cabeçalho
            if os.path.exists(cabecalho_path):
                self.df_cabecalho = pd.read_csv(cabecalho_path)
                print(f"📊 Colunas do cabeçalho: {list(self.df_cabecalho.columns)}")
                
                # Normalizar nomes das colunas (remover espaços e caracteres especiais)
                self.df_cabecalho.columns = self.df_cabecalho.columns.str.strip()
                
                # Tentar diferentes variações de nome para valor
                valor_cols = [col for col in self.df_cabecalho.columns 
                            if any(word in col.upper() for word in ['VALOR', 'TOTAL', 'VLR'])]
                
                if valor_cols:
                    valor_col = valor_cols[0]
                    print(f"✅ Coluna de valor encontrada: {valor_col}")
                    self.df_cabecalho[valor_col] = pd.to_numeric(
                        self.df_cabecalho[valor_col], errors='coerce'
                    )
                
                # Tentar diferentes variações para data
                data_cols = [col for col in self.df_cabecalho.columns 
                           if any(word in col.upper() for word in ['DATA', 'EMISSAO', 'EMISSÃO'])]
                
                if data_cols:
                    data_col = data_cols[0]
                    print(f"✅ Coluna de data encontrada: {data_col}")
                    self.df_cabecalho[data_col] = pd.to_datetime(
                        self.df_cabecalho[data_col], errors='coerce'
                    )
                
                print(f"✅ Cabeçalho carregado: {len(self.df_cabecalho)} registros")
            else:
                print(f"❌ Arquivo não encontrado: {cabecalho_path}")
            
            # Carregar itens
            if os.path.exists(itens_path):
                # Tentar diferentes separadores e encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    for sep in [',', ';', '\t', '|']:
                        try:
                            self.df_itens = pd.read_csv(itens_path, sep=sep, encoding=encoding)
                            if len(self.df_itens.columns) > 3:  # Se tem colunas suficientes
                                print(f"✅ Arquivo de itens carregado com separador '{sep}' e encoding '{encoding}'")
                                break
                        except Exception as e:
                            continue
                    if self.df_itens is not None and len(self.df_itens.columns) > 3:
                        break
                
                if self.df_itens is not None and not self.df_itens.empty:
                    print(f"📊 Colunas dos itens: {list(self.df_itens.columns)}")
                    
                    # Normalizar nomes das colunas
                    self.df_itens.columns = self.df_itens.columns.str.strip()
                    
                    # Remover linhas completamente vazias
                    self.df_itens = self.df_itens.dropna(how='all')
                    
                    # Converter colunas numéricas
                    numeric_patterns = ['QUANTIDADE', 'QTD', 'VALOR', 'VLR', 'PRECO', 'PREÇO']
                    for col in self.df_itens.columns:
                        if any(pattern in col.upper() for pattern in numeric_patterns):
                            self.df_itens[col] = pd.to_numeric(self.df_itens[col], errors='coerce')
                    
                    print(f"✅ Itens carregados: {len(self.df_itens)} registros")
                else:
                    print("⚠️ Não foi possível carregar o arquivo de itens")
                    self.df_itens = None
            else:
                print(f"❌ Arquivo não encontrado: {itens_path}")
                
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {str(e)}")
            print(f"Detalhes do erro: {traceback.format_exc()}")
    
    def _get_column_by_pattern(self, df, patterns):
        """Encontra coluna por padrões de nome"""
        if df is None or df.empty:
            return None
        
        for pattern in patterns:
            for col in df.columns:
                if pattern.upper() in col.upper():
                    return col
        return None
    
    def _generate_fiscal_analysis(self, pergunta=""):
        """Gera análise fiscal completa dos dados"""
        pergunta_lower = pergunta.lower()
        is_relatorio = any(word in pergunta_lower for word in ['relatório', 'relatorio', 'análise completa', 'resumo', 'dashboard'])
        
        analise = {
            'periodo': self._get_periodo_analise(),
            'resumo_financeiro': self._get_resumo_financeiro(),
            'top_fornecedores': self._get_top_fornecedores(),
            'analise_geografica': self._get_analise_geografica(),
            'estatisticas_operacionais': self._get_estatisticas_operacionais()
        }
        
        # Incluir produtos se disponível
        produtos = self._get_produtos_principais()
        if produtos:
            analise['produtos_principais'] = produtos
        
        # Para relatórios, incluir análises extras
        if is_relatorio:
            analise.update({
                'distribuicao_valores': self._get_distribuicao_valores(),
                'conformidade': self._get_analise_conformidade(),
                'tendencias': self._get_tendencias()
            })
        
        return analise
    
    def _get_periodo_analise(self):
        """Retorna informações do período analisado"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {'inicio': 'N/A', 'fim': 'N/A', 'total_dias': 0}
        
        # Buscar coluna de data
        data_col = self._get_column_by_pattern(self.df_cabecalho, ['DATA', 'EMISSAO', 'EMISSÃO'])
        
        if data_col and data_col in self.df_cabecalho.columns:
            data_min = self.df_cabecalho[data_col].min()
            data_max = self.df_cabecalho[data_col].max()
            return {
                'inicio': data_min.strftime('%d/%m/%Y') if pd.notna(data_min) else 'N/A',
                'fim': data_max.strftime('%d/%m/%Y') if pd.notna(data_max) else 'N/A',
                'total_dias': (data_max - data_min).days if pd.notna(data_min) and pd.notna(data_max) else 0
            }
        
        return {'inicio': 'N/A', 'fim': 'N/A', 'total_dias': 0}
    
    def _get_resumo_financeiro(self):
        """Resumo financeiro das notas fiscais"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        # Buscar coluna de valor
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        
        if not valor_col:
            print("⚠️ Coluna de valor não encontrada no cabeçalho")
            return {}
        
        df = self.df_cabecalho.dropna(subset=[valor_col])
        
        if df.empty:
            return {}
        
        return {
            'valor_total': float(df[valor_col].sum()),
            'quantidade_nfs': int(len(df)),
            'valor_medio': float(df[valor_col].mean()),
            'valor_mediano': float(df[valor_col].median()),
            'maior_nf': float(df[valor_col].max()),
            'menor_nf': float(df[valor_col].min()),
            'desvio_padrao': float(df[valor_col].std())
        }
    
    def _get_top_fornecedores(self, top_n=5):
        """Top fornecedores por valor e quantidade"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        # Buscar colunas necessárias
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        fornecedor_col = self._get_column_by_pattern(self.df_cabecalho, ['RAZAO', 'SOCIAL', 'EMITENTE', 'FORNECEDOR'])
        uf_col = self._get_column_by_pattern(self.df_cabecalho, ['UF', 'ESTADO'])
        
        if not valor_col or not fornecedor_col:
            print("⚠️ Colunas necessárias não encontradas para análise de fornecedores")
            return {}
        
        agg_dict = {valor_col: ['sum', 'count', 'mean']}
        if uf_col:
            agg_dict[uf_col] = 'first'
        
        top_fornecedores = self.df_cabecalho.groupby(fornecedor_col).agg(agg_dict).round(2)
        
        # Simplificar nomes das colunas
        if uf_col:
            top_fornecedores.columns = ['valor_total', 'qtd_nfs', 'valor_medio', 'uf']
        else:
            top_fornecedores.columns = ['valor_total', 'qtd_nfs', 'valor_medio']
        
        return top_fornecedores.sort_values('valor_total', ascending=False).head(top_n).to_dict('index')
    
    def _get_analise_geografica(self):
        """Análise por UF dos emitentes"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        # Buscar colunas necessárias
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        uf_col = self._get_column_by_pattern(self.df_cabecalho, ['UF', 'ESTADO'])
        fornecedor_col = self._get_column_by_pattern(self.df_cabecalho, ['RAZAO', 'SOCIAL', 'EMITENTE', 'FORNECEDOR'])
        
        if not valor_col or not uf_col:
            print("⚠️ Colunas necessárias não encontradas para análise geográfica")
            return {}
        
        agg_dict = {valor_col: ['sum', 'count', 'mean']}
        if fornecedor_col:
            agg_dict[fornecedor_col] = 'nunique'
        
        por_uf = self.df_cabecalho.groupby(uf_col).agg(agg_dict).round(2)
        
        if fornecedor_col:
            por_uf.columns = ['valor_total', 'qtd_nfs', 'valor_medio', 'qtd_fornecedores']
        else:
            por_uf.columns = ['valor_total', 'qtd_nfs', 'valor_medio']
        
        return por_uf.sort_values('valor_total', ascending=False).to_dict('index')
    
    def _get_produtos_principais(self, top_n=10):
        """Principais produtos por valor"""
        if self.df_itens is None or self.df_itens.empty:
            print("⚠️ DataFrame de itens não disponível")
            return {}
        
        try:
            # Buscar colunas necessárias
            produto_col = self._get_column_by_pattern(self.df_itens, ['DESCRICAO', 'DESCRIÇÃO', 'PRODUTO', 'SERVICO'])
            
            if not produto_col:
                print("⚠️ Coluna de descrição do produto não encontrada")
                return {}
            
            # Buscar colunas de valores
            valor_total_col = self._get_column_by_pattern(self.df_itens, ['VALOR TOTAL', 'VLR TOTAL', 'TOTAL'])
            quantidade_col = self._get_column_by_pattern(self.df_itens, ['QUANTIDADE', 'QTD'])
            valor_unit_col = self._get_column_by_pattern(self.df_itens, ['VALOR UNIT', 'VLR UNIT', 'UNITARIO'])
            ncm_col = self._get_column_by_pattern(self.df_itens, ['NCM', 'SH'])
            
            # Construir dicionário de agregação
            agg_dict = {}
            
            if valor_total_col:
                agg_dict[valor_total_col] = 'sum'
            elif quantidade_col and valor_unit_col:
                # Calcular valor total se não existir
                self.df_itens['VALOR_CALCULADO'] = pd.to_numeric(self.df_itens[quantidade_col], errors='coerce') * pd.to_numeric(self.df_itens[valor_unit_col], errors='coerce')
                agg_dict['VALOR_CALCULADO'] = 'sum'
            
            if quantidade_col:
                agg_dict[quantidade_col] = 'sum'
            if valor_unit_col:
                agg_dict[valor_unit_col] = 'mean'
            if ncm_col:
                agg_dict[ncm_col] = 'first'
            
            if not agg_dict:
                print("⚠️ Nenhuma coluna numérica encontrada para análise de produtos")
                return {}
            
            df_clean = self.df_itens.dropna(subset=[produto_col])
            produtos = df_clean.groupby(produto_col).agg(agg_dict).round(2)
            
            # Ordenar por valor total se disponível
            if valor_total_col in produtos.columns:
                sort_col = valor_total_col
            elif 'VALOR_CALCULADO' in produtos.columns:
                sort_col = 'VALOR_CALCULADO'
            else:
                sort_col = list(produtos.columns)[0]
            
            return produtos.sort_values(sort_col, ascending=False).head(top_n).to_dict('index')
            
        except Exception as e:
            print(f"❌ Erro na análise de produtos: {str(e)}")
            return {}
    
    def _get_estatisticas_operacionais(self):
        """Estatísticas operacionais das notas"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        stats = {}
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        
        if not valor_col:
            return {}
        
        # Por natureza da operação
        natureza_col = self._get_column_by_pattern(self.df_cabecalho, ['NATUREZA', 'OPERACAO', 'OPERAÇÃO'])
        if natureza_col:
            natureza = self.df_cabecalho.groupby(natureza_col)[valor_col].agg(['sum', 'count']).round(2)
            stats['por_natureza'] = natureza.to_dict('index')
        
        # Por indicador IE
        ie_col = self._get_column_by_pattern(self.df_cabecalho, ['INDICADOR', 'IE', 'DESTINATARIO'])
        if ie_col:
            ie_dest = self.df_cabecalho.groupby(ie_col)[valor_col].agg(['sum', 'count']).round(2)
            stats['por_ie_destinatario'] = ie_dest.to_dict('index')
        
        return stats
    
    def _get_distribuicao_valores(self):
        """Distribuição de valores das notas fiscais"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        
        if not valor_col:
            return {}
        
        valores = self.df_cabecalho[valor_col].dropna()
        percentis = [10, 25, 50, 75, 90, 95, 99]
        
        return {
            f'percentil_{p}': float(valores.quantile(p/100)) for p in percentis
        }
    
    def _get_analise_conformidade(self):
        """Análise básica de conformidade"""
        conformidade = {
            'nfs_sem_valor': 0,
            'nfs_valor_zero': 0,
            'chaves_duplicadas': 0,
            'itens_sem_ncm': 0
        }
        
        try:
            if self.df_cabecalho is not None and not self.df_cabecalho.empty:
                valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
                chave_col = self._get_column_by_pattern(self.df_cabecalho, ['CHAVE', 'ACESSO'])
                
                if valor_col:
                    conformidade['nfs_sem_valor'] = int(self.df_cabecalho[valor_col].isna().sum())
                    conformidade['nfs_valor_zero'] = int((self.df_cabecalho[valor_col] == 0).sum())
                
                if chave_col:
                    conformidade['chaves_duplicadas'] = int(self.df_cabecalho.duplicated(subset=[chave_col]).sum())
            
            if self.df_itens is not None and not self.df_itens.empty:
                ncm_col = self._get_column_by_pattern(self.df_itens, ['NCM', 'SH'])
                if ncm_col:
                    conformidade['itens_sem_ncm'] = int(self.df_itens[ncm_col].isna().sum())
                    
        except Exception as e:
            print(f"⚠️ Erro na análise de conformidade: {str(e)}")
        
        return conformidade
    
    def _get_tendencias(self):
        """Análise de tendências temporais"""
        if self.df_cabecalho is None or self.df_cabecalho.empty:
            return {}
        
        data_col = self._get_column_by_pattern(self.df_cabecalho, ['DATA', 'EMISSAO', 'EMISSÃO'])
        valor_col = self._get_column_by_pattern(self.df_cabecalho, ['VALOR', 'TOTAL', 'VLR'])
        
        if not data_col or not valor_col:
            return {}
        
        df_temp = self.df_cabecalho.copy()
        df_temp['mes'] = df_temp[data_col].dt.to_period('M')
        
        if df_temp['mes'].nunique() > 1:
            por_mes = df_temp.groupby('mes')[valor_col].agg(['sum', 'count']).round(2)
            return por_mes.to_dict('index')
        
        return {}
    
    def create_agent(self):
        """Cria o agente especialista fiscal"""
        return Agent(
            role="Analista Fiscal Senior",
            goal="Gerar relatórios fiscais detalhados e análises precisas de notas fiscais brasileiras",
            backstory="""Você é um especialista em análise fiscal brasileira com mais de 15 anos de experiência.
            Sua expertise inclui:
            - Análise detalhada de conformidade tributária
            - Interpretação de dados fiscais complexos e identificação de padrões
            - Geração de relatórios executivos claros e objetivos
            - Identificação de anomalias e oportunidades de otimização fiscal
            - Conhecimento profundo da legislação tributária brasileira
            
            Sempre forneça números exatos, insights relevantes e recomendações práticas baseadas nos dados.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_task(self, pergunta, analise_dados):
        """Cria tarefa personalizada baseada na pergunta"""
        pergunta_lower = pergunta.lower()
        
        if any(word in pergunta_lower for word in ['relatório', 'relatorio', 'análise completa', 'dashboard']):
            task_description = f"""
            GERAR RELATÓRIO FISCAL EXECUTIVO COMPLETO baseado nos dados analisados.
            
            Pergunta do usuário: {pergunta}
            
            DADOS DISPONÍVEIS PARA ANÁLISE:
            {self._format_complete_analysis(analise_dados)}
            
            ESTRUTURA OBRIGATÓRIA DO RELATÓRIO:
            
            # RELATÓRIO FISCAL EXECUTIVO
            
            ## 1. RESUMO EXECUTIVO
            - Visão geral do período analisado
            - Principais números e indicadores
            
            ## 2. ANÁLISE FINANCEIRA DETALHADA
            - Valor total das operações
            - Estatísticas descritivas (média, mediana, desvio padrão)
            - Distribuição de valores
            
            ## 3. ANÁLISE DE FORNECEDORES
            - Top 5 fornecedores por valor
            - Concentração de fornecedores
            - Análise de risco
            
            ## 4. DISTRIBUIÇÃO GEOGRÁFICA
            - Análise por UF
            - Concentração regional
            
            ## 5. ANÁLISE DE PRODUTOS/SERVIÇOS
            - Principais itens por valor
            - Categorização NCM
            
            ## 6. INDICADORES DE CONFORMIDADE
            - Inconsistências identificadas
            - Alertas de conformidade
            
            ## 7. RECOMENDAÇÕES ESTRATÉGICAS
            - Oportunidades de otimização
            - Ações recomendadas
            
            Use formatação markdown e seja detalhado com os números apresentados.
            """
            expected_output = "Relatório fiscal executivo completo, estruturado e detalhado em formato markdown"
        else:
            task_description = f"""
            RESPONDER PERGUNTA ESPECÍFICA sobre dados fiscais de forma precisa e detalhada.
            
            Pergunta: {pergunta}
            
            Dados disponíveis: {self._format_analysis(analise_dados)}
            
            Instruções:
            - Responda de forma direta e precisa usando os números fornecidos
            - Forneça contexto e interpretação dos dados
            - Use formatação clara e organize a informação
            - Se possível, inclua insights adicionais relevantes
            """
            expected_output = "Resposta objetiva, precisa e bem contextualizada com dados exatos"
        
        return Task(
            description=task_description,
            expected_output=expected_output,
            agent=None
        )
    
    def _format_complete_analysis(self, analise):
        """Formata análise completa para relatório"""
        if not analise:
            return "Dados não disponíveis"
        
        texto = f"""
## DADOS DO PERÍODO ANALISADO
- Período: {analise['periodo']['inicio']} a {analise['periodo']['fim']} ({analise['periodo']['total_dias']} dias)

## RESUMO FINANCEIRO CONSOLIDADO
"""
        resumo = analise.get('resumo_financeiro', {})
        if resumo:
            texto += f"""- Valor Total das Operações: R$ {resumo.get('valor_total', 0):,.2f}
- Quantidade de Notas Fiscais: {resumo.get('quantidade_nfs', 0):,}
- Valor Médio por NF: R$ {resumo.get('valor_medio', 0):,.2f}
- Valor Mediano: R$ {resumo.get('valor_mediano', 0):,.2f}
- Maior Nota Fiscal: R$ {resumo.get('maior_nf', 0):,.2f}
- Menor Nota Fiscal: R$ {resumo.get('menor_nf', 0):,.2f}
- Desvio Padrão: R$ {resumo.get('desvio_padrao', 0):,.2f}
"""

        texto += "\n## TOP 5 PRINCIPAIS FORNECEDORES\n"
        for i, (nome, dados) in enumerate(list(analise['top_fornecedores'].items())[:5], 1):
            uf_info = f" - {dados.get('uf', 'N/A')}" if dados.get('uf') else ""
            texto += f"{i}. **{nome}**{uf_info}\n"
            texto += f"   - Valor Total: R$ {dados['valor_total']:,.2f}\n"
            texto += f"   - Quantidade NFs: {dados['qtd_nfs']}\n"
            texto += f"   - Valor Médio: R$ {dados['valor_medio']:,.2f}\n\n"
        
        texto += "## DISTRIBUIÇÃO GEOGRÁFICA (POR UF)\n"
        for uf, dados in list(analise['analise_geografica'].items())[:10]:
            texto += f"- **{uf}**: R$ {dados['valor_total']:,.2f} ({dados['qtd_nfs']} NFs"
            if 'qtd_fornecedores' in dados:
                texto += f", {dados['qtd_fornecedores']} fornecedores"
            texto += ")\n"
        
        if analise.get('produtos_principais'):
            texto += "\n## TOP 5 PRODUTOS/SERVIÇOS\n"
            for i, (produto, dados) in enumerate(list(analise['produtos_principais'].items())[:5], 1):
                produto_nome = produto[:80] + "..." if len(produto) > 80 else produto
                texto += f"{i}. **{produto_nome}**\n"
                
                # Verificar qual coluna de valor está disponível
                valor = None
                if 'VALOR TOTAL' in dados:
                    valor = dados['VALOR TOTAL']
                elif 'VALOR_CALCULADO' in dados:
                    valor = dados['VALOR_CALCULADO']
                
                if valor is not None:
                    texto += f"   - Valor Total: R$ {valor:,.2f}\n"
                
                if 'QUANTIDADE' in dados:
                    texto += f"   - Quantidade: {dados['QUANTIDADE']:,.0f}\n"
                
                if 'VALOR UNITÁRIO' in dados or 'VALOR UNIT' in dados:
                    valor_unit = dados.get('VALOR UNITÁRIO', dados.get('VALOR UNIT', 0))
                    texto += f"   - Valor Unitário Médio: R$ {valor_unit:,.2f}\n"
                
                texto += "\n"
        
        if analise.get('conformidade'):
            conf = analise['conformidade']
            texto += f"""
## ANÁLISE DE CONFORMIDADE
- Notas sem valor informado: {conf['nfs_sem_valor']}
- Notas com valor zero: {conf['nfs_valor_zero']}
- Chaves de acesso duplicadas: {conf['chaves_duplicadas']}
- Itens sem código NCM: {conf['itens_sem_ncm']}
"""

        if analise.get('distribuicao_valores'):
            dist = analise['distribuicao_valores']
            texto += f"""
## DISTRIBUIÇÃO DE VALORES (PERCENTIS)
- 10% das NFs até: R$ {dist.get('percentil_10', 0):,.2f}
- 25% das NFs até: R$ {dist.get('percentil_25', 0):,.2f}
- 50% das NFs até: R$ {dist.get('percentil_50', 0):,.2f}
- 75% das NFs até: R$ {dist.get('percentil_75', 0):,.2f}
- 90% das NFs até: R$ {dist.get('percentil_90', 0):,.2f}
"""
        
        return texto
    
    def _format_analysis(self, analise):
        """Formata análise simples"""
        return self._format_complete_analysis(analise)
    
    def run(self, pergunta):
        """Executa análise baseada na pergunta"""
        try:
            print(f"🚀 Iniciando análise para: {pergunta}")
            
            # Verificar se há dados básicos
            if self.df_cabecalho is None or self.df_cabecalho.empty:
                return """❌ **ERRO: Dados não encontrados**
                
Verifique se:
1. Os arquivos CSV estão no diretório 'knowledge/'
2. Os nomes dos arquivos estão corretos:
   - 202401_NFs_Cabecalho.csv
   - 202401_NFs_Itens.csv
3. Os arquivos não estão corrompidos
4. Você tem permissão de leitura nos arquivos

Estrutura esperada do projeto:
```
projeto/
├── knowledge/
│   ├── 202401_NFs_Cabecalho.csv
│   └── 202401_NFs_Itens.csv
└── crew.py
```"""
            
            print("📊 Gerando análise dos dados...")
            
            # Gerar análise
            analise_dados = self._generate_fiscal_analysis(pergunta)
            
            if not analise_dados or not analise_dados.get('resumo_financeiro'):
                return """❌ **ERRO: Não foi possível processar os dados**
                
Possíveis causas:
1. Estrutura do CSV não está no formato esperado
2. Colunas obrigatórias não foram encontradas
3. Dados estão corrompidos ou vazios

Colunas esperadas no cabeçalho:
- Coluna com 'VALOR' (ex: VALOR NOTA FISCAL, VALOR TOTAL)
- Coluna com 'DATA' (ex: DATA EMISSÃO)
- Coluna com fornecedor (ex: RAZÃO SOCIAL EMITENTE)
- Coluna com UF (ex: UF EMITENTE)"""
            
            print("🤖 Criando agente e executando análise...")
            
            # Criar agente e tarefa
            agent = self.create_agent()
            task = self.create_task(pergunta, analise_dados)
            task.agent = agent
            
            # Executar crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )
            
            print("⚡ Executando crew...")
            resultado = crew.kickoff()
            
            print("✅ Análise concluída com sucesso!")
            return str(resultado)
            
        except Exception as e:
            # Log mais detalhado do erro
            error_detail = traceback.format_exc()
            print(f"❌ Erro detalhado: {error_detail}")
            
            return f"""❌ **ERRO NA ANÁLISE: {str(e)}**

**Diagnóstico:**
- Verifique se o Ollama está rodando: `ollama serve`
- Verifique se o modelo está disponível: `ollama list`
- Teste o modelo: `ollama run llama3.2:3b`

**Verificações dos dados:**
- Arquivos CSV no local correto: knowledge/
- Permissões de leitura nos arquivos
- Formato dos CSVs (separador, encoding)

**Estrutura esperada:**
```
knowledge/
├── 202401_NFs_Cabecalho.csv (cabeçalho das NFs)
└── 202401_NFs_Itens.csv (itens das NFs)
```

**Erro técnico:** {error_detail[-500:]}"""
    
    def get_data_info(self):
        """Retorna informações detalhadas sobre os dados carregados"""
        info = {
            'status': 'success',
            'cabecalho': None,
            'itens': None,
            'diagnostico': []
        }
        
        try:
            if self.df_cabecalho is not None:
                info['cabecalho'] = {
                    'registros': len(self.df_cabecalho),
                    'colunas': list(self.df_cabecalho.columns),
                    'colunas_numericas': list(self.df_cabecalho.select_dtypes(include=[np.number]).columns),
                    'colunas_data': list(self.df_cabecalho.select_dtypes(include=['datetime64']).columns),
                    'memoria_mb': round(self.df_cabecalho.memory_usage(deep=True).sum() / 1024 / 1024, 2)
                }
                info['diagnostico'].append("✅ Cabeçalho carregado com sucesso")
            else:
                info['diagnostico'].append("❌ Cabeçalho não foi carregado")
            
            if self.df_itens is not None:
                info['itens'] = {
                    'registros': len(self.df_itens),
                    'colunas': list(self.df_itens.columns),
                    'colunas_numericas': list(self.df_itens.select_dtypes(include=[np.number]).columns),
                    'memoria_mb': round(self.df_itens.memory_usage(deep=True).sum() / 1024 / 1024, 2)
                }
                info['diagnostico'].append("✅ Itens carregados com sucesso")
            else:
                info['diagnostico'].append("⚠️ Itens não foram carregados (opcional)")
            
            # Verificar conexão com Ollama
            try:
                # Teste simples de conexão
                test_response = self.llm.invoke("teste")
                info['diagnostico'].append("✅ Conexão com Ollama funcionando")
            except Exception as e:
                info['diagnostico'].append(f"❌ Problema com Ollama: {str(e)}")
                info['status'] = 'warning'
                
        except Exception as e:
            info['status'] = 'error'
            info['diagnostico'].append(f"❌ Erro no diagnóstico: {str(e)}")
            
        return info
    
    def test_analysis(self):
        """Testa uma análise simples para verificar se tudo está funcionando"""
        try:
            print("🧪 Testando análise básica...")
            
            if self.df_cabecalho is None or self.df_cabecalho.empty:
                return "❌ Teste falhou: Sem dados de cabeçalho"
            
            # Teste básico de análise
            resumo = self._get_resumo_financeiro()
            
            if not resumo:
                return "❌ Teste falhou: Não foi possível gerar resumo financeiro"
            
            # Teste do agente
            pergunta_teste = "Qual o valor total das notas fiscais?"
            resultado = self.run(pergunta_teste)
            
            if "❌" in resultado:
                return f"❌ Teste falhou: {resultado}"
            
            return f"✅ Teste bem-sucedido! Valor total encontrado: R$ {resumo.get('valor_total', 0):,.2f}"
            
        except Exception as e:
            return f"❌ Teste falhou com erro: {str(e)}"


# Função de conveniência para uso direto
def criar_fiscal_crew():
    """Cria e retorna uma instância do FiscalCrew"""
    return FiscalCrew()


# Exemplo de uso
if __name__ == "__main__":
    # Criar instância
    fiscal_crew = FiscalCrew()
    
    # Verificar informações dos dados
    print("=" * 50)
    print("INFORMAÇÕES DOS DADOS CARREGADOS")
    print("=" * 50)
    info = fiscal_crew.get_data_info()
    
    for diag in info['diagnostico']:
        print(diag)
    
    if info['cabecalho']:
        print(f"\n📊 Cabeçalho: {info['cabecalho']['registros']} registros")
        print(f"Colunas: {info['cabecalho']['colunas']}")
    
    if info['itens']:
        print(f"\n📦 Itens: {info['itens']['registros']} registros")
        print(f"Colunas: {info['itens']['colunas']}")
    
    # Teste básico
    print("\n" + "=" * 50)
    print("TESTE DE FUNCIONAMENTO")
    print("=" * 50)
    print(fiscal_crew.test_analysis())
    
    # Exemplo de pergunta
    if info['status'] == 'success':
        print("\n" + "=" * 50)
        print("EXEMPLO DE ANÁLISE")
        print("=" * 50)
        resultado = fiscal_crew.run("Gere um relatório fiscal completo dos dados")
        print(resultado)