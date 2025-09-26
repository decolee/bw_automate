"""
Asynchronous Programming and Concurrency Patterns
Testing asyncio, threading, multiprocessing, and concurrent execution patterns
"""

import asyncio
import threading
import multiprocessing
import concurrent.futures
import time
import random
import logging
import queue
import signal
import os
import sys
from typing import List, Dict, Any, Optional, Callable, Awaitable, Generator
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from functools import wraps, partial
from collections import deque, defaultdict
import json
import socket
import tempfile

# Async/Await Patterns
class AsyncTaskManager:
    def __init__(self):
        self.tasks = {}
        self.running = False
        self.semaphore = asyncio.Semaphore(10)  # Limit concurrent tasks
        
    async def create_task(self, coro: Awaitable, task_id: str = None) -> str:
        """Create and track an async task"""
        if task_id is None:
            task_id = f"task_{len(self.tasks)}"
        
        task = asyncio.create_task(coro)
        self.tasks[task_id] = {
            'task': task,
            'created_at': datetime.now(),
            'status': 'running'
        }
        
        # Add completion callback
        task.add_done_callback(lambda t: self._task_completed(task_id, t))
        return task_id
    
    def _task_completed(self, task_id: str, task: asyncio.Task):
        """Handle task completion"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now()
            
            if task.exception():
                self.tasks[task_id]['error'] = str(task.exception())
                self.tasks[task_id]['status'] = 'failed'
    
    async def wait_for_task(self, task_id: str, timeout: float = None) -> Any:
        """Wait for a specific task to complete"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]['task']
        try:
            if timeout:
                return await asyncio.wait_for(task, timeout=timeout)
            else:
                return await task
        except asyncio.TimeoutError:
            task.cancel()
            self.tasks[task_id]['status'] = 'cancelled'
            raise
    
    async def wait_for_all(self, timeout: float = None) -> Dict[str, Any]:
        """Wait for all tasks to complete"""
        active_tasks = {
            task_id: info['task'] 
            for task_id, info in self.tasks.items() 
            if info['status'] == 'running'
        }
        
        if not active_tasks:
            return {}
        
        try:
            if timeout:
                done, pending = await asyncio.wait(
                    active_tasks.values(), 
                    timeout=timeout, 
                    return_when=asyncio.ALL_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
            else:
                await asyncio.gather(*active_tasks.values(), return_exceptions=True)
        except Exception as e:
            logging.error(f"Error waiting for tasks: {e}")
        
        results = {}
        for task_id, task in active_tasks.items():
            try:
                results[task_id] = task.result()
            except Exception as e:
                results[task_id] = f"Error: {e}"
        
        return results
    
    def get_task_status(self) -> Dict[str, Dict]:
        """Get status of all tasks"""
        return {
            task_id: {
                'status': info['status'],
                'created_at': info['created_at'].isoformat(),
                'completed_at': info.get('completed_at', {}).isoformat() if info.get('completed_at') else None,
                'error': info.get('error')
            }
            for task_id, info in self.tasks.items()
        }

# Async Context Managers
@asynccontextmanager
async def async_database_connection(connection_string: str):
    """Simulated async database connection context manager"""
    print(f"Connecting to database: {connection_string}")
    connection = {
        'connected': True,
        'connection_string': connection_string,
        'queries_executed': 0
    }
    
    try:
        await asyncio.sleep(0.1)  # Simulate connection time
        yield connection
    finally:
        print(f"Closing database connection. Queries executed: {connection['queries_executed']}")
        connection['connected'] = False

@asynccontextmanager
async def async_rate_limiter(requests_per_second: float):
    """Async rate limiter context manager"""
    last_request_time = 0
    min_interval = 1.0 / requests_per_second
    
    async def rate_limited_function():
        nonlocal last_request_time
        current_time = time.time()
        time_since_last = current_time - last_request_time
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        last_request_time = time.time()
    
    yield rate_limited_function

# Async Generators and Iterators
class AsyncDataStream:
    def __init__(self, data_source: List[Any], chunk_size: int = 10, delay: float = 0.1):
        self.data_source = data_source
        self.chunk_size = chunk_size
        self.delay = delay
        self.position = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.position >= len(self.data_source):
            raise StopAsyncIteration
        
        # Simulate async data fetching
        await asyncio.sleep(self.delay)
        
        chunk_end = min(self.position + self.chunk_size, len(self.data_source))
        chunk = self.data_source[self.position:chunk_end]
        self.position = chunk_end
        
        return chunk

async def async_data_generator(count: int, delay: float = 0.1) -> Generator[Dict, None, None]:
    """Async generator for streaming data"""
    for i in range(count):
        await asyncio.sleep(delay)
        yield {
            'id': i,
            'timestamp': datetime.now().isoformat(),
            'data': f"Record {i}",
            'random_value': random.randint(1, 100)
        }

# Async HTTP Client Simulation
class AsyncHTTPClient:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        self.session_stats = {
            'requests_made': 0,
            'total_response_time': 0,
            'errors': 0
        }
    
    async def get(self, url: str, timeout: float = 5.0) -> Dict:
        """Simulated async HTTP GET request"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Simulate network request
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
                # Simulate random failures
                if random.random() < 0.1:  # 10% failure rate
                    raise Exception(f"HTTP Error 500: Internal Server Error for {url}")
                
                response_time = time.time() - start_time
                self.session_stats['requests_made'] += 1
                self.session_stats['total_response_time'] += response_time
                
                return {
                    'url': url,
                    'status_code': 200,
                    'response_time': response_time,
                    'data': f"Response data from {url}",
                    'headers': {'Content-Type': 'application/json'},
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.session_stats['errors'] += 1
                return {
                    'url': url,
                    'status_code': 500,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    async def batch_get(self, urls: List[str], max_concurrent: int = 5) -> List[Dict]:
        """Make multiple HTTP requests concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_get(url: str):
            async with semaphore:
                return await self.get(url)
        
        tasks = [limited_get(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Threading Patterns
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1):
        with self._lock:
            self._value += amount
    
    def decrement(self, amount: int = 1):
        with self._lock:
            self._value -= amount
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value

class ThreadPool:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        self.counter = ThreadSafeCounter()
    
    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task to the thread pool"""
        task_id = f"thread_task_{self.counter.value}"
        self.counter.increment()
        
        future = self.executor.submit(func, *args, **kwargs)
        self.tasks[task_id] = {
            'future': future,
            'submitted_at': datetime.now(),
            'function': func.__name__ if hasattr(func, '__name__') else str(func)
        }
        
        return task_id
    
    def get_result(self, task_id: str, timeout: float = None) -> Any:
        """Get result from a specific task"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        future = self.tasks[task_id]['future']
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise
        except Exception as e:
            raise e
    
    def get_all_results(self, timeout: float = None) -> Dict[str, Any]:
        """Get results from all submitted tasks"""
        results = {}
        
        for task_id, task_info in self.tasks.items():
            try:
                results[task_id] = task_info['future'].result(timeout=timeout)
            except Exception as e:
                results[task_id] = f"Error: {e}"
        
        return results
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        self.executor.shutdown(wait=wait)

# Producer-Consumer Pattern
class ProducerConsumer:
    def __init__(self, queue_size: int = 10):
        self.queue = queue.Queue(maxsize=queue_size)
        self.producers = []
        self.consumers = []
        self.running = False
        self.stats = {
            'items_produced': 0,
            'items_consumed': 0,
            'production_errors': 0,
            'consumption_errors': 0
        }
        self.stats_lock = threading.Lock()
    
    def producer_worker(self, producer_id: str, produce_func: Callable, 
                       production_rate: float = 1.0):
        """Producer worker function"""
        while self.running:
            try:
                item = produce_func()
                self.queue.put(item, timeout=1.0)
                
                with self.stats_lock:
                    self.stats['items_produced'] += 1
                
                time.sleep(1.0 / production_rate)  # Rate limiting
                
            except queue.Full:
                logging.warning(f"Producer {producer_id}: Queue is full")
            except Exception as e:
                with self.stats_lock:
                    self.stats['production_errors'] += 1
                logging.error(f"Producer {producer_id} error: {e}")
    
    def consumer_worker(self, consumer_id: str, consume_func: Callable,
                       consumption_rate: float = 1.0):
        """Consumer worker function"""
        while self.running:
            try:
                item = self.queue.get(timeout=1.0)
                consume_func(item)
                self.queue.task_done()
                
                with self.stats_lock:
                    self.stats['items_consumed'] += 1
                
                time.sleep(1.0 / consumption_rate)  # Rate limiting
                
            except queue.Empty:
                continue
            except Exception as e:
                with self.stats_lock:
                    self.stats['consumption_errors'] += 1
                logging.error(f"Consumer {consumer_id} error: {e}")
    
    def start(self, num_producers: int = 2, num_consumers: int = 2,
              produce_func: Callable = None, consume_func: Callable = None):
        """Start producer and consumer threads"""
        self.running = True
        
        # Default functions
        if produce_func is None:
            produce_func = lambda: {
                'id': random.randint(1000, 9999),
                'data': f"Item {datetime.now().isoformat()}",
                'value': random.uniform(0, 100)
            }
        
        if consume_func is None:
            consume_func = lambda item: print(f"Processed: {item}")
        
        # Start producers
        for i in range(num_producers):
            producer = threading.Thread(
                target=self.producer_worker,
                args=(f"producer_{i}", produce_func, 2.0),
                daemon=True
            )
            producer.start()
            self.producers.append(producer)
        
        # Start consumers
        for i in range(num_consumers):
            consumer = threading.Thread(
                target=self.consumer_worker,
                args=(f"consumer_{i}", consume_func, 1.5),
                daemon=True
            )
            consumer.start()
            self.consumers.append(consumer)
    
    def stop(self):
        """Stop all producers and consumers"""
        self.running = False
        
        # Wait for threads to finish
        for producer in self.producers:
            producer.join(timeout=2.0)
        
        for consumer in self.consumers:
            consumer.join(timeout=2.0)
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self.stats_lock:
            return self.stats.copy()

# Multiprocessing Patterns
class ProcessPool:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.pool = None
        self.tasks = {}
    
    def __enter__(self):
        self.pool = multiprocessing.Pool(processes=self.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pool:
            self.pool.close()
            self.pool.join()
    
    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task to the process pool"""
        if not self.pool:
            raise RuntimeError("ProcessPool must be used as context manager")
        
        task_id = f"process_task_{len(self.tasks)}"
        result = self.pool.apply_async(func, args, kwargs)
        
        self.tasks[task_id] = {
            'result': result,
            'submitted_at': datetime.now(),
            'function': func.__name__ if hasattr(func, '__name__') else str(func)
        }
        
        return task_id
    
    def get_result(self, task_id: str, timeout: float = None) -> Any:
        """Get result from a specific task"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        result = self.tasks[task_id]['result']
        return result.get(timeout=timeout)
    
    def map(self, func: Callable, iterable: List[Any], chunksize: int = None) -> List[Any]:
        """Map function over iterable using multiple processes"""
        if not self.pool:
            raise RuntimeError("ProcessPool must be used as context manager")
        
        return self.pool.map(func, iterable, chunksize=chunksize)

def cpu_intensive_task(n: int) -> Dict:
    """CPU intensive task for multiprocessing testing"""
    start_time = time.time()
    
    # Simulate CPU intensive work
    result = 0
    for i in range(n * 1000000):
        result += i ** 0.5
    
    return {
        'input': n,
        'result': result,
        'execution_time': time.time() - start_time,
        'process_id': os.getpid()
    }

# Event-Driven Patterns
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        with self.lock:
            self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        with self.lock:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
    
    def publish(self, event_type: str, data: Any = None):
        """Publish an event"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'event_id': f"event_{len(self.event_history)}"
        }
        
        with self.lock:
            self.event_history.append(event)
            callbacks = self.subscribers[event_type].copy()
        
        # Execute callbacks outside of lock to prevent deadlocks
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Handle async callbacks
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception as e:
                logging.error(f"Error in event callback: {e}")
    
    def get_event_history(self, event_type: str = None, limit: int = None) -> List[Dict]:
        """Get event history"""
        with self.lock:
            events = list(self.event_history)
        
        if event_type:
            events = [e for e in events if e['type'] == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events

# Async Server Pattern
class AsyncServer:
    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self.server = None
        self.clients = {}
        self.message_handlers = {}
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add a message handler for specific message types"""
        self.message_handlers[message_type] = handler
    
    async def handle_client(self, reader: asyncio.StreamReader, 
                           writer: asyncio.StreamWriter):
        """Handle individual client connection"""
        client_address = writer.get_extra_info('peername')
        client_id = f"{client_address[0]}:{client_address[1]}"
        
        self.clients[client_id] = {
            'reader': reader,
            'writer': writer,
            'connected_at': datetime.now(),
            'messages_received': 0
        }
        
        try:
            while True:
                # Read message
                data = await reader.read(1024)
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                self.clients[client_id]['messages_received'] += 1
                
                try:
                    # Parse message (assuming JSON format)
                    parsed_message = json.loads(message)
                    message_type = parsed_message.get('type', 'unknown')
                    
                    # Handle message
                    if message_type in self.message_handlers:
                        response = await self.message_handlers[message_type](parsed_message)
                    else:
                        response = {'type': 'error', 'message': f'Unknown message type: {message_type}'}
                    
                    # Send response
                    response_data = json.dumps(response).encode('utf-8') + b'\n'
                    writer.write(response_data)
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    error_response = {'type': 'error', 'message': 'Invalid JSON format'}
                    response_data = json.dumps(error_response).encode('utf-8') + b'\n'
                    writer.write(response_data)
                    await writer.drain()
                
        except Exception as e:
            logging.error(f"Error handling client {client_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def start(self):
        """Start the async server"""
        self.server = await asyncio.start_server(
            self.handle_client, 
            self.host, 
            self.port
        )
        
        logging.info(f"Server started on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    def get_client_stats(self) -> Dict:
        """Get statistics about connected clients"""
        return {
            'total_clients': len(self.clients),
            'clients': {
                client_id: {
                    'connected_at': info['connected_at'].isoformat(),
                    'messages_received': info['messages_received']
                }
                for client_id, info in self.clients.items()
            }
        }

# Example usage and testing
async def main():
    print("Testing Async Patterns...")
    
    # Test async task manager
    task_manager = AsyncTaskManager()
    
    async def sample_task(duration: float, task_name: str):
        await asyncio.sleep(duration)
        return f"Task {task_name} completed after {duration}s"
    
    # Create some tasks
    task1_id = await task_manager.create_task(sample_task(1.0, "Task1"))
    task2_id = await task_manager.create_task(sample_task(2.0, "Task2"))
    task3_id = await task_manager.create_task(sample_task(0.5, "Task3"))
    
    # Wait for specific task
    result1 = await task_manager.wait_for_task(task1_id)
    print(f"Task 1 result: {result1}")
    
    # Test async HTTP client
    client = AsyncHTTPClient(max_connections=5)
    urls = [
        "https://api.example.com/users",
        "https://api.example.com/posts", 
        "https://api.example.com/comments"
    ]
    
    responses = await client.batch_get(urls)
    print(f"HTTP responses: {len(responses)} received")
    
    # Test async data stream
    data = list(range(50))
    stream = AsyncDataStream(data, chunk_size=5, delay=0.01)
    
    chunks_received = 0
    async for chunk in stream:
        chunks_received += 1
        if chunks_received >= 3:  # Limit for testing
            break
    
    print(f"Received {chunks_received} data chunks")
    
    # Test event bus
    event_bus = EventBus()
    
    def handle_user_event(event):
        print(f"User event received: {event['data']}")
    
    event_bus.subscribe('user_action', handle_user_event)
    event_bus.publish('user_action', {'action': 'login', 'user_id': 123})
    
    print("Async patterns testing completed!")

if __name__ == "__main__":
    # Test threading patterns
    print("Testing Threading Patterns...")
    
    thread_pool = ThreadPool(max_workers=3)
    
    def sample_work(duration: float, work_id: str):
        time.sleep(duration)
        return f"Work {work_id} completed after {duration}s"
    
    # Submit some tasks
    task_ids = []
    for i in range(5):
        task_id = thread_pool.submit(sample_work, random.uniform(0.5, 2.0), f"task_{i}")
        task_ids.append(task_id)
    
    # Get results
    results = thread_pool.get_all_results(timeout=10.0)
    print(f"Thread pool results: {len(results)} tasks completed")
    
    thread_pool.shutdown()
    
    # Test producer-consumer
    producer_consumer = ProducerConsumer(queue_size=5)
    producer_consumer.start(num_producers=2, num_consumers=1)
    
    time.sleep(3)  # Let it run for 3 seconds
    stats = producer_consumer.get_stats()
    print(f"Producer-Consumer stats: {stats}")
    
    producer_consumer.stop()
    
    # Test multiprocessing
    print("Testing Multiprocessing Patterns...")
    
    with ProcessPool(max_workers=2) as pool:
        # Submit CPU intensive tasks
        tasks = [1, 2, 3, 4, 5]
        results = pool.map(cpu_intensive_task, tasks)
        print(f"Multiprocessing results: {len(results)} tasks completed")
    
    # Run async patterns
    print("Running async main...")
    asyncio.run(main())