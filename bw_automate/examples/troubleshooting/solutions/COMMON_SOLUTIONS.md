# 🔧 Soluções para Problemas Comuns

Este arquivo contém soluções práticas para os problemas mais frequentes encontrados ao usar o BW_AUTOMATE.

## 🚀 Soluções Rápidas

### 1. Análise com Baixa Taxa de Match

**Problema**: "Taxa de match: 23.4%" - poucas tabelas reconhecidas.

**Solução Imediata**:
```bash
# Use configuração mais permissiva
python run_analysis.py \
  --source-dir ./dags \
  --tables-xlsx ./tabelas.xlsx \
  --config examples/input_formats/config_examples/permissive_config.json
```

**Arquivo `permissive_config.json`**:
```json
{
  "table_matching": {
    "fuzzy_match_threshold": 60,
    "remove_prefixes": ["tmp_", "temp_", "staging_", "dev_", "test_"],
    "remove_suffixes": ["_temp", "_tmp", "_bak", "_old", "_dev"],
    "case_sensitive": false,
    "normalize_names": true
  },
  "analysis_settings": {
    "include_temp_tables": false,
    "schemas_to_analyze": ["public", "staging", "reports", "analytics", "financeiro", "ecommerce", "development"]
  }
}
```

### 2. Erro de Memória em Projetos Grandes

**Problema**: "MemoryError" ao analisar muitos arquivos.

**Solução**:
```json
{
  "performance": {
    "memory_limit_mb": 512,
    "chunk_size": 100,
    "enable_caching": false
  },
  "analysis_settings": {
    "max_files_to_analyze": 200,
    "enable_advanced_sql_analysis": false
  },
  "reporting": {
    "generate_lineage_visualization": false,
    "export_to_powerbi": false
  }
}
```

### 3. Dependências Faltando

**Problema**: Erros de importação.

**Solução Completa**:
```bash
# Instala tudo de uma vez
pip install pandas numpy networkx fuzzywuzzy python-levenshtein \
           plotly matplotlib seaborn rich openpyxl psycopg2-binary \
           pyyaml

# Verifica instalação
python -c "import pandas, numpy, networkx, fuzzywuzzy, plotly; print('OK')"
```

### 4. SQL Complexo Não Detectado

**Problema**: Queries complexas não são reconhecidas.

**Configuração Avançada**:
```json
{
  "sql_extraction": {
    "include_dynamic_sql": true,
    "parse_multiline_strings": true,
    "minimum_sql_length": 5,
    "analyze_f_strings": true,
    "detect_cte_patterns": true,
    "identify_subqueries": true,
    "parse_window_functions": true
  }
}
```

### 5. Arquivo Excel com Problemas

**Problema**: "Excel file format cannot be determined".

**Solução Passo-a-passo**:
```python
# 1. Verifica o arquivo
import pandas as pd

try:
    df = pd.read_excel('tabelas.xlsx')
    print(f"✅ Arquivo OK: {len(df)} linhas, {len(df.columns)} colunas")
    print("Colunas:", list(df.columns))
except Exception as e:
    print(f"❌ Erro: {e}")
    
    # 2. Tenta com diferentes engines
    try:
        df = pd.read_excel('tabelas.xlsx', engine='openpyxl')
        print("✅ Funcionou com engine openpyxl")
    except:
        print("❌ Problema persiste")

# 3. Cria arquivo limpo se necessário
if 'df' in locals():
    # Limpa dados
    df = df.dropna(subset=['table_name'])
    df = df.drop_duplicates()
    
    # Salva arquivo limpo
    df.to_excel('tabelas_limpo.xlsx', index=False)
    print("✅ Arquivo limpo salvo como 'tabelas_limpo.xlsx'")
```

## 🛠️ Scripts de Correção Automática

### Script 1: Limpeza de Arquivo Excel

```python
#!/usr/bin/env python3
"""
Script para limpar e validar arquivo Excel de tabelas
"""

import pandas as pd
import re
import sys

def clean_excel_file(input_file, output_file=None):
    """Limpa arquivo Excel de tabelas"""
    
    if not output_file:
        output_file = input_file.replace('.xlsx', '_limpo.xlsx')
    
    print(f"🔍 Lendo arquivo: {input_file}")
    
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    print(f"📊 Dados originais: {len(df)} linhas, {len(df.columns)} colunas")
    
    # 1. Remove linhas com table_name vazio
    df = df.dropna(subset=['table_name'])
    print(f"🧹 Após remover vazios: {len(df)} linhas")
    
    # 2. Remove duplicatas
    df = df.drop_duplicates(subset=['table_name'])
    print(f"🧹 Após remover duplicatas: {len(df)} linhas")
    
    # 3. Valida nomes de tabelas
    valid_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    invalid_tables = []
    
    for idx, table_name in df['table_name'].items():
        if not re.match(valid_pattern, str(table_name)):
            invalid_tables.append(table_name)
    
    if invalid_tables:
        print(f"⚠️ Tabelas com nomes inválidos: {invalid_tables[:5]}")
        # Remove ou corrige
        df = df[df['table_name'].str.match(valid_pattern, na=False)]
        print(f"🧹 Após validação: {len(df)} linhas")
    
    # 4. Adiciona colunas padrão se não existirem
    if 'schema' not in df.columns:
        df['schema'] = 'public'
        print("➕ Adicionada coluna 'schema' com valor 'public'")
    
    if 'description' not in df.columns:
        df['description'] = ''
        print("➕ Adicionada coluna 'description' vazia")
    
    # 5. Salva arquivo limpo
    try:
        df.to_excel(output_file, index=False)
        print(f"✅ Arquivo limpo salvo: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python clean_excel.py arquivo.xlsx [arquivo_saida.xlsx]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = clean_excel_file(input_file, output_file)
    sys.exit(0 if success else 1)
```

