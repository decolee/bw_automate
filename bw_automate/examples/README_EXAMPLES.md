# 📚 BW_AUTOMATE - Guia de Exemplos e Formatos de Entrada

Este diretório contém exemplos completos de como estruturar os arquivos de entrada para o BW_AUTOMATE.

## 📁 Estrutura dos Exemplos

```
examples/
├── README_EXAMPLES.md              # Este arquivo
├── input_formats/                  # Formatos de entrada esperados
│   ├── tables_postgresql.xlsx      # Exemplo de arquivo de tabelas
│   ├── tables_template.xlsx        # Template vazio para suas tabelas
│   └── config_examples/            # Exemplos de configuração
├── sample_airflow_dags/            # Códigos Python de exemplo
│   ├── dag_example_1.py           # DAG com operações básicas
│   ├── dag_example_2.py           # DAG com SQL complexo
│   └── dag_example_3.py           # DAG com operações pandas
├── expected_outputs/               # Exemplos de saída esperada
│   ├── sample_reports/            # Relatórios de exemplo
│   └── sample_analysis.json       # Análise JSON de exemplo
└── troubleshooting/               # Exemplos de problemas comuns
    ├── problematic_files/         # Arquivos que geram problemas
    └── solutions/                 # Soluções para cada problema
```

## 🎯 Casos de Uso Exemplificados

### 1. **Projeto Financeiro** 💰
- Tabelas: contas, transacoes, clientes
- DAGs: etl_financeiro, relatorio_mensal
- Complexidade: Média

### 2. **Projeto E-commerce** 🛒
- Tabelas: produtos, pedidos, usuarios, estoque
- DAGs: sync_produtos, processo_pedidos
- Complexidade: Alta

### 3. **Projeto Analytics** 📊
- Tabelas: events, users, sessions, metrics
- DAGs: daily_analytics, user_segmentation
- Complexidade: Muito Alta

## 📋 Formatos de Entrada Suportados

### 📊 Arquivo de Tabelas PostgreSQL

**Formato Esperado**: `.xlsx` ou `.xls`

**Colunas Obrigatórias**:
- `table_name`: Nome da tabela
- `schema`: Schema da tabela (opcional, padrão: 'public')

**Colunas Opcionais**:
- `description`: Descrição da tabela
- `owner`: Responsável pela tabela
- `criticality`: Nível de criticidade (HIGH, MEDIUM, LOW)
- `environment`: Ambiente (PROD, DEV, STAGING)

### 🐍 Códigos Python Suportados

**Extensões**: `.py`

**Padrões Detectados**:
- SQL direto em strings
- Operações pandas (`read_sql`, `to_sql`)
- SQLAlchemy
- Psycopg2
- F-strings com SQL
- CTEs e subqueries

## ⚡ Como Usar os Exemplos

### 1. **Teste Rápido**
```bash
cd BW_AUTOMATE
python run_analysis.py \
  --source-dir examples/sample_airflow_dags \
  --tables-xlsx examples/input_formats/tables_postgresql.xlsx \
  --output-dir examples/test_output
```

### 2. **Teste com Configuração**
```bash
python run_analysis.py \
  --source-dir examples/sample_airflow_dags \
  --tables-xlsx examples/input_formats/tables_postgresql.xlsx \
  --config examples/input_formats/config_examples/complete_config.json \
  --output-dir examples/test_output \
  --verbose
```

### 3. **Análise de Problemas**
```bash
python run_analysis.py \
  --source-dir examples/troubleshooting/problematic_files \
  --tables-xlsx examples/input_formats/tables_postgresql.xlsx \
  --output-dir examples/debug_output \
  --verbose
```

## 🔧 Personalizando para Seu Projeto

1. **Copie o template de tabelas**:
   ```bash
   cp examples/input_formats/tables_template.xlsx suas_tabelas.xlsx
   ```

2. **Preencha suas tabelas** no Excel

3. **Configure o BW_AUTOMATE**:
   ```bash
   cp examples/input_formats/config_examples/complete_config.json seu_config.json
   ```

4. **Execute a análise**:
   ```bash
   python run_analysis.py \
     --source-dir /seu/projeto/dags \
     --tables-xlsx suas_tabelas.xlsx \
     --config seu_config.json
   ```

## ❓ Dúvidas Frequentes

### ❓ Que formato de arquivo Excel usar?
**R**: Use `.xlsx` (preferível) ou `.xls`. Certifique-se de que a primeira linha contém os cabeçalhos.

### ❓ Como estruturar nomes de tabelas com schema?
**R**: Use duas colunas separadas: `table_name` e `schema`, ou uma coluna `table_name` com formato `schema.table`.

### ❓ O sistema detecta tabelas dinâmicas?
**R**: Sim! O sistema detecta f-strings e concatenação de strings para nomes de tabelas dinâmicos.

### ❓ Como lidar com tabelas temporárias?
**R**: Tabelas com prefixos `temp_`, `tmp_`, `staging_` são automaticamente marcadas como temporárias.

## 📞 Suporte

Se você encontrar problemas com os exemplos:

1. Verifique os logs em `BW_AUTOMATE/logs/`
2. Consulte `examples/troubleshooting/`
3. Execute com `--verbose` para mais detalhes
4. Abra uma issue no GitHub com os logs de erro

---

**💡 Dica**: Sempre teste com os exemplos fornecidos antes de usar com seus dados reais!