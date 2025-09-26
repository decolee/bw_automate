#!/usr/bin/env python3
"""
BW_AUTOMATE - Advanced Features
==============================

Funcionalidades avançadas: cache inteligente, análise de schema,
detecção de padrões ETL, e integração com APIs.

Autor: Assistant Claude
Data: 2025-09-20
"""

import os
import json
import hashlib
import sqlite3
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from dataclasses import dataclass, asdict
import threading
import queue
import time

try:
    from utils import SafeLogger, ensure_directory
    from error_handler import safe_execute, ErrorContext
    from performance_optimizer import memoize_with_ttl, LazyLoader
except ImportError:
    # Fallbacks simples
    class SafeLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def ensure_directory(path): 
        os.makedirs(path, exist_ok=True)
        return path
    
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return None
    
    class ErrorContext:
        def __init__(self, name): self.name = name
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    def memoize_with_ttl(*args, **kwargs):
        def decorator(func): return func
        return decorator
    
    class LazyLoader:
        def __init__(self, func, *args, **kwargs):
            self.value = func(*args, **kwargs)


@dataclass
class CacheEntry:
    """Entrada do cache com metadados"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: int
    
    @property
    def is_expired(self) -> bool:
        """Verifica se entrada expirou"""
        if self.ttl_seconds <= 0:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def age_seconds(self) -> float:
        """Idade da entrada em segundos"""
        return (datetime.now() - self.created_at).total_seconds()


class IntelligentCache:
    """Cache inteligente com LRU, TTL e persistência"""
    
    def __init__(self, 
                 max_size_mb: float = 100.0,
                 max_entries: int = 1000,
                 default_ttl: int = 3600,
                 cache_dir: str = "BW_AUTOMATE/cache"):
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cache_dir = ensure_directory(cache_dir)
        
        self.entries: Dict[str, CacheEntry] = {}
        self.total_size_bytes = 0
        self.hits = 0
        self.misses = 0
        
        self.logger = SafeLogger("IntelligentCache")
        self._lock = threading.RLock()
        
        # Carrega cache persistido
        self._load_from_disk()
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        with self._lock:
            if key not in self.entries:
                self.misses += 1
                return None
            
            entry = self.entries[key]
            
            # Verifica se expirou
            if entry.is_expired:
                self._remove_entry(key)
                self.misses += 1
                return None
            
            # Atualiza estatísticas de acesso
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self.hits += 1
            
            self.logger.debug(f"Cache hit: {key}")
            return entry.value
    
    def put(self, key: str, value: Any, ttl: int = None) -> bool:
        """Armazena valor no cache"""
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Calcula tamanho do objeto
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 1024  # Estimativa se não conseguir serializar
            
            # Verifica se cabe no cache
            if size_bytes > self.max_size_mb * 1024 * 1024:
                self.logger.warning(f"Objeto muito grande para cache: {size_bytes / 1024 / 1024:.1f}MB")
                return False
            
            # Remove entrada existente se houver
            if key in self.entries:
                self._remove_entry(key)
            
            # Cria nova entrada
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                size_bytes=size_bytes,
                ttl_seconds=ttl
            )
            
            # Faz espaço se necessário
            self._make_space(size_bytes)
            
            # Adiciona entrada
            self.entries[key] = entry
            self.total_size_bytes += size_bytes
            
            self.logger.debug(f"Cache put: {key} ({size_bytes} bytes)")
            return True
    
    def _remove_entry(self, key: str):
        """Remove entrada do cache"""
        if key in self.entries:
            entry = self.entries[key]
            self.total_size_bytes -= entry.size_bytes
            del self.entries[key]
    
    def _make_space(self, needed_bytes: int):
        """Faz espaço no cache removendo entradas antigas"""
        max_size_bytes = self.max_size_mb * 1024 * 1024
        
        # Remove entradas expiradas primeiro
        expired_keys = [k for k, e in self.entries.items() if e.is_expired]
        for key in expired_keys:
            self._remove_entry(key)
        
        # Se ainda precisar de espaço, usa estratégia LRU
        while (self.total_size_bytes + needed_bytes > max_size_bytes or 
               len(self.entries) >= self.max_entries):
            
            if not self.entries:
                break
            
            # Encontra entrada menos recentemente usada
            lru_key = min(self.entries.keys(), 
                         key=lambda k: self.entries[k].accessed_at)
            self._remove_entry(lru_key)
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            self.entries.clear()
            self.total_size_bytes = 0
            self.hits = 0
            self.misses = 0
            self.logger.info("Cache limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self.entries),
                'max_entries': self.max_entries,
                'size_mb': self.total_size_bytes / 1024 / 1024,
                'max_size_mb': self.max_size_mb,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': hit_rate,
                'oldest_entry_age_seconds': min(
                    (e.age_seconds for e in self.entries.values()),
                    default=0
                )
            }
    
    def _save_to_disk(self):
        """Salva cache no disco"""
        try:
            cache_file = os.path.join(self.cache_dir, "cache.db")
            
            with sqlite3.connect(cache_file) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        created_at TEXT,
                        ttl_seconds INTEGER
                    )
                """)
                
                # Limpa tabela
                conn.execute("DELETE FROM cache_entries")
                
                # Salva entradas válidas
                for key, entry in self.entries.items():
                    if not entry.is_expired:
                        try:
                            value_blob = pickle.dumps(entry.value)
                            conn.execute("""
                                INSERT INTO cache_entries 
                                (key, value, created_at, ttl_seconds)
                                VALUES (?, ?, ?, ?)
                            """, (
                                key, 
                                value_blob,
                                entry.created_at.isoformat(),
                                entry.ttl_seconds
                            ))
                        except:
                            # Pula entradas que não podem ser serializadas
                            continue
                
                conn.commit()
                self.logger.debug("Cache salvo no disco")
                
        except Exception as e:
            self.logger.error(f"Erro salvando cache: {e}")
    
    def _load_from_disk(self):
        """Carrega cache do disco"""
        try:
            cache_file = os.path.join(self.cache_dir, "cache.db")
            
            if not os.path.exists(cache_file):
                return
            
            with sqlite3.connect(cache_file) as conn:
                cursor = conn.execute("""
                    SELECT key, value, created_at, ttl_seconds 
                    FROM cache_entries
                """)
                
                loaded_count = 0
                for row in cursor:
                    key, value_blob, created_at_str, ttl_seconds = row
                    
                    try:
                        value = pickle.loads(value_blob)
                        created_at = datetime.fromisoformat(created_at_str)
                        
                        # Verifica se não expirou
                        if ttl_seconds > 0:
                            expiry = created_at + timedelta(seconds=ttl_seconds)
                            if datetime.now() > expiry:
                                continue
                        
                        # Recria entrada
                        entry = CacheEntry(
                            key=key,
                            value=value,
                            created_at=created_at,
                            accessed_at=created_at,
                            access_count=0,
                            size_bytes=len(value_blob),
                            ttl_seconds=ttl_seconds
                        )
                        
                        self.entries[key] = entry
                        self.total_size_bytes += entry.size_bytes
                        loaded_count += 1
                        
                    except:
                        # Pula entradas corrompidas
                        continue
                
                self.logger.info(f"Cache carregado: {loaded_count} entradas")
                
        except Exception as e:
            self.logger.error(f"Erro carregando cache: {e}")
    
    def __del__(self):
        """Salva cache ao destruir objeto"""
        try:
            self._save_to_disk()
        except:
            pass