### Script 2: Diagnóstico Completo

```python
#!/usr/bin/env python3
"""
Script de diagnóstico completo do BW_AUTOMATE
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica versão do Python"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info >= (3, 8):
        print(f"✅ Python {version} (OK)")
        return True
    else:
        print(f"❌ Python {version} (Necessário 3.8+)")
        return False

def check_dependencies():
    """Verifica dependências"""
    required = ['pandas', 'numpy', 'networkx', 'fuzzywuzzy']
    optional = ['plotly', 'matplotlib', 'seaborn', 'rich', 'openpyxl']
    
    all_ok = True
    
    print("\n📦 Dependências Obrigatórias:")
    for dep in required:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - INSTALE COM: pip install {dep}")
            all_ok = False
    
    print("\n📦 Dependências Opcionais:")
    for dep in optional:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"⚠️ {dep} - pip install {dep}")
    
    return all_ok

def check_examples():
    """Verifica arquivos de exemplo"""
    examples_dir = Path("examples")
    
    if not examples_dir.exists():
        print("\n❌ Diretório 'examples' não encontrado")
        return False
    
    required_files = [
        "input_formats/tables_postgresql.xlsx",
        "sample_airflow_dags/dag_example_1_basic.py",
        "input_formats/config_examples/complete_config.json"
    ]
    
    print("\n📁 Arquivos de Exemplo:")
    all_ok = True
    
    for file_path in required_files:
        full_path = examples_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_ok = False
    
    return all_ok

def run_basic_test():
    """Executa teste básico"""
    print("\n🧪 Executando Teste Básico...")
    
    cmd = [
        sys.executable, "run_analysis.py",
        "--source-dir", "examples/sample_airflow_dags",
        "--tables-xlsx", "examples/input_formats/tables_postgresql.xlsx",
        "--output-dir", "test_diagnostic_output"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Teste básico passou!")
            return True
        else:
            print("❌ Teste básico falhou:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Teste básico demorou muito (timeout)")
        return False
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal de diagnóstico"""
    print("🔍 BW_AUTOMATE - Diagnóstico Completo")
    print("=" * 50)
    
    checks = [
        ("Versão Python", check_python_version),
        ("Dependências", check_dependencies),
        ("Arquivos de Exemplo", check_examples),
        ("Teste Básico", run_basic_test)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔍 {name}...")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("🎉 Sistema está funcionando perfeitamente!")
        print("\n💡 Próximos passos:")
        print("1. Execute com seus dados reais")
        print("2. Consulte o README para uso avançado")
        print("3. Configure conforme necessário")
    else:
        print("⚠️ Algumas verificações falharam")
        print("\n💡 Ações recomendadas:")
        print("1. Instale dependências faltando")
        print("2. Verifique arquivos de exemplo")
        print("3. Consulte TROUBLESHOOTING_GUIDE.md")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 📋 Checklist de Problemas

### Antes de Executar

- [ ] Python 3.8+ instalado
- [ ] Dependências obrigatórias instaladas (`pip install pandas numpy networkx fuzzywuzzy`)
- [ ] Arquivo Excel existe e é legível
- [ ] Diretório de código contém arquivos .py
- [ ] Permissões de leitura/escrita adequadas

### Se Taxa de Match Baixa

- [ ] Reduza `fuzzy_match_threshold` para 60-70
- [ ] Configure `remove_prefixes` e `remove_suffixes`
- [ ] Use `case_sensitive: false`
- [ ] Inclua todos os schemas no Excel
- [ ] Verifique se tabelas no código existem no catálogo

### Se Problemas de Performance

- [ ] Limite `max_files_to_analyze`
- [ ] Desabilite `enable_advanced_sql_analysis`
- [ ] Use `memory_limit_mb` menor
- [ ] Desabilite visualizações pesadas
- [ ] Processe em lotes menores

### Se Relatórios Não Geram

- [ ] Instale dependências de visualização (`pip install plotly matplotlib`)
- [ ] Verifique permissões do diretório de saída
- [ ] Use configuração básica primeiro
- [ ] Verifique se análise encontrou dados

## 🔗 Links Úteis

- **Arquivo de configuração completa**: `examples/input_formats/config_examples/complete_config.json`
- **Configuração mínima**: `examples/input_formats/config_examples/minimal_config.json`
- **Configuração de debug**: `examples/input_formats/config_examples/debug_config.json`
- **Template Excel**: `examples/input_formats/tables_template.xlsx`
- **DAGs de exemplo**: `examples/sample_airflow_dags/`

---

**💡 Dica Final**: Sempre teste com os exemplos fornecidos antes de usar seus dados reais. Isso ajuda a identificar se o problema é de configuração ou nos seus dados.