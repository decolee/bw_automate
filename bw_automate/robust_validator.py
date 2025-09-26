#!/usr/bin/env python3
"""
Robust Validator v2.0
======================

Sistema de validação robusto para entrada e dados do BW_AUTOMATE.
Inclui validações de:
- Arquivos de entrada
- Formatos de dados
- Integridade de dados
- Configurações
- Compatibilidade de sistema

Principais funcionalidades:
- Validação preventiva
- Mensagens de erro claras
- Sugestões de correção
- Recuperação automática
- Relatórios de validação

Autor: BW_AUTOMATE v2.0
Data: 2025-09-20
"""

import os
import json
import pandas as pd
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import importlib.util

@dataclass
class ValidationResult:
    """Resultado de uma validação"""
    is_valid: bool
    error_message: str = ""
    warning_message: str = ""
    suggestion: str = ""
    auto_fix_applied: bool = False
    severity: str = "info"  # info, warning, error, critical

@dataclass
class ValidationReport:
    """Relatório completo de validação"""
    overall_status: str  # PASS, WARN, FAIL
    total_validations: int
    passed_validations: int
    failed_validations: int
    warnings_count: int
    results: List[ValidationResult]
    auto_fixes_applied: int
    suggestions_count: int

class RobustValidator:
    """
    Validador robusto para todas as entradas do BW_AUTOMATE
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o validador
        
        Args:
            config: Configurações do validador
        """
        self.config = config or {}
        self.setup_logging()
        
        # Configurações de validação
        self.validation_config = {
            'max_file_size_mb': self.config.get('max_file_size_mb', 100),
            'max_files_count': self.config.get('max_files_count', 10000),
            'required_python_version': self.config.get('required_python_version', '3.8'),
            'auto_fix_enabled': self.config.get('auto_fix_enabled', True),
            'strict_mode': self.config.get('strict_mode', False)
        }
        
        # Extensões de arquivo suportadas
        self.supported_extensions = {
            'python': ['.py'],
            'excel': ['.xlsx', '.xls'],
            'config': ['.json', '.yaml', '.yml'],
            'data': ['.csv', '.json', '.parquet']
        }
        
        # Padrões de validação
        self.validation_patterns = {
            'table_name': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
            'schema_name': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
            'file_name': r'^[a-zA-Z0-9_\-\.]+$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        }
        
        # Dependências opcionais
        self.optional_dependencies = {
            'plotly': 'Gráficos interativos avançados',
            'matplotlib': 'Gráficos estáticos',
            'seaborn': 'Visualizações estatísticas',
            'rich': 'Interface CLI aprimorada',
            'openpyxl': 'Leitura de arquivos Excel',
            'psycopg2': 'Conexão com PostgreSQL'
        }
        
    def setup_logging(self):
        """Configura logging para o validador"""
        self.logger = logging.getLogger('RobustValidator')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def validate_system_requirements(self) -> ValidationResult:
        """Valida requisitos do sistema"""
        
        try:
            # Versão do Python
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            required_version = self.validation_config['required_python_version']
            
            if python_version < required_version:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Python {python_version} encontrado, mas é necessário Python {required_version} ou superior",
                    suggestion=f"Atualize sua instalação do Python para a versão {required_version} ou superior",
                    severity="critical"
                )
            
            # Dependências obrigatórias
            required_packages = ['pandas', 'numpy', 'networkx']
            missing_packages = []
            
            for package in required_packages:
                try:
                    importlib.import_module(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Pacotes obrigatórios não encontrados: {', '.join(missing_packages)}",
                    suggestion=f"Instale com: pip install {' '.join(missing_packages)}",
                    severity="critical"
                )
            
            # Dependências opcionais
            missing_optional = []
            for package, description in self.optional_dependencies.items():
                try:
                    importlib.import_module(package)
                except ImportError:
                    missing_optional.append(f"{package} ({description})")
            
            warning_msg = ""
            if missing_optional:
                warning_msg = f"Dependências opcionais não encontradas: {', '.join(missing_optional[:3])}"
                if len(missing_optional) > 3:
                    warning_msg += f" e mais {len(missing_optional) - 3}"
            
            return ValidationResult(
                is_valid=True,
                warning_message=warning_msg,
                suggestion="Para funcionalidades completas, instale: pip install plotly matplotlib seaborn rich openpyxl psycopg2-binary",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Erro ao validar requisitos do sistema: {str(e)}",
                severity="critical"
            )
    
    def validate_input_directory(self, directory_path: str) -> ValidationResult:
        """Valida diretório de entrada"""
        
        try:
            path_obj = Path(directory_path)
            
            # Verifica se existe
            if not path_obj.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Diretório não encontrado: {directory_path}",
                    suggestion="Verifique se o caminho está correto e se você tem permissões de acesso",
                    severity="error"
                )
            
            # Verifica se é diretório
            if not path_obj.is_dir():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Caminho não é um diretório: {directory_path}",
                    suggestion="Especifique um diretório válido, não um arquivo",
                    severity="error"
                )
            
            # Verifica permissões de leitura
            if not os.access(directory_path, os.R_OK):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Sem permissão de leitura no diretório: {directory_path}",
                    suggestion="Verifique as permissões do diretório",
                    severity="error"
                )
            
            # Conta arquivos Python
            python_files = list(path_obj.rglob("*.py"))
            
            if not python_files:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Nenhum arquivo Python (.py) encontrado em: {directory_path}",
                    suggestion="Verifique se o diretório contém arquivos Python ou especifique o diretório correto",
                    severity="error"
                )
            
            # Verifica se há muitos arquivos
            max_files = self.validation_config['max_files_count']
            if len(python_files) > max_files:
                return ValidationResult(
                    is_valid=True,
                    warning_message=f"Muitos arquivos encontrados ({len(python_files)}), análise limitada a {max_files}",
                    suggestion=f"Para analisar todos os arquivos, aumente 'max_files_count' na configuração",
                    severity="warning"
                )
            
            # Verifica tamanho total
            total_size = sum(f.stat().st_size for f in python_files if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            max_size = self.validation_config['max_file_size_mb']
            
            if total_size_mb > max_size:
                return ValidationResult(
                    is_valid=True,
                    warning_message=f"Tamanho total dos arquivos ({total_size_mb:.1f}MB) excede limite recomendado ({max_size}MB)",
                    suggestion="Considere analisar subdiretórios menores ou aumentar o limite",
                    severity="warning"
                )
            
            return ValidationResult(
                is_valid=True,
                suggestion=f"Diretório válido com {len(python_files)} arquivos Python ({total_size_mb:.1f}MB)",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Erro ao validar diretório: {str(e)}",
                severity="error"
            )
    
    def validate_excel_file(self, file_path: str) -> ValidationResult:
        """Valida arquivo Excel de tabelas"""
        
        try:
            path_obj = Path(file_path)
            
            # Verifica se existe
            if not path_obj.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Arquivo Excel não encontrado: {file_path}",
                    suggestion="Verifique se o caminho está correto",
                    severity="error"
                )
            
            # Verifica extensão
            if path_obj.suffix.lower() not in self.supported_extensions['excel']:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Extensão de arquivo não suportada: {path_obj.suffix}",
                    suggestion="Use arquivos .xlsx ou .xls",
                    severity="error"
                )
            
            # Verifica se pode ler o arquivo
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Erro ao ler arquivo Excel: {str(e)}",
                    suggestion="Verifique se o arquivo não está corrompido ou aberto em outro programa",
                    severity="error"
                )
            
            # Validações do conteúdo
            validation_issues = []
            auto_fixes = []
            
            # Verifica se não está vazio
            if df.empty:
                return ValidationResult(
                    is_valid=False,
                    error_message="Arquivo Excel está vazio",
                    suggestion="Adicione dados ao arquivo Excel",
                    severity="error"
                )
            
            # Verifica colunas obrigatórias
            required_columns = ['table_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Colunas obrigatórias não encontradas: {', '.join(missing_columns)}",
                    suggestion="Adicione a coluna 'table_name' ao arquivo Excel",
                    severity="error"
                )
            
            # Verifica valores nulos na coluna obrigatória
            null_tables = df['table_name'].isnull().sum()
            if null_tables > 0:
                validation_issues.append(f"{null_tables} linhas com table_name vazio")
                if self.validation_config['auto_fix_enabled']:
                    df = df.dropna(subset=['table_name'])
                    auto_fixes.append("Removidas linhas com table_name vazio")
            
            # Verifica nomes de tabelas válidos
            invalid_names = []
            table_pattern = self.validation_patterns['table_name']
            
            for idx, table_name in df['table_name'].items():
                if isinstance(table_name, str) and not re.match(table_pattern, table_name):
                    invalid_names.append(table_name)
            
            if invalid_names:
                validation_issues.append(f"Nomes de tabela inválidos: {', '.join(invalid_names[:5])}")
                if len(invalid_names) > 5:
                    validation_issues.append(f"... e mais {len(invalid_names) - 5}")
            
            # Verifica duplicatas
            duplicates = df['table_name'].duplicated().sum()
            if duplicates > 0:
                validation_issues.append(f"{duplicates} nomes de tabela duplicados")
                if self.validation_config['auto_fix_enabled']:
                    df = df.drop_duplicates(subset=['table_name'])
                    auto_fixes.append("Removidas linhas duplicadas")
            
            # Verifica schema (se presente)
            if 'schema' in df.columns:
                invalid_schemas = []
                schema_pattern = self.validation_patterns['schema_name']
                
                for idx, schema in df['schema'].dropna().items():
                    if isinstance(schema, str) and not re.match(schema_pattern, schema):
                        invalid_schemas.append(schema)
                
                if invalid_schemas:
                    validation_issues.append(f"Nomes de schema inválidos: {', '.join(invalid_schemas[:3])}")
            
            # Determina resultado
            has_errors = any("inválidos" in issue for issue in validation_issues)
            
            if has_errors and self.validation_config['strict_mode']:
                return ValidationResult(
                    is_valid=False,
                    error_message="; ".join(validation_issues),
                    suggestion="Corrija os nomes inválidos de tabelas/schemas",
                    severity="error"
                )
            
            warning_msg = "; ".join(validation_issues) if validation_issues else ""
            auto_fix_msg = "; ".join(auto_fixes) if auto_fixes else ""
            
            return ValidationResult(
                is_valid=True,
                warning_message=warning_msg,
                suggestion=f"Arquivo Excel válido com {len(df)} tabelas. {auto_fix_msg}",
                auto_fix_applied=bool(auto_fixes),
                severity="info" if not validation_issues else "warning"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Erro ao validar arquivo Excel: {str(e)}",
                severity="error"
            )
    
    def validate_config_file(self, config_path: str) -> ValidationResult:
        """Valida arquivo de configuração"""
        
        try:
            if not config_path:
                return ValidationResult(
                    is_valid=True,
                    suggestion="Nenhum arquivo de configuração especificado - usando configurações padrão",
                    severity="info"
                )
            
            path_obj = Path(config_path)
            
            # Verifica se existe
            if not path_obj.exists():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Arquivo de configuração não encontrado: {config_path}",
                    suggestion="Verifique o caminho ou remova o parâmetro --config para usar configurações padrão",
                    severity="error"
                )
            
            # Verifica extensão
            if path_obj.suffix.lower() not in ['.json', '.yaml', '.yml']:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Formato de configuração não suportado: {path_obj.suffix}",
                    suggestion="Use arquivos .json, .yaml ou .yml",
                    severity="error"
                )
            
            # Tenta carregar o arquivo
            try:
                if path_obj.suffix.lower() == '.json':
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                else:
                    # YAML
                    try:
                        import yaml
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                    except ImportError:
                        return ValidationResult(
                            is_valid=False,
                            error_message="PyYAML não está instalado - não é possível ler arquivos YAML",
                            suggestion="Instale PyYAML com: pip install pyyaml ou use arquivo .json",
                            severity="error"
                        )
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Erro de sintaxe JSON: {str(e)}",
                    suggestion="Verifique a sintaxe do arquivo JSON",
                    severity="error"
                )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Erro ao ler configuração: {str(e)}",
                    suggestion="Verifique se o arquivo está acessível e não corrompido",
                    severity="error"
                )
            
            # Valida estrutura da configuração
            validation_issues = []
            
            # Verifica seções conhecidas
            known_sections = ['analysis_settings', 'reporting', 'logging', 'performance', 'validation']
            unknown_sections = [key for key in config.keys() if key not in known_sections and not key.startswith('_')]
            
            if unknown_sections:
                validation_issues.append(f"Seções desconhecidas: {', '.join(unknown_sections[:3])}")
            
            # Valida valores específicos
            if 'analysis_settings' in config:
                settings = config['analysis_settings']
                
                if 'fuzzy_match_threshold' in settings:
                    threshold = settings['fuzzy_match_threshold']
                    if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
                        validation_issues.append("fuzzy_match_threshold deve ser um número entre 0 e 100")
                
                if 'max_files_to_analyze' in settings:
                    max_files = settings['max_files_to_analyze']
                    if not isinstance(max_files, int) or max_files <= 0:
                        validation_issues.append("max_files_to_analyze deve ser um número inteiro positivo")
            
            warning_msg = "; ".join(validation_issues) if validation_issues else ""
            
            return ValidationResult(
                is_valid=True,
                warning_message=warning_msg,
                suggestion=f"Arquivo de configuração válido com {len(config)} seções",
                severity="info" if not validation_issues else "warning"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Erro ao validar configuração: {str(e)}",
                severity="error"
            )
    
    def validate_output_directory(self, output_dir: str, create_if_missing: bool = True) -> ValidationResult:
        """Valida diretório de saída"""
        
        try:
            path_obj = Path(output_dir)
            
            # Verifica se existe
            if not path_obj.exists():
                if create_if_missing:
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        return ValidationResult(
                            is_valid=True,
                            suggestion=f"Diretório de saída criado: {output_dir}",
                            auto_fix_applied=True,
                            severity="info"
                        )
                    except Exception as e:
                        return ValidationResult(
                            is_valid=False,
                            error_message=f"Não foi possível criar diretório de saída: {str(e)}",
                            suggestion="Verifique permissões ou especifique outro diretório",
                            severity="error"
                        )
                else:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Diretório de saída não existe: {output_dir}",
                        suggestion="Crie o diretório ou permita criação automática",
                        severity="error"
                    )
            
            # Verifica se é diretório
            if not path_obj.is_dir():
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Caminho de saída não é um diretório: {output_dir}",
                    suggestion="Especifique um diretório válido",
                    severity="error"
                )
            
            # Verifica permissões de escrita
            if not os.access(output_dir, os.W_OK):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Sem permissão de escrita no diretório: {output_dir}",
                    suggestion="Verifique as permissões do diretório ou especifique outro local",
                    severity="error"
                )
            
            # Verifica espaço disponível (aproximadamente)
            try:
                statvfs = os.statvfs(output_dir)
                free_space_mb = statvfs.f_frsize * statvfs.f_bavail / (1024 * 1024)
                
                if free_space_mb < 100:  # Menos de 100MB
                    return ValidationResult(
                        is_valid=True,
                        warning_message=f"Pouco espaço em disco ({free_space_mb:.1f}MB disponível)",
                        suggestion="Libere espaço em disco para evitar problemas",
                        severity="warning"
                    )
            except:
                pass  # Não disponível em todos os sistemas
            
            return ValidationResult(
                is_valid=True,
                suggestion=f"Diretório de saída válido: {output_dir}",
                severity="info"
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Erro ao validar diretório de saída: {str(e)}",
                severity="error"
            )
    
    def validate_all_inputs(self, 
                           source_dir: str,
                           tables_xlsx: str,
                           config_path: str = None,
                           output_dir: str = None) -> ValidationReport:
        """Valida todas as entradas do sistema"""
        
        self.logger.info("Iniciando validação completa de entradas...")
        
        validations = []
        
        # 1. Requisitos do sistema
        self.logger.info("Validando requisitos do sistema...")
        validations.append(("Requisitos do Sistema", self.validate_system_requirements()))
        
        # 2. Diretório de origem
        self.logger.info("Validando diretório de origem...")
        validations.append(("Diretório de Origem", self.validate_input_directory(source_dir)))
        
        # 3. Arquivo Excel
        self.logger.info("Validando arquivo de tabelas...")
        validations.append(("Arquivo de Tabelas", self.validate_excel_file(tables_xlsx)))
        
        # 4. Configuração (se fornecida)
        if config_path:
            self.logger.info("Validando arquivo de configuração...")
            validations.append(("Configuração", self.validate_config_file(config_path)))
        
        # 5. Diretório de saída (se fornecido)
        if output_dir:
            self.logger.info("Validando diretório de saída...")
            validations.append(("Diretório de Saída", self.validate_output_directory(output_dir)))
        
        # Compila resultados
        results = [result for _, result in validations]
        
        total_validations = len(results)
        passed_validations = len([r for r in results if r.is_valid])
        failed_validations = total_validations - passed_validations
        warnings_count = len([r for r in results if r.warning_message])
        auto_fixes_applied = len([r for r in results if r.auto_fix_applied])
        suggestions_count = len([r for r in results if r.suggestion])
        
        # Determina status geral
        if failed_validations > 0:
            overall_status = "FAIL"
        elif warnings_count > 0:
            overall_status = "WARN"
        else:
            overall_status = "PASS"
        
        report = ValidationReport(
            overall_status=overall_status,
            total_validations=total_validations,
            passed_validations=passed_validations,
            failed_validations=failed_validations,
            warnings_count=warnings_count,
            results=results,
            auto_fixes_applied=auto_fixes_applied,
            suggestions_count=suggestions_count
        )
        
        self.logger.info(f"Validação concluída: {overall_status} ({passed_validations}/{total_validations} passou)")
        
        return report
    
    def print_validation_report(self, report: ValidationReport, validations: List[Tuple[str, ValidationResult]]):
        """Imprime relatório de validação formatado"""
        
        print("\n" + "="*80)
        print("🔍 BW_AUTOMATE - RELATÓRIO DE VALIDAÇÃO")
        print("="*80)
        
        # Status geral
        status_emoji = {
            "PASS": "✅",
            "WARN": "⚠️", 
            "FAIL": "❌"
        }
        
        print(f"\n{status_emoji.get(report.overall_status, '❓')} Status Geral: {report.overall_status}")
        print(f"📊 Validações: {report.passed_validations}/{report.total_validations} aprovadas")
        
        if report.warnings_count > 0:
            print(f"⚠️ Avisos: {report.warnings_count}")
        
        if report.auto_fixes_applied > 0:
            print(f"🔧 Correções automáticas: {report.auto_fixes_applied}")
        
        # Detalhes por validação
        print(f"\n📋 Detalhes das Validações:")
        print("-" * 80)
        
        for (validation_name, result) in zip([name for name, _ in validations], report.results):
            status_icon = "✅" if result.is_valid else "❌"
            severity_icon = {
                "critical": "🚨",
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️"
            }.get(result.severity, "")
            
            print(f"\n{status_icon} {validation_name} {severity_icon}")
            
            if result.error_message:
                print(f"   ❌ Erro: {result.error_message}")
            
            if result.warning_message:
                print(f"   ⚠️ Aviso: {result.warning_message}")
            
            if result.suggestion:
                print(f"   💡 Sugestão: {result.suggestion}")
            
            if result.auto_fix_applied:
                print(f"   🔧 Correção automática aplicada")
        
        # Resumo de ações
        if report.overall_status == "FAIL":
            print(f"\n❌ VALIDAÇÃO FALHOU")
            print(f"Corrija os erros acima antes de prosseguir.")
        elif report.overall_status == "WARN":
            print(f"\n⚠️ VALIDAÇÃO COM AVISOS")
            print(f"Você pode prosseguir, mas considere as sugestões acima.")
        else:
            print(f"\n✅ VALIDAÇÃO APROVADA")
            print(f"Todas as entradas são válidas!")
        
        print("\n" + "="*80)
        print(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print("="*80 + "\n")
    
    def export_validation_report(self, report: ValidationReport, output_path: str) -> str:
        """Exporta relatório de validação para JSON"""
        
        report_data = {
            'validation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'validator_version': '2.0',
                'total_validations': report.total_validations
            },
            'summary': {
                'overall_status': report.overall_status,
                'passed_validations': report.passed_validations,
                'failed_validations': report.failed_validations,
                'warnings_count': report.warnings_count,
                'auto_fixes_applied': report.auto_fixes_applied
            },
            'detailed_results': []
        }
        
        for result in report.results:
            result_data = {
                'is_valid': result.is_valid,
                'severity': result.severity,
                'error_message': result.error_message,
                'warning_message': result.warning_message,
                'suggestion': result.suggestion,
                'auto_fix_applied': result.auto_fix_applied
            }
            report_data['detailed_results'].append(result_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Relatório de validação exportado: {output_path}")
        return output_path