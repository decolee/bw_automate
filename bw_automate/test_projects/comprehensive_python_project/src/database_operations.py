#!/usr/bin/env python3
"""
Database Operations - Comprehensive SQL and ORM Examples
Testing all database patterns for complete mapping
"""

import sqlite3
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from contextlib import contextmanager
import logging

# Database connection patterns
DATABASE_URL = "postgresql://user:password@localhost:5432/testdb"
SQLITE_PATH = "test_database.db"
MONGO_CONNECTION = "mongodb://localhost:27017/testdb"

# SQL Injection vulnerability examples (for security testing)
def vulnerable_query_concatenation(user_id: str):
    """SECURITY ISSUE: SQL injection vulnerability via string concatenation"""
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return query

def vulnerable_query_format(user_id: str, status: str):
    """SECURITY ISSUE: SQL injection via string formatting"""
    query = "SELECT * FROM users WHERE id = %s AND status = '%s'" % (user_id, status)
    return query

def vulnerable_query_fstring(table_name: str):
    """SECURITY ISSUE: SQL injection via f-string"""
    query = f"SELECT * FROM {table_name} WHERE active = 1"
    return query

# Hardcoded credentials (security testing)
DB_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

# Raw SQL patterns
class RawSQLOperations:
    """Raw SQL operations for testing detection"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def create_tables(self):
        """CREATE TABLE operations"""
        create_users = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_posts = """
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(200) NOT NULL,
            content TEXT,
            published BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        create_temp_analytics = """
        CREATE TEMP TABLE temp_analytics AS
        SELECT 
            u.id,
            u.username,
            COUNT(p.id) as post_count,
            AVG(LENGTH(p.content)) as avg_content_length
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        GROUP BY u.id, u.username
        """
        
        return [create_users, create_posts, create_temp_analytics]
    
    def insert_operations(self):
        """INSERT operations with various patterns"""
        insert_user = """
        INSERT INTO users (username, email, password_hash)
        VALUES ('john_doe', 'john@example.com', 'hashed_password_123')
        """
        
        insert_multiple = """
        INSERT INTO posts (user_id, title, content, published)
        VALUES 
            (1, 'First Post', 'This is the content of the first post', TRUE),
            (1, 'Second Post', 'Content for the second post', FALSE),
            (2, 'Another Post', 'Different user posting content', TRUE)
        """
        
        insert_from_select = """
        INSERT INTO user_statistics (user_id, total_posts, last_post_date)
        SELECT 
            u.id,
            COUNT(p.id),
            MAX(p.created_at)
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        GROUP BY u.id
        """
        
        return [insert_user, insert_multiple, insert_from_select]
    
    def select_operations(self):
        """SELECT operations with complex patterns"""
        simple_select = "SELECT * FROM users WHERE active = 1"
        
        join_select = """
        SELECT 
            u.username,
            u.email,
            p.title,
            p.created_at
        FROM users u
        INNER JOIN posts p ON u.id = p.user_id
        WHERE p.published = TRUE
        ORDER BY p.created_at DESC
        LIMIT 10
        """
        
        complex_cte = """
        WITH user_stats AS (
            SELECT 
                user_id,
                COUNT(*) as post_count,
                AVG(LENGTH(content)) as avg_length
            FROM posts
            WHERE published = TRUE
            GROUP BY user_id
        ),
        top_users AS (
            SELECT user_id, post_count
            FROM user_stats
            WHERE post_count > 5
        )
        SELECT 
            u.username,
            us.post_count,
            us.avg_length
        FROM top_users tu
        JOIN users u ON tu.user_id = u.id
        JOIN user_stats us ON tu.user_id = us.user_id
        ORDER BY us.post_count DESC
        """
        
        window_function = """
        SELECT 
            username,
            created_at,
            ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
            RANK() OVER (ORDER BY created_at DESC) as recency_rank,
            LAG(created_at) OVER (ORDER BY created_at) as prev_user_date
        FROM users
        WHERE active = TRUE
        """
        
        return [simple_select, join_select, complex_cte, window_function]
    
    def update_operations(self):
        """UPDATE operations"""
        simple_update = """
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP 
        WHERE username = 'john_doe'
        """
        
        complex_update = """
        UPDATE posts 
        SET 
            title = UPPER(title),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id IN (
            SELECT id FROM users WHERE created_at > '2023-01-01'
        )
        """
        
        update_with_join = """
        UPDATE posts 
        SET category_id = c.id
        FROM categories c
        WHERE posts.title ILIKE '%' || c.name || '%'
        """
        
        return [simple_update, complex_update, update_with_join]
    
    def delete_operations(self):
        """DELETE operations"""
        simple_delete = "DELETE FROM posts WHERE published = FALSE"
        
        delete_with_subquery = """
        DELETE FROM users 
        WHERE id NOT IN (
            SELECT DISTINCT user_id 
            FROM posts 
            WHERE user_id IS NOT NULL
        )
        """
        
        truncate_table = "TRUNCATE TABLE temp_analytics CASCADE"
        
        return [simple_delete, delete_with_subquery, truncate_table]

