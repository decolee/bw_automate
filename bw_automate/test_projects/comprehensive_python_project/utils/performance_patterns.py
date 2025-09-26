#!/usr/bin/env python3
"""
Performance Patterns - Testing performance-related code patterns
Both efficient and inefficient patterns for analysis
"""

import time
import threading
import multiprocessing
import concurrent.futures
import asyncio
import weakref
import gc
import sys
from typing import List, Dict, Any, Iterator, Generator
from collections import defaultdict, deque, Counter
from functools import lru_cache, wraps, partial
from itertools import islice, chain, cycle, compress
import heapq
import bisect

# === INEFFICIENT PATTERNS (Performance Issues) ===

class InEfficientPatterns:
    """Examples of inefficient code patterns for performance testing"""
    
    def inefficient_string_concatenation(self, items: List[str]) -> str:
        """PERFORMANCE ISSUE: String concatenation in loop"""
        result = ""
        for item in items:
            result += item + " "  # Creates new string each time
        return result
    
    def inefficient_list_concatenation(self, lists: List[List[int]]) -> List[int]:
        """PERFORMANCE ISSUE: List concatenation in loop"""
        result = []
        for lst in lists:
            result = result + lst  # Creates new list each time
        return result
    
    def inefficient_membership_check(self, items: List[int], targets: List[int]) -> List[bool]:
        """PERFORMANCE ISSUE: List membership check O(n)"""
        results = []
        for target in targets:
            if target in items:  # O(n) for each check
                results.append(True)
            else:
                results.append(False)
        return results
    
    def inefficient_nested_loops(self, data: List[List[int]]) -> int:
        """PERFORMANCE ISSUE: Unnecessary nested loops"""
        total = 0
        for i in range(len(data)):
            for j in range(len(data[i])):
                for k in range(len(data[i])):  # Redundant loop
                    if j == k:
                        total += data[i][j]
        return total
    
    def inefficient_sorting_in_loop(self, data: List[List[int]]) -> List[List[int]]:
        """PERFORMANCE ISSUE: Sorting in loop when not necessary"""
        results = []
        for sublist in data:
            sorted_list = sorted(sublist)  # Sorting each time
            results.append(sorted_list)
        return results
    
    def inefficient_dict_access(self, data: Dict[str, Any]) -> List[Any]:
        """PERFORMANCE ISSUE: Repeated dict.keys() calls"""
        results = []
        for _ in range(1000):
            for key in data.keys():  # Creates new view each time
                if key in data:  # Redundant check
                    results.append(data[key])
        return results
    
    def memory_leak_pattern(self) -> List[Any]:
        """PERFORMANCE ISSUE: Memory leak pattern"""
        cache = []
        for i in range(10000):
            large_object = [0] * 1000  # Large object
            cache.append(large_object)  # Never cleaned up
            if i % 100 == 0:
                # Partial cleanup but creates fragmentation
                cache = cache[::2]
        return cache
    
    def inefficient_file_operations(self, filename: str):
        """PERFORMANCE ISSUE: Multiple file opens"""
        results = []
        for i in range(100):
            with open(filename, 'r') as f:  # Opening file multiple times
                content = f.read()
                results.append(len(content))
        return results
    
    def inefficient_regex_compilation(self, texts: List[str]) -> List[bool]:
        """PERFORMANCE ISSUE: Recompiling regex in loop"""
        import re
        results = []
        for text in texts:
            pattern = re.compile(r'\d+')  # Compiling each time
            if pattern.search(text):
                results.append(True)
            else:
                results.append(False)
        return results
    
    def inefficient_exception_handling(self, data: List[str]) -> List[int]:
        """PERFORMANCE ISSUE: Exception handling for flow control"""
        results = []
        for item in data:
            try:
                value = int(item)  # Using exceptions for control flow
                results.append(value)
            except ValueError:
                results.append(0)
        return results

# === EFFICIENT PATTERNS (Performance Optimizations) ===

