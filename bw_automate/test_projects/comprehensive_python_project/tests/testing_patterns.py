#!/usr/bin/env python3
"""
Testing Patterns - Comprehensive testing examples
Unit tests, integration tests, mocks, fixtures, and testing frameworks
"""

import unittest
import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, MagicMock, patch, call, ANY
from unittest.mock import PropertyMock, create_autospec
from typing import List, Dict, Any, Optional
import datetime
from dataclasses import dataclass
from contextlib import contextmanager

# Test data and fixtures
@dataclass
class User:
    id: int
    username: str
    email: str
    is_active: bool = True
    created_at: datetime.datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.now()

class UserService:
    """Service class for testing"""
    
    def __init__(self, database=None, email_service=None):
        self.database = database
        self.email_service = email_service
    
    def create_user(self, username: str, email: str) -> User:
        """Create a new user"""
        if self.get_user_by_email(email):
            raise ValueError("User with this email already exists")
        
        user = User(
            id=self._generate_id(),
            username=username,
            email=email
        )
        
        self.database.save(user)
        self.email_service.send_welcome_email(user.email)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.database.find_by_email(email)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user"""
        user = self.database.find_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.database.save(user)
        return True
    
    def _generate_id(self) -> int:
        """Generate unique ID"""
        return self.database.get_next_id()

class Database:
    """Mock database for testing"""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def save(self, user: User):
        self.users[user.id] = user
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)
    
    def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def get_next_id(self) -> int:
        current_id = self.next_id
        self.next_id += 1
        return current_id

class EmailService:
    """Mock email service for testing"""
    
    def send_welcome_email(self, email: str):
        """Send welcome email"""
        pass
    
    def send_notification(self, email: str, message: str):
        """Send notification email"""
        pass

# === UNITTEST PATTERNS ===

class TestUserServiceUnittest(unittest.TestCase):
    """Unittest examples with various patterns"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.database = Database()
        self.email_service = EmailService()
        self.user_service = UserService(self.database, self.email_service)
    
    def tearDown(self):
        """Clean up after tests"""
        # Cleanup code here
        pass
    
    def test_create_user_success(self):
        """Test successful user creation"""
        username = "testuser"
        email = "test@example.com"
        
        user = self.user_service.create_user(username, email)
        
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.created_at)
        self.assertIsInstance(user.id, int)
    
    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email"""
        email = "duplicate@example.com"
        
        # Create first user
        self.user_service.create_user("user1", email)
        
        # Attempt to create second user with same email
        with self.assertRaises(ValueError) as context:
            self.user_service.create_user("user2", email)
        
        self.assertIn("already exists", str(context.exception))
    
    def test_get_user_by_email_exists(self):
        """Test getting existing user by email"""
        email = "existing@example.com"
        created_user = self.user_service.create_user("testuser", email)
        
        found_user = self.user_service.get_user_by_email(email)
        
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.id, created_user.id)
        self.assertEqual(found_user.email, email)
    
    def test_get_user_by_email_not_exists(self):
        """Test getting non-existing user by email"""
        found_user = self.user_service.get_user_by_email("nonexistent@example.com")
        self.assertIsNone(found_user)
    
    def test_deactivate_user_success(self):
        """Test successful user deactivation"""
        user = self.user_service.create_user("testuser", "test@example.com")
        
        result = self.user_service.deactivate_user(user.id)
        
        self.assertTrue(result)
        deactivated_user = self.database.find_by_id(user.id)
        self.assertFalse(deactivated_user.is_active)
    
    def test_deactivate_user_not_found(self):
        """Test deactivating non-existing user"""
        result = self.user_service.deactivate_user(999)
        self.assertFalse(result)
    
    @unittest.skip("Skipping this test for demonstration")
    def test_skipped_test(self):
        """This test is skipped"""
        pass
    
    @unittest.expectedFailure
    def test_expected_failure(self):
        """This test is expected to fail"""
        self.assertEqual(1, 2)  # This will fail as expected

class TestUserServiceMocking(unittest.TestCase):
    """Testing with mocks and patches"""
    
    def setUp(self):
        self.mock_database = Mock(spec=Database)
        self.mock_email_service = Mock(spec=EmailService)
        self.user_service = UserService(self.mock_database, self.mock_email_service)
    
    def test_create_user_with_mocks(self):
        """Test user creation with mocked dependencies"""
        # Setup mocks
        self.mock_database.find_by_email.return_value = None
        self.mock_database.get_next_id.return_value = 123
        
        # Execute
        user = self.user_service.create_user("testuser", "test@example.com")
        
        # Verify
        self.assertEqual(user.id, 123)
        self.mock_database.save.assert_called_once()
        self.mock_email_service.send_welcome_email.assert_called_once_with("test@example.com")
    
    def test_create_user_duplicate_with_mock(self):
        """Test duplicate user creation with mock"""
        existing_user = User(1, "existing", "test@example.com")
        self.mock_database.find_by_email.return_value = existing_user
        
        with self.assertRaises(ValueError):
            self.user_service.create_user("newuser", "test@example.com")
        
        # Verify database save was not called
        self.mock_database.save.assert_not_called()
        self.mock_email_service.send_welcome_email.assert_not_called()
    
    @patch('datetime.datetime')
    def test_user_creation_time_patched(self, mock_datetime):
        """Test with patched datetime"""
        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        self.mock_database.find_by_email.return_value = None
        self.mock_database.get_next_id.return_value = 1
        
        user = self.user_service.create_user("testuser", "test@example.com")
        
        # This would require User to use the mocked datetime
        # self.assertEqual(user.created_at, fixed_time)
    
    def test_mock_call_verification(self):
        """Test various mock call verification patterns"""
        self.mock_database.find_by_email.return_value = None
        self.mock_database.get_next_id.return_value = 1
        
        self.user_service.create_user("user1", "user1@example.com")
        self.user_service.create_user("user2", "user2@example.com")
        
        # Verify call count
        self.assertEqual(self.mock_database.save.call_count, 2)
        
        # Verify specific calls
        self.mock_database.find_by_email.assert_has_calls([
            call("user1@example.com"),
            call("user2@example.com")
        ])
        
        # Verify any call with specific argument
        self.mock_email_service.send_welcome_email.assert_any_call("user1@example.com")

# === PYTEST PATTERNS ===

class TestUserServicePytest:
    """Pytest examples with fixtures and parametrization"""
    
    @pytest.fixture
    def database(self):
        """Database fixture"""
        return Database()
    
    @pytest.fixture
    def email_service(self):
        """Email service fixture"""
        return EmailService()
    
    @pytest.fixture
    def user_service(self, database, email_service):
        """User service fixture"""
        return UserService(database, email_service)
    
    @pytest.fixture
    def sample_user(self, user_service):
        """Sample user fixture"""
        return user_service.create_user("sampleuser", "sample@example.com")
    
    def test_create_user_pytest(self, user_service):
        """Test user creation with pytest"""
        user = user_service.create_user("testuser", "test@example.com")
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
    
    def test_duplicate_user_pytest(self, user_service):
        """Test duplicate user creation with pytest"""
        email = "duplicate@example.com"
        user_service.create_user("user1", email)
        
        with pytest.raises(ValueError, match="already exists"):
            user_service.create_user("user2", email)
    
    @pytest.mark.parametrize("username,email,expected_valid", [
        ("validuser", "valid@example.com", True),
        ("", "empty@example.com", False),  # Would need validation
        ("user", "invalid-email", False),   # Would need validation
        ("user123", "user123@test.org", True),
    ])
    def test_user_creation_parametrized(self, user_service, username, email, expected_valid):
        """Parametrized test for user creation validation"""
        if expected_valid:
            user = user_service.create_user(username, email)
            assert user.username == username
            assert user.email == email
        else:
            # This would require actual validation in UserService
            pass
    
    @pytest.mark.slow
    def test_slow_operation(self, user_service):
        """Test marked as slow"""
        # Simulate slow operation
        import time
        time.sleep(0.1)
        user = user_service.create_user("slowuser", "slow@example.com")
        assert user is not None
    
    @pytest.mark.integration
    def test_integration_test(self, user_service):
        """Integration test marker"""
        user = user_service.create_user("integrationuser", "integration@example.com")
        found_user = user_service.get_user_by_email("integration@example.com")
        assert found_user.id == user.id
    
    def test_with_temp_file(self, tmp_path):
        """Test using temporary file fixture"""
        test_file = tmp_path / "test_data.json"
        test_data = {"test": "data"}
        
        test_file.write_text(json.dumps(test_data))
        loaded_data = json.loads(test_file.read_text())
        
        assert loaded_data == test_data
    
    def test_with_capsys(self, capsys):
        """Test capturing stdout/stderr"""
        print("Test output")
        captured = capsys.readouterr()
        assert "Test output" in captured.out

# === MOCK PATTERNS ===

class TestMockingPatterns(unittest.TestCase):
    """Advanced mocking patterns"""
    
    def test_mock_property(self):
        """Test mocking properties"""
        mock_user = Mock()
        type(mock_user).is_active = PropertyMock(return_value=True)
        
        self.assertTrue(mock_user.is_active)
    
    def test_mock_side_effect(self):
        """Test mock with side effects"""
        mock_database = Mock()
        
        # Side effect as function
        def find_by_id_side_effect(user_id):
            if user_id == 1:
                return User(1, "user1", "user1@example.com")
            return None
        
        mock_database.find_by_id.side_effect = find_by_id_side_effect
        
        user1 = mock_database.find_by_id(1)
        user2 = mock_database.find_by_id(2)
        
        self.assertIsNotNone(user1)
        self.assertIsNone(user2)
    
    def test_mock_side_effect_exception(self):
        """Test mock raising exceptions"""
        mock_service = Mock()
        mock_service.risky_operation.side_effect = ConnectionError("Database unavailable")
        
        with self.assertRaises(ConnectionError):
            mock_service.risky_operation()
    
    def test_autospec_mock(self):
        """Test autospec mocking"""
        mock_database = create_autospec(Database, spec_set=True)
        
        # This will work
        mock_database.save(Mock())
        
        # This would raise AttributeError with autospec
        # mock_database.nonexistent_method()
    
    def test_mock_context_manager(self):
        """Test mocking context managers"""
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.read.return_value = "file content"
        
        with patch('builtins.open', return_value=mock_file):
            with open('test.txt', 'r') as f:
                content = f.read()
        
        self.assertEqual(content, "file content")
        mock_file.__enter__.assert_called_once()
        mock_file.__exit__.assert_called_once()
    
    @patch.object(UserService, '_generate_id')
    def test_patch_object(self, mock_generate_id):
        """Test patching object methods"""
        mock_generate_id.return_value = 999
        
        database = Database()
        email_service = EmailService()
        user_service = UserService(database, email_service)
        
        user = user_service.create_user("testuser", "test@example.com")
        
        self.assertEqual(user.id, 999)
        mock_generate_id.assert_called_once()

# === ASYNC TESTING PATTERNS ===

class AsyncUserService:
    """Async version for testing async patterns"""
    
    def __init__(self, database=None, email_service=None):
        self.database = database
        self.email_service = email_service
    
    async def create_user_async(self, username: str, email: str) -> User:
        """Async user creation"""
        existing = await self.get_user_by_email_async(email)
        if existing:
            raise ValueError("User already exists")
        
        user = User(
            id=await self._generate_id_async(),
            username=username,
            email=email
        )
        
        await self.database.save_async(user)
        await self.email_service.send_welcome_email_async(user.email)
        return user
    
    async def get_user_by_email_async(self, email: str) -> Optional[User]:
        """Async get user by email"""
        await asyncio.sleep(0.01)  # Simulate async operation
        return await self.database.find_by_email_async(email)
    
    async def _generate_id_async(self) -> int:
        """Async ID generation"""
        return await self.database.get_next_id_async()

class TestAsyncPatterns(unittest.TestCase):
    """Testing async code patterns"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_async_user_creation(self):
        """Test async user creation"""
        async def test_logic():
            mock_database = Mock()
            mock_email_service = Mock()
            
            # Setup async mocks
            mock_database.find_by_email_async = Mock(return_value=asyncio.coroutine(lambda: None)())
            mock_database.get_next_id_async = Mock(return_value=asyncio.coroutine(lambda: 123)())
            mock_database.save_async = Mock(return_value=asyncio.coroutine(lambda x: None)())
            mock_email_service.send_welcome_email_async = Mock(return_value=asyncio.coroutine(lambda x: None)())
            
            service = AsyncUserService(mock_database, mock_email_service)
            user = await service.create_user_async("testuser", "test@example.com")
            
            self.assertEqual(user.id, 123)
            self.assertEqual(user.username, "testuser")
        
        self.loop.run_until_complete(test_logic())
    
    def test_async_with_pytest_asyncio(self):
        """Example of how pytest-asyncio would work"""
        # This would require pytest-asyncio plugin
        # @pytest.mark.asyncio
        # async def test_async_function():
        #     result = await some_async_function()
        #     assert result == expected_value
        pass

