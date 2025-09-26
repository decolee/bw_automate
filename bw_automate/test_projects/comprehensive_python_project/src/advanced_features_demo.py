#!/usr/bin/env python3
"""
Advanced Python Features Demo - Testing All Modern Constructs
This file contains comprehensive examples of Python 3.6+ features for testing
"""

import asyncio
import functools
import typing
from typing import Union, Optional, List, Dict, Set, Tuple, Any, Literal, Final, Protocol, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum, auto, IntEnum
from abc import ABC, abstractmethod
from contextlib import contextmanager, asynccontextmanager
from collections import defaultdict, namedtuple
import weakref
import logging
import json
import sys

# Python 3.8+ imports
try:
    from typing import TypedDict, get_type_hints
    from functools import singledispatch, singledispatchmethod, cached_property
except ImportError:
    TypedDict = dict
    singledispatch = None
    singledispatchmethod = None
    cached_property = property

# Python 3.10+ features
try:
    from types import UnionType
except ImportError:
    UnionType = None

# Type annotations and hints
UserID = typing.NewType('UserID', int)
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Final variables (Python 3.8+)
MAX_CONNECTIONS: Final[int] = 100
DEFAULT_TIMEOUT: Final[float] = 30.0
API_VERSION: Final[str] = "v1.0"

# Literal types (Python 3.8+)
Status = Literal["pending", "running", "completed", "failed"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# TypedDict (Python 3.8+)
class UserInfo(TypedDict):
    id: int
    name: str
    email: str
    active: bool
    roles: List[str]

# Protocol (Python 3.8+)
class Drawable(Protocol):
    def draw(self) -> None: ...
    def get_area(self) -> float: ...

# Generic types
class GenericRepository(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []
    
    def add(self, item: T) -> None:
        self._items.append(item)
    
    def get_all(self) -> List[T]:
        return self._items.copy()

# Advanced Enums
class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    CREATED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    
    def __str__(self) -> str:
        return self.name.lower()

# Dataclasses with advanced features
@dataclass(frozen=True, order=True)
class Point3D:
    x: float
    y: float
    z: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict, compare=False)
    
    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

@dataclass
class Task:
    id: UserID
    title: str
    priority: Priority
    status: TaskStatus = TaskStatus.CREATED
    tags: Set[str] = field(default_factory=set)
    created_at: Optional[float] = field(default_factory=lambda: time.time())
    
    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")

# Metaclass example
class SingletonMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port
        self.connected = False
    
    def connect(self) -> bool:
        if not self.connected:
            print(f"Connecting to {self.host}:{self.port}")
            self.connected = True
        return self.connected

# Descriptors
class ValidatedAttribute:
    def __init__(self, validator_func, default=None):
        self.validator = validator_func
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.default)
    
    def __set__(self, obj, value):
        if not self.validator(value):
            raise ValueError(f"Invalid value for {self.name}: {value}")
        setattr(obj, self.name, value)

class User:
    email = ValidatedAttribute(lambda x: "@" in x and "." in x, "")
    age = ValidatedAttribute(lambda x: 0 <= x <= 150, 0)
    
    def __init__(self, email: str, age: int):
        self.email = email
        self.age = age

# Property decorators and cached properties
class APIClient:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._session = None
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    @base_url.setter
    def base_url(self, value: str) -> None:
        if not value.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        self._base_url = value
    
    @cached_property
    def session(self):
        """Expensive operation cached after first access"""
        print("Creating session...")
        import requests
        return requests.Session()
    
    @staticmethod
    def validate_response_code(code: int) -> bool:
        return 200 <= code < 300
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'APIClient':
        return cls(config['base_url'])

# Context managers
@contextmanager
def database_transaction():
    print("Starting transaction")
    try:
        yield
        print("Committing transaction")
    except Exception as e:
        print(f"Rolling back transaction: {e}")
        raise
    finally:
        print("Closing transaction")

@asynccontextmanager
async def async_database_transaction():
    print("Starting async transaction")
    try:
        yield
        print("Committing async transaction")
    except Exception as e:
        print(f"Rolling back async transaction: {e}")
        raise
    finally:
        print("Closing async transaction")

