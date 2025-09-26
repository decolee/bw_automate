#!/usr/bin/env python3
"""
Security Vulnerabilities Demo - Testing Security Analysis Detection
Contains various security issues for comprehensive security scanning
"""

import os
import sys
import subprocess
import pickle
import yaml
import json
import hashlib
import random
import requests
import urllib.request
import socket
import ssl
from pathlib import Path
import tempfile
import shutil

# === HARDCODED SECRETS AND CREDENTIALS ===

# API Keys and tokens (SECURITY ISSUE)
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12345678"
STRIPE_SECRET_KEY = "sk_test_1234567890abcdef1234567890abcdef"
JWT_SECRET = "supersecret123456789"
DATABASE_PASSWORD = "admin123456"
API_SECRET = "my-super-secret-api-key-2023"

# Connection strings with credentials (SECURITY ISSUE)
DB_CONNECTION = "postgresql://admin:password123@localhost:5432/production"
REDIS_URL = "redis://user:secretpassword@localhost:6379/0"
MONGO_URI = "mongodb://admin:mongopass@localhost:27017/production"

# Configuration with sensitive data (SECURITY ISSUE)
CONFIG = {
    "database": {
        "host": "localhost",
        "user": "admin",
        "password": "production_password_2023",
        "port": 5432
    },
    "api_keys": {
        "openai": "sk-1234567890abcdef",
        "anthropic": "ant-api-03-12345",
        "google": "AIzaSyABC123DEF456GHI789JKL"
    },
    "encryption_key": "AES256-SECRET-KEY-FOR-ENCRYPTION"
}

# === SQL INJECTION VULNERABILITIES ===

def vulnerable_user_login(username: str, password: str):
    """SECURITY ISSUE: SQL injection via string concatenation"""
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    return execute_query(query)

def vulnerable_search(search_term: str):
    """SECURITY ISSUE: SQL injection via string formatting"""
    query = "SELECT * FROM products WHERE name LIKE '%%%s%%'" % search_term
    return execute_query(query)

def vulnerable_dynamic_table(table_name: str, user_id: int):
    """SECURITY ISSUE: SQL injection via f-string"""
    query = f"SELECT * FROM {table_name} WHERE user_id = {user_id}"
    return execute_query(query)

def vulnerable_order_by(sort_column: str):
    """SECURITY ISSUE: SQL injection in ORDER BY clause"""
    query = f"SELECT * FROM users ORDER BY {sort_column}"
    return execute_query(query)

def vulnerable_batch_insert(user_data: list):
    """SECURITY ISSUE: SQL injection in batch operations"""
    values = []
    for user in user_data:
        values.append(f"('{user['name']}', '{user['email']}')")
    query = f"INSERT INTO users (name, email) VALUES {', '.join(values)}"
    return execute_query(query)

def execute_query(query: str):
    """Simulated query execution"""
    print(f"Executing: {query}")
    return []

# === INSECURE FUNCTIONS AND OPERATIONS ===

def dangerous_eval_usage(user_input: str):
    """SECURITY ISSUE: Using eval() with user input"""
    result = eval(user_input)  # Extremely dangerous!
    return result

def dangerous_exec_usage(code_string: str):
    """SECURITY ISSUE: Using exec() with dynamic content"""
    exec(code_string)  # Can execute arbitrary code

def insecure_pickle_load(data: bytes):
    """SECURITY ISSUE: Unpickling untrusted data"""
    return pickle.loads(data)  # Can execute arbitrary code

def unsafe_yaml_load(yaml_content: str):
    """SECURITY ISSUE: Using unsafe YAML loader"""
    return yaml.load(yaml_content)  # Should use safe_load

def insecure_subprocess_shell(user_command: str):
    """SECURITY ISSUE: Shell injection via subprocess"""
    result = subprocess.run(user_command, shell=True, capture_output=True)
    return result.stdout

def dangerous_input_usage():
    """SECURITY ISSUE: Using input() in production code"""
    user_data = input("Enter your data: ")  # Can be exploited
    return user_data

# === FILE SYSTEM VULNERABILITIES ===

def path_traversal_vulnerability(filename: str):
    """SECURITY ISSUE: Path traversal attack"""
    # User could provide "../../../etc/passwd"
    file_path = os.path.join("/var/uploads", filename)
    with open(file_path, 'r') as f:
        return f.read()

