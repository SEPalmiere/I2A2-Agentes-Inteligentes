                    'arquivo_gerado': resultado_tradicional.get('arquivo') if isinstance(resultado_tradicional, dict) else None,
                    'emails_enviados': resultado_tradicional.get('emails_enviados', False) if isinstance(resultado_tradicional, dict) else False
                },
                'timestamp_processamento': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'arquivos_processados': len(self.vr_system.arquivos_carregados),
                'competenci# =============================================================================
# SISTEMA CREWAI COMPLETO PARA VR/VA - ARQUIVO DE INTEGRAÇÃO FINAL
# =============================================================================

from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
import os
import yaml
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class VRCrewAISystem:
    """Sistema completo de agentes CrewAI para automação VR/VA"""
    
    def __init__(self, vr_system):
        self.vr_system = vr_system
        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        
        # Carregar configurações dos agentes e tarefas
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()
        
    def _load_agents_config(self):
        """Carrega configurações dos agentes do arquivo YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agents.yaml')
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # Configuração padrão caso arquivo não exista
            return self._get_default_agents_config()
    
    def _load_tasks_config(self):
        """Carrega configurações das tarefas do arquivo YAML"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'tasks.yaml')
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # Configuração padrão caso arquivo não exista
            return self._get_default_tasks_config()
    
    def _get_default_agents_config(self):
        """Configuração padrão dos agentes"""
        return {
            'data_consolidator': {
                'role': 'Data Consolidator Specialist',
                'goal': 'Consolidar múltiplas planilhas Excel de RH em uma base única e estruturada',
                'backstory': 'Especialista em consolidação de dados com 15+ anos de experiência'
            },
            'business_rules_engine': {
                'role': 'Business Rules Engine Specialist', 
                'goal': 'Aplicar regras complexas de RH e acordos sindicais',
                'backstory': 'Especialista em legislação trabalhista brasileira'
            },
            'vr_calculator': {
                'role': 'VR Calculator Specialist',
                'goal': 'Calcular valores precisos de VR/VA por funcionário',
                'backstory': 'Especialista em cálculos financeiros de benefícios'
            },
            'quality_assurance': {
                'role': 'Quality Assurance Specialist',
                'goal': 'Validar dados e detectar inconsistências',
                'backstory': 'Auditor sênior especializado em qualidade de dados'
            },
            'purchase_manager': {
                'role': 'Purchase Manager Specialist',
                'goal': 'Processar compras com fornecedores',
                'backstory': 'Especialista em gestão de compras corporativas'
            },
            'communication_hub': {
                'role': 'Communication Hub Specialist',
                'goal': 'Gerenciar comunicações e envios automatizados',
                'backstory': 'Especialista em comunicação corporativa'
            }
        }
    
    def _get_default_tasks_config(self):
        """Configuração padrão das tarefas"""
        return {
            'data_consolidation': {
                'description': 'Consolidar múltiplas planilhas de RH em base única',
                'expected_output': 'Base consolidada com relatório de qualidade'
            },
            'business_rules_application': {
                'description': 'Aplicar regras de negócio e acordos coletivos',
                'expected_output': 'Base elegível com regras aplicadas'
            },
            'vr_value_calculation': {
                'description': 'Calcular valores precisos de VR/VA',
                'expected_output': 'Base com valores calculados'
            },
            'quality_validation': {
                'description': 'Validar qualidade dos dados processados',
                'expected_output': 'Relatório de qualidade com aprovação'
            },
            'purchase_processing': {
                'description': 'Processar compra e preparar documentação',
                'expected_output': 'Arquivo Excel e documentação de compra'
            },
            'communication_management': {
                'description': 'Gerenciar comunicações do processo',
                'expected_output': 'Emails enviados e relatórios gerados'
            }
        }
    
    def create_data_consolidator_agent(self):
        """Criar agente consolidador de dados"""
        config = self.agents_config.get('data_consolidator', {})
        
        return Agent(
            role=config.get('role', 'Data Consolidator Specialist'),
            goal=config.get('goal', 'Consolidar dados de múltiplas fontes'),
            backstory=config.get('backstory', 'Especialista em consolidação de dados'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_business_rules_engine_agent(self):
        """Criar agente de regras de negócio"""
        config = self.agents_config.get('business_rules_engine', {})
        
        return Agent(
            role=config.get('role', 'Business Rules Engine Specialist'),
            goal=config.get('goal', 'Aplicar regras de negócio'),
            backstory=config.get('backstory', 'Especialista em regras trabalhistas'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_vr_calculator_agent(self):
        """Criar agente calculadora de VR"""
        config = self.agents_config.get('vr_calculator', {})
        
        return Agent(
            role=config.get('role', 'VR Calculator Specialist'),
            goal=config.get('goal', 'Calcular valores de VR/VA'),
            backstory=config.get('backstory', 'Especialista em cálculos financeiros'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_quality_assurance_agent(self):
        """Criar agente de garantia de qualidade"""
        config = self.agents_config.get('quality_assurance', {})
        
        return Agent(
            role=config.get('role', 'Quality Assurance Specialist'),
            goal=config.get('goal', 'Validar qualidade dos dados'),
            backstory=config.get('backstory', 'Especialista em qualidade'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_purchase_manager_agent(self):
        """Criar agente gerenciador de compras"""
        config = self.agents_config.get('purchase_manager', {})
        
        return Agent(
            role=config.get('role', 'Purchase Manager Specialist'),
            goal=config.get('goal', 'Gerenciar compras'),
            backstory=config.get('backstory', 'Especialista em compras'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_communication_hub_agent(self):
        """Criar agente central de comunicação"""
        config = self.agents_config.get('communication_hub', {})
        
        return Agent(
            role=config.get('role', 'Communication Hub Specialist'),
            goal=config.get('goal', 'Gerenciar comunicações'),
            backstory=config.get('backstory', 'Especialista em comunicação'),
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def create_data_consolidation_task(self, agent):
        """Criar tarefa de consolidação de dados"""
        config = self.tasks_config.get('data_consolidation', {})
        
        description = f"""
        {config.get('description', 'Consolidar dados de múltiplas fontes')}
        
        DADOS DISPONÍVEIS PARA CONSOLIDAÇÃO:
        - Arquivos carregados: {list(self.vr_system.arquivos_carregados.keys())}
        - Total de registros ativos: {len(self.vr_system.datasets.get('ativos', []))}
        - Competência sendo processada: {self.vr_system.competencia}
        
        STATUS ATUAL DOS DATASETS:
        {self._format_datasets_status()}
        
        Execute a consolidação completa conforme especificações técnicas.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Base consolidada'),
            agent=agent
        )
    
    def create_business_rules_task(self, agent):
        """Criar tarefa de aplicação de regras de negócio"""
        config = self.tasks_config.get('business_rules_application', {})
        
        description = f"""
        {config.get('description', 'Aplicar regras de negócio')}
        
        CONFIGURAÇÕES ATUAIS:
        - Competência: {self.vr_system.competencia}
        - Dia corte desligamento: {self.vr_system.config.get('dia_corte_desligamento', 15)}
        - Percentual empresa: {self.vr_system.config.get('percentual_empresa', 0.8)*100}%
        - Cargos excluídos: {self.vr_system.config.get('cargos_excluidos', [])}
        
        BASE CONSOLIDADA STATUS:
        {self._format_base_status()}
        
        Execute aplicação completa das regras conforme acordos coletivos.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Base com regras aplicadas'),
            agent=agent
        )
    
    def create_vr_calculation_task(self, agent):
        """Criar tarefa de cálculo de VR"""
        config = self.tasks_config.get('vr_value_calculation', {})
        
        description = f"""
        {config.get('description', 'Calcular valores de VR/VA')}
        
        CONFIGURAÇÕES FINANCEIRAS:
        - Percentual empresa: {self.vr_system.config.get('percentual_empresa', 0.8)*100}%
        - Percentual funcionário: {self.vr_system.config.get('percentual_funcionario', 0.2)*100}%
        
        DADOS DE SINDICATOS E VALORES:
        {self._format_sindicatos_valores()}
        
        Execute cálculos precisos conforme especificações técnicas.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Base com valores calculados'),
            agent=agent
        )
    
    def create_quality_assurance_task(self, agent):
        """Criar tarefa de garantia de qualidade"""
        config = self.tasks_config.get('quality_validation', {})
        
        description = f"""
        {config.get('description', 'Validar qualidade dos dados')}
        
        DADOS A VALIDAR:
        - Total de registros processados: {len(self.vr_system.base_consolidada) if self.vr_system.base_consolidada is not None else 0}
        - Arquivos fonte: {len(self.vr_system.arquivos_carregados)}
        
        Execute validação rigorosa conforme critérios de qualidade estabelecidos.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Relatório de qualidade'),
            agent=agent
        )
    
    def create_purchase_management_task(self, agent):
        """Criar tarefa de gestão de compras"""
        config = self.tasks_config.get('purchase_processing', {})
        
        description = f"""
        {config.get('description', 'Processar compra de VR/VA')}
        
        INFORMAÇÕES DA COMPRA:
        - Competência: {self.vr_system.competencia}
        - Data processamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        Prepare documentação completa para envio ao fornecedor.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Documentação de compra'),
            agent=agent
        )
    
    def create_communication_task(self, agent):
        """Criar tarefa de comunicação"""
        config = self.tasks_config.get('communication_management', {})
        
        description = f"""
        {config.get('description', 'Gerenciar comunicações')}
        
        EMAILS A ENVIAR:
        1. Empresa VR: drpalmiere@gmail.com - "Pedido de Compra de Vales"
        2. RH Interno: drpalmiere@gmail.com - "Compra realizada com Sucesso"
        
        COMPETÊNCIA: {self.vr_system.competencia}
        
        Execute comunicações conforme templates estabelecidos.
        """
        
        return Task(
            description=description,
            expected_output=config.get('expected_output', 'Comunicações enviadas'),
            agent=agent
        )
    
    def _format_datasets_status(self):
        """Formatar status dos datasets para exibição"""
        if not self.vr_system.datasets:
            return "Nenhum dataset carregado"
        
        status = []
        for key, df in self.vr_system.datasets.items():
            if df is not None:
                status.append(f"- {key}: {len(df)} registros")
            else:
                status.append(f"- {key}: Não carregado")
        
        return "\n".join(status)
    
    def _format_base_status(self):
        """Formatar status da base consolidada"""
        if self.vr_system.base_consolidada is None:
            return "Base consolidada não criada ainda"
        
        return f"Base consolidada com {len(self.vr_system.base_consolidada)} registros"
    
    def _format_sindicatos_valores(self):
        """Formatar informações de sindicatos e valores"""
        if 'dias_uteis' not in self.vr_system.datasets or 'valores_sindicato' not in self.vr_system.datasets:
            return "Dados de sindicatos não disponíveis"
        
        info = []
        
        # Dias úteis
        dias_df = self.vr_system.datasets.get('dias_uteis')
        if dias_df is not None and not dias_df.empty:
            info.append("DIAS ÚTEIS POR SINDICATO:")
            for _, row in dias_df.iterrows():
                info.append(f"- {row.get('SINDICATO', 'N/A')}: {row.get('DIAS_UTEIS', 'N/A')} dias")
        
        # Valores por estado
        valores_df = self.vr_system.datasets.get('valores_sindicato')
        if valores_df is not None and not valores_df.empty:
            info.append("\nVALORES POR ESTADO:")
            for _, row in valores_df.iterrows():
                estado = row.iloc[0] if len(row) > 0 else 'N/A'
                valor = row.iloc[1] if len(row) > 1 else 'N/A'
                info.append(f"- {estado}: {valor}")
        
        return "\n".join(info) if info else "Informações não disponíveis"
    
    def execute_vr_workflow(self):
        """Executar o workflow completo com todos os agentes"""
        try:
            print("🤖 INICIANDO WORKFLOW CREWAI PARA VR/VA")
            print("=" * 60)
            
            # Verificar se todos os arquivos estão carregados
            arquivos_ok, faltando = self.vr_system.verificar_arquivos_necessarios()
            if not arquivos_ok:
                return False, f"Arquivos faltando: {faltando}"
            
            # Criar agentes
            print("👥 Criando agentes especializados...")
            data_consolidator = self.create_data_consolidator_agent()
            business_rules_engine = self.create_business_rules_engine_agent()
            vr_calculator = self.create_vr_calculator_agent()
            quality_assurance = self.create_quality_assurance_agent()
            purchase_manager = self.create_purchase_manager_agent()
            communication_hub = self.create_communication_hub_agent()
            
            print("📋 Criando tarefas...")
            # Criar tarefas
            task1 = self.create_data_consolidation_task(data_consolidator)
            task2 = self.create_business_rules_task(business_rules_engine)
            task3 = self.create_vr_calculation_task(vr_calculator)
            task4 = self.create_quality_assurance_task(quality_assurance)
            task5 = self.create_purchase_management_task(purchase_manager)
            task6 = self.create_communication_task(communication_hub)
            
            print("🔧 Montando equipe CrewAI...")
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
            
            print("⚡ Executando processo tradicional...")
            # Executar o processo tradicional primeiro
            sucesso_tradicional, resultado_tradicional = self.vr_system.executar_processo_completo()
            
            if not sucesso_tradicional:
                return False, f"Erro no processo tradicional: {resultado_tradicional}"
            
            print("🧠 Executando análise CrewAI...")
            # Executar análise CrewAI
            try:
                crew_result = crew.kickoff()
                analise_crewai = str(crew_result)
            except Exception as e:
                print(f"⚠️ Erro na análise CrewAI (continuando com resultado tradicional): {e}")
                analise_crewai = f"Análise CrewAI não disponível: {str(e)}"
            
            # Compilar resultados finais
            resultado_final = {
                'resultado_tradicional': resultado_tradicional,
                'analise_crewai': analise_crewai,
                'metricas_finais': {
                    'colaboradores': len(self.vr_system.resultado_final) if self.vr_system.resultado_final is not None else 0,
                    'valor_total': self.vr_system.resultado_final['TOTAL'].sum() if self.vr_system.resultado_final is not None else 0,
                    'custo_empresa': self.vr_system.resultado_final['Custo empresa'].sum() if self.vr_system.resultado_final is not None else 0,
                    'arquivo_gerado': resultado_tradicional.get('arquivo