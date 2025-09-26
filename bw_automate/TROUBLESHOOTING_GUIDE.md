# 🚨 BW_AUTOMATE - Guia de Solução de Problemas

Este guia abrangente ajuda a resolver problemas comuns e otimizar o uso do BW_AUTOMATE.

## 📋 Índice

- [Problemas de Instalação](#-problemas-de-instalação)
- [Problemas de Entrada](#-problemas-de-entrada)
- [Problemas de Análise](#-problemas-de-análise)
- [Problemas de Performance](#-problemas-de-performance)
- [Problemas de Relatórios](#-problemas-de-relatórios)
- [Problemas de Configuração](#-problemas-de-configuração)
- [Erros Comuns](#-erros-comuns)
- [Diagnostico Avançado](#-diagnóstico-avançado)
- [FAQ](#-perguntas-frequentes)

---

## 🔧 Problemas de Instalação

### ❌ Erro: "ModuleNotFoundError: No module named 'pandas'"

**Problema**: Dependências não instaladas.

**Soluções**:
```bash
# Instala dependências básicas
pip install pandas numpy networkx fuzzywuzzy

# Instala dependências completas
pip install -r BW_AUTOMATE/requirements.txt

# Para ambiente conda
conda install pandas numpy networkx
pip install fuzzywuzzy python-levenshtein
```

**Verificação**:
```bash
python -c "import pandas, numpy, networkx; print('Dependências OK')"
```

### ❌ Erro: "ImportError: No module named 'plotly'"

**Problema**: Dependências opcionais não instaladas.

**Impacto**: Gráficos interativos não funcionarão.

**Soluções**:
```bash
# Instala dependências de visualização
pip install plotly matplotlib seaborn

# Ou instala tudo
pip install plotly matplotlib seaborn rich openpyxl psycopg2-binary
```

**Workaround**: Use configuração sem gráficos:
```json
{
  "reporting": {
    "generate_interactive_charts": false,
    "export_to_powerbi": false
  }
}
```

### ❌ Erro: "Permission denied" ao instalar pacotes

**Problema**: Problemas de permissão.

**Soluções**:
```bash
# Instala para usuário atual
pip install --user -r requirements.txt

# Ou usa ambiente virtual
python -m venv bw_automate_env
source bw_automate_env/bin/activate  # Linux/Mac
# ou
bw_automate_env\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

## 📁 Problemas de Entrada

### ❌ Erro: "FileNotFoundError: Arquivo de tabelas não encontrado"

**Problema**: Caminho incorreto para arquivo Excel.

**Verificação**:
```bash
# Verifica se arquivo existe
ls -la /caminho/para/tabelas.xlsx

# Verifica permissões
file /caminho/para/tabelas.xlsx
```

**Soluções**:
```bash
# Usa caminho absoluto
python run_analysis.py \
  --source-dir /caminho/completo/para/dags \
  --tables-xlsx /caminho/completo/para/tabelas.xlsx

# Verifica a partir do diretório atual
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx
```

### ❌ Erro: "Nenhum arquivo Python encontrado"

**Problema**: Diretório não contém arquivos .py.

**Verificação**:
```bash
# Lista arquivos Python no diretório
find /caminho/para/dags -name "*.py" -type f

# Verifica estrutura do diretório
tree /caminho/para/dags
```

**Soluções**:
1. **Diretório correto**: Aponte para diretório com DAGs
2. **Extensões**: Verifique se arquivos têm extensão .py
3. **Subdiretórios**: Use diretório pai se DAGs estão em subpastas

### ❌ Erro: "Excel file format cannot be determined"

**Problema**: Arquivo Excel corrompido ou formato inválido.

**Verificação**:
```python
import pandas as pd
try:
    df = pd.read_excel('tabelas.xlsx')
    print(f"Arquivo OK: {len(df)} linhas")
except Exception as e:
    print(f"Erro: {e}")
```

**Soluções**:
1. **Recriar arquivo**: Use template fornecido
2. **Converter formato**: Salve como .xlsx no Excel
3. **Usar CSV**: Converta para CSV se problema persistir

```python
# Exemplo de conversão
import pandas as pd
df = pd.read_csv('tabelas.csv')
df.to_excel('tabelas.xlsx', index=False)
```

---

## 🔍 Problemas de Análise

### ❌ Erro: "Taxa de match muito baixa (< 50%)"

**Problema**: Poucas tabelas encontradas correspondem ao catálogo.

**Diagnóstico**:
```bash
# Executa com logs detalhados
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --verbose
```

**Possíveis Causas**:
1. **Nomenclatura inconsistente**: Tabelas têm nomes diferentes
2. **Schemas diferentes**: Código usa schemas não mapeados
3. **Threshold muito alto**: Critério de match muito rigoroso

**Soluções**:
```json
{
  "table_matching": {
    "fuzzy_match_threshold": 70,
    "remove_prefixes": ["tmp_", "temp_", "dev_"],
    "case_sensitive": false
  }
}
```

### ❌ Warning: "Muitas tabelas temporárias detectadas"

**Problema**: Alto uso de tabelas temporárias.

**Análise**:
- Verifique se padrões de temp estão corretos
- Confirme se são realmente temporárias

**Configuração**:
```json
{
  "analysis_settings": {
    "include_temp_tables": false
  },
  "table_matching": {
    "remove_prefixes": ["tmp_", "temp_", "staging_", "dev_"]
  }
}
```

### ❌ Erro: "SQL statement parsing failed"

**Problema**: SQL mal formado quebra análise.

**Exemplo de SQL problemático**:
```sql
-- SQL mal formado
SELECT usuario_id, nome FROM usuarios WHERE ativo = true AND
-- Falta fechamento
```

**Soluções**:
1. **Use arquivos de exemplo**: Teste com DAGs limpos primeiro
2. **Modo tolerante**: Configure para ignorar erros

```json
{
  "sql_extraction": {
    "ignore_parsing_errors": true,
    "minimum_sql_length": 20
  }
}
```

---

## ⚡ Problemas de Performance

### ❌ Erro: "MemoryError: Unable to allocate array"

**Problema**: Insuficiência de memória.

**Soluções**:
```json
{
  "performance": {
    "memory_limit_mb": 1024,
    "parallel_processing": false,
    "chunk_size": 500
  },
  "analysis_settings": {
    "max_files_to_analyze": 500
  }
}
```

**Execução otimizada**:
```bash
# Processa em lotes menores
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --config minimal_config.json
```

### ❌ Lentidão: Análise muito demorada

**Diagnóstico**:
```bash
# Executa com profiling
time python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --verbose
```

**Otimizações**:
```json
{
  "analysis_settings": {
    "max_files_to_analyze": 1000,
    "enable_advanced_sql_analysis": false
  },
  "reporting": {
    "generate_lineage_visualization": false,
    "export_to_powerbi": false
  },
  "performance": {
    "enable_caching": true,
    "parallel_processing": true,
    "max_workers": 2
  }
}
```

---

## 📊 Problemas de Relatórios

### ❌ Erro: "Template not found" em relatórios HTML

**Problema**: Módulos de visualização não disponíveis.

**Verificação**:
```python
try:
    import plotly
    print("Plotly disponível")
except ImportError:
    print("Plotly não disponível")
```

**Soluções**:
```bash
# Instala dependências de visualização
pip install plotly matplotlib seaborn

# Ou usa modo básico
```

**Configuração sem gráficos**:
```json
{
  "reporting": {
    "generate_executive_dashboard": true,
    "generate_technical_report": true,
    "generate_interactive_charts": false
  }
}
```

### ❌ Relatórios HTML vazios ou malformados

**Problema**: Dados insuficientes ou erros de template.

**Diagnóstico**:
1. Verifique se análise encontrou dados
2. Confirme se templates estão íntegros

**Soluções**:
```bash
# Regenera relatórios
python run_analysis.py \
  --source-dir ./examples/sample_airflow_dags \
  --tables-xlsx ./examples/input_formats/tables_postgresql.xlsx \
  --output-dir ./test_reports
```

---

## ⚙️ Problemas de Configuração

### ❌ Erro: "Invalid JSON in config file"

**Problema**: Sintaxe incorreta no arquivo de configuração.

**Verificação**:
```bash
# Valida JSON
python -c "import json; print(json.load(open('config.json')))"

# Ou usa ferramenta online
# jsonlint.com
```

**Problemas comuns**:
```json
{
  // ❌ Comentários não são válidos em JSON
  "fuzzy_match_threshold": 80,
  "schemas_to_analyze": ["public", "staging",] // ❌ Vírgula extra
}
```

**JSON correto**:
```json
{
  "fuzzy_match_threshold": 80,
  "schemas_to_analyze": ["public", "staging"]
}
```

### ❌ Configurações não surtem efeito

**Problema**: Configuração não está sendo carregada.

**Verificação**:
```bash
# Especifica configuração explicitamente
python run_analysis.py \
  --config /caminho/completo/para/config.json \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --verbose
```

**Debug de configuração**:
```json
{
  "logging": {
    "log_level": "DEBUG",
    "log_to_console": true
  }
}
```

---

## 🚨 Erros Comuns

### 1. "UnicodeDecodeError"

**Causa**: Problemas de encoding em arquivos.

**Solução**:
```bash
# Converte encoding
iconv -f ISO-8859-1 -t UTF-8 arquivo.py > arquivo_utf8.py

# Ou especifica encoding
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --encoding utf-8
```

### 2. "Permission denied" ao criar relatórios

**Causa**: Sem permissão no diretório de saída.

**Solução**:
```bash
# Cria diretório com permissões
mkdir -p ./meus_relatorios
chmod 755 ./meus_relatorios

# Especifica diretório
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --output-dir ./meus_relatorios
```

### 3. "ConnectionError" com PostgreSQL

**Causa**: Tentativa de conexão com banco.

**Nota**: BW_AUTOMATE analisa código, não conecta ao banco.

**Solução**: Ignore warnings de conexão.

---

## 🔍 Diagnóstico Avançado

### Script de Diagnóstico

```python
#!/usr/bin/env python3
"""
Script de diagnóstico para BW_AUTOMATE
"""

import sys
import os
import json
from pathlib import Path

def diagnostic_check():
    print("🔍 BW_AUTOMATE - Diagnóstico do Sistema")
    print("=" * 50)
    
    # Versão Python
    print(f"Python: {sys.version}")
    
    # Dependências
    dependencies = ['pandas', 'numpy', 'networkx', 'fuzzywuzzy']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: OK")
        except ImportError:
            print(f"❌ {dep}: FALTANDO")
    
    # Dependências opcionais
    optional_deps = ['plotly', 'matplotlib', 'seaborn', 'rich']
    for dep in optional_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}: OK")
        except ImportError:
            print(f"⚠️ {dep}: OPCIONAL - FALTANDO")
    
    # Arquivos de exemplo
    examples_dir = Path("examples")
    if examples_dir.exists():
        print(f"✅ Diretório de exemplos: OK")
        
        excel_file = examples_dir / "input_formats" / "tables_postgresql.xlsx"
        if excel_file.exists():
            print(f"✅ Arquivo Excel de exemplo: OK")
        else:
            print(f"❌ Arquivo Excel de exemplo: FALTANDO")
    else:
        print(f"❌ Diretório de exemplos: FALTANDO")
    
    print("\n🏁 Diagnóstico concluído!")

if __name__ == "__main__":
    diagnostic_check()
```

### Teste de Funcionalidade Básica

```bash
# Executa teste com exemplos
python run_analysis.py \
  --source-dir examples/sample_airflow_dags \
  --tables-xlsx examples/input_formats/tables_postgresql.xlsx \
  --config examples/input_formats/config_examples/debug_config.json \
  --output-dir test_output \
  --verbose
```

### Análise de Logs

```bash
# Localiza logs
find . -name "*.log" -type f -mtime -1

# Examina logs recentes
tail -f BW_AUTOMATE/logs/bw_automate_*.log

# Busca erros específicos
grep -i "error\|exception\|failed" BW_AUTOMATE/logs/*.log
```

---

## ❓ Perguntas Frequentes

### Q: O BW_AUTOMATE conecta ao banco PostgreSQL?
**R**: Não! O BW_AUTOMATE analisa apenas o código Python/SQL. Não faz conexões com banco de dados.

### Q: Por que algumas tabelas não são detectadas?
**R**: Possíveis motivos:
- SQL dinâmico complexo
- Tabelas em schemas não mapeados
- Nomenclatura inconsistente
- Operações em código não-SQL (ex: APIs)

### Q: Como melhorar a taxa de match?
**R**: 
1. Reduza `fuzzy_match_threshold`
2. Adicione prefixos/sufixos para remoção
3. Inclua todos os schemas no arquivo Excel
4. Use modo case-insensitive

### Q: É possível analisar outros SGBDs além de PostgreSQL?
**R**: Atualmente focado em PostgreSQL, mas pode detectar SQL genérico. Para outros SGBDs, ajuste padrões de detecção.

### Q: Como processar projetos muito grandes?
**R**:
1. Use `max_files_to_analyze`
2. Desabilite análises avançadas
3. Processe por subdiretórios
4. Use configuração de performance

### Q: Os relatórios podem ser customizados?
**R**: Sim! Edite templates HTML ou crie novos geradores baseados nos dados JSON exportados.

### Q: Como integrar com CI/CD?
**R**: Use configuração automatizada:
```bash
python run_analysis.py \
  --source-dir $CI_PROJECT_DIR/dags \
  --tables-xlsx $CI_PROJECT_DIR/schemas/tables.xlsx \
  --config $CI_PROJECT_DIR/.bw_automate_config.json \
  --output-dir $CI_PROJECT_DIR/reports
```

---

## 📞 Suporte Adicional

### Coletando Informações para Suporte

Se nenhuma solução funcionou, colete as seguintes informações:

```bash
# Informações do sistema
python --version
pip list | grep -E "(pandas|numpy|networkx|plotly)"

# Execução com debug máximo
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --verbose > debug_output.txt 2>&1

# Estrutura dos arquivos
find ./dags -name "*.py" | head -10
ls -la ./tabelas.xlsx
```

### Reportando Problemas

Ao reportar problemas, inclua:
1. **Versão do Python**: `python --version`
2. **Sistema operacional**: Linux/Windows/Mac
3. **Comando executado**: Comando completo usado
4. **Logs de erro**: Output completo do erro
5. **Arquivo de configuração**: Se usando configuração customizada
6. **Dados de exemplo**: Se possível, exemplo que reproduz o problema

---

**💡 Lembre-se**: A maioria dos problemas pode ser resolvida com configuração adequada e validação de entradas. Use sempre os exemplos fornecidos para testar primeiro!