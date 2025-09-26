#!/usr/bin/env python3
"""
Data Models - Comprehensive Class and ORM Examples
Testing class hierarchies, inheritance, and data modeling patterns
"""

from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, field, InitVar, asdict
from typing import Any, Dict, List, Optional, Union, ClassVar, Generic, TypeVar
from enum import Enum, IntEnum, Flag, IntFlag, auto
import datetime
import uuid
import json
from decimal import Decimal
import weakref
from collections import defaultdict, UserDict, UserList

# Type variables for generics
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Enums for status and types
class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING = "pending"

class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5

class Permissions(Flag):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    DELETE = auto()
    ADMIN = READ | WRITE | EXECUTE | DELETE

class FileType(IntFlag):
    TEXT = 1
    BINARY = 2
    IMAGE = 4
    VIDEO = 8
    AUDIO = 16
    DOCUMENT = TEXT | IMAGE
    MEDIA = IMAGE | VIDEO | AUDIO

# Abstract base classes
class BaseModel(ABC):
    """Abstract base model with common functionality"""
    
    def __init__(self):
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self._observers = []
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate model data"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create from dictionary"""
        pass
    
    def add_observer(self, observer):
        """Add observer for model changes"""
        self._observers.append(weakref.ref(observer))
    
    def notify_observers(self, event: str, data: Any = None):
        """Notify all observers of changes"""
        for observer_ref in self._observers[:]:
            observer = observer_ref()
            if observer is None:
                self._observers.remove(observer_ref)
            else:
                observer.on_model_change(self, event, data)

class Serializable(ABC):
    """Mixin for serialization capabilities"""
    
    @abstractmethod
    def serialize(self) -> str:
        """Serialize to string"""
        pass
    
    @classmethod
    @abstractmethod
    def deserialize(cls, data: str) -> 'Serializable':
        """Deserialize from string"""
        pass