# === TESTING UTILITIES ===

class TestFixtures:
    """Test fixture and utility patterns"""
    
    @staticmethod
    @contextmanager
    def temp_file_context(content: str = ""):
        """Context manager for temporary file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            yield temp_path
        finally:
            os.unlink(temp_path)
    
    @staticmethod
    def create_test_user(username: str = "testuser", email: str = "test@example.com") -> User:
        """Factory function for test users"""
        return User(
            id=1,
            username=username,
            email=email,
            created_at=datetime.datetime(2023, 1, 1)
        )
    
    @staticmethod
    def assert_user_equal(user1: User, user2: User):
        """Custom assertion for user equality"""
        assert user1.id == user2.id
        assert user1.username == user2.username
        assert user1.email == user2.email
        assert user1.is_active == user2.is_active

class TestDataBuilders:
    """Test data builder pattern"""
    
    class UserBuilder:
        """Builder pattern for test users"""
        
        def __init__(self):
            self.user_data = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'is_active': True,
                'created_at': datetime.datetime.now()
            }
        
        def with_id(self, user_id: int):
            self.user_data['id'] = user_id
            return self
        
        def with_username(self, username: str):
            self.user_data['username'] = username
            return self
        
        def with_email(self, email: str):
            self.user_data['email'] = email
            return self
        
        def inactive(self):
            self.user_data['is_active'] = False
            return self
        
        def build(self) -> User:
            return User(**self.user_data)
    
    def test_builder_pattern(self):
        """Test using builder pattern"""
        user = (TestDataBuilders.UserBuilder()
                .with_id(123)
                .with_username("builderuser")
                .with_email("builder@example.com")
                .inactive()
                .build())
        
        assert user.id == 123
        assert user.username == "builderuser"
        assert user.is_active is False

# === PERFORMANCE TESTING ===

class TestPerformance(unittest.TestCase):
    """Performance testing patterns"""
    
    def test_execution_time(self):
        """Test execution time constraints"""
        import time
        
        start_time = time.perf_counter()
        
        # Operation to test
        result = sum(range(10000))
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        # Assert operation completes within reasonable time
        self.assertLess(execution_time, 0.1)  # Less than 100ms
        self.assertEqual(result, 49995000)
    
    def test_memory_usage(self):
        """Test memory usage patterns"""
        import sys
        
        # Create large data structure
        large_list = list(range(100000))
        
        # Check memory usage (simplified)
        memory_size = sys.getsizeof(large_list)
        
        # Assert reasonable memory usage
        self.assertLess(memory_size, 10 * 1024 * 1024)  # Less than 10MB

# Example test suite organization
if __name__ == "__main__":
    # Running specific test classes
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestUserServiceUnittest))
    suite.addTest(unittest.makeSuite(TestUserServiceMocking))
    suite.addTest(unittest.makeSuite(TestMockingPatterns))
    suite.addTest(unittest.makeSuite(TestAsyncPatterns))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")