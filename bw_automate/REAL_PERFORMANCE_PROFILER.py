#!/usr/bin/env python3
"""
⚡ REAL PERFORMANCE PROFILER
Enterprise-grade performance analysis with actual measurements
"""

import cProfile
import pstats
import tracemalloc
import time
import threading
import concurrent.futures
import psutil
import gc
import sys
import json
import os
import statistics
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict
import logging

class SystemResourceMonitor:
    """Real-time system resource monitoring"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.measurements = []
        
    def start_monitoring(self):
        """Start resource monitoring in background thread"""
        self.monitoring = True
        self.measurements = []
        
        def monitor():
            while self.monitoring:
                try:
                    measurement = {
                        'timestamp': time.time(),
                        'cpu_percent': self.process.cpu_percent(),
                        'memory_mb': self.process.memory_info().rss / 1024 / 1024,
                        'memory_percent': self.process.memory_percent(),
                        'threads': self.process.num_threads(),
                        'open_files': len(self.process.open_files()),
                        'system_cpu': psutil.cpu_percent(),
                        'system_memory': psutil.virtual_memory().percent
                    }
                    self.measurements.append(measurement)
                    time.sleep(0.1)  # Sample every 100ms
                except Exception:
                    pass
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return statistics"""
        self.monitoring = False
        
        if not self.measurements:
            return {}
        
        # Calculate statistics
        cpu_values = [m['cpu_percent'] for m in self.measurements]
        memory_values = [m['memory_mb'] for m in self.measurements]
        
        return {
            'duration_seconds': self.measurements[-1]['timestamp'] - self.measurements[0]['timestamp'],
            'samples_collected': len(self.measurements),
            'cpu_usage': {
                'average': statistics.mean(cpu_values),
                'peak': max(cpu_values),
                'minimum': min(cpu_values)
            },
            'memory_usage': {
                'average_mb': statistics.mean(memory_values),
                'peak_mb': max(memory_values),
                'minimum_mb': min(memory_values)
            },
            'thread_count': {
                'average': statistics.mean([m['threads'] for m in self.measurements]),
                'peak': max([m['threads'] for m in self.measurements])
            }
        }