class SchemaAnalyzer:
    """Analisador avançado de schemas de banco"""
    
    def __init__(self):
        self.logger = SafeLogger("SchemaAnalyzer")
        
        # Padrões de nomenclatura comuns
        self.naming_patterns = {
            'fact_tables': [r'fact_.*', r'f_.*', r'.*_fact'],
            'dimension_tables': [r'dim_.*', r'd_.*', r'.*_dim'],
            'staging_tables': [r'stg_.*', r'staging_.*', r'.*_staging'],
            'temp_tables': [r'temp_.*', r'tmp_.*', r'.*_temp'],
            'log_tables': [r'log_.*', r'.*_log', r'audit_.*'],
            'config_tables': [r'config_.*', r'.*_config', r'settings_.*']
        }
        
        # Convenções de schema
        self.schema_conventions = {
            'transactional': ['public', 'prod', 'production'],
            'staging': ['staging', 'stg', 'stage'],
            'reporting': ['reports', 'reporting', 'dwh', 'warehouse'],
            'analytics': ['analytics', 'analysis', 'bi'],
            'logging': ['logs', 'audit', 'monitoring'],
            'configuration': ['config', 'settings', 'admin']
        }
    
    def analyze_table_patterns(self, tables: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa padrões nas tabelas"""
        results = {
            'table_types': {},
            'schema_distribution': {},
            'naming_conventions': {},
            'recommendations': []
        }
        
        # Analisa tipos de tabela
        for table_key, table_info in tables.items():
            table_name = table_info.get('table_name', table_key.split('.')[-1])
            schema = table_info.get('schema', 'public')
            
            # Classifica por padrão de nome
            table_type = self._classify_table_by_name(table_name)
            if table_type not in results['table_types']:
                results['table_types'][table_type] = []
            results['table_types'][table_type].append(table_name)
            
            # Distribui por schema
            if schema not in results['schema_distribution']:
                results['schema_distribution'][schema] = 0
            results['schema_distribution'][schema] += 1
        
        # Analisa convenções de nomenclatura
        results['naming_conventions'] = self._analyze_naming_conventions(tables)
        
        # Gera recomendações
        results['recommendations'] = self._generate_schema_recommendations(results)
        
        return results
    
    def _classify_table_by_name(self, table_name: str) -> str:
        """Classifica tabela por padrão de nome"""
        import re
        
        for table_type, patterns in self.naming_patterns.items():
            for pattern in patterns:
                if re.match(pattern, table_name, re.IGNORECASE):
                    return table_type
        
        return 'business_tables'
    
    def _analyze_naming_conventions(self, tables: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa convenções de nomenclatura"""
        conventions = {
            'uses_underscores': 0,
            'uses_camelcase': 0,
            'has_prefixes': 0,
            'has_suffixes': 0,
            'mixed_case': 0,
            'all_lowercase': 0
        }
        
        import re
        
        for table_key, table_info in tables.items():
            table_name = table_info.get('table_name', table_key.split('.')[-1])
            
            if '_' in table_name:
                conventions['uses_underscores'] += 1
            
            if re.search(r'[a-z][A-Z]', table_name):
                conventions['uses_camelcase'] += 1
            
            if re.match(r'^[a-z]+_', table_name):
                conventions['has_prefixes'] += 1
            
            if re.match(r'.*_[a-z]+$', table_name):
                conventions['has_suffixes'] += 1
            
            if table_name != table_name.lower():
                conventions['mixed_case'] += 1
            else:
                conventions['all_lowercase'] += 1
        
        return conventions
    
    def _generate_schema_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        # Recomendações de nomenclatura
        naming = analysis['naming_conventions']
        total_tables = sum(naming.values()) if naming else 1
        
        if naming.get('mixed_case', 0) / total_tables > 0.1:
            recommendations.append(
                "Considere padronizar nomes de tabelas para lowercase para melhor compatibilidade"
            )
        
        if naming.get('uses_underscores', 0) / total_tables < 0.8:
            recommendations.append(
                "Recomenda-se usar underscores para separar palavras em nomes de tabelas"
            )
        
        # Recomendações de schema
        schema_dist = analysis['schema_distribution']
        if len(schema_dist) == 1 and 'public' in schema_dist:
            recommendations.append(
                "Considere organizar tabelas em schemas específicos (staging, reports, etc.)"
            )
        
        # Recomendações de organização
        table_types = analysis['table_types']
        if 'temp_tables' in table_types and len(table_types['temp_tables']) > 0:
            recommendations.append(
                f"Detectadas {len(table_types['temp_tables'])} tabelas temporárias - "
                "considere schema dedicado para staging"
            )
        
        return recommendations
    
    def detect_etl_patterns(self, analysis_results: List[Any]) -> Dict[str, Any]:
        """Detecta padrões ETL nos códigos analisados"""
        patterns = {
            'extract_patterns': [],
            'transform_patterns': [],
            'load_patterns': [],
            'common_operations': {},
            'data_flow_complexity': 'low'
        }
        
        operation_counts = {}
        total_tables = set()
        
        for result in analysis_results:
            # Analisa operações de leitura (Extract)
            for table_ref in result.tables_read:
                operation = 'EXTRACT'
                if operation not in operation_counts:
                    operation_counts[operation] = 0
                operation_counts[operation] += 1
                total_tables.add(table_ref.name)
            
            # Analisa operações de escrita (Load)
            for table_ref in result.tables_written:
                operation = f"LOAD_{table_ref.operation}"
                if operation not in operation_counts:
                    operation_counts[operation] = 0
                operation_counts[operation] += 1
                total_tables.add(table_ref.name)
        
        patterns['common_operations'] = operation_counts
        
        # Determina complexidade do fluxo
        if len(total_tables) > 50:
            patterns['data_flow_complexity'] = 'high'
        elif len(total_tables) > 20:
            patterns['data_flow_complexity'] = 'medium'
        
        return patterns


class APIIntegrator:
    """Integrador com APIs externas (GitHub, Airflow, etc.)"""
    
    def __init__(self):
        self.logger = SafeLogger("APIIntegrator")
    
    def get_airflow_dag_info(self, airflow_url: str, dag_id: str) -> Optional[Dict]:
        """Busca informações de DAG via API do Airflow"""
        try:
            import requests
            
            # Simula chamada à API (implementação básica)
            endpoint = f"{airflow_url}/api/v1/dags/{dag_id}"
            
            with ErrorContext("AIRFLOW_API"):
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"Erro API Airflow: {response.status_code}")
                    return None
                    
        except ImportError:
            self.logger.warning("requests não disponível para integração com APIs")
            return None
        except Exception as e:
            self.logger.error(f"Erro integrando com Airflow API: {e}")
            return None
    
    def check_github_updates(self, repo_url: str) -> Optional[Dict]:
        """Verifica atualizações no repositório GitHub"""
        try:
            import requests
            
            # Extrai owner/repo da URL
            if 'github.com' not in repo_url:
                return None
            
            parts = repo_url.replace('https://github.com/', '').strip('/').split('/')
            if len(parts) < 2:
                return None
            
            owner, repo = parts[0], parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            
            with ErrorContext("GITHUB_API"):
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            self.logger.error(f"Erro verificando GitHub: {e}")
            
        return None


