# 🤖 Agente Fiscal - Análise de Notas Fiscais

Sistema inteligente para análise de notas fiscais usando CrewAI e Ollama, com interface web em Streamlit.

## 📋 Pré-requisitos

- Python 3.10.11
- Ollama instalado e rodando
- Arquivos CSV de notas fiscais

## 🚀 Instalação e Configuração

### 1. Clone/Configure o projeto
```bash
# Estrutura do projeto
├── venv/                          
├── knowledge/                     
│   ├── 202401_NFs_Cabecalho.csv
│   └── 202401_NFs_Itens.csv
├── config/                        
│   ├── agents.yaml
│   └── tasks.yaml
├── src/                          
│   ├── __init__.py
│   ├── app.py
│   ├── crew.py
│   └── main.py
├── requirements.txt
├── .env                         
└── README.md
```

### 2. Instale o Ollama
```bash
# Windows: Baixe de https://ollama.ai/download
# Após instalar, execute:
ollama serve
ollama pull llama3.2:3b
```

### 3. Configure o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
O arquivo `.env` já está configurado. Ajuste os caminhos se necessário:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
CSV_CABECALHO_PATH=C:/Projetos/Agent/knowledge/202401_NFs_Cabecalho.csv
CSV_ITENS_PATH=C:/Projetos/Agent/knowledge/202401_NFs_Itens.csv
```

## 🎯 Como Usar

### Método 1: Execução Automática
```bash
cd src
python main.py
```

### Método 2: Execução Manual
```bash
cd src
streamlit run app.py
```

## 💡 Exemplos de Perguntas

- "Qual o valor total das notas fiscais?"
- "Quais são os principais fornecedores?"
- "Quantas notas foram emitidas em janeiro de 2024?"
- "Qual o produto mais vendido?"
- "Há alguma inconsistência nos dados?"
- "Qual o valor médio por nota fiscal?"

## 🔧 Estrutura dos Arquivos

### `src/main.py`
- Arquivo principal com verificações automáticas
- Instala dependências se necessário
- Verifica se Ollama está rodando
- Inicia o Streamlit

### `src/crew.py`
- Configura o agente CrewAI
- Carrega e processa os dados CSV
- Executa as análises fiscais

### `src/app.py`
- Interface web do Streamlit
- Campo para perguntas
- Exibe resultados das análises

### `src/__init__.py`
- Torna a pasta src um pacote Python

## 🛠️ Solução de Problemas

### Ollama não conecta
```bash
# Verifique se está rodando:
curl http://localhost:11434/api/tags

# Se não estiver, inicie:
ollama serve
```

### Erro de dependências
```bash
# Reinstale as dependências:
pip install -r requirements.txt --force-reinstall
```

### Arquivos CSV não encontrados
- Verifique se os arquivos estão na pasta `knowledge/`
- Confirme os caminhos no arquivo `.env`

### Erro de encoding nos CSV
- Certifique-se que os CSVs estão em UTF-8
- Se necessário, converta: `pandas.read_csv(file, encoding='latin-1')`

## 📊 Funcionalidades

- ✅ Análise automática de notas fiscais
- ✅ Interface web intuitiva
- ✅ Processamento de múltiplos CSVs
- ✅ Respostas contextualizadas
- ✅ Verificações automáticas de sistema
- ✅ Suporte a LLM local (Ollama)

## 🔄 Atualizações

Para atualizar o sistema:
1. Atualize os arquivos CSV
2. Reinicie o Streamlit
3. Os dados serão recarregados automaticamente

## 📞 Suporte

Se encontrar problemas:
1. Verifique se o Ollama está rodando
2. Confirme se os arquivos CSV existem
3. Verifique as dependências do Python
4. Consulte os logs no terminal

---
*Desenvolvido com CrewAI, Streamlit e Ollama* 🚀