def insecure_file_permissions():
    """SECURITY ISSUE: Creating files with insecure permissions"""
    temp_file = "/tmp/sensitive_data.txt"
    with open(temp_file, 'w') as f:
        f.write("Sensitive information")
    os.chmod(temp_file, 0o777)  # World readable/writable

def unsafe_temp_file_usage():
    """SECURITY ISSUE: Insecure temporary file creation"""
    # Creates predictable filenames
    temp_filename = f"/tmp/data_{random.randint(1000, 9999)}.txt"
    with open(temp_filename, 'w') as f:
        f.write("Sensitive data")
    return temp_filename

def directory_traversal_write(user_path: str, content: str):
    """SECURITY ISSUE: Unrestricted file write"""
    # No validation of user_path
    with open(user_path, 'w') as f:
        f.write(content)

def insecure_file_deletion(file_pattern: str):
    """SECURITY ISSUE: Unsafe file deletion"""
    # Using shell expansion
    os.system(f"rm -f {file_pattern}")

# === NETWORK SECURITY VULNERABILITIES ===

def insecure_http_request(url: str):
    """SECURITY ISSUE: Unvalidated HTTP requests"""
    # No URL validation, SSRF vulnerability
    response = requests.get(url)
    return response.content

def disable_ssl_verification(url: str):
    """SECURITY ISSUE: Disabled SSL verification"""
    response = requests.get(url, verify=False)  # Disables SSL verification
    return response.content

def insecure_socket_connection(host: str, port: int):
    """SECURITY ISSUE: Unencrypted socket connection"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    # No encryption or validation
    return sock

def weak_ssl_context():
    """SECURITY ISSUE: Weak SSL/TLS configuration"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def ftp_with_credentials(host: str):
    """SECURITY ISSUE: Unencrypted FTP with hardcoded credentials"""
    import ftplib
    ftp = ftplib.FTP(host)
    ftp.login("admin", "password123")  # Hardcoded credentials over unencrypted connection
    return ftp

# === CRYPTOGRAPHIC VULNERABILITIES ===

def weak_hash_function(password: str):
    """SECURITY ISSUE: Using weak hash function"""
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is broken

def insecure_random_generation():
    """SECURITY ISSUE: Using insecure random for security purposes"""
    # Should use secrets module for cryptographic randomness
    token = str(random.randint(100000, 999999))
    session_id = str(random.random())
    return token, session_id

def hardcoded_encryption_key():
    """SECURITY ISSUE: Hardcoded encryption key"""
    from cryptography.fernet import Fernet
    
    # Hardcoded key (should be generated and stored securely)
    key = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
    fernet = Fernet(key)
    return fernet

def weak_password_validation(password: str):
    """SECURITY ISSUE: Weak password requirements"""
    # Minimal validation
    if len(password) >= 6:  # Too short minimum
        return True
    return False

def insecure_session_management():
    """SECURITY ISSUE: Insecure session handling"""
    session_data = {
        "user_id": 123,
        "is_admin": True,
        "expires": "never"  # No expiration
    }
    # Storing sensitive data in easily predictable format
    session_token = f"user_{session_data['user_id']}_admin"
    return session_token

# === INJECTION VULNERABILITIES ===

def command_injection(user_input: str):
    """SECURITY ISSUE: Command injection vulnerability"""
    # User could inject: "file.txt; rm -rf /"
    command = f"cat {user_input}"
    os.system(command)

def ldap_injection_vulnerability(username: str):
    """SECURITY ISSUE: LDAP injection"""
    # User could inject: "admin)(|(password=*))"
    ldap_query = f"(&(uid={username})(objectClass=person))"
    return ldap_query

def xpath_injection(user_id: str):
    """SECURITY ISSUE: XPath injection"""
    # User could inject: "' or '1'='1"
    xpath_query = f"//user[@id='{user_id}']"
    return xpath_query

def nosql_injection(user_input: str):
    """SECURITY ISSUE: NoSQL injection"""
    # User could inject: {"$ne": ""}
    mongo_query = {"username": user_input}
    return mongo_query

# === DESERIALIZATION VULNERABILITIES ===

def unsafe_json_deserialization(json_data: str):
    """SECURITY ISSUE: Unsafe JSON handling"""
    # Could be exploited with custom object hooks
    return json.loads(json_data)

def pickle_deserialization_vulnerability(pickle_data: bytes):
    """SECURITY ISSUE: Pickle deserialization"""
    # Pickle can execute arbitrary code during deserialization
    return pickle.loads(pickle_data)