# Decorators and advanced decorator patterns
def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

def log_calls(logger=None):
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised: {e}")
                raise
        return wrapper
    return decorator

# Singledispatch (Python 3.8+)
@singledispatch
def serialize(obj):
    """Generic serialization function"""
    return str(obj)

@serialize.register
def _(obj: int):
    return {"type": "int", "value": obj}

@serialize.register
def _(obj: str):
    return {"type": "str", "value": obj}

@serialize.register
def _(obj: list):
    return {"type": "list", "items": [serialize(item) for item in obj]}

@serialize.register
def _(obj: dict):
    return {"type": "dict", "data": {k: serialize(v) for k, v in obj.items()}}

# Async programming
class AsyncDataProcessor:
    def __init__(self, concurrency: int = 5):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
    
    async def process_item(self, item: Any) -> Any:
        async with self.semaphore:
            await asyncio.sleep(0.1)  # Simulate processing
            return f"processed_{item}"
    
    async def process_batch(self, items: List[Any]) -> List[Any]:
        tasks = [self.process_item(item) for item in items]
        return await asyncio.gather(*tasks)
    
    async def process_stream(self, items: List[Any]):
        """Async generator for streaming processing"""
        for item in items:
            result = await self.process_item(item)
            yield result

# Async context manager usage
async def example_async_operations():
    processor = AsyncDataProcessor()
    
    # Async with statement
    async with async_database_transaction():
        items = list(range(10))
        results = await processor.process_batch(items)
        print(f"Processed {len(results)} items")
    
    # Async comprehension
    async_results = [item async for item in processor.process_stream(range(5))]
    print(f"Stream results: {async_results}")
    
    # Async for loop
    async for result in processor.process_stream(range(3)):
        print(f"Streamed: {result}")

# Advanced function annotations
def complex_function(
    data: Dict[str, Union[int, str, List[Any]]],
    callback: Optional[typing.Callable[[Any], None]] = None,
    /,  # Positional-only parameters (Python 3.8+)
    timeout: float = 30.0,
    *,  # Keyword-only parameters
    validate: bool = True,
    log_level: LogLevel = "INFO"
) -> Tuple[bool, Optional[str]]:
    """
    Complex function demonstrating advanced type hints and parameter styles
    
    Args:
        data: Input data dictionary (positional-only)
        callback: Optional callback function (positional-only)
        timeout: Operation timeout
        validate: Whether to validate input (keyword-only)
        log_level: Logging level (keyword-only)
    
    Returns:
        Tuple of success status and optional error message
    """
    if validate and not data:
        return False, "Empty data provided"
    
    if callback:
        callback(data)
    
    return True, None