class EfficientPatterns:
    """Examples of efficient code patterns"""
    
    def efficient_string_concatenation(self, items: List[str]) -> str:
        """OPTIMIZED: String joining"""
        return " ".join(items)
    
    def efficient_list_concatenation(self, lists: List[List[int]]) -> List[int]:
        """OPTIMIZED: List comprehension with chain"""
        from itertools import chain
        return list(chain.from_iterable(lists))
    
    def efficient_membership_check(self, items: List[int], targets: List[int]) -> List[bool]:
        """OPTIMIZED: Set membership check O(1)"""
        item_set = set(items)
        return [target in item_set for target in targets]
    
    def efficient_nested_loops(self, data: List[List[int]]) -> int:
        """OPTIMIZED: Single loop with sum"""
        return sum(sum(sublist) for sublist in data)
    
    def efficient_sorting_once(self, data: List[List[int]]) -> List[List[int]]:
        """OPTIMIZED: Sort once and reuse"""
        return [sorted(sublist) for sublist in data]
    
    def efficient_dict_access(self, data: Dict[str, Any]) -> List[Any]:
        """OPTIMIZED: Cache keys and use items()"""
        results = []
        for _ in range(1000):
            results.extend(data.values())  # Direct value access
        return results
    
    def memory_efficient_pattern(self) -> Iterator[List[int]]:
        """OPTIMIZED: Generator for memory efficiency"""
        for i in range(10000):
            yield [0] * 1000  # Generate on demand
    
    @lru_cache(maxsize=128)
    def cached_expensive_operation(self, n: int) -> int:
        """OPTIMIZED: Cached expensive computation"""
        # Simulate expensive operation
        time.sleep(0.01)
        return n * n
    
    def efficient_file_operations(self, filename: str):
        """OPTIMIZED: Single file read"""
        with open(filename, 'r') as f:
            content = f.read()
        
        return [len(content) for _ in range(100)]
    
    def efficient_regex_pattern(self, texts: List[str]) -> List[bool]:
        """OPTIMIZED: Compile regex once"""
        import re
        pattern = re.compile(r'\d+')  # Compile once
        return [bool(pattern.search(text)) for text in texts]
    
    def efficient_validation(self, data: List[str]) -> List[int]:
        """OPTIMIZED: Validation without exceptions"""
        results = []
        for item in data:
            if item.isdigit():  # Check before conversion
                results.append(int(item))
            else:
                results.append(0)
        return results

# === ALGORITHM EFFICIENCY EXAMPLES ===

