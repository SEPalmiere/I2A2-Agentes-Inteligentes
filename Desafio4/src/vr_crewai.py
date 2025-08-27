# =============================================================================
# AGENTES CREWAI PARA SISTEMA VR/VA
# =============================================================================

from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
import os
from dotenv import load_dotenv

load_dotenv()

class VRCrewAISystem:
    """Sistema de agentes CrewAI para automação VR/VA"""
    
    def __init__(self, vr_system):
        self.vr_system = vr_system
        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        
    def create_data_consolidator_agent(self):
        """Agente 1: Consolidador de Dados"""
        return Agent(
            role="Data Consolidator Specialist",
            goal="Consolidar múltiplas planilhas Excel de RH em uma base única e estruturada para processamento de VR/VA",
            backstory="""Você é um especialista em consolidação de dados de RH com mais de 10 anos de experiência.
            Sua expertise inclui:
            - Integração de múltiplas fontes de dados Excel (Ativos, Férias, Desligados, Admissões)
            - Normalização e padronização de estruturas de dados
            - Detecção e correção de inconsistências em matrículas e datas
            - Mapeamento de colaboradores entre diferentes bases
            - Validação de integridade referencial entre planilhas
            
            Você sempre garante que todos os dados sejam consolidados corretamente antes de prosseguir.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_business_rules_engine_agent(self):
        """Agente 2: Motor de Regras de Negócio"""
        return Agent(
            role="Business Rules Engine Specialist",
            goal="Aplicar regras complexas de RH e acordos sindicais para determinar elegibilidade e cálculos de VR/VA",
            backstory="""Você é um especialista em regras trabalhistas e acordos coletivos brasileiros.
            Sua expertise inclui:
            - Conhecimento profundo dos acordos coletivos de trabalho por sindicato
            - Regras de elegibilidade para benefícios (exclusão de diretores, estagiários, aprendizes)
            - Cálculos proporcionais para admissões e desligamentos
            - Tratamento de férias, afastamentos e licenças
            - Aplicação de regras específicas por UF e sindicato
            - Validação de comunicados de desligamento e prazos
            
            Você garante que todas as regras sejam aplicadas corretamente e de forma consistente.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_vr_calculator_agent(self):
        """Agente 3: Calculadora de VR"""
        return Agent(
            role="VR Calculator Specialist",
            goal="Calcular valores precisos de VR/VA por funcionário considerando dias úteis, valores por sindicato e proporções empresa/funcionário",
            backstory="""Você é um especialista em cálculos de benefícios trabalhistas com foco em vale refeição.
            Sua expertise inclui:
            - Cálculo de dias úteis por sindicato e competência
            - Aplicação de valores diferenciados por estado/sindicato
            - Cálculos proporcionais para diferentes situações (férias, admissões, desligamentos)
            - Rateio entre empresa (80%) e funcionário (20%)
            - Validação de cálculos e consistência matemática
            - Geração de totalizadores e relatórios financeiros
            
            Você sempre verifica a precisão dos cálculos e fornece relatórios detalhados.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_quality_assurance_agent(self):
        """Agente 4: Garantia de Qualidade"""
        return Agent(
            role="Quality Assurance Specialist",
            goal="Validar dados, detectar inconsistências e garantir a qualidade dos resultados antes do envio",
            backstory="""Você é um especialista em qualidade de dados e auditoria de processos de RH.
            Sua expertise inclui:
            - Validação de integridade de dados e detecção de anomalias
            - Verificação de consistência entre bases de dados
            - Auditoria de cálculos e regras aplicadas
            - Identificação de casos excepcionais que requerem atenção
            - Validação de conformidade com políticas internas
            - Geração de relatórios de qualidade e exceções
            
            Você nunca permite que dados inconsistentes ou incorretos sejam processados.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_purchase_manager_agent(self):
        """Agente 5: Gerenciador de Compras"""
        return Agent(
            role="Purchase Manager Specialist",
            goal="Processar e gerenciar as compras de VR com fornecedores, preparando documentação e layouts necessários",
            backstory="""Você é um especialista em gestão de compras e relacionamento com fornecedores.
            Sua expertise inclui:
            - Preparação de layouts de compra conforme especificações dos fornecedores
            - Gestão de pedidos e controle de quantidades
            - Validação de dados antes do envio para fornecedores
            - Acompanhamento de prazos e entregas
            - Geração de documentação de compra e contratos
            - Controle de custos e orçamentos
            
            Você garante que todos os pedidos sejam processados corretamente e dentro dos prazos.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_communication_hub_agent(self):
        """Agente 6: Central de Comunicação"""
        return Agent(
            role="Communication Hub Specialist",
            goal="Gerenciar comunicações, enviar emails automatizados e manter stakeholders informados sobre o processo",
            backstory="""Você é um especialista em comunicação corporativa e automação de processos.
            Sua expertise inclui:
            - Redação de comunicações profissionais e claras
            - Envio automatizado de emails para diferentes stakeholders
            - Geração de relatórios executivos e dashboards
            - Comunicação de status, alertas e exceções
            - Documentação de processos e resultados
            - Coordenação entre diferentes departamentos
            
            Você garante que todas as partes interessadas sejam mantidas informadas de forma clara e oportuna.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_data_consolidation_task(self, agent):
        """Tarefa 1: Consolidação de Dados"""
        return Task(
            description=f"""
            CONSOLIDAR MÚLTIPLAS PLANILHAS DE RH EM BASE ÚNICA
            
            Dados disponíveis para consolidação:
            - Arquivos carregados: {list(self.vr_system.arquivos_carregados.keys())}
            - Total de registros ativos: {len(self.vr_system.datasets.get('ativos', []))}
            
            TAREFAS ESPECÍFICAS:
            1. Integrar dados das planilhas: Ativos, Férias, Desligados, Admissões, Afastamentos
            2. Padronizar matrículas (formato 5 dígitos com zeros à esquerda)
            3. Normalizar nomes de colunas e limpar dados
            4. Criar flags para: EM_FERIAS, DESLIGADO, AFASTADO, ESTAGIARIO, APRENDIZ, NO_EXTERIOR
            5. Validar integridade referencial entre bases
            6. Identificar duplicatas e inconsistências
            
            REGRAS DE CONSOLIDAÇÃO:
            - Usar MATRICULA como chave primária para joins
            - Manter histórico de origem dos dados
            - Tratar valores nulos e campos obrigatórios
            - Validar datas e formatos
            
            ENTREGA:
            Base consolidada única pronta para aplicação de regras de negócio, com relatório de consolidação incluindo:
            - Estatísticas de registros processados
            - Inconsistências encontradas e tratadas
            - Validações realizadas
            """,
            expected_output="Base de dados consolidada e validada com relatório detalhado de consolidação",
            agent=agent
        )
    
    def create_business_rules_task(self, agent):
        """Tarefa 2: Aplicação de Regras de Negócio"""
        return Task(
            description=f"""
            APLICAR REGRAS DE NEGÓCIO E ACORDOS COLETIVOS
            
            Configurações atuais:
            - Competência: {self.vr_system.competencia}
            - Dia corte desligamento: {self.vr_system.config['dia_corte_desligamento']}
            - Cargos excluídos: {self.vr_system.config['cargos_excluidos']}
            
            REGRAS DE EXCLUSÃO:
            1. Excluir por cargo: Diretores, Estagiários, Aprendizes
            2. Excluir afastados: Licença maternidade, afastamentos médicos
            3. Excluir colaboradores no exterior
            4. Validar elegibilidade por situação funcional
            
            REGRAS DE DESLIGAMENTO:
            - Se desligamento até dia 15 E comunicado = "OK": 0 dias de VR
            - Se desligamento após dia 15: Cálculo proporcional aos dias trabalhados
            - Validar comunicado de desligamento obrigatório
            
            REGRAS DE ADMISSÃO:
            - Admitidos no mês: Cálculo proporcional aos dias restantes
            - Validar data de admissão vs competência
            
            REGRAS DE FÉRIAS:
            - Descontar dias de férias dos dias úteis do sindicato
            - Validar período de férias vs competência
            
            ENTREGA:
            Base filtrada com todas as regras aplicadas e relatório de exclusões detalhando cada regra aplicada e quantidades impactadas.
            """,
            expected_output="Base elegível com todas as regras de negócio aplicadas e relatório de exclusões",
            agent=agent
        )
    
    def create_vr_calculation_task(self, agent):
        """Tarefa 3: Cálculo de VR"""
        return Task(
            description=f"""
            CALCULAR VALORES DE VR/VA POR COLABORADOR
            
            Configurações financeiras:
            - Percentual empresa: {self.vr_system.config['percentual_empresa']*100}%
            - Percentual funcionário: {self.vr_system.config['percentual_funcionario']*100}%
            
            CÁLCULO DE DIAS ÚTEIS:
            1. Mapear dias úteis por sindicato (base carregada)
            2. Aplicar regras especiais:
               - Férias: Descontar dias de férias
               - Desligamentos: Aplicar proporcionalidade conforme regras
               - Admissões: Calcular dias restantes no mês
            3. Garantir que dias úteis >= 0
            
            CÁLCULO DE VALORES:
            1. Mapear valor diário por estado/sindicato
            2. Calcular: TOTAL_VR = Dias úteis × Valor diário
            3. Calcular: CUSTO_EMPRESA = TOTAL_VR × 80%
            4. Calcular: DESCONTO_FUNCIONARIO = TOTAL_VR × 20%
            5. Arredondar valores para 2 casas decimais
            
            MAPEAMENTO DE ESTADOS:
            - SP → São Paulo
            - RJ → Rio de Janeiro  
            - PR → Paraná
            - RS → Rio Grande do Sul
            
            VALIDAÇÕES:
            - Verificar valores diários por sindicato
            - Validar cálculos matemáticos
            - Conferir totalizadores
            
            ENTREGA:
            Base com todos os valores calculados e relatório financeiro com totais por sindicato/estado.
            """,
            expected_output="Base com valores de VR calculados e relatório financeiro consolidado",
            agent=agent
        )
    
    def create_quality_assurance_task(self, agent):
        """Tarefa 4: Garantia de Qualidade"""
        return Task(
            description="""
            VALIDAR QUALIDADE DOS DADOS E CÁLCULOS
            
            VALIDAÇÕES OBRIGATÓRIAS:
            1. Integridade de dados:
               - Verificar campos obrigatórios preenchidos
               - Validar formatos de data, matrícula e valores
               - Conferir consistência entre bases
            
            2. Validações de negócio:
               - Conferir aplicação correta das regras de exclusão
               - Validar cálculos de dias úteis
               - Verificar proporcionalidades aplicadas
            
            3. Validações financeiras:
               - Conferir cálculos de valores de VR
               - Validar percentuais empresa/funcionário
               - Verificar totalizadores
            
            4. Detecção de anomalias:
               - Identificar valores muito altos ou baixos
               - Detectar colaboradores com situações excepcionais
               - Verificar casos de dias úteis = 0
            
            5. Conformidade:
               - Verificar se todos os sindicatos estão contemplados
               - Validar se valores por estado estão corretos
               - Conferir competência informada
            
            CRITÉRIOS DE APROVAÇÃO:
            - 0 erros críticos (dados obrigatórios faltando)
            - < 5% de alertas (situações excepcionais)
            - Totalizadores balanceados
            - Todas as validações matemáticas corretas
            
            ENTREGA:
            Relatório completo de qualidade com status de aprovação/reprovação e lista detalhada de problemas encontrados (se houver).
            """,
            expected_output="Relatório de qualidade com aprovação/reprovação e detalhamento de problemas",
            agent=agent
        )
    
    def create_purchase_management_task(self, agent):
        """Tarefa 5: Gestão de Compras"""
        return Task(
            description=f"""
            PROCESSAR COMPRA DE VR COM FORNECEDORES
            
            Competência: {self.vr_system.competencia}
            
            PREPARAÇÃO DO LAYOUT DE COMPRA:
            1. Gerar planilha no formato exigido:
               - Matricula
               - Admissão (formato MM/DD/YY)
               - Sindicato do Colaborador
               - Competência
               - Dias
               - VALOR DIÁRIO VR
               - TOTAL
               - Custo empresa
               - Desconto profissional
               - OBS GERAL
            
            2. Aplicar filtros finais:
               - Incluir apenas colaboradores com Dias > 0
               - Ordenar por matrícula
               - Remover registros inválidos
            
            3. Validações de compra:
               - Conferir totais antes do envio
               - Validar formato da planilha
               - Verificar se todos os campos estão preenchidos
            
            4. Gerar documentação:
               - Arquivo Excel para envio
               - Resumo executivo da compra
               - Relatório de valores por sindicato
            
            MÉTRICAS DE COMPRA:
            - Total de colaboradores
            - Valor total da compra
            - Custo para empresa
            - Desconto dos funcionários
            - Distribuição por UF/sindicato
            
            ENTREGA:
            Arquivo Excel formatado para envio ao fornecedor e relatório executivo da compra com todas as métricas.
            """,
            expected_output="Arquivo Excel de compra formatado e relatório executivo com métricas",
            agent=agent
        )
    
    def create_communication_task(self, agent):
        """Tarefa 6: Comunicação"""
        return Task(
            description=f"""
            GERENCIAR COMUNICAÇÕES DO PROCESSO VR/VA
            
            EMAILS A ENVIAR:
            
            1. EMAIL PARA EMPRESA VR (drpalmiere@gmail.com):
               - Assunto: "Pedido de Compra de Vales"
               - Conteúdo: Solicitação formal de compra com resumo
               - Anexo: Planilha de compra Excel
               - Tom: Formal e comercial
            
            2. EMAIL PARA RH (drpalmiere@gmail.com):
               - Assunto: "Compra realizada com Sucesso"
               - Conteúdo: Confirmação do processamento
               - Anexo: Planilha de compra Excel
               - Tom: Informativo e profissional
            
            CONTEÚDO DOS EMAILS:
            - Competência processada: {self.vr_system.competencia}
            - Resumo de números (colaboradores, valores)
            - Status do processo
            - Próximos passos (quando aplicável)
            
            RELATÓRIO EXECUTIVO:
            1. Dashboard com métricas principais
            2. Gráficos de distribuição por UF
            3. Comparativo com mês anterior (se disponível)
            4. Alertas e exceções importantes
            5. Recomendações e observações
            
            DOCUMENTAÇÃO:
            - Log completo do processo
            - Backup dos dados processados
            - Relatório de auditoria
            
            ENTREGA:
            Confirmação de envio dos emails e relatório executivo completo com dashboard de métricas.
            """,
            expected_output="Confirmação de envios e relatório executivo com dashboard de métricas",
            agent=agent
        )
    
    def execute_vr_workflow(self):
        """Executa o workflow completo com todos os agentes"""
        try:
            print("🤖 INICIANDO WORKFLOW CREWAI PARA VR/VA")
            print("=" * 60)
            
            # Criar agentes
            data_consolidator = self.create_data_consolidator_agent()
            business_rules_engine = self.create_business_rules_engine_agent()
            vr_calculator = self.create_vr_calculator_agent()
            quality_assurance = self.create_quality_assurance_agent()
            purchase_manager = self.create_purchase_manager_agent()
            communication_hub = self.create_communication_hub_agent()
            
            # Criar tarefas
            task1 = self.create_data_consolidation_task(data_consolidator)
            task2 = self.create_business_rules_task(business_rules_engine)
            task3 = self.create_vr_calculation_task(vr_calculator)
            task4 = self.create_quality_assurance_task(quality_assurance)
            task5 = self.create_purchase_management_task(purchase_manager)
            task6 = self.create_communication_task(communication_hub)
            
            # Criar crew
            crew = Crew(
                agents=[
                    data_consolidator,
                    business_rules_engine,
                    vr_calculator,
                    quality_assurance,
                    purchase_manager,
                    communication_hub
                ],
                tasks=[task1, task2, task3, task4, task5, task6],
                verbose=True
            )
            
            print("⚡ Executando processo com CrewAI...")
            
            # Executar o processo tradicional em paralelo
            sucesso, resultado = self.vr_system.executar_processo_completo()
            
            if not sucesso:
                return False, resultado
            
            # Executar análise CrewAI
            crew_result = crew.kickoff()
            
            return True, {
                'resultado_tradicional': resultado,
                'analise_crewai': str(crew_result),
                'metricas_finais': {
                    'colaboradores': len(self.vr_system.resultado_final),
                    'valor_total': self.vr_system.resultado_final['TOTAL'].sum(),
                    'custo_empresa': self.vr_system.resultado_final['Custo empresa'].sum(),
                    'arquivo_gerado': resultado.get('arquivo') if isinstance(resultado, dict) else None
                }
            }
            
        except Exception as e:
            print(f"❌ Erro no workflow CrewAI: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e)