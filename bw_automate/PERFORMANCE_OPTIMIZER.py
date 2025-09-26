#!/usr/bin/env python3
"""
Performance Optimizer for Large Codebase Analysis
Optimizes analysis performance through caching, parallel processing, and smart filtering
"""

import os
import sys
import time
import json
import hashlib
import threading
import multiprocessing
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import pickle
import sqlite3
from collections import defaultdict
import fnmatch

@dataclass
class AnalysisCache:
    file_path: str
    file_hash: str
    last_modified: float
    analysis_results: Dict
    analysis_timestamp: datetime
    file_size: int

@dataclass
class PerformanceMetrics:
    total_files: int
    analyzed_files: int
    skipped_files: int
    cache_hits: int
    cache_misses: int
    total_time: float
    analysis_time: float
    cache_time: float
    avg_file_time: float

class CacheManager:
    def __init__(self, cache_dir: str = ".bw_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "analysis_cache.db"
        self.memory_cache = {}
        self.max_memory_cache = 1000
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite cache database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_cache (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT NOT NULL,
                    last_modified REAL NOT NULL,
                    file_size INTEGER NOT NULL,
                    analysis_results TEXT NOT NULL,
                    analysis_timestamp TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_hash ON file_cache(file_hash)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_modified ON file_cache(last_modified)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to initialize cache database: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate file hash for caching"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception:
            return ""
    
    def is_file_cached(self, file_path: str) -> bool:
        """Check if file analysis is cached and still valid"""
        try:
            stat_info = os.stat(file_path)
            current_mtime = stat_info.st_mtime
            current_size = stat_info.st_size
            
            # Check memory cache first
            if file_path in self.memory_cache:
                cached = self.memory_cache[file_path]
                if (cached.last_modified == current_mtime and 
                    cached.file_size == current_size):
                    return True
                else:
                    del self.memory_cache[file_path]
            
            # Check database cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_hash, last_modified, file_size 
                FROM file_cache 
                WHERE file_path = ?
            ''', (file_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                cached_hash, cached_mtime, cached_size = result
                if (cached_mtime == current_mtime and cached_size == current_size):
                    return True
                else:
                    # Remove outdated cache entry
                    self.remove_from_cache(file_path)
            
            return False
            
        except Exception as e:
            logging.warning(f"Error checking cache for {file_path}: {e}")
            return False
    
    def get_cached_analysis(self, file_path: str) -> Optional[Dict]:
        """Get cached analysis results"""
        try:
            # Check memory cache first
            if file_path in self.memory_cache:
                return self.memory_cache[file_path].analysis_results
            
            # Check database cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT analysis_results, last_modified, file_size, analysis_timestamp
                FROM file_cache 
                WHERE file_path = ?
            ''', (file_path,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                analysis_json, last_modified, file_size, timestamp = result
                analysis_results = json.loads(analysis_json)
                
                # Add to memory cache
                cache_entry = AnalysisCache(
                    file_path=file_path,
                    file_hash="",
                    last_modified=last_modified,
                    analysis_results=analysis_results,
                    analysis_timestamp=datetime.fromisoformat(timestamp),
                    file_size=file_size
                )
                
                if len(self.memory_cache) < self.max_memory_cache:
                    self.memory_cache[file_path] = cache_entry
                
                return analysis_results
            
            return None
            
        except Exception as e:
            logging.warning(f"Error getting cached analysis for {file_path}: {e}")
            return None
    
    def cache_analysis(self, file_path: str, analysis_results: Dict):
        """Cache analysis results"""
        try:
            stat_info = os.stat(file_path)
            file_hash = self.get_file_hash(file_path)
            
            cache_entry = AnalysisCache(
                file_path=file_path,
                file_hash=file_hash,
                last_modified=stat_info.st_mtime,
                analysis_results=analysis_results,
                analysis_timestamp=datetime.now(),
                file_size=stat_info.st_size
            )
            
            # Add to memory cache
            if len(self.memory_cache) < self.max_memory_cache:
                self.memory_cache[file_path] = cache_entry
            
            # Add to database cache
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO file_cache 
                (file_path, file_hash, last_modified, file_size, analysis_results, analysis_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                file_hash,
                stat_info.st_mtime,
                stat_info.st_size,
                json.dumps(analysis_results),
                cache_entry.analysis_timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.warning(f"Error caching analysis for {file_path}: {e}")
    
    def remove_from_cache(self, file_path: str):
        """Remove file from cache"""
        try:
            if file_path in self.memory_cache:
                del self.memory_cache[file_path]
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('DELETE FROM file_cache WHERE file_path = ?', (file_path,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.warning(f"Error removing from cache {file_path}: {e}")
    
    def cleanup_old_cache(self, max_age_days: int = 30):
        """Clean up old cache entries"""
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM file_cache 
                WHERE analysis_timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logging.info(f"Cleaned up {deleted_count} old cache entries")
            
        except Exception as e:
            logging.error(f"Error cleaning up cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM file_cache')
            total_cached = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT SUM(file_size) FROM file_cache
            ''')
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'memory_cache_size': len(self.memory_cache),
                'database_cache_size': total_cached,
                'total_cached_file_size': total_size,
                'cache_hit_rate': 0  # Will be calculated during analysis
            }
            
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return {}

class SmartFileFilter:
    def __init__(self):
        self.skip_patterns = [
            '.git/*', '.svn/*', '.hg/*',
            '__pycache__/*', '*.pyc', '*.pyo', '*.pyd',
            '.venv/*', 'venv/*', 'env/*',
            'node_modules/*', '.npm/*',
            '.DS_Store', 'Thumbs.db',
            '*.log', '*.tmp', '*.temp',
            '.pytest_cache/*', '.coverage',
            'build/*', 'dist/*', '*.egg-info/*'
        ]
        
        self.size_limits = {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'min_file_size': 1  # 1 byte
        }
        
        self.priority_patterns = [
            '*.py', '*.pyx', '*.pyi',
            'requirements*.txt', 'setup.py',
            'Dockerfile', 'docker-compose*',
            '*.sql', '*.yaml', '*.yml'
        ]
    
    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped"""
        path = Path(file_path)
        
        # Check skip patterns
        for pattern in self.skip_patterns:
            if fnmatch.fnmatch(str(path), pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        
        # Check file size
        try:
            file_size = path.stat().st_size
            if (file_size > self.size_limits['max_file_size'] or 
                file_size < self.size_limits['min_file_size']):
                return True
        except Exception:
            return True
        
        return False
    
    def get_file_priority(self, file_path: str) -> int:
        """Get file analysis priority (higher number = higher priority)"""
        path = Path(file_path)
        
        # Python files have highest priority
        if path.suffix == '.py':
            return 100
        
        # Configuration files
        for pattern in self.priority_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return 50
        
        # Other text files
        text_extensions = {'.txt', '.md', '.rst', '.yaml', '.yml', '.json', '.xml'}
        if path.suffix.lower() in text_extensions:
            return 25
        
        return 1

class ParallelAnalyzer:
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.cache_manager = CacheManager()
        self.file_filter = SmartFileFilter()
        self.metrics = PerformanceMetrics(
            total_files=0, analyzed_files=0, skipped_files=0,
            cache_hits=0, cache_misses=0, total_time=0,
            analysis_time=0, cache_time=0, avg_file_time=0
        )
    
    def analyze_single_file(self, file_path: str, analyzer_func: callable) -> Optional[Dict]:
        """Analyze single file with caching"""
        start_time = time.time()
        
        try:
            # Check if should skip
            if self.file_filter.should_skip_file(file_path):
                self.metrics.skipped_files += 1
                return None
            
            # Check cache
            cache_start = time.time()
            if self.cache_manager.is_file_cached(file_path):
                cached_result = self.cache_manager.get_cached_analysis(file_path)
                if cached_result:
                    self.metrics.cache_hits += 1
                    self.metrics.cache_time += time.time() - cache_start
                    return cached_result
            
            self.metrics.cache_misses += 1
            self.metrics.cache_time += time.time() - cache_start
            
            # Perform analysis
            analysis_start = time.time()
            result = analyzer_func(file_path)
            self.metrics.analysis_time += time.time() - analysis_start
            
            # Cache result
            if result:
                self.cache_manager.cache_analysis(file_path, result)
                self.metrics.analyzed_files += 1
            
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing {file_path}: {e}")
            return None
        finally:
            self.metrics.total_time += time.time() - start_time
    
    def analyze_directory_parallel(self, directory: str, analyzer_func: callable, 
                                 file_pattern: str = "*.py") -> Dict[str, Any]:
        """Analyze directory in parallel"""
        start_time = time.time()
        directory_path = Path(directory)
        
        # Find all files
        all_files = []
        for file_path in directory_path.rglob(file_pattern):
            if file_path.is_file():
                all_files.append(str(file_path))
        
        self.metrics.total_files = len(all_files)
        
        # Sort by priority
        all_files.sort(key=self.file_filter.get_file_priority, reverse=True)
        
        # Analyze in parallel
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.analyze_single_file, file_path, analyzer_func): file_path
                for file_path in all_files
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results[file_path] = result
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
        
        # Calculate final metrics
        total_time = time.time() - start_time
        self.metrics.total_time = total_time
        
        if self.metrics.analyzed_files > 0:
            self.metrics.avg_file_time = self.metrics.analysis_time / self.metrics.analyzed_files
        
        return {
            'results': results,
            'metrics': asdict(self.metrics),
            'cache_stats': self.cache_manager.get_cache_stats()
        }
    
    def analyze_with_progress(self, directory: str, analyzer_func: callable,
                            progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Analyze with progress reporting"""
        directory_path = Path(directory)
        all_files = list(directory_path.rglob("*.py"))
        self.metrics.total_files = len(all_files)
        
        results = {}
        processed = 0
        
        for file_path in all_files:
            file_str = str(file_path)
            result = self.analyze_single_file(file_str, analyzer_func)
            
            if result:
                results[file_str] = result
            
            processed += 1
            
            if progress_callback:
                progress_callback({
                    'processed': processed,
                    'total': len(all_files),
                    'current_file': file_str,
                    'progress_percent': (processed / len(all_files)) * 100
                })
        
        return {
            'results': results,
            'metrics': asdict(self.metrics)
        }

class MemoryOptimizer:
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.current_memory_usage = 0
        self.result_chunks = []
        self.chunk_size = 100  # Files per chunk
    
    def should_flush_memory(self) -> bool:
        """Check if memory should be flushed"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > self.max_memory_mb
        except ImportError:
            # Fallback to chunk-based flushing
            return len(self.result_chunks) > self.chunk_size
    
    def optimize_results(self, results: Dict) -> Dict:
        """Optimize results to reduce memory usage"""
        optimized = {}
        
        for file_path, result in results.items():
            # Keep only essential information
            if isinstance(result, dict):
                optimized[file_path] = {
                    'summary': result.get('summary', {}),
                    'constructs_count': result.get('constructs_count', 0),
                    'security_issues': result.get('security_issues', []),
                    'performance_issues': result.get('performance_issues', [])
                }
            else:
                optimized[file_path] = result
        
        return optimized

# Example usage function
def create_optimized_analyzer():
    """Create an optimized analyzer instance"""
    return ParallelAnalyzer(max_workers=8)

if __name__ == "__main__":
    # Test the performance optimizer
    print("Testing Performance Optimizer...")
    
    def dummy_analyzer(file_path: str) -> Dict:
        """Dummy analyzer for testing"""
        return {
            'file_path': file_path,
            'analysis_time': time.time(),
            'constructs_count': 50,
            'summary': 'Test analysis'
        }
    
    optimizer = ParallelAnalyzer(max_workers=4)
    
    # Test on our test directory
    test_dir = "/home/dev/code/bw_automate/test_projects/comprehensive_python_project"
    
    print(f"Analyzing directory: {test_dir}")
    results = optimizer.analyze_directory_parallel(test_dir, dummy_analyzer)
    
    print(f"Results: {len(results['results'])} files analyzed")
    print(f"Metrics: {results['metrics']}")
    print(f"Cache stats: {results['cache_stats']}")
    
    print("Performance Optimizer test completed!")