class AlgorithmExamples:
    """Different algorithm implementations for comparison"""
    
    def bubble_sort(self, arr: List[int]) -> List[int]:
        """INEFFICIENT: O(n²) bubble sort"""
        arr = arr.copy()
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    
    def quick_sort(self, arr: List[int]) -> List[int]:
        """EFFICIENT: O(n log n) average case"""
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return self.quick_sort(left) + middle + self.quick_sort(right)
    
    def linear_search(self, arr: List[int], target: int) -> int:
        """INEFFICIENT: O(n) linear search"""
        for i, value in enumerate(arr):
            if value == target:
                return i
        return -1
    
    def binary_search(self, arr: List[int], target: int) -> int:
        """EFFICIENT: O(log n) binary search"""
        left, right = 0, len(arr) - 1
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1
    
    def fibonacci_recursive(self, n: int) -> int:
        """INEFFICIENT: O(2^n) recursive fibonacci"""
        if n <= 1:
            return n
        return self.fibonacci_recursive(n - 1) + self.fibonacci_recursive(n - 2)
    
    @lru_cache(maxsize=None)
    def fibonacci_memoized(self, n: int) -> int:
        """EFFICIENT: O(n) memoized fibonacci"""
        if n <= 1:
            return n
        return self.fibonacci_memoized(n - 1) + self.fibonacci_memoized(n - 2)
    
    def fibonacci_iterative(self, n: int) -> int:
        """EFFICIENT: O(n) iterative fibonacci"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

# === MEMORY MANAGEMENT PATTERNS ===

class MemoryPatterns:
    """Memory management and optimization patterns"""
    
    def __init__(self):
        self.cache = {}
        self.weak_cache = weakref.WeakValueDictionary()
    
    def memory_heavy_operation(self, size: int) -> List[int]:
        """Create large data structure"""
        return list(range(size))
    
    def with_manual_cleanup(self, size: int):
        """Manual memory cleanup"""
        large_data = self.memory_heavy_operation(size)
        # Process data
        result = sum(large_data)
        # Manual cleanup
        del large_data
        gc.collect()  # Force garbage collection
        return result
    
    def with_weak_references(self, obj: Any) -> weakref.ref:
        """Using weak references to avoid circular references"""
        return weakref.ref(obj)
    
    def generator_for_memory_efficiency(self, n: int) -> Generator[int, None, None]:
        """Use generator for memory efficiency"""
        for i in range(n):
            # Yield values on demand instead of creating large list
            yield i * i
    
    def slots_for_memory_optimization(self):
        """Class with __slots__ for memory optimization"""
        class OptimizedClass:
            __slots__ = ['x', 'y', 'z']  # Reduces memory overhead
            
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        return OptimizedClass
    
    def memory_pool_pattern(self):
        """Object pool pattern for memory reuse"""
        class ObjectPool:
            def __init__(self, create_func, max_size=10):
                self.create_func = create_func
                self.pool = deque(maxlen=max_size)
            
            def get_object(self):
                if self.pool:
                    return self.pool.popleft()
                return self.create_func()
            
            def return_object(self, obj):
                # Reset object state
                if hasattr(obj, 'reset'):
                    obj.reset()
                self.pool.append(obj)
        
        return ObjectPool

# === CONCURRENCY PATTERNS ===

class ConcurrencyPatterns:
    """Concurrency and parallelism patterns"""
    
    def cpu_bound_task(self, n: int) -> int:
        """CPU-intensive task"""
        total = 0
        for i in range(n):
            total += i * i
        return total
    
    def io_bound_task(self, duration: float) -> str:
        """I/O-bound task simulation"""
        time.sleep(duration)
        return f"Task completed after {duration}s"
    
    def sequential_processing(self, tasks: List[int]) -> List[int]:
        """INEFFICIENT: Sequential processing"""
        results = []
        for task in tasks:
            result = self.cpu_bound_task(task)
            results.append(result)
        return results
    
    def thread_pool_processing(self, tasks: List[int]) -> List[int]:
        """OPTIMIZED: Thread pool for I/O-bound tasks"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.cpu_bound_task, task) for task in tasks]
            results = [future.result() for future in futures]
        return results
    
    def process_pool_processing(self, tasks: List[int]) -> List[int]:
        """OPTIMIZED: Process pool for CPU-bound tasks"""
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self.cpu_bound_task, tasks))
        return results
    
    async def async_processing(self, tasks: List[float]) -> List[str]:
        """OPTIMIZED: Async processing for I/O-bound tasks"""
        async def async_io_task(duration: float) -> str:
            await asyncio.sleep(duration)
            return f"Async task completed after {duration}s"
        
        results = await asyncio.gather(*[async_io_task(task) for task in tasks])
        return results
    
    def producer_consumer_pattern(self):
        """Producer-consumer pattern with queue"""
        import queue
        
        def producer(q: queue.Queue, items: List[Any]):
            for item in items:
                q.put(item)
                time.sleep(0.1)
            q.put(None)  # Sentinel value
        
        def consumer(q: queue.Queue) -> List[Any]:
            results = []
            while True:
                item = q.get()
                if item is None:
                    break
                # Process item
                results.append(f"Processed: {item}")
                q.task_done()
            return results
        
        return producer, consumer

# === DATA STRUCTURE OPTIMIZATIONS ===

class DataStructureOptimizations:
    """Optimized data structure usage"""
    
    def efficient_counting(self, items: List[str]) -> Dict[str, int]:
        """OPTIMIZED: Use Counter for counting"""
        return dict(Counter(items))
    
    def inefficient_counting(self, items: List[str]) -> Dict[str, int]:
        """INEFFICIENT: Manual counting"""
        counts = {}
        for item in items:
            if item in counts:
                counts[item] += 1
            else:
                counts[item] = 1
        return counts
    
    def efficient_grouping(self, items: List[tuple]) -> Dict[str, List[Any]]:
        """OPTIMIZED: Use defaultdict for grouping"""
        groups = defaultdict(list)
        for key, value in items:
            groups[key].append(value)
        return dict(groups)
    
    def efficient_deque_operations(self) -> deque:
        """OPTIMIZED: Use deque for queue operations"""
        d = deque()
        for i in range(1000):
            d.appendleft(i)  # O(1) operation
        return d
    
    def inefficient_list_operations(self) -> List[int]:
        """INEFFICIENT: List operations with O(n) complexity"""
        lst = []
        for i in range(1000):
            lst.insert(0, i)  # O(n) operation
        return lst
    
    def efficient_set_operations(self, list1: List[int], list2: List[int]) -> tuple:
        """OPTIMIZED: Set operations for intersection/union"""
        set1, set2 = set(list1), set(list2)
        intersection = set1 & set2
        union = set1 | set2
        difference = set1 - set2
        return intersection, union, difference
    
    def efficient_heap_operations(self, items: List[int]) -> List[int]:
        """OPTIMIZED: Use heap for priority queue"""
        heap = items.copy()
        heapq.heapify(heap)
        
        # Get top 5 smallest items
        top_5 = []
        for _ in range(min(5, len(heap))):
            if heap:
                top_5.append(heapq.heappop(heap))
        return top_5

