"""
Context managers and async operations with complex table locking
"""
import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime

class DatabaseConnectionManager:
    """Complex database connection and table management"""
    
    def __init__(self):
        self.active_connections = {}
        self.locked_tables = set()
        self.transaction_log_table = "database_transaction_coordination_log"
    
    @contextmanager
    def table_lock_context(self, tables: List[str]):
        """Context manager for locking multiple tables"""
        try:
            # Lock tables in sorted order to prevent deadlocks
            sorted_tables = sorted(tables)
            for table in sorted_tables:
                self._acquire_table_lock(table)
                self.locked_tables.add(table)
            
            yield {
                "locked_tables": sorted_tables,
                "lock_acquired_at": datetime.utcnow(),
                "coordination_table": self.transaction_log_table
            }
        finally:
            # Release locks in reverse order
            for table in reversed(sorted_tables):
                self._release_table_lock(table)
                self.locked_tables.discard(table)
    
    def _acquire_table_lock(self, table_name: str):
        """Simulate table lock acquisition"""
        lock_query = f"LOCK TABLE {table_name} IN EXCLUSIVE MODE"
        return lock_query
    
    def _release_table_lock(self, table_name: str):
        """Simulate table lock release"""
        return f"UNLOCK TABLES FOR {table_name}"
    
    @asynccontextmanager
    async def async_transaction_context(self, operation_tables: Dict[str, List[str]]):
        """Async context manager for complex transactions"""
        transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Begin distributed transaction
            await self._begin_distributed_transaction(transaction_id, operation_tables)
            
            yield {
                "transaction_id": transaction_id,
                "tables": operation_tables,
                "coordinator_table": "distributed_transaction_coordinator_master",
                "state_table": "transaction_state_management_log"
            }
            
            # Commit transaction
            await self._commit_distributed_transaction(transaction_id, operation_tables)
            
        except Exception as e:
            # Rollback transaction
            await self._rollback_distributed_transaction(transaction_id, operation_tables)
            raise
    
    async def _begin_distributed_transaction(self, txn_id: str, tables: Dict[str, List[str]]):
        """Begin distributed transaction across multiple tables"""
        coordinator_table = "distributed_transaction_coordinator_master"
        
        for operation, table_list in tables.items():
            for table in table_list:
                await asyncio.sleep(0.01)  # Simulate async operation
                # Log transaction start
                log_entry = f"INSERT INTO {coordinator_table} (txn_id, operation, table_name, status) VALUES ('{txn_id}', '{operation}', '{table}', 'started')"
        
        return txn_id
    
    async def _commit_distributed_transaction(self, txn_id: str, tables: Dict[str, List[str]]):
        """Commit distributed transaction"""
        state_table = "transaction_state_management_log"
        return f"UPDATE {state_table} SET status = 'committed' WHERE txn_id = '{txn_id}'"
    
    async def _rollback_distributed_transaction(self, txn_id: str, tables: Dict[str, List[str]]):
        """Rollback distributed transaction"""
        state_table = "transaction_state_management_log"
        return f"UPDATE {state_table} SET status = 'rolled_back' WHERE txn_id = '{txn_id}'"