class RealPerformanceProfiler:
    """Production-grade performance profiler with real measurements"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.resource_monitor = SystemResourceMonitor()
        
    def _setup_logging(self):
        """Setup production logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def profile_function_execution(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Profile a function's execution with detailed metrics"""
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Memory tracking
        tracemalloc.start()
        gc.collect()  # Clean start
        
        # CPU profiling
        profiler = cProfile.Profile()
        
        # Execute function
        start_time = time.perf_counter()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        profiler.disable()
        end_time = time.perf_counter()
        
        # Get memory stats
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Stop resource monitoring
        resource_stats = self.resource_monitor.stop_monitoring()
        
        # Analyze profiling data
        stats = pstats.Stats(profiler)
        
        # Get function statistics
        function_stats = []
        for func_name, stats_data in stats.stats.items():
            if len(stats_data) >= 4:
                calls, tottime, cumtime = stats_data[0], stats_data[1], stats_data[2]
                function_stats.append({
                    'function': f"{func_name[0]}:{func_name[1]}({func_name[2]})",
                    'calls': calls,
                    'total_time': tottime,
                    'cumulative_time': cumtime,
                    'time_per_call': tottime / calls if calls > 0 else 0
                })
        
        # Sort by total time
        function_stats.sort(key=lambda x: x['total_time'], reverse=True)
        
        execution_time = end_time - start_time
        
        return {
            'execution_time_seconds': execution_time,
            'success': success,
            'error': error,
            'memory': {
                'current_mb': current_memory / 1024 / 1024,
                'peak_mb': peak_memory / 1024 / 1024,
                'efficiency_score': self._calculate_memory_efficiency(peak_memory, execution_time)
            },
            'cpu': {
                'profile_overhead': getattr(stats, 'total_tt', 0),
                'function_calls': sum(data[0] for data in stats.stats.values() if len(data) > 0),
                'top_functions': function_stats[:10]
            },
            'system_resources': resource_stats,
            'performance_score': self._calculate_performance_score(execution_time, peak_memory, success)
        }
    
    def benchmark_file_processing(self, file_path: str) -> Dict[str, Any]:
        """Benchmark file processing performance"""
        
        def process_file():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simulate real analysis work
            lines = content.split('\n')
            char_count = len(content)
            word_count = len(content.split())
            
            # AST parsing performance
            try:
                import ast
                tree = ast.parse(content)
                node_count = len(list(ast.walk(tree)))
            except:
                node_count = 0
            
            return {
                'lines': len(lines),
                'characters': char_count,
                'words': word_count,
                'ast_nodes': node_count
            }
        
        file_size = os.path.getsize(file_path)
        
        # Profile the file processing
        profile_result = self.profile_function_execution(process_file)
        
        # Calculate throughput metrics
        if profile_result['success']:
            execution_time = profile_result['execution_time_seconds']
            throughput = {
                'bytes_per_second': file_size / execution_time if execution_time > 0 else 0,
                'mb_per_second': (file_size / 1024 / 1024) / execution_time if execution_time > 0 else 0,
                'lines_per_second': profile_result.get('result', {}).get('lines', 0) / execution_time if execution_time > 0 else 0
            }
        else:
            throughput = {'bytes_per_second': 0, 'mb_per_second': 0, 'lines_per_second': 0}
        
        return {
            'file_path': file_path,
            'file_size_bytes': file_size,
            'file_size_mb': file_size / 1024 / 1024,
            'throughput': throughput,
            'profile_data': profile_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def benchmark_concurrent_processing(self, file_paths: List[str], max_workers: int = 4) -> Dict[str, Any]:
        """Benchmark concurrent file processing"""
        
        start_time = time.perf_counter()
        self.resource_monitor.start_monitoring()
        
        # Test different concurrency strategies
        results = {}
        
        # Sequential processing
        sequential_start = time.perf_counter()
        sequential_results = []
        for file_path in file_paths:
            result = self.benchmark_file_processing(file_path)
            sequential_results.append(result)
        sequential_time = time.perf_counter() - sequential_start
        
        # Parallel processing with ThreadPoolExecutor
        thread_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            thread_results = list(executor.map(self.benchmark_file_processing, file_paths))
        thread_time = time.perf_counter() - thread_start
        
        # Parallel processing with ProcessPoolExecutor (if feasible)
        try:
            process_start = time.perf_counter()
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                process_results = list(executor.map(self.benchmark_file_processing, file_paths))
            process_time = time.perf_counter() - process_start
        except Exception as e:
            process_results = []
            process_time = float('inf')
            self.logger.warning(f"Process pool failed: {e}")
        
        total_time = time.perf_counter() - start_time
        resource_stats = self.resource_monitor.stop_monitoring()
        
        # Calculate speedup ratios
        thread_speedup = sequential_time / thread_time if thread_time > 0 else 0
        process_speedup = sequential_time / process_time if process_time < float('inf') and process_time > 0 else 0
        
        # Calculate efficiency scores
        thread_efficiency = thread_speedup / max_workers if max_workers > 0 else 0
        process_efficiency = process_speedup / max_workers if max_workers > 0 and process_speedup > 0 else 0
        
        return {
            'file_count': len(file_paths),
            'max_workers': max_workers,
            'timing': {
                'sequential_seconds': sequential_time,
                'threaded_seconds': thread_time,
                'process_seconds': process_time if process_time < float('inf') else None,
                'total_benchmark_seconds': total_time
            },
            'speedup': {
                'threaded_speedup': thread_speedup,
                'process_speedup': process_speedup if process_speedup > 0 else None
            },
            'efficiency': {
                'threaded_efficiency': thread_efficiency,
                'process_efficiency': process_efficiency if process_efficiency > 0 else None
            },
            'recommendations': self._generate_concurrency_recommendations(
                thread_speedup, process_speedup, thread_efficiency, process_efficiency
            ),
            'system_resources': resource_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def profile_project(self, project_path: str) -> Dict[str, Any]:
        """Alias for unified CLI compatibility"""
        return self.analyze_project_performance(project_path)
    
    def analyze_project_performance(self, project_path: str) -> Dict[str, Any]:
        """Comprehensive performance analysis of entire project"""
        
        project_path = Path(project_path)
        python_files = list(project_path.rglob("*.py"))
        
        if not python_files:
            return {'error': 'No Python files found'}
        
        self.logger.info(f"Performance analysis of {len(python_files)} files")
        
        start_time = time.perf_counter()
        
        # Sample files for detailed analysis (limit to prevent excessive runtime)
        sample_size = min(20, len(python_files))
        sample_files = python_files[:sample_size]
        
        # Individual file benchmarks
        file_benchmarks = []
        for file_path in sample_files:
            try:
                benchmark = self.benchmark_file_processing(str(file_path))
                file_benchmarks.append(benchmark)
            except Exception as e:
                self.logger.error(f"Benchmark failed for {file_path}: {e}")
        
        # Concurrent processing benchmark
        concurrent_benchmark = self.benchmark_concurrent_processing(
            [str(f) for f in sample_files[:10]]  # Limit for concurrency test
        )
        
        # Calculate aggregate metrics
        total_size = sum(os.path.getsize(f) for f in python_files)
        analyzed_size = sum(b['file_size_bytes'] for b in file_benchmarks)
        
        # Performance statistics
        execution_times = [b['profile_data']['execution_time_seconds'] for b in file_benchmarks]
        memory_peaks = [b['profile_data']['memory']['peak_mb'] for b in file_benchmarks]
        throughputs = [b['throughput']['mb_per_second'] for b in file_benchmarks if b['throughput']['mb_per_second'] > 0]
        
        analysis_time = time.perf_counter() - start_time
        
        # Calculate overall performance score
        avg_throughput = statistics.mean(throughputs) if throughputs else 0
        avg_memory = statistics.mean(memory_peaks) if memory_peaks else 0
        
        performance_score = self._calculate_overall_performance_score(
            avg_throughput, avg_memory, concurrent_benchmark['speedup']['threaded_speedup']
        )
        
        return {
            'project_path': str(project_path),
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': len(python_files),
                'analyzed_files': len(file_benchmarks),
                'total_size_mb': total_size / 1024 / 1024,
                'analyzed_size_mb': analyzed_size / 1024 / 1024,
                'analysis_duration_seconds': analysis_time
            },
            'performance_metrics': {
                'average_throughput_mb_per_sec': statistics.mean(throughputs) if throughputs else 0,
                'peak_throughput_mb_per_sec': max(throughputs) if throughputs else 0,
                'average_memory_usage_mb': statistics.mean(memory_peaks) if memory_peaks else 0,
                'peak_memory_usage_mb': max(memory_peaks) if memory_peaks else 0,
                'average_execution_time_seconds': statistics.mean(execution_times) if execution_times else 0
            },
            'concurrency_performance': concurrent_benchmark,
            'overall_performance_score': performance_score,
            'performance_grade': self._get_performance_grade(performance_score),
            'optimization_recommendations': self._generate_optimization_recommendations(
                avg_throughput, avg_memory, concurrent_benchmark
            ),
            'detailed_file_benchmarks': file_benchmarks
        }
    
    def _calculate_memory_efficiency(self, peak_memory_bytes: int, execution_time: float) -> float:
        """Calculate memory efficiency score (0-100)"""
        # Lower memory usage and faster execution = higher score
        mb_per_second = (peak_memory_bytes / 1024 / 1024) / execution_time if execution_time > 0 else float('inf')
        
        # Normalize to 0-100 scale (lower is better for memory usage)
        if mb_per_second == 0:
            return 100
        elif mb_per_second < 1:
            return 95
        elif mb_per_second < 5:
            return 85
        elif mb_per_second < 10:
            return 75
        elif mb_per_second < 25:
            return 60
        elif mb_per_second < 50:
            return 40
        elif mb_per_second < 100:
            return 20
        else:
            return 5
    
    def _calculate_performance_score(self, execution_time: float, peak_memory: int, success: bool) -> float:
        """Calculate overall performance score (0-100)"""
        if not success:
            return 0
        
        # Speed score (faster = higher score)
        if execution_time < 0.01:
            speed_score = 100
        elif execution_time < 0.1:
            speed_score = 90
        elif execution_time < 0.5:
            speed_score = 80
        elif execution_time < 1.0:
            speed_score = 70
        elif execution_time < 2.0:
            speed_score = 60
        elif execution_time < 5.0:
            speed_score = 40
        else:
            speed_score = 20
        
        # Memory score
        memory_mb = peak_memory / 1024 / 1024
        if memory_mb < 1:
            memory_score = 100
        elif memory_mb < 5:
            memory_score = 90
        elif memory_mb < 10:
            memory_score = 80
        elif memory_mb < 25:
            memory_score = 70
        elif memory_mb < 50:
            memory_score = 60
        elif memory_mb < 100:
            memory_score = 40
        else:
            memory_score = 20
        
        # Weighted average
        return (speed_score * 0.6 + memory_score * 0.4)
    
    def _calculate_overall_performance_score(self, throughput: float, memory: float, speedup: float) -> float:
        """Calculate overall project performance score"""
        
        # Throughput score
        if throughput > 50:
            throughput_score = 100
        elif throughput > 25:
            throughput_score = 90
        elif throughput > 10:
            throughput_score = 80
        elif throughput > 5:
            throughput_score = 70
        elif throughput > 1:
            throughput_score = 60
        else:
            throughput_score = 40
        
        # Memory efficiency score
        if memory < 5:
            memory_score = 100
        elif memory < 10:
            memory_score = 90
        elif memory < 25:
            memory_score = 80
        elif memory < 50:
            memory_score = 70
        elif memory < 100:
            memory_score = 60
        else:
            memory_score = 40
        
        # Concurrency score
        if speedup > 3:
            concurrency_score = 100
        elif speedup > 2:
            concurrency_score = 90
        elif speedup > 1.5:
            concurrency_score = 80
        elif speedup > 1.2:
            concurrency_score = 70
        else:
            concurrency_score = 60
        
        # Weighted combination
        return (throughput_score * 0.4 + memory_score * 0.3 + concurrency_score * 0.3)
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert performance score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_concurrency_recommendations(self, thread_speedup: float, process_speedup: float, 
                                            thread_efficiency: float, process_efficiency: float) -> List[str]:
        """Generate concurrency optimization recommendations"""
        recommendations = []
        
        if thread_speedup < 1.2:
            recommendations.append("Threading shows minimal benefit - consider I/O bound optimizations")
        elif thread_efficiency < 0.5:
            recommendations.append("Threading efficiency is low - reduce thread contention")
        
        if process_speedup and process_speedup > thread_speedup * 1.2:
            recommendations.append("Multiprocessing shows better performance - consider process-based parallelism")
        elif process_speedup and process_speedup < thread_speedup:
            recommendations.append("Threading outperforms multiprocessing - stick with threads")
        
        if thread_efficiency > 0.8:
            recommendations.append("Excellent threading efficiency - current approach is optimal")
        
        return recommendations or ["Performance characteristics are within normal range"]
    
    def _generate_optimization_recommendations(self, throughput: float, memory: float, 
                                             concurrent_data: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        if throughput < 5:
            recommendations.append("Low throughput detected - optimize I/O operations and parsing algorithms")
        
        if memory > 50:
            recommendations.append("High memory usage - implement memory-efficient processing techniques")
        
        speedup = concurrent_data['speedup']['threaded_speedup']
        if speedup < 1.5:
            recommendations.append("Limited concurrency benefits - focus on algorithmic optimizations")
        elif speedup > 3:
            recommendations.append("Excellent concurrency scaling - consider increasing parallelism")
        
        if not recommendations:
            recommendations.append("Performance is well-optimized - maintain current implementation")
        
        return recommendations

def main():
    """Main entry point for performance profiler"""
    if len(sys.argv) != 2:
        print("Usage: python REAL_PERFORMANCE_PROFILER.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"Error: Path {project_path} does not exist")
        sys.exit(1)
    
    print("⚡ Starting Real Performance Analysis...")
    
    profiler = RealPerformanceProfiler()
    results = profiler.analyze_project_performance(project_path)
    
    # Save results
    output_file = "REAL_PERFORMANCE_REPORT.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display summary
    if 'error' not in results:
        summary = results['summary']
        metrics = results['performance_metrics']
        
        print(f"\n📊 Performance Summary:")
        print(f"   Files analyzed: {summary['analyzed_files']}/{summary['total_files']}")
        print(f"   Total size: {summary['total_size_mb']:.1f} MB")
        print(f"   Analysis time: {summary['analysis_duration_seconds']:.2f}s")
        
        print(f"\n⚡ Performance Metrics:")
        print(f"   Throughput: {metrics['average_throughput_mb_per_sec']:.1f} MB/s")
        print(f"   Peak throughput: {metrics['peak_throughput_mb_per_sec']:.1f} MB/s")
        print(f"   Average memory: {metrics['average_memory_usage_mb']:.1f} MB")
        print(f"   Peak memory: {metrics['peak_memory_usage_mb']:.1f} MB")
        
        print(f"\n🎯 Overall Performance:")
        print(f"   Score: {results['overall_performance_score']:.1f}/100")
        print(f"   Grade: {results['performance_grade']}")
        
        concurrency = results['concurrency_performance']
        print(f"\n🔄 Concurrency Performance:")
        print(f"   Threading speedup: {concurrency['speedup']['threaded_speedup']:.2f}x")
        if concurrency['speedup']['process_speedup']:
            print(f"   Process speedup: {concurrency['speedup']['process_speedup']:.2f}x")
        
        if results['optimization_recommendations']:
            print(f"\n💡 Optimization Recommendations:")
            for i, rec in enumerate(results['optimization_recommendations'], 1):
                print(f"   {i}. {rec}")
    else:
        print(f"Error: {results['error']}")
    
    print(f"\n📄 Detailed report saved to: {output_file}")
    print("✅ Performance analysis completed!")

if __name__ == "__main__":
    main()