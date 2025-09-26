#!/usr/bin/env python3
"""
BW_AUTOMATE - Performance Optimizer
===================================

Módulo para otimização de performance e uso de memória do BW_AUTOMATE.

Autor: Assistant Claude
Data: 2025-09-20
"""

import gc
import sys
import os
import time
import threading
from typing import Any, Callable, Dict, List, Optional, Iterator
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
from dataclasses import dataclass
from collections import deque
import weakref

try:
    from utils import SafeLogger, memory_usage_mb, progress_bar
except ImportError:
    # Fallback se utils não estiver disponível
    class SafeLogger:
        def debug(self, msg): print(f"DEBUG: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def memory_usage_mb(): return -1.0
    def progress_bar(iterable, **kwargs): return iterable


@dataclass
class PerformanceMetrics:
    """Métricas de performance"""
    start_time: float
    end_time: float
    memory_before: float
    memory_after: float
    cpu_time: float
    function_name: str
    
    @property
    def execution_time(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def memory_delta(self) -> float:
        return self.memory_after - self.memory_before


class MemoryManager:
    """Gerenciador de memória otimizado"""
    
    def __init__(self, max_memory_mb: float = 1024.0):
        self.max_memory_mb = max_memory_mb
        self.logger = SafeLogger("MemoryManager")
        self._cached_objects = weakref.WeakSet()
        self._large_objects = []
    
    def register_large_object(self, obj: Any, name: str = None):
        """Registra objeto grande para monitoramento"""
        size_mb = sys.getsizeof(obj) / 1024 / 1024
        self._large_objects.append({
            'object': weakref.ref(obj),
            'name': name or str(type(obj)),
            'size_mb': size_mb,
            'created_at': time.time()
        })
        
        if size_mb > 50:  # Objeto maior que 50MB
            self.logger.warning(f"Objeto grande registrado: {name} ({size_mb:.1f}MB)")
    
    def check_memory_usage(self) -> bool:
        """Verifica se uso de memória está dentro do limite"""
        current_memory = memory_usage_mb()
        if current_memory > 0 and current_memory > self.max_memory_mb:
            self.logger.warning(f"Uso de memória alto: {current_memory:.1f}MB (limite: {self.max_memory_mb}MB)")
            return False
        return True
    
    def force_garbage_collection(self):
        """Força garbage collection"""
        before = memory_usage_mb()
        collected = gc.collect()
        after = memory_usage_mb()
        
        if before > 0 and after > 0:
            freed = before - after
            self.logger.info(f"GC: {collected} objetos coletados, {freed:.1f}MB liberados")
        else:
            self.logger.info(f"GC: {collected} objetos coletados")
    
    def cleanup_large_objects(self):
        """Remove referências de objetos grandes que não existem mais"""
        active_objects = []
        for obj_info in self._large_objects:
            if obj_info['object']() is not None:  # Objeto ainda existe
                active_objects.append(obj_info)
        
        cleaned = len(self._large_objects) - len(active_objects)
        self._large_objects = active_objects
        
        if cleaned > 0:
            self.logger.info(f"Limpeza: {cleaned} referências de objetos removidas")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Gera relatório de uso de memória"""
        current_memory = memory_usage_mb()
        
        # Filtra objetos ainda ativos
        active_large_objects = [
            obj for obj in self._large_objects 
            if obj['object']() is not None
        ]
        
        total_large_objects_mb = sum(obj['size_mb'] for obj in active_large_objects)
        
        return {
            'current_memory_mb': current_memory,
            'max_memory_mb': self.max_memory_mb,
            'memory_usage_percent': (current_memory / self.max_memory_mb * 100) if current_memory > 0 else 0,
            'large_objects_count': len(active_large_objects),
            'large_objects_total_mb': total_large_objects_mb,
            'top_large_objects': sorted(
                active_large_objects, 
                key=lambda x: x['size_mb'], 
                reverse=True
            )[:5]
        }


class ChunkedProcessor:
    """Processador que divide dados em chunks para economizar memória"""
    
    def __init__(self, chunk_size: int = 1000, show_progress: bool = True):
        self.chunk_size = chunk_size
        self.show_progress = show_progress
        self.logger = SafeLogger("ChunkedProcessor")
    
    def process_in_chunks(self, 
                         data: List[Any], 
                         processor_func: Callable,
                         combine_func: Callable = None) -> Any:
        """
        Processa dados em chunks
        
        Args:
            data: Lista de dados para processar
            processor_func: Função que processa um chunk
            combine_func: Função para combinar resultados (opcional)
            
        Returns:
            Resultado processado
        """
        total_items = len(data)
        chunks = [data[i:i + self.chunk_size] for i in range(0, total_items, self.chunk_size)]
        
        self.logger.info(f"Processando {total_items} itens em {len(chunks)} chunks de {self.chunk_size}")
        
        results = []
        
        chunk_iter = progress_bar(chunks, desc="Processando chunks") if self.show_progress else chunks
        
        for i, chunk in enumerate(chunk_iter):
            try:
                chunk_result = processor_func(chunk)
                results.append(chunk_result)
                
                # Força garbage collection a cada 10 chunks
                if (i + 1) % 10 == 0:
                    gc.collect()
                    
            except Exception as e:
                self.logger.error(f"Erro processando chunk {i}: {e}")
                raise
        
        # Combina resultados se função fornecida
        if combine_func:
            return combine_func(results)
        else:
            return results


class LazyLoader:
    """Carregador lazy para objetos grandes"""
    
    def __init__(self, loader_func: Callable, *args, **kwargs):
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs
        self._value = None
        self._loaded = False
        self.logger = SafeLogger("LazyLoader")
    
    @property
    def value(self):
        """Carrega valor sob demanda"""
        if not self._loaded:
            self.logger.debug(f"Carregando {self.loader_func.__name__}")
            start_time = time.time()
            self._value = self.loader_func(*self.args, **self.kwargs)
            load_time = time.time() - start_time
            self.logger.debug(f"Carregamento concluído em {load_time:.2f}s")
            self._loaded = True
        return self._value
    
    def unload(self):
        """Descarrega valor da memória"""
        if self._loaded:
            self._value = None
            self._loaded = False
            gc.collect()
            self.logger.debug("Valor descarregado da memória")
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded


class FileIterator:
    """Iterator otimizado para arquivos grandes"""
    
    def __init__(self, file_path: str, chunk_size: int = 8192):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.logger = SafeLogger("FileIterator")
    
    def read_lines(self) -> Iterator[str]:
        """Lê arquivo linha por linha sem carregar tudo na memória"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    yield line.rstrip('\n\r')
        except Exception as e:
            self.logger.error(f"Erro lendo arquivo {self.file_path}: {e}")
            raise
    
    def read_chunks(self) -> Iterator[str]:
        """Lê arquivo em chunks de tamanho fixo"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            self.logger.error(f"Erro lendo arquivo {self.file_path}: {e}")
            raise


def memoize_with_ttl(ttl_seconds: int = 3600, maxsize: int = 128):
    """
    Decorator para memoização com TTL (Time To Live)
    
    Args:
        ttl_seconds: Tempo de vida do cache em segundos
        maxsize: Tamanho máximo do cache
    """
    def decorator(func: Callable) -> Callable:
        # Cache com timestamp
        cache = {}
        cache_order = deque(maxlen=maxsize)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cria chave do cache
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Verifica se existe no cache e não expirou
            if key in cache:
                value, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return value
                else:
                    # Remove entrada expirada
                    del cache[key]
            
            # Calcula novo valor
            result = func(*args, **kwargs)
            
            # Adiciona ao cache
            cache[key] = (result, current_time)
            cache_order.append(key)
            
            # Remove entradas antigas se cache estiver cheio
            while len(cache) > maxsize:
                old_key = cache_order.popleft()
                if old_key in cache:
                    del cache[old_key]
            
            return result
        
        # Adiciona métodos auxiliares
        wrapper.cache_info = lambda: {
            'hits': 0,  # Simplificado
            'misses': 0,
            'maxsize': maxsize,
            'currsize': len(cache)
        }
        wrapper.cache_clear = lambda: cache.clear()
        
        return wrapper
    return decorator


def profile_performance(include_memory: bool = True):
    """Decorator para profiling de performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = SafeLogger(f"PROFILE_{func.__name__}")
            
            # Métricas iniciais
            start_time = time.time()
            memory_before = memory_usage_mb() if include_memory else 0
            
            try:
                result = func(*args, **kwargs)
                
                # Métricas finais
                end_time = time.time()
                memory_after = memory_usage_mb() if include_memory else 0
                
                # Calcula métricas
                execution_time = end_time - start_time
                memory_delta = memory_after - memory_before if include_memory else 0
                
                # Log das métricas
                logger.info(f"Executado em {execution_time:.3f}s")
                if include_memory and memory_before > 0:
                    logger.info(f"Memória: {memory_before:.1f}MB → {memory_after:.1f}MB (Δ {memory_delta:+.1f}MB)")
                
                return result
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.error(f"Erro após {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


class BatchProcessor:
    """Processador em lotes com paralelização opcional"""
    
    def __init__(self, 
                 batch_size: int = 100,
                 max_workers: int = None,
                 use_threading: bool = True):
        self.batch_size = batch_size
        self.max_workers = max_workers or min(4, mp.cpu_count())
        self.use_threading = use_threading
        self.logger = SafeLogger("BatchProcessor")
    
    def process_batches(self, 
                       items: List[Any],
                       processor_func: Callable,
                       show_progress: bool = True) -> List[Any]:
        """
        Processa itens em lotes com paralelização
        
        Args:
            items: Lista de itens para processar
            processor_func: Função que processa um lote
            show_progress: Se deve mostrar barra de progresso
            
        Returns:
            Lista de resultados
        """
        # Divide em lotes
        batches = [items[i:i + self.batch_size] 
                  for i in range(0, len(items), self.batch_size)]
        
        self.logger.info(f"Processando {len(items)} itens em {len(batches)} lotes "
                        f"usando {self.max_workers} workers")
        
        results = []
        
        if self.max_workers == 1:
            # Processamento sequencial
            batch_iter = progress_bar(batches, desc="Processando") if show_progress else batches
            for batch in batch_iter:
                result = processor_func(batch)
                results.append(result)
        else:
            # Processamento paralelo
            ExecutorClass = ThreadPoolExecutor if self.use_threading else mp.Pool
            
            with ExecutorClass(max_workers=self.max_workers) as executor:
                future_to_batch = {executor.submit(processor_func, batch): batch 
                                 for batch in batches}
                
                if show_progress:
                    futures_iter = progress_bar(as_completed(future_to_batch), 
                                               total=len(batches), 
                                               desc="Processando")
                else:
                    futures_iter = as_completed(future_to_batch)
                
                for future in futures_iter:
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Erro em lote: {e}")
                        raise
        
        return results


# Instância global do gerenciador de memória
memory_manager = MemoryManager()


def optimize_dataframe(df, categorical_threshold: int = 50) -> Any:
    """
    Otimiza DataFrame pandas para uso de memória
    
    Args:
        df: DataFrame para otimizar
        categorical_threshold: Limite para converter para categorical
        
    Returns:
        DataFrame otimizado
    """
    try:
        import pandas as pd
        
        if not isinstance(df, pd.DataFrame):
            return df
        
        logger = SafeLogger("optimize_dataframe")
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Converte strings com poucos valores únicos para categorical
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() < categorical_threshold:
                df[col] = df[col].astype('category')
        
        # Converte inteiros para tipos menores quando possível
        for col in df.select_dtypes(include=['int64']).columns:
            col_min, col_max = df[col].min(), df[col].max()
            if col_min >= -128 and col_max <= 127:
                df[col] = df[col].astype('int8')
            elif col_min >= -32768 and col_max <= 32767:
                df[col] = df[col].astype('int16')
            elif col_min >= -2147483648 and col_max <= 2147483647:
                df[col] = df[col].astype('int32')
        
        # Converte floats para float32 quando possível (com cuidado)
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        reduction = ((original_memory - optimized_memory) / original_memory) * 100
        
        logger.info(f"DataFrame otimizado: {original_memory:.1f}MB → {optimized_memory:.1f}MB "
                   f"({reduction:.1f}% redução)")
        
        return df
        
    except ImportError:
        # pandas não disponível
        return df
    except Exception as e:
        SafeLogger().error(f"Erro otimizando DataFrame: {e}")
        return df


if __name__ == "__main__":
    # Teste das funcionalidades de performance
    print("⚡ BW_AUTOMATE Performance Optimizer - Teste")
    print("=" * 50)
    
    # Teste do gerenciador de memória
    print("\n🧠 Testando Memory Manager...")
    print(f"Memória atual: {memory_usage_mb():.1f}MB")
    
    report = memory_manager.get_memory_report()
    print(f"Uso de memória: {report['memory_usage_percent']:.1f}%")
    
    # Teste do chunked processor
    print("\n📊 Testando Chunked Processor...")
    data = list(range(1000))
    
    @profile_performance()
    def process_chunk(chunk):
        return sum(chunk)
    
    processor = ChunkedProcessor(chunk_size=100, show_progress=False)
    results = processor.process_in_chunks(data, process_chunk, sum)
    print(f"Resultado: {results}")
    
    # Teste de memoização
    print("\n💾 Testando Memoização...")
    
    @memoize_with_ttl(ttl_seconds=60)
    def expensive_function(n):
        time.sleep(0.01)  # Simula operação cara
        return n * n
    
    start = time.time()
    result1 = expensive_function(5)
    time1 = time.time() - start
    
    start = time.time()
    result2 = expensive_function(5)  # Deve vir do cache
    time2 = time.time() - start
    
    print(f"Primeira chamada: {time1:.3f}s")
    print(f"Segunda chamada (cache): {time2:.3f}s")
    print(f"Speedup: {time1/time2:.1f}x")
    
    print("\n🎯 Performance Optimizer funcionando!")