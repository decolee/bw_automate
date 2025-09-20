#!/usr/bin/env python3
"""
BW_AUTOMATE - Validador de Instalação
=====================================

Script para validar se todos os arquivos estão presentes e a estrutura está correta.

Autor: Assistant Claude  
Data: 2025-09-20
"""

import os
import sys
import json
from pathlib import Path


def validate_file_structure():
    """Valida estrutura de arquivos do BW_AUTOMATE"""
    print("🔍 Validando estrutura de arquivos...")
    
    required_files = [
        'airflow_table_mapper.py',
        'sql_pattern_extractor.py', 
        'table_mapper_engine.py',
        'report_generator.py',
        'run_analysis.py',
        'config.json',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
        else:
            print(f"   ✅ {file_name}")
    
    if missing_files:
        print(f"\n❌ Arquivos faltando: {', '.join(missing_files)}")
        return False
    
    print("\n✅ Todos os arquivos principais estão presentes")
    return True


def validate_config_file():
    """Valida arquivo de configuração"""
    print("\n🔍 Validando arquivo de configuração...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_sections = [
            'analysis_settings',
            'sql_extraction', 
            'table_matching',
            'reporting',
            'logging'
        ]
        
        for section in required_sections:
            if section in config:
                print(f"   ✅ Seção '{section}' encontrada")
            else:
                print(f"   ❌ Seção '{section}' faltando")
                return False
        
        print("\n✅ Arquivo de configuração válido")
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Erro no JSON de configuração: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Erro ao validar configuração: {e}")
        return False


def validate_python_syntax():
    """Valida sintaxe Python dos módulos principais"""
    print("\n🔍 Validando sintaxe Python...")
    
    python_files = [
        'airflow_table_mapper.py',
        'sql_pattern_extractor.py',
        'table_mapper_engine.py', 
        'report_generator.py',
        'run_analysis.py'
    ]
    
    for file_name in python_files:
        try:
            with open(file_name, 'r') as f:
                content = f.read()
            
            # Compila para verificar sintaxe
            compile(content, file_name, 'exec')
            print(f"   ✅ {file_name}")
            
        except SyntaxError as e:
            print(f"   ❌ {file_name}: Erro de sintaxe na linha {e.lineno}")
            return False
        except Exception as e:
            print(f"   ❌ {file_name}: {e}")
            return False
    
    print("\n✅ Sintaxe Python válida em todos os módulos")
    return True


def check_dependencies():
    """Verifica se dependências podem ser importadas"""
    print("\n🔍 Verificando dependências básicas...")
    
    basic_deps = [
        ('json', 'Biblioteca padrão Python'),
        ('os', 'Biblioteca padrão Python'),
        ('sys', 'Biblioteca padrão Python'),
        ('re', 'Biblioteca padrão Python'),
        ('datetime', 'Biblioteca padrão Python'),
        ('pathlib', 'Biblioteca padrão Python'),
        ('logging', 'Biblioteca padrão Python')
    ]
    
    for module, description in basic_deps:
        try:
            __import__(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - Não encontrado")
            return False
    
    print("\n✅ Dependências básicas disponíveis")
    
    # Verifica dependências externas (sem falhar se não estiverem instaladas)
    print("\n🔍 Verificando dependências externas (opcionais)...")
    
    external_deps = [
        'pandas', 'numpy', 'matplotlib', 'networkx', 
        'plotly', 'fuzzywuzzy', 'sqlparse', 'jinja2'
    ]
    
    available = []
    missing = []
    
    for module in external_deps:
        try:
            __import__(module)
            available.append(module)
            print(f"   ✅ {module}")
        except ImportError:
            missing.append(module)
            print(f"   ⚠️  {module} - Não instalado")
    
    if missing:
        print(f"\n📦 Para instalar dependências faltando:")
        print(f"   pip install {' '.join(missing)}")
        print("   ou execute: pip install -r requirements.txt")
    
    return True


def validate_permissions():
    """Valida permissões de execução"""
    print("\n🔍 Validando permissões...")
    
    executable_files = ['run_analysis.py', 'example_usage.py']
    
    for file_name in executable_files:
        if os.path.exists(file_name):
            if os.access(file_name, os.X_OK):
                print(f"   ✅ {file_name} - Executável")
            else:
                print(f"   ⚠️  {file_name} - Sem permissão de execução")
                print(f"      Execute: chmod +x {file_name}")
        else:
            print(f"   ❌ {file_name} - Arquivo não encontrado")
    
    print("\n✅ Validação de permissões concluída")
    return True


def show_installation_summary():
    """Mostra resumo da instalação"""
    print("\n" + "="*60)
    print("📊 RESUMO DA VALIDAÇÃO BW_AUTOMATE")
    print("="*60)
    
    # Conta arquivos
    total_files = len([f for f in os.listdir('.') if f.endswith('.py')])
    file_size = sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))
    
    print(f"📁 Total de arquivos Python: {total_files}")
    print(f"💾 Tamanho total: {file_size / 1024:.1f} KB")
    print(f"🐍 Versão Python: {sys.version.split()[0]}")
    print(f"📂 Diretório atual: {os.getcwd()}")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("1. Instalar dependências: pip install -r requirements.txt")
    print("2. Preparar arquivo XLSX com lista de tabelas PostgreSQL")
    print("3. Executar análise: python run_analysis.py --help")
    print("4. Consultar documentação: README.md")
    
    print("\n💡 EXEMPLO DE USO:")
    print("python run_analysis.py \\")
    print("  --source-dir /caminho/para/airflow/dags \\")
    print("  --tables-xlsx /caminho/para/tabelas.xlsx")
    
    print("\n✨ BW_AUTOMATE instalado e validado com sucesso!")
    print("="*60)


def main():
    """Função principal de validação"""
    print("🚀 BW_AUTOMATE - VALIDADOR DE INSTALAÇÃO")
    print("="*50)
    
    # Lista de validações
    validations = [
        ("Estrutura de Arquivos", validate_file_structure),
        ("Arquivo de Configuração", validate_config_file), 
        ("Sintaxe Python", validate_python_syntax),
        ("Dependências", check_dependencies),
        ("Permissões", validate_permissions)
    ]
    
    results = []
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erro durante validação '{name}': {e}")
            results.append((name, False))
    
    # Mostra resumo
    print("\n" + "="*50)
    print("📋 RESULTADO DAS VALIDAÇÕES")
    print("="*50)
    
    success_count = 0
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name:.<30} {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 Validações bem-sucedidas: {success_count}/{len(results)}")
    
    if success_count == len(results):
        show_installation_summary()
        return 0
    else:
        print("\n⚠️  Algumas validações falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)