# === CACHING AND MEMOIZATION ===

class CachingPatterns:
    """Various caching and memoization patterns"""
    
    def __init__(self):
        self.manual_cache = {}
    
    @lru_cache(maxsize=128)
    def lru_cached_function(self, x: int, y: int) -> int:
        """LRU cache decorator"""
        time.sleep(0.01)  # Simulate expensive operation
        return x * y + x + y
    
    def manual_caching(self, x: int, y: int) -> int:
        """Manual caching implementation"""
        key = (x, y)
        if key in self.manual_cache:
            return self.manual_cache[key]
        
        # Expensive computation
        result = x * y + x + y
        self.manual_cache[key] = result
        return result
    
    def timed_cache(self, ttl_seconds: int = 60):
        """Time-based cache decorator"""
        def decorator(func):
            cache = {}
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))
                now = time.time()
                
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return result
                
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result
            
            return wrapper
        return decorator
    
    @timed_cache(ttl_seconds=30)
    def expensive_api_call(self, endpoint: str) -> Dict[str, Any]:
        """Simulated expensive API call with caching"""
        time.sleep(0.5)  # Simulate network delay
        return {"endpoint": endpoint, "data": "response_data", "timestamp": time.time()}

# Performance measurement utilities
class PerformanceMeasurement:
    """Performance measurement and profiling utilities"""
    
    @staticmethod
    def time_function(func, *args, **kwargs):
        """Measure function execution time"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def memory_usage():
        """Get current memory usage"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    @staticmethod
    def profile_function(func):
        """Decorator to profile function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import cProfile
            import pstats
            
            profiler = cProfile.Profile()
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(10)  # Top 10 time consumers
            
            return result
        return wrapper

# Example usage and testing
if __name__ == "__main__":
    print("=== Performance Patterns Testing ===")
    
    # Test inefficient patterns
    inefficient = InEfficientPatterns()
    efficient = EfficientPatterns()
    
    # String concatenation comparison
    test_strings = ["hello", "world", "python", "performance"] * 1000
    
    start_time = time.perf_counter()
    result1 = inefficient.inefficient_string_concatenation(test_strings)
    time1 = time.perf_counter() - start_time
    
    start_time = time.perf_counter()
    result2 = efficient.efficient_string_concatenation(test_strings)
    time2 = time.perf_counter() - start_time
    
    print(f"String concatenation:")
    print(f"  Inefficient: {time1:.4f}s")
    print(f"  Efficient: {time2:.4f}s")
    print(f"  Speedup: {time1/time2:.2f}x")
    
    # Algorithm comparison
    algorithms = AlgorithmExamples()
    test_data = list(range(1000, 0, -1))  # Reverse sorted for worst case
    
    start_time = time.perf_counter()
    sorted1 = algorithms.bubble_sort(test_data[:100])  # Smaller dataset for bubble sort
    time1 = time.perf_counter() - start_time
    
    start_time = time.perf_counter()
    sorted2 = algorithms.quick_sort(test_data)
    time2 = time.perf_counter() - start_time
    
    print(f"\nSorting algorithms:")
    print(f"  Bubble sort (100 items): {time1:.4f}s")
    print(f"  Quick sort (1000 items): {time2:.4f}s")
    
    # Caching test
    caching = CachingPatterns()
    
    start_time = time.perf_counter()
    for i in range(10):
        result = caching.lru_cached_function(i % 5, i % 3)  # Repeated calls
    time_cached = time.perf_counter() - start_time
    
    print(f"\nCaching test:")
    print(f"  LRU cached calls: {time_cached:.4f}s")
    
    # Memory pattern test
    memory = MemoryPatterns()
    print(f"\nMemory optimization:")
    
    # Test generator vs list
    start_mem = PerformanceMeasurement.memory_usage()
    gen = memory.generator_for_memory_efficiency(1000000)
    first_10 = list(islice(gen, 10))
    end_mem = PerformanceMeasurement.memory_usage()
    print(f"  Generator memory usage: {end_mem - start_mem:.2f} MB")
    
    print("\n=== Performance testing completed! ===")