# SQLAlchemy ORM patterns
try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, Session
    from sqlalchemy.sql import text
    
    Base = declarative_base()
    
    class User(Base):
        """SQLAlchemy User model"""
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True)
        username = Column(String(50), unique=True, nullable=False)
        email = Column(String(100), unique=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        created_at = Column(DateTime)
        
        posts = relationship("Post", back_populates="user")
    
    class Post(Base):
        """SQLAlchemy Post model"""
        __tablename__ = 'posts'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        title = Column(String(200), nullable=False)
        content = Column(Text)
        published = Column(Boolean, default=False)
        
        user = relationship("User", back_populates="posts")
    
    class SQLAlchemyOperations:
        """SQLAlchemy ORM operations"""
        
        def __init__(self, database_url: str):
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
        
        def create_user(self, username: str, email: str, password: str) -> User:
            """Create new user with ORM"""
            session = self.SessionLocal()
            try:
                user = User(
                    username=username,
                    email=email,
                    password_hash=password
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
            finally:
                session.close()
        
        def get_users_with_posts(self) -> List[User]:
            """Query with relationship loading"""
            session = self.SessionLocal()
            try:
                users = session.query(User)\
                    .join(Post)\
                    .filter(Post.published == True)\
                    .all()
                return users
            finally:
                session.close()
        
        def execute_raw_sql(self, query: str) -> List[Dict]:
            """Execute raw SQL with SQLAlchemy"""
            session = self.SessionLocal()
            try:
                result = session.execute(text(query))
                return [dict(row) for row in result]
            finally:
                session.close()
        
        def bulk_operations(self, users_data: List[Dict]):
            """Bulk insert operations"""
            session = self.SessionLocal()
            try:
                session.bulk_insert_mappings(User, users_data)
                session.commit()
            finally:
                session.close()

except ImportError:
    # SQLAlchemy not available
    class SQLAlchemyOperations:
        def __init__(self, database_url: str):
            print("SQLAlchemy not available")

# Django ORM patterns (simulation)
class DjangoORMPatterns:
    """Simulated Django ORM patterns for testing"""
    
    def query_patterns(self):
        """Various Django ORM query patterns"""
        patterns = [
            # Basic queries
            "User.objects.all()",
            "User.objects.filter(active=True)",
            "User.objects.get(id=1)",
            "User.objects.exclude(status='inactive')",
            
            # Complex queries
            "User.objects.filter(posts__published=True).distinct()",
            "User.objects.select_related('profile').prefetch_related('posts')",
            "User.objects.annotate(post_count=Count('posts'))",
            "User.objects.aggregate(avg_age=Avg('age'))",
            
            # Q objects and complex filters
            "User.objects.filter(Q(name__icontains='john') | Q(email__endswith='example.com'))",
            "User.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))",
            
            # Raw queries
            "User.objects.raw('SELECT * FROM users WHERE active = %s', [True])",
            "User.objects.extra(where=['age > %s'], params=[18])",
        ]
        return patterns
    
    def model_operations(self):
        """Django model operations"""
        operations = [
            # Create
            "user = User.objects.create(username='test', email='test@example.com')",
            "User.objects.bulk_create([User(username=f'user{i}') for i in range(100)])",
            
            # Update
            "User.objects.filter(active=False).update(status='inactive')",
            "user.save()",
            
            # Delete
            "User.objects.filter(last_login__lt=cutoff_date).delete()",
            "user.delete()",
        ]
        return operations

# Pandas SQL operations
try:
    import pandas as pd
    
    class PandasSQLOperations:
        """Pandas SQL operations for testing"""
        
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
        
        def read_operations(self):
            """Pandas read_sql operations"""
            # Direct SQL queries
            df1 = pd.read_sql("SELECT * FROM users WHERE active = 1", self.connection_string)
            
            df2 = pd.read_sql_query(
                "SELECT u.*, COUNT(p.id) as post_count "
                "FROM users u LEFT JOIN posts p ON u.id = p.user_id "
                "GROUP BY u.id", 
                self.connection_string
            )
            
            # Read table
            df3 = pd.read_sql_table("users", self.connection_string)
            
            # Parameterized queries
            df4 = pd.read_sql(
                "SELECT * FROM posts WHERE user_id = %(user_id)s AND created_at > %(date)s",
                self.connection_string,
                params={'user_id': 1, 'date': '2023-01-01'}
            )
            
            return [df1, df2, df3, df4]
        
        def write_operations(self, dataframes: List[pd.DataFrame]):
            """Pandas to_sql operations"""
            df_users, df_posts = dataframes[:2]
            
            # Basic write
            df_users.to_sql('users_backup', self.connection_string, if_exists='replace')
            
            # Append mode
            df_posts.to_sql('posts', self.connection_string, if_exists='append', index=False)
            
            # Custom parameters
            df_users.to_sql(
                'users_export',
                self.connection_string,
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=1000
            )

except ImportError:
    class PandasSQLOperations:
        def __init__(self, connection_string: str):
            print("Pandas not available")

# MongoDB operations (PyMongo)
try:
    from pymongo import MongoClient
    
    class MongoDBOperations:
        """MongoDB operations for NoSQL testing"""
        
        def __init__(self, connection_string: str):
            self.client = MongoClient(connection_string)
            self.db = self.client.testdb
        
        def collection_operations(self):
            """MongoDB collection operations"""
            users = self.db.users
            
            # Insert operations
            user_doc = {
                "username": "john_doe",
                "email": "john@example.com",
                "profile": {
                    "age": 30,
                    "location": "New York"
                }
            }
            users.insert_one(user_doc)
            
            # Bulk insert
            bulk_users = [
                {"username": f"user_{i}", "email": f"user{i}@example.com"}
                for i in range(100)
            ]
            users.insert_many(bulk_users)
            
            # Query operations
            active_users = users.find({"active": True})
            user_by_email = users.find_one({"email": "john@example.com"})
            
            # Complex queries
            pipeline = [
                {"$match": {"active": True}},
                {"$group": {
                    "_id": "$location",
                    "count": {"$sum": 1},
                    "avg_age": {"$avg": "$profile.age"}
                }},
                {"$sort": {"count": -1}}
            ]
            location_stats = users.aggregate(pipeline)
            
            # Update operations
            users.update_one(
                {"username": "john_doe"},
                {"$set": {"last_login": "2023-01-01"}}
            )
            
            users.update_many(
                {"active": {"$ne": True}},
                {"$set": {"status": "inactive"}}
            )
            
            # Delete operations
            users.delete_one({"username": "temp_user"})
            users.delete_many({"status": "inactive"})

except ImportError:
    class MongoDBOperations:
        def __init__(self, connection_string: str):
            print("PyMongo not available")

# Database connection management
@contextmanager
def database_connection(connection_string: str):
    """Context manager for database connections"""
    if "sqlite" in connection_string:
        conn = sqlite3.connect(connection_string)
    else:
        # Simulate other database connections
        conn = None
        print(f"Simulating connection to {connection_string}")
    
    try:
        yield conn
    finally:
        if conn:
            conn.close()

class ConnectionPool:
    """Database connection pool implementation"""
    
    def __init__(self, connection_string: str, pool_size: int = 10):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.connections = []
        self.in_use = set()
    
    def get_connection(self):
        """Get connection from pool"""
        if self.connections:
            conn = self.connections.pop()
        else:
            conn = self._create_connection()
        
        self.in_use.add(conn)
        return conn
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if conn in self.in_use:
            self.in_use.remove(conn)
            if len(self.connections) < self.pool_size:
                self.connections.append(conn)
            else:
                self._close_connection(conn)
    
    def _create_connection(self):
        """Create new database connection"""
        if "sqlite" in self.connection_string:
            return sqlite3.connect(self.connection_string)
        else:
            return f"connection_to_{self.connection_string}"
    
    def _close_connection(self, conn):
        """Close database connection"""
        if hasattr(conn, 'close'):
            conn.close()

# Async database operations
class AsyncDatabaseOperations:
    """Async database operations"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def async_query(self, query: str) -> List[Dict]:
        """Async database query"""
        await asyncio.sleep(0.1)  # Simulate async DB operation
        
        # Simulate different query types
        if "SELECT" in query.upper():
            return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        elif "INSERT" in query.upper():
            return [{"affected_rows": 1}]
        elif "UPDATE" in query.upper():
            return [{"affected_rows": 3}]
        elif "DELETE" in query.upper():
            return [{"affected_rows": 2}]
        else:
            return []
    
    async def batch_operations(self, queries: List[str]) -> List[List[Dict]]:
        """Execute multiple queries asynchronously"""
        tasks = [self.async_query(query) for query in queries]
        return await asyncio.gather(*tasks)
    
    async def transaction(self, queries: List[str]) -> bool:
        """Async transaction management"""
        try:
            # Simulate transaction start
            await asyncio.sleep(0.01)
            
            results = []
            for query in queries:
                result = await self.async_query(query)
                results.append(result)
            
            # Simulate commit
            await asyncio.sleep(0.01)
            return True
            
        except Exception as e:
            # Simulate rollback
            await asyncio.sleep(0.01)
            logging.error(f"Transaction failed: {e}")
            return False

# Performance testing and optimization
class DatabasePerformanceTest:
    """Database performance testing utilities"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def inefficient_queries(self):
        """Examples of inefficient queries for performance testing"""
        return [
            # N+1 query problem
            "SELECT * FROM users",  # followed by multiple:
            "SELECT * FROM posts WHERE user_id = ?",
            
            # Missing indexes
            "SELECT * FROM large_table WHERE non_indexed_column = 'value'",
            
            # Cartesian product
            "SELECT * FROM users, posts WHERE users.active = 1",
            
            # Inefficient subqueries
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM posts WHERE title LIKE '%search%')",
            
            # Full table scans
            "SELECT COUNT(*) FROM large_table WHERE UPPER(text_column) = 'VALUE'",
        ]
    
    def optimized_queries(self):
        """Optimized versions of the above queries"""
        return [
            # Proper joins instead of N+1
            "SELECT u.*, p.* FROM users u LEFT JOIN posts p ON u.id = p.user_id",
            
            # Index usage
            "SELECT * FROM large_table WHERE indexed_column = 'value'",
            
            # Proper joins
            "SELECT u.*, p.* FROM users u INNER JOIN posts p ON u.id = p.user_id WHERE u.active = 1",
            
            # Efficient joins instead of subqueries
            "SELECT DISTINCT u.* FROM users u INNER JOIN posts p ON u.id = p.user_id WHERE p.title LIKE '%search%'",
            
            # Function-based indexes
            "SELECT COUNT(*) FROM large_table WHERE text_column = 'VALUE'",  # assuming functional index
        ]

# Migration and schema management
class DatabaseMigrations:
    """Database migration patterns"""
    
    def create_migration_001_initial(self):
        """Initial database schema"""
        return """
        -- Migration 001: Initial schema
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_users_email ON users(email);
        CREATE INDEX idx_users_username ON users(username);
        """
    
    def create_migration_002_add_posts(self):
        """Add posts table"""
        return """
        -- Migration 002: Add posts table
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            published BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_posts_user_id ON posts(user_id);
        CREATE INDEX idx_posts_published ON posts(published);
        CREATE INDEX idx_posts_created_at ON posts(created_at);
        """
    
    def create_migration_003_add_profile_fields(self):
        """Add profile fields to users"""
        return """
        -- Migration 003: Add profile fields
        ALTER TABLE users ADD COLUMN first_name VARCHAR(50);
        ALTER TABLE users ADD COLUMN last_name VARCHAR(50);
        ALTER TABLE users ADD COLUMN date_of_birth DATE;
        ALTER TABLE users ADD COLUMN profile_image_url VARCHAR(500);
        ALTER TABLE users ADD COLUMN bio TEXT;
        ALTER TABLE users ADD COLUMN location VARCHAR(100);
        ALTER TABLE users ADD COLUMN website_url VARCHAR(500);
        
        CREATE INDEX idx_users_location ON users(location);
        """

# Example usage and comprehensive testing
if __name__ == "__main__":
    print("=== Database Operations Testing ===")
    
    # Test raw SQL operations
    sql_ops = RawSQLOperations(DATABASE_URL)
    
    print("CREATE TABLE operations:")
    for query in sql_ops.create_tables():
        print(f"  {query[:50]}...")
    
    print("\nINSERT operations:")
    for query in sql_ops.insert_operations():
        print(f"  {query[:50]}...")
    
    print("\nSELECT operations:")
    for query in sql_ops.select_operations():
        print(f"  {query[:50]}...")
    
    print("\nUPDATE operations:")
    for query in sql_ops.update_operations():
        print(f"  {query[:50]}...")
    
    print("\nDELETE operations:")
    for query in sql_ops.delete_operations():
        print(f"  {query[:50]}...")
    
    # Test Django ORM patterns
    django_patterns = DjangoORMPatterns()
    print("\nDjango ORM patterns:")
    for pattern in django_patterns.query_patterns()[:5]:
        print(f"  {pattern}")
    
    # Test vulnerable patterns (for security analysis)
    print("\nSecurity vulnerabilities detected:")
    print(f"  Vulnerable concatenation: {vulnerable_query_concatenation('1 OR 1=1')}")
    print(f"  Vulnerable format: {vulnerable_query_format('1', '; DROP TABLE users; --')}")
    print(f"  Hardcoded password: {DB_PASSWORD[:10]}...")
    
    # Test migrations
    migrations = DatabaseMigrations()
    print("\nDatabase migrations:")
    print("  Migration 001: Initial schema")
    print("  Migration 002: Add posts table")
    print("  Migration 003: Add profile fields")
    
    print("\n=== Database testing completed! ===")