class ConfigurationManager:
    """Gerenciador avançado de configurações"""
    
    def __init__(self, config_file: str = "BW_AUTOMATE/config.json"):
        self.config_file = config_file
        self.logger = SafeLogger("ConfigManager")
        self._config = {}
        self._watchers = []
        
        self.load_config()
    
    def load_config(self):
        """Carrega configuração do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info(f"Configuração carregada: {self.config_file}")
            else:
                self.logger.warning(f"Arquivo de configuração não encontrado: {self.config_file}")
                self._config = self._get_default_config()
        except Exception as e:
            self.logger.error(f"Erro carregando configuração: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "analysis_settings": {
                "fuzzy_match_threshold": 80,
                "include_temp_tables": True,
                "max_files_to_analyze": 1000
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl_hours": 24,
                "max_memory_mb": 1024
            },
            "advanced_features": {
                "schema_analysis": True,
                "etl_pattern_detection": True,
                "api_integration": False
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Busca valor de configuração com notação de ponto"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Define valor de configuração"""
        keys = key.split('.')
        config_ref = self._config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        config_ref[keys[-1]] = value
        self._notify_watchers(key, value)
    
    def save_config(self):
        """Salva configuração no arquivo"""
        try:
            ensure_directory(os.path.dirname(self.config_file))
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info("Configuração salva")
        except Exception as e:
            self.logger.error(f"Erro salvando configuração: {e}")
    
    def add_watcher(self, callback):
        """Adiciona callback para mudanças de configuração"""
        self._watchers.append(callback)
    
    def _notify_watchers(self, key: str, value: Any):
        """Notifica watchers sobre mudanças"""
        for callback in self._watchers:
            try:
                callback(key, value)
            except Exception as e:
                self.logger.error(f"Erro em watcher de configuração: {e}")