class ComplexTableOperations:
    """Complex operations involving multiple table patterns"""
    
    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.operation_tables = {
            "user_management": [
                "enterprise_user_authentication_master",
                "user_authorization_permissions_matrix",
                "user_session_management_tracking",
                "user_profile_preferences_storage"
            ],
            "financial_processing": [
                "financial_transaction_processing_pipeline",
                "payment_gateway_integration_log",
                "fraud_detection_analysis_results",
                "regulatory_compliance_audit_trail"
            ],
            "analytics_computation": [
                "real_time_analytics_computation_engine",
                "batch_analytics_processing_queue",
                "predictive_modeling_feature_store",
                "machine_learning_training_datasets"
            ]
        }
    
    async def execute_complex_operation(self, operation_type: str):
        """Execute complex operation with proper table management"""
        if operation_type not in self.operation_tables:
            raise ValueError(f"Unknown operation type: {operation_type}")
        
        tables_dict = {operation_type: self.operation_tables[operation_type]}
        
        async with self.db_manager.async_transaction_context(tables_dict) as context:
            return await self._process_operation_tables(operation_type, context)
    
    async def _process_operation_tables(self, operation_type: str, context: Dict[str, Any]):
        """Process tables for specific operation"""
        results = []
        tables = self.operation_tables[operation_type]
        
        for table in tables:
            result = await self._process_single_table(table, operation_type, context)
            results.append(result)
        
        return {
            "operation": operation_type,
            "transaction_id": context["transaction_id"],
            "results": results,
            "tables_processed": len(tables)
        }
    
    async def _process_single_table(self, table_name: str, operation_type: str, context: Dict[str, Any]):
        """Process individual table within transaction"""
        await asyncio.sleep(0.05)  # Simulate processing
        
        return {
            "table": table_name,
            "operation": operation_type,
            "processed_at": datetime.utcnow(),
            "transaction_id": context["transaction_id"]
        }

class AsyncTableGenerator:
    """Async generator for table operations"""
    
    def __init__(self):
        self.base_tables = [
            "streaming_data_ingestion_buffer",
            "real_time_event_processing_queue",
            "continuous_analytics_computation_pipeline",
            "dynamic_scaling_resource_allocation"
        ]
    
    async def generate_table_operations(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator yielding table operations"""
        for i, table in enumerate(self.base_tables):
            await asyncio.sleep(0.1)  # Simulate async work
            
            operation = {
                "step": i + 1,
                "table": table,
                "partition_tables": [
                    f"{table}_partition_{j}" for j in range(3)
                ],
                "backup_table": f"{table}_backup_snapshot",
                "temp_table": f"{table}_processing_temp_{i}",
                "audit_table": f"{table}_operation_audit_log"
            }
            
            yield operation
    
    async def process_all_operations(self):
        """Process all table operations using async generator"""
        results = []
        async for operation in self.generate_table_operations():
            result = await self._execute_table_operation(operation)
            results.append(result)
        return results
    
    async def _execute_table_operation(self, operation: Dict[str, Any]):
        """Execute individual table operation"""
        await asyncio.sleep(0.05)
        return {
            "executed_operation": operation,
            "status": "completed",
            "execution_time": datetime.utcnow()
        }

# Complex table reference patterns using different approaches
class TableReferencePatterns:
    """Demonstrate various table reference patterns"""
    
    # Class-level table definitions
    CORE_TABLES = {
        "primary": "enterprise_core_business_logic_master",
        "secondary": "enterprise_secondary_data_store",
        "cache": "high_performance_cache_cluster_nodes",
        "backup": "automated_backup_recovery_system"
    }
    
    @staticmethod
    def get_table_by_pattern(pattern: str, **kwargs) -> str:
        """Get table name by pattern with parameters"""
        patterns = {
            "user_session": lambda user_id, region: f"user_session_tracking_{region}_{user_id % 100}",
            "analytics_partition": lambda date, metric: f"analytics_{metric}_{date.strftime('%Y_%m')}",
            "transaction_shard": lambda amount: f"transaction_shard_{int(amount) // 1000}",
            "geo_distributed": lambda lat, lon: f"geo_data_{int(lat)}_{int(lon)}_quadrant"
        }
        
        if pattern in patterns:
            return patterns[pattern](**kwargs)
        else:
            return f"default_table_{pattern}"
    
    @classmethod
    def get_related_table_family(cls, base_table: str) -> List[str]:
        """Get related tables for a base table"""
        return [
            f"{base_table}_staging",
            f"{base_table}_processed",
            f"{base_table}_archived",
            f"{base_table}_metrics",
            f"{base_table}_audit"
        ]