# Walrus operator (Python 3.8+)
def process_data_with_walrus(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Demonstrates walrus operator usage"""
    results = []
    
    for item in data:
        # Walrus operator in if statement
        if (processed_value := item.get('value', 0)) > 10:
            results.append({
                'original': item,
                'processed': processed_value * 2,
                'status': 'high_value'
            })
        # Walrus operator in while loop
        elif (retry_count := item.get('retries', 0)) < 3:
            results.append({
                'original': item,
                'processed': processed_value,
                'status': 'retry',
                'next_retry': retry_count + 1
            })
    
    return results

# Pattern matching (Python 3.10+) - Note: This will only work in Python 3.10+
def analyze_data_structure(data):
    """Demonstrates pattern matching (requires Python 3.10+)"""
    # This is a string representation for compatibility
    pattern_matching_example = '''
    match data:
        case {"type": "user", "id": user_id, "name": str(name)} if len(name) > 0:
            return f"User {name} with ID {user_id}"
        case {"type": "admin", "permissions": list(perms)} if len(perms) > 0:
            return f"Admin with permissions: {', '.join(perms)}"
        case {"type": "guest"}:
            return "Guest user"
        case {"data": [first, *rest]} if len(rest) > 0:
            return f"List starting with {first}, {len(rest)} more items"
        case int(x) if x > 100:
            return f"Large number: {x}"
        case str(s) if s.startswith("prefix_"):
            return f"Prefixed string: {s}"
        case _:
            return "Unknown data structure"
    '''
    
    # Fallback implementation for older Python versions
    if isinstance(data, dict):
        if data.get("type") == "user" and "id" in data and "name" in data:
            return f"User {data['name']} with ID {data['id']}"
        elif data.get("type") == "admin" and "permissions" in data:
            return f"Admin with permissions: {', '.join(data['permissions'])}"
        elif data.get("type") == "guest":
            return "Guest user"
    elif isinstance(data, int) and data > 100:
        return f"Large number: {data}"
    elif isinstance(data, str) and data.startswith("prefix_"):
        return f"Prefixed string: {data}"
    
    return "Unknown data structure"

# Comprehensive example class combining multiple features
class AdvancedDataManager:
    """Comprehensive class demonstrating multiple Python features"""
    
    def __init__(self, name: str, capacity: int = 1000):
        self.name = name
        self.capacity = capacity
        self._data: Dict[str, Any] = {}
        self._observers: List[typing.Callable] = []
        self._lock = asyncio.Lock()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._notify_observers(key, value)
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __repr__(self) -> str:
        return f"AdvancedDataManager(name='{self.name}', items={len(self._data)})"
    
    @log_calls()
    @retry(max_attempts=3)
    def add_observer(self, callback: typing.Callable[[str, Any], None]) -> None:
        """Add observer with decorator demonstrations"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def _notify_observers(self, key: str, value: Any) -> None:
        """Notify all observers of data changes"""
        for observer in self._observers:
            try:
                observer(key, value)
            except Exception as e:
                logging.error(f"Observer notification failed: {e}")
    
    async def async_batch_update(self, updates: Dict[str, Any]) -> None:
        """Async batch update with proper locking"""
        async with self._lock:
            for key, value in updates.items():
                self[key] = value
                await asyncio.sleep(0.001)  # Yield control
    
    @property
    def is_full(self) -> bool:
        return len(self._data) >= self.capacity
    
    @cached_property
    def statistics(self) -> Dict[str, Any]:
        """Expensive computation cached after first access"""
        return {
            'total_items': len(self._data),
            'capacity_used': len(self._data) / self.capacity * 100,
            'data_types': {
                type(v).__name__: sum(1 for v2 in self._data.values() if type(v2) == type(v))
                for v in self._data.values()
            }
        }

# Complex inheritance hierarchy
class BaseProcessor(ABC):
    """Abstract base class for processors"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def async_process(self, data: Any) -> Any:
        """Async process - must be implemented by subclasses"""
        pass

class TextProcessor(BaseProcessor):
    """Text processing implementation"""
    
    def process(self, data: str) -> str:
        return data.strip().upper()
    
    async def async_process(self, data: str) -> str:
        await asyncio.sleep(0.01)
        return self.process(data)

class NumberProcessor(BaseProcessor):
    """Number processing implementation"""
    
    def process(self, data: Union[int, float]) -> float:
        return float(data) * 2
    
    async def async_process(self, data: Union[int, float]) -> float:
        await asyncio.sleep(0.01)
        return self.process(data)

# Multiple inheritance with mixins
class LoggingMixin:
    """Mixin for adding logging capabilities"""
    
    def log(self, message: str, level: str = "INFO") -> None:
        print(f"[{level}] {self.__class__.__name__}: {message}")

class CachingMixin:
    """Mixin for adding caching capabilities"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: Dict[str, Any] = {}
    
    def get_cached(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set_cache(self, key: str, value: Any) -> None:
        self._cache[key] = value

class AdvancedTextProcessor(TextProcessor, LoggingMixin, CachingMixin):
    """Advanced processor with multiple inheritance"""
    
    def __init__(self, cache_size: int = 100):
        super().__init__()
        self.cache_size = cache_size
    
    def process(self, data: str) -> str:
        cache_key = f"process_{hash(data)}"
        
        if cached := self.get_cached(cache_key):
            self.log(f"Cache hit for key: {cache_key}")
            return cached
        
        result = super().process(data)
        self.set_cache(cache_key, result)
        self.log(f"Processed and cached: {data[:20]}...")
        
        return result

# Exception handling with custom exceptions
class DataProcessingError(Exception):
    """Custom exception for data processing errors"""
    
    def __init__(self, message: str, data: Any = None, cause: Exception = None):
        super().__init__(message)
        self.data = data
        self.cause = cause

class ValidationError(DataProcessingError):
    """Specific validation error"""
    pass

def validate_and_process_data(data: Any) -> Any:
    """Comprehensive error handling example"""
    try:
        if data is None:
            raise ValidationError("Data cannot be None", data=data)
        
        if isinstance(data, str) and not data.strip():
            raise ValidationError("String data cannot be empty", data=data)
        
        if isinstance(data, (list, dict)) and len(data) == 0:
            raise ValidationError("Container data cannot be empty", data=data)
        
        # Process the data
        if isinstance(data, str):
            return data.strip().title()
        elif isinstance(data, (int, float)):
            return data * 1.1
        elif isinstance(data, list):
            return [validate_and_process_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: validate_and_process_data(v) for k, v in data.items()}
        else:
            return str(data)
    
    except ValidationError:
        raise  # Re-raise validation errors
    except Exception as e:
        raise DataProcessingError(f"Unexpected error processing data", data=data, cause=e) from e

# Generator functions and yield expressions
def fibonacci_generator(n: int):
    """Generator for Fibonacci sequence"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

def data_pipeline(items: List[Any]):
    """Generator pipeline for data processing"""
    for item in items:
        if item is not None:
            processed = yield item
            if processed:
                yield f"processed_{processed}"

async def async_fibonacci_generator(n: int):
    """Async generator for Fibonacci sequence"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
        await asyncio.sleep(0.001)  # Yield control

# Weak references
class Observer:
    def __init__(self, name: str):
        self.name = name
    
    def notify(self, message: str):
        print(f"Observer {self.name} received: {message}")

class Subject:
    def __init__(self):
        self._observers = weakref.WeakSet()
    
    def attach(self, observer: Observer):
        self._observers.add(observer)
    
    def notify_all(self, message: str):
        for observer in self._observers:
            observer.notify(message)

# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Test various features
    print("=== Advanced Python Features Demo ===")
    
    # Type annotations test
    user_info: UserInfo = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "active": True,
        "roles": ["user", "admin"]
    }
    
    # Dataclass test
    point = Point3D(1.0, 2.0, 3.0, {"color": "red"})
    print(f"Point: {point}, Distance: {point.distance_from_origin():.2f}")
    
    # Enum test
    task = Task(UserID(123), "Complete project", Priority.HIGH)
    print(f"Task: {task}")
    
    # Singledispatch test
    print(f"Serialize int: {serialize(42)}")
    print(f"Serialize list: {serialize([1, 'hello', 3.14])}")
    
    # Decorator test
    @retry(max_attempts=2)
    @log_calls()
    def unreliable_function(x: int) -> int:
        if x < 5:
            raise ValueError("Too small!")
        return x * 2
    
    try:
        result = unreliable_function(10)
        print(f"Function result: {result}")
    except ValueError as e:
        print(f"Function failed: {e}")
    
    # Walrus operator test
    test_data = [
        {"value": 15, "retries": 0},
        {"value": 5, "retries": 2},
        {"value": 25, "retries": 0}
    ]
    walrus_results = process_data_with_walrus(test_data)
    print(f"Walrus operator results: {len(walrus_results)} items processed")
    
    # Pattern matching test
    test_cases = [
        {"type": "user", "id": 123, "name": "Alice"},
        {"type": "admin", "permissions": ["read", "write"]},
        {"type": "guest"},
        42,
        150,
        "prefix_test_string",
        "regular_string"
    ]
    
    for case in test_cases:
        result = analyze_data_structure(case)
        print(f"Pattern match for {case}: {result}")
    
    print("\n=== Demo completed successfully! ===")