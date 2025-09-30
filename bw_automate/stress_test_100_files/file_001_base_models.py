"""
Base models with complex SQLAlchemy inheritance and metaclasses
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Any, Dict
import asyncio

Base = declarative_base()

class TableMetaclass(type):
    """Metaclass that dynamically generates table names"""
    def __new__(cls, name, bases, attrs):
        if name != 'BaseModel':
            # Generate complex table name
            table_name = f"enterprise_{name.lower()}_master_v2"
            attrs['__tablename__'] = table_name
        return super().__new__(cls, name, bases, attrs)

class BaseModel(Base, metaclass=TableMetaclass):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class UserAccountsMixin:
    """Mixin for user account related tables"""
    @declared_attr
    def user_id(cls):
        return Column(Integer, ForeignKey('enterprise_useraccounts_master_v2.id'))
    
    @declared_attr
    def account_type(cls):
        return Column(String(50), default='standard')

class AuditMixin:
    """Mixin for audit trail functionality"""
    @declared_attr
    def audit_log_table(cls):
        return f"financial_transaction_audit_log_{cls.__name__.lower()}"
    
    created_by = Column(Integer, ForeignKey('enterprise_useraccounts_master_v2.id'))
    modified_by = Column(Integer, ForeignKey('enterprise_useraccounts_master_v2.id'))

class UserAccounts(BaseModel, UserAccountsMixin, AuditMixin):
    """Complex user accounts model with multiple inheritance"""
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_data = Column(Text)
    
    # Dynamic relationship to financial tables
    @property
    def financial_transactions_table(self):
        return "financial_transaction_processing_queue"
    
    # Complex async method referencing multiple tables
    async def get_related_data(self):
        tables = [
            "real_time_analytics_aggregation_staging",
            "microservice_order_fulfillment_events",
            "enterprise_security_audit_master_v2"
        ]
        return await asyncio.gather(*[self._query_table(table) for table in tables])
    
    async def _query_table(self, table_name: str):
        # Simulate complex table query
        return f"SELECT * FROM {table_name} WHERE user_id = {self.id}"

# Factory function for dynamic table creation
def create_table_model(table_name: str, additional_fields: Dict[str, Any] = None):
    """Factory function to create models dynamically"""
    class_name = ''.join([word.capitalize() for word in table_name.split('_')])
    
    attrs = {
        '__tablename__': table_name,
        'id': Column(Integer, primary_key=True),
        'data': Column(Text)
    }
    
    if additional_fields:
        attrs.update(additional_fields)
    
    return type(class_name, (Base,), attrs)

# Create dynamic models
ProcessingQueue = create_table_model("financial_transaction_processing_queue")
AnalyticsStaging = create_table_model("real_time_analytics_aggregation_staging")
OrderEvents = create_table_model("microservice_order_fulfillment_events")