class Auditable(ABC):
    """Mixin for audit trail"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit_log = []
    
    def log_change(self, field: str, old_value: Any, new_value: Any, user_id: Optional[str] = None):
        """Log field changes"""
        entry = {
            'timestamp': datetime.datetime.now(),
            'field': field,
            'old_value': old_value,
            'new_value': new_value,
            'user_id': user_id
        }
        self.audit_log.append(entry)

# Complex inheritance hierarchy
class Entity(BaseModel, Serializable, Auditable):
    """Base entity with full functionality"""
    
    def __init__(self, entity_id: Optional[str] = None):
        super().__init__()
        self.id = entity_id or str(uuid.uuid4())
        self.version = 1
    
    def validate(self) -> bool:
        return bool(self.id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        entity = cls(data.get('id'))
        entity.version = data.get('version', 1)
        return entity
    
    def serialize(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def deserialize(cls, data: str) -> 'Entity':
        return cls.from_dict(json.loads(data))

# Dataclass examples with advanced features
@dataclass(frozen=True, order=True)
class Coordinate:
    """Immutable coordinate with ordering"""
    x: float
    y: float
    z: float = 0.0
    
    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5
    
    def __post_init__(self):
        if any(abs(coord) > 1000 for coord in (self.x, self.y, self.z)):
            raise ValueError("Coordinates must be within ±1000")

@dataclass
class User(Entity):
    """User model with comprehensive features"""
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    status: UserStatus = UserStatus.PENDING
    permissions: Permissions = Permissions.READ
    profile_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    login_count: int = 0
    last_login: Optional[datetime.datetime] = None
    
    # Class variables
    MIN_USERNAME_LENGTH: ClassVar[int] = 3
    MAX_USERNAME_LENGTH: ClassVar[int] = 50
    
    # InitVar for computed fields
    password: InitVar[Optional[str]] = None
    
    def __post_init__(self, password: Optional[str]):
        super().__init__()
        if password:
            self.set_password(password)
        self._password_hash = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
    
    def set_password(self, password: str):
        """Set password with hashing"""
        import hashlib
        self._password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.log_change('password', None, '[REDACTED]')
    
    def validate(self) -> bool:
        if not (self.MIN_USERNAME_LENGTH <= len(self.username) <= self.MAX_USERNAME_LENGTH):
            return False
        if '@' not in self.email:
            return False
        return super().validate()
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'status': self.status.value,
            'permissions': self.permissions.value,
            'profile_data': self.profile_data,
            'tags': self.tags,
            'login_count': self.login_count,
            'last_login': self.last_login.isoformat() if self.last_login else None
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        user = cls(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            status=UserStatus(data.get('status', 'pending')),
            permissions=Permissions(data.get('permissions', 1)),
            profile_data=data.get('profile_data', {}),
            tags=data.get('tags', []),
            login_count=data.get('login_count', 0)
        )
        user.id = data.get('id')
        if data.get('last_login'):
            user.last_login = datetime.datetime.fromisoformat(data['last_login'])
        return user

@dataclass
class Product(Entity):
    """Product model with pricing and inventory"""
    name: str
    description: str = ""
    price: Decimal = field(default_factory=lambda: Decimal('0.00'))
    currency: str = "USD"
    category_id: Optional[str] = None
    sku: str = field(default="")
    in_stock: bool = True
    stock_quantity: int = 0
    weight: Optional[float] = None
    dimensions: Optional[Coordinate] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__init__()
        if not self.sku:
            self.sku = f"PRD-{self.id[:8].upper()}"
    
    @property
    def is_available(self) -> bool:
        return self.in_stock and self.stock_quantity > 0
    
    @property
    def formatted_price(self) -> str:
        return f"{self.price:.2f} {self.currency}"
    
    def update_stock(self, quantity: int, operation: str = "set"):
        """Update stock quantity"""
        old_quantity = self.stock_quantity
        
        if operation == "add":
            self.stock_quantity += quantity
        elif operation == "subtract":
            self.stock_quantity = max(0, self.stock_quantity - quantity)
        else:  # set
            self.stock_quantity = max(0, quantity)
        
        self.log_change('stock_quantity', old_quantity, self.stock_quantity)
        
        if self.stock_quantity == 0:
            self.in_stock = False

@dataclass
class Order(Entity):
    """Order model with line items"""
    user_id: str
    order_number: str = field(default="")
    status: str = "pending"
    items: List['OrderItem'] = field(default_factory=list)
    shipping_address: Dict[str, str] = field(default_factory=dict)
    billing_address: Dict[str, str] = field(default_factory=dict)
    subtotal: Decimal = field(default_factory=lambda: Decimal('0.00'))
    tax_amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    shipping_cost: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    def __post_init__(self):
        super().__init__()
        if not self.order_number:
            self.order_number = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{self.id[:8].upper()}"
    
    def add_item(self, product_id: str, quantity: int, unit_price: Decimal):
        """Add item to order"""
        item = OrderItem(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        self.items.append(item)
        self.calculate_totals()
    
    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = self.subtotal * Decimal('0.08')  # 8% tax
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost

@dataclass
class OrderItem:
    """Order line item"""
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    @property
    def total_price(self) -> Decimal:
        return (self.unit_price * self.quantity) - self.discount_amount

# Generic classes and containers
class Repository(Generic[T]):
    """Generic repository pattern"""
    
    def __init__(self):
        self._items: Dict[str, T] = {}
        self._indexes: Dict[str, Dict[Any, List[str]]] = defaultdict(lambda: defaultdict(list))
    
    def add(self, item: T) -> None:
        """Add item to repository"""
        if hasattr(item, 'id'):
            self._items[item.id] = item
            self._update_indexes(item)
    
    def get(self, item_id: str) -> Optional[T]:
        """Get item by ID"""
        return self._items.get(item_id)
    
    def get_all(self) -> List[T]:
        """Get all items"""
        return list(self._items.values())
    
    def find_by(self, field: str, value: Any) -> List[T]:
        """Find items by field value"""
        if field in self._indexes and value in self._indexes[field]:
            item_ids = self._indexes[field][value]
            return [self._items[item_id] for item_id in item_ids if item_id in self._items]
        return []
    
    def remove(self, item_id: str) -> bool:
        """Remove item from repository"""
        if item_id in self._items:
            item = self._items[item_id]
            del self._items[item_id]
            self._remove_from_indexes(item)
            return True
        return False
    
    def _update_indexes(self, item: T):
        """Update search indexes"""
        if hasattr(item, 'id'):
            for attr_name in dir(item):
                if not attr_name.startswith('_') and hasattr(item, attr_name):
                    attr_value = getattr(item, attr_name)
                    if isinstance(attr_value, (str, int, float, bool)):
                        self._indexes[attr_name][attr_value].append(item.id)
    
    def _remove_from_indexes(self, item: T):
        """Remove item from indexes"""
        if hasattr(item, 'id'):
            for index_dict in self._indexes.values():
                for value_list in index_dict.values():
                    if item.id in value_list:
                        value_list.remove(item.id)

class CacheableRepository(Repository[T]):
    """Repository with caching capabilities"""
    
    def __init__(self, cache_size: int = 100):
        super().__init__()
        self.cache_size = cache_size
        self._cache: Dict[str, T] = {}
        self._cache_access_order: List[str] = []
    
    def get(self, item_id: str) -> Optional[T]:
        """Get item with caching"""
        # Check cache first
        if item_id in self._cache:
            self._update_cache_access(item_id)
            return self._cache[item_id]
        
        # Get from main storage
        item = super().get(item_id)
        if item:
            self._add_to_cache(item_id, item)
        
        return item
    
    def _add_to_cache(self, item_id: str, item: T):
        """Add item to cache with LRU eviction"""
        if len(self._cache) >= self.cache_size:
            # Remove least recently used item
            lru_id = self._cache_access_order.pop(0)
            del self._cache[lru_id]
        
        self._cache[item_id] = item
        self._cache_access_order.append(item_id)
    
    def _update_cache_access(self, item_id: str):
        """Update access order for LRU"""
        if item_id in self._cache_access_order:
            self._cache_access_order.remove(item_id)
            self._cache_access_order.append(item_id)

# Descriptors and properties
class ValidatedField:
    """Descriptor for field validation"""
    
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

class Person:
    """Person with validated fields"""
    
    age = ValidatedField(lambda x: 0 <= x <= 150, 0)
    email = ValidatedField(lambda x: '@' in x and '.' in x, "")
    phone = ValidatedField(lambda x: len(x) >= 10, "")
    
    def __init__(self, name: str, age: int = 0, email: str = "", phone: str = ""):
        self.name = name
        self.age = age
        self.email = email
        self.phone = phone

# Metaclass examples
class SingletonMeta(type):
    """Singleton metaclass"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    """Singleton database connection"""
    
    def __init__(self, host: str = "localhost", port: int = 5432):
        if hasattr(self, 'initialized'):
            return
        self.host = host
        self.port = port
        self.connected = False
        self.initialized = True
    
    def connect(self):
        """Connect to database"""
        if not self.connected:
            print(f"Connecting to {self.host}:{self.port}")
            self.connected = True
        return self.connected

class AutoRegisterMeta(type):
    """Metaclass that auto-registers classes"""
    registry = {}
    
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        if name != 'AutoRegisterBase':
            mcs.registry[name] = cls
        return cls

class AutoRegisterBase(metaclass=AutoRegisterMeta):
    """Base class with auto-registration"""
    pass

class PluginA(AutoRegisterBase):
    """Plugin A"""
    def execute(self):
        return "Plugin A executed"

class PluginB(AutoRegisterBase):
    """Plugin B"""
    def execute(self):
        return "Plugin B executed"

# Collection classes
class UserDict(UserDict):
    """Custom user dictionary"""
    
    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Keys must be strings")
        super().__setitem__(key.lower(), value)
    
    def __getitem__(self, key):
        return super().__getitem__(key.lower())

class ObservableList(UserList):
    """List that notifies observers of changes"""
    
    def __init__(self, initlist=None):
        super().__init__(initlist)
        self._observers = []
    
    def add_observer(self, observer):
        self._observers.append(observer)
    
    def append(self, item):
        super().append(item)
        self._notify_observers('append', item)
    
    def remove(self, item):
        super().remove(item)
        self._notify_observers('remove', item)
    
    def _notify_observers(self, operation, item):
        for observer in self._observers:
            observer.on_list_change(operation, item)

# Complex class relationships
class Organization(Entity):
    """Organization with hierarchical structure"""
    
    def __init__(self, name: str, org_type: str = "company"):
        super().__init__()
        self.name = name
        self.org_type = org_type
        self.parent_org: Optional['Organization'] = None
        self.child_orgs: List['Organization'] = []
        self.employees: List[User] = []
        self.departments: List['Department'] = []
    
    def add_child_org(self, child_org: 'Organization'):
        """Add child organization"""
        child_org.parent_org = self
        self.child_orgs.append(child_org)
    
    def add_employee(self, employee: User):
        """Add employee to organization"""
        self.employees.append(employee)
        employee.profile_data['organization_id'] = self.id
    
    def get_all_employees(self) -> List[User]:
        """Get all employees including from child organizations"""
        all_employees = self.employees.copy()
        for child_org in self.child_orgs:
            all_employees.extend(child_org.get_all_employees())
        return all_employees

class Department(Entity):
    """Department within organization"""
    
    def __init__(self, name: str, organization: Organization):
        super().__init__()
        self.name = name
        self.organization = organization
        self.manager: Optional[User] = None
        self.employees: List[User] = []
        self.budget: Decimal = Decimal('0.00')
        organization.departments.append(self)
    
    def set_manager(self, manager: User):
        """Set department manager"""
        self.manager = manager
        if manager not in self.employees:
            self.employees.append(manager)
        manager.profile_data['department_id'] = self.id
        manager.profile_data['is_manager'] = True

class Project(Entity):
    """Project with team members and tasks"""
    
    def __init__(self, name: str, department: Department):
        super().__init__()
        self.name = name
        self.department = department
        self.project_manager: Optional[User] = None
        self.team_members: List[User] = []
        self.tasks: List['Task'] = []
        self.start_date: Optional[datetime.date] = None
        self.end_date: Optional[datetime.date] = None
        self.status: str = "planned"
        self.budget: Decimal = Decimal('0.00')
    
    def add_team_member(self, user: User, role: str = "developer"):
        """Add team member to project"""
        self.team_members.append(user)
        user.profile_data['current_project_id'] = self.id
        user.profile_data['project_role'] = role

class Task(Entity):
    """Task within project"""
    
    def __init__(self, title: str, project: Project):
        super().__init__()
        self.title = title
        self.project = project
        self.assignee: Optional[User] = None
        self.priority: Priority = Priority.MEDIUM
        self.status: str = "todo"
        self.description: str = ""
        self.estimated_hours: float = 0.0
        self.actual_hours: float = 0.0
        self.due_date: Optional[datetime.date] = None
        project.tasks.append(self)
    
    def assign_to(self, user: User):
        """Assign task to user"""
        self.assignee = user
        self.log_change('assignee', None, user.id)

# Example usage and relationships
if __name__ == "__main__":
    print("=== Data Models Testing ===")
    
    # Test basic models
    user = User(
        username="john_doe",
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        password="secure_password"
    )
    print(f"Created user: {user.full_name} ({user.username})")
    
    # Test product model
    coordinate = Coordinate(10.5, 20.3, 5.0)
    product = Product(
        name="Laptop Computer",
        description="High-performance laptop",
        price=Decimal('999.99'),
        dimensions=coordinate
    )
    print(f"Created product: {product.name} - {product.formatted_price}")
    
    # Test repository
    user_repo = Repository[User]()
    user_repo.add(user)
    
    found_users = user_repo.find_by('username', 'john_doe')
    print(f"Found {len(found_users)} users with username 'john_doe'")
    
    # Test organization hierarchy
    company = Organization("Tech Corp", "company")
    engineering_dept = Department("Engineering", company)
    project = Project("Web Platform", engineering_dept)
    
    company.add_employee(user)
    engineering_dept.set_manager(user)
    project.add_team_member(user, "lead_developer")
    
    print(f"Organization structure:")
    print(f"  Company: {company.name}")
    print(f"  Department: {engineering_dept.name}")
    print(f"  Project: {project.name}")
    print(f"  Manager: {engineering_dept.manager.full_name}")
    
    # Test singleton
    db1 = DatabaseConnection()
    db2 = DatabaseConnection()
    print(f"Singleton test: {db1 is db2}")  # Should be True
    
    # Test auto-registration
    print(f"Registered plugins: {list(AutoRegisterMeta.registry.keys())}")
    
    # Test validation
    person = Person("Alice", age=25, email="alice@example.com")
    try:
        person.age = 200  # Should raise ValueError
    except ValueError as e:
        print(f"Validation error: {e}")
    
    print("\n=== Data models testing completed! ===")