# Instâncias globais
intelligent_cache = IntelligentCache()
schema_analyzer = SchemaAnalyzer()
api_integrator = APIIntegrator()
config_manager = ConfigurationManager()


def cached_analysis(cache_key: str, ttl: int = 3600):
    """Decorator para cache de análises"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Busca no cache primeiro
            cached_result = intelligent_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executa função
            result = func(*args, **kwargs)
            
            # Armazena no cache
            intelligent_cache.put(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Teste das funcionalidades avançadas
    print("🚀 BW_AUTOMATE Advanced Features - Teste")
    print("=" * 50)
    
    # Teste do cache inteligente
    print("\n💾 Testando Cache Inteligente...")
    cache = IntelligentCache(max_size_mb=1, max_entries=5)
    
    cache.put("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    print(f"Cache result: {result}")
    
    stats = cache.get_stats()
    print(f"Cache stats: {stats['hit_rate_percent']:.1f}% hit rate")
    
    # Teste do analisador de schema
    print("\n🗃️ Testando Schema Analyzer...")
    analyzer = SchemaAnalyzer()
    
    sample_tables = {
        'public.users': {'table_name': 'users', 'schema': 'public'},
        'staging.stg_orders': {'table_name': 'stg_orders', 'schema': 'staging'},
        'reports.fact_sales': {'table_name': 'fact_sales', 'schema': 'reports'}
    }
    
    analysis = analyzer.analyze_table_patterns(sample_tables)
    print(f"Padrões detectados: {list(analysis['table_types'].keys())}")
    
    # Teste do gerenciador de configuração
    print("\n⚙️ Testando Configuration Manager...")
    config = ConfigurationManager()
    
    threshold = config.get('analysis_settings.fuzzy_match_threshold', 80)
    print(f"Configuração: fuzzy_match_threshold = {threshold}")
    
    print("\n🎯 Funcionalidades avançadas funcionando!")