def eval_based_deserialization(data_string: str):
    """SECURITY ISSUE: Using eval for deserialization"""
    # Extremely dangerous - can execute any Python code
    return eval(f"dict({data_string})")

# === INFORMATION DISCLOSURE ===

def debug_info_exposure(user_request):
    """SECURITY ISSUE: Exposing debug information"""
    try:
        process_request(user_request)
    except Exception as e:
        # Exposing internal paths and sensitive info
        error_details = {
            "error": str(e),
            "file": __file__,
            "line": sys.exc_info()[2].tb_lineno,
            "locals": locals(),
            "globals": list(globals().keys())
        }
        return error_details

def sensitive_data_logging(user_data: dict):
    """SECURITY ISSUE: Logging sensitive information"""
    import logging
    
    # Logging passwords and sensitive data
    logging.info(f"User login attempt: {user_data}")  # Contains password
    logging.debug(f"Full user object: {user_data}")
    
    print(f"Debug: User password is {user_data.get('password')}")

def stack_trace_exposure():
    """SECURITY ISSUE: Exposing stack traces to users"""
    try:
        1 / 0  # Intentional error
    except Exception as e:
        import traceback
        # Returning full stack trace to user
        return {
            "error": "Internal server error",
            "details": traceback.format_exc(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "executable": sys.executable
            }
        }

# === ACCESS CONTROL VULNERABILITIES ===

def insecure_direct_object_reference(user_id: int, file_id: str):
    """SECURITY ISSUE: Direct object reference without authorization"""
    # No check if user owns the file
    file_path = f"/files/{file_id}"
    with open(file_path, 'r') as f:
        return f.read()

def privilege_escalation_vulnerability(user_role: str, action: str):
    """SECURITY ISSUE: Inadequate privilege checking"""
    # Weak role checking
    if user_role in ["admin", "user", "guest"]:  # Too permissive
        if action == "delete_all_users":
            return perform_admin_action(action)
    return "Access denied"

def session_fixation_vulnerability():
    """SECURITY ISSUE: Session fixation"""
    # Not regenerating session ID after login
    session_id = "fixed_session_12345"
    return session_id

# === BUSINESS LOGIC VULNERABILITIES ===

def race_condition_vulnerability(user_id: int, amount: float):
    """SECURITY ISSUE: Race condition in financial transaction"""
    # No locking mechanism
    current_balance = get_user_balance(user_id)
    if current_balance >= amount:
        # Race condition here - balance could change
        new_balance = current_balance - amount
        update_user_balance(user_id, new_balance)
        return True
    return False

def integer_overflow_vulnerability(quantity: int, price: int):
    """SECURITY ISSUE: Integer overflow in calculations"""
    # No bounds checking
    total_cost = quantity * price
    return total_cost

def business_logic_bypass(user_type: str, discount_code: str):
    """SECURITY ISSUE: Business logic flaw"""
    # Can be bypassed by manipulating user_type
    if user_type == "premium":
        discount = 50
    elif discount_code == "SAVE20":
        discount = 20
    else:
        discount = 0
    
    # Logic flaw: can combine premium + discount code
    return discount

# === CONFIGURATION VULNERABILITIES ===

def insecure_default_configuration():
    """SECURITY ISSUE: Insecure default settings"""
    config = {
        "debug": True,  # Should be False in production
        "secret_key": "default_secret",  # Should be random
        "allowed_hosts": ["*"],  # Too permissive
        "ssl_required": False,  # Should be True
        "password_min_length": 4,  # Too short
        "session_timeout": 86400 * 30,  # 30 days - too long
        "admin_panel_enabled": True,  # Should be disabled if not needed
        "error_reporting": "detailed"  # Should be minimal in production
    }
    return config

def hardcoded_paths_and_urls():
    """SECURITY ISSUE: Hardcoded sensitive paths"""
    admin_url = "https://production-server.com/admin/secret-panel"
    backup_path = "/var/backups/database_dump_2023.sql"
    log_file = "/var/log/application/sensitive-operations.log"
    
    return {
        "admin_url": admin_url,
        "backup_path": backup_path,
        "log_file": log_file
    }

# === HELPER FUNCTIONS ===

def process_request(request):
    """Helper function"""
    pass

def get_user_balance(user_id: int):
    """Helper function"""
    return 1000.0

def update_user_balance(user_id: int, new_balance: float):
    """Helper function"""
    pass

def perform_admin_action(action: str):
    """Helper function"""
    return f"Performed: {action}"

# === COMPREHENSIVE SECURITY TEST ===

class SecurityVulnerabilityDemo:
    """Comprehensive security vulnerability demonstration"""
    
    def __init__(self):
        self.api_key = "sk-1234567890abcdef"  # Hardcoded API key
        self.db_password = "admin123"  # Hardcoded password
    
    def demonstrate_all_vulnerabilities(self):
        """Execute all vulnerability demonstrations"""
        print("=== Security Vulnerability Demonstration ===")
        
        # SQL Injection
        print("\n1. SQL Injection Vulnerabilities:")
        vulnerable_user_login("admin' OR '1'='1' --", "password")
        vulnerable_search("'; DROP TABLE users; --")
        
        # Command Injection
        print("\n2. Command Injection:")
        command_injection("file.txt; cat /etc/passwd")
        
        # Insecure Functions
        print("\n3. Dangerous Function Usage:")
        try:
            dangerous_eval_usage("__import__('os').system('echo hacked')")
        except:
            pass
        
        # File System Vulnerabilities
        print("\n4. File System Vulnerabilities:")
        try:
            path_traversal_vulnerability("../../../etc/passwd")
        except:
            pass
        
        # Network Security
        print("\n5. Network Security Issues:")
        try:
            insecure_http_request("http://internal-server/admin")
        except:
            pass
        
        # Cryptographic Issues
        print("\n6. Cryptographic Vulnerabilities:")
        weak_hash = weak_hash_function("password123")
        print(f"Weak hash: {weak_hash}")
        
        # Information Disclosure
        print("\n7. Information Disclosure:")
        debug_info = debug_info_exposure({"test": "data"})
        
        # Business Logic
        print("\n8. Business Logic Flaws:")
        race_result = race_condition_vulnerability(1, 100.0)
        
        print("\n=== Vulnerability demonstration completed ===")

# Multiple classes with different vulnerability patterns
class UserAuthentication:
    """User authentication with security issues"""
    
    def __init__(self):
        self.secret_key = "hardcoded_jwt_secret_2023"  # SECURITY ISSUE
        self.admin_password = "admin123"  # SECURITY ISSUE
    
    def authenticate_user(self, username: str, password: str):
        """SECURITY ISSUE: Weak authentication"""
        # No rate limiting, weak password policy
        if username == "admin" and password == self.admin_password:
            return self.generate_token(username)
        
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        return self.execute_auth_query(query)
    
    def generate_token(self, username: str):
        """SECURITY ISSUE: Weak token generation"""
        # Predictable token generation
        import time
        timestamp = int(time.time())
        token = f"{username}_{timestamp}_{self.secret_key[:8]}"
        return token
    
    def execute_auth_query(self, query: str):
        """Simulate database query"""
        print(f"Auth query: {query}")
        return "authenticated"

class DataProcessor:
    """Data processing with multiple vulnerabilities"""
    
    def __init__(self):
        self.encryption_key = b'hardcoded_key_123456'  # SECURITY ISSUE
    
    def process_uploaded_file(self, filename: str, content: bytes):
        """SECURITY ISSUE: Insecure file processing"""
        # No file type validation
        # Path traversal vulnerability
        file_path = f"/uploads/{filename}"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Deserializing untrusted data
        if filename.endswith('.pkl'):
            return pickle.loads(content)  # SECURITY ISSUE
        
        return file_path
    
    def execute_user_code(self, code: str):
        """SECURITY ISSUE: Executing user-provided code"""
        # Extremely dangerous - arbitrary code execution
        exec(code)  # SECURITY ISSUE
    
    def process_yaml_config(self, yaml_content: str):
        """SECURITY ISSUE: Unsafe YAML processing"""
        return yaml.load(yaml_content)  # Should use safe_load

if __name__ == "__main__":
    # Demonstrate all security vulnerabilities
    demo = SecurityVulnerabilityDemo()
    demo.demonstrate_all_vulnerabilities()
    
    # Test authentication vulnerabilities
    auth = UserAuthentication()
    auth.authenticate_user("admin", "admin123")
    
    # Test data processing vulnerabilities
    processor = DataProcessor()
    processor.process_uploaded_file("../../../etc/passwd", b"malicious content")
    
    print("\n=== Security vulnerability testing completed! ===")
    print("This file contains numerous security issues for testing purposes.")