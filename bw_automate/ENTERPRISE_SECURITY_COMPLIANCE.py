#!/usr/bin/env python3
"""
ENTERPRISE SECURITY & COMPLIANCE MODULE - BW AUTOMATE SYSTEM
Sistema completo de segurança e compliance para ambientes corporativos
Implementa criptografia, auditoria, controle de acesso e conformidade regulatória
"""

import os
import json
import hashlib
import hmac
import secrets
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
import re
import jwt

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("Installing cryptography for encryption...")
    os.system("pip install cryptography")
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend

try:
    import pyjwt
except ImportError:
    print("Installing PyJWT for token management...")
    os.system("pip install PyJWT")
    import jwt

try:
    import bcrypt
except ImportError:
    print("Installing bcrypt for password hashing...")
    os.system("pip install bcrypt")
    import bcrypt


class SecurityLevel(Enum):
    """Níveis de segurança"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Padrões de compliance"""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"


class AccessLevel(Enum):
    """Níveis de acesso"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPERUSER = "superuser"


@dataclass
class SecurityEvent:
    """Evento de segurança"""
    event_id: str
    event_type: str
    severity: SecurityLevel
    user_id: Optional[str]
    resource: str
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = None
    risk_score: float = 0.0


@dataclass
class User:
    """Usuário do sistema"""
    user_id: str
    username: str
    email: str
    password_hash: str
    access_level: AccessLevel
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None


@dataclass
class AccessControlRule:
    """Regra de controle de acesso"""
    rule_id: str
    user_id: Optional[str]
    resource_pattern: str
    allowed_actions: List[str]
    denied_actions: List[str]
    conditions: Dict[str, Any]
    expires_at: Optional[datetime] = None


class EncryptionManager:
    """Gerenciador de criptografia"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or self._generate_master_key()
        self.fernet = Fernet(self.master_key.encode()[:44] + b'=')
        
        # Gera par de chaves RSA para criptografia assimétrica
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def _generate_master_key(self) -> str:
        """Gera chave mestra"""
        return Fernet.generate_key().decode()
    
    def encrypt_data(self, data: str) -> str:
        """Criptografa dados com chave simétrica"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Descriptografa dados"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Criptografa arquivo"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.fernet.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str):
        """Descriptografa arquivo"""
        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.fernet.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
    
    def encrypt_with_public_key(self, data: str) -> bytes:
        """Criptografa com chave pública RSA"""
        return self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_with_private_key(self, encrypted_data: bytes) -> str:
        """Descriptografa com chave privada RSA"""
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()
    
    def get_public_key_pem(self) -> str:
        """Retorna chave pública em formato PEM"""
        return self.public_key.public_key_serialization(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Gera hash seguro dos dados"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt


class UserManager:
    """Gerenciador de usuários"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.encryption = EncryptionManager()
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de usuários"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                access_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT 1,
                failed_login_attempts INTEGER DEFAULT 0,
                mfa_enabled BOOLEAN DEFAULT 0,
                mfa_secret TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, email: str, password: str, 
                   access_level: AccessLevel = AccessLevel.READ) -> User:
        """Cria novo usuário"""
        user_id = secrets.token_urlsafe(16)
        
        # Hash da senha
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            access_level=access_level,
            created_at=datetime.now()
        )
        
        # Salva no banco
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (user_id, username, email, password_hash, access_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.user_id, user.username, user.email, user.password_hash,
              user.access_level.value, user.created_at.isoformat()))
        conn.commit()
        conn.close()
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Verifica senha
        stored_hash = row[3]
        if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
            # Incrementa tentativas de login falhadas
            self._increment_failed_attempts(row[0])
            return None
        
        # Reset failed attempts on successful login
        self._reset_failed_attempts(row[0])
        
        user = User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            access_level=AccessLevel(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            last_login=datetime.fromisoformat(row[6]) if row[6] else None,
            is_active=bool(row[7]),
            failed_login_attempts=row[8],
            mfa_enabled=bool(row[9]),
            mfa_secret=row[10]
        )
        
        # Atualiza último login
        self._update_last_login(user.user_id)
        
        return user
    
    def _increment_failed_attempts(self, user_id: str):
        """Incrementa tentativas de login falhadas"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    def _reset_failed_attempts(self, user_id: str):
        """Reset tentativas de login falhadas"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'UPDATE users SET failed_login_attempts = 0 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    def _update_last_login(self, user_id: str):
        """Atualiza último login"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'UPDATE users SET last_login = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
    
    def create_session(self, user_id: str, expires_in_hours: int = 24,
                      ip_address: str = None, user_agent: str = None) -> str:
        """Cria sessão de usuário"""
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=expires_in_hours)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO sessions (session_id, user_id, created_at, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, created_at.isoformat(), expires_at.isoformat(),
              ip_address, user_agent))
        conn.commit()
        conn.close()
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Valida sessão e retorna user_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT user_id FROM sessions 
            WHERE session_id = ? AND expires_at > ? AND is_active = 1
        ''', (session_id, datetime.now().isoformat()))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None


class AccessControlManager:
    """Gerenciador de controle de acesso"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de controle de acesso"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS access_rules (
                rule_id TEXT PRIMARY KEY,
                user_id TEXT,
                resource_pattern TEXT NOT NULL,
                allowed_actions TEXT NOT NULL,
                denied_actions TEXT NOT NULL,
                conditions TEXT,
                expires_at TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_rule(self, rule: AccessControlRule):
        """Adiciona regra de acesso"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO access_rules 
            (rule_id, user_id, resource_pattern, allowed_actions, denied_actions, conditions, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rule.rule_id, rule.user_id, rule.resource_pattern,
            json.dumps(rule.allowed_actions), json.dumps(rule.denied_actions),
            json.dumps(rule.conditions), 
            rule.expires_at.isoformat() if rule.expires_at else None,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def check_access(self, user_id: str, resource: str, action: str) -> bool:
        """Verifica se usuário tem acesso ao recurso"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT allowed_actions, denied_actions, conditions FROM access_rules
            WHERE (user_id = ? OR user_id IS NULL) 
            AND (expires_at IS NULL OR expires_at > ?)
        ''', (user_id, datetime.now().isoformat()))
        
        rules = cursor.fetchall()
        conn.close()
        
        # Por padrão, nega acesso
        access_granted = False
        
        for rule in rules:
            allowed_actions = json.loads(rule[0])
            denied_actions = json.loads(rule[1])
            conditions = json.loads(rule[2])
            
            # Verifica se a ação está explicitamente negada
            if action in denied_actions:
                return False
            
            # Verifica se a ação está permitida
            if action in allowed_actions or '*' in allowed_actions:
                # TODO: Verificar condições adicionais
                access_granted = True
        
        return access_granted


class AuditLogger:
    """Sistema de auditoria e logs de segurança"""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuração de logging
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo de auditoria
        audit_handler = logging.FileHandler(self.log_dir / 'security_audit.log')
        audit_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        self.logger.addHandler(audit_handler)
        
        # Banco de dados para eventos estruturados
        self.db_path = self.log_dir / 'security_events.db'
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de eventos"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                user_id TEXT,
                resource TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                risk_score REAL DEFAULT 0.0
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_event(self, event: SecurityEvent):
        """Registra evento de segurança"""
        # Log estruturado no banco
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO security_events 
            (event_id, event_type, severity, user_id, resource, action, timestamp, 
             ip_address, user_agent, details, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id, event.event_type, event.severity.value,
            event.user_id, event.resource, event.action,
            event.timestamp.isoformat(), event.ip_address, event.user_agent,
            json.dumps(event.details), event.risk_score
        ))
        conn.commit()
        conn.close()
        
        # Log textual
        log_message = (
            f"EVENT: {event.event_type} | "
            f"SEVERITY: {event.severity.value} | "
            f"USER: {event.user_id} | "
            f"RESOURCE: {event.resource} | "
            f"ACTION: {event.action} | "
            f"RISK: {event.risk_score}"
        )
        
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            self.logger.error(log_message)
        elif event.severity == SecurityLevel.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_events(self, start_date: datetime = None, end_date: datetime = None,
                  severity: SecurityLevel = None, user_id: str = None) -> List[SecurityEvent]:
        """Recupera eventos de segurança"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event = SecurityEvent(
                event_id=row[0],
                event_type=row[1],
                severity=SecurityLevel(row[2]),
                user_id=row[3],
                resource=row[4],
                action=row[5],
                timestamp=datetime.fromisoformat(row[6]),
                ip_address=row[7],
                user_agent=row[8],
                details=json.loads(row[9]) if row[9] else None,
                risk_score=row[10]
            )
            events.append(event)
        
        return events


class ComplianceChecker:
    """Verificador de conformidade regulatória"""
    
    def __init__(self):
        self.standards = {
            ComplianceStandard.GDPR: self._check_gdpr_compliance,
            ComplianceStandard.SOX: self._check_sox_compliance,
            ComplianceStandard.HIPAA: self._check_hipaa_compliance,
            ComplianceStandard.PCI_DSS: self._check_pci_compliance,
            ComplianceStandard.ISO27001: self._check_iso27001_compliance,
            ComplianceStandard.NIST: self._check_nist_compliance
        }
    
    def check_compliance(self, standard: ComplianceStandard, 
                        system_config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade com padrão específico"""
        if standard not in self.standards:
            return {"error": f"Standard {standard.value} not supported"}
        
        return self.standards[standard](system_config)
    
    def _check_gdpr_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade GDPR"""
        checks = {
            "data_encryption": self._check_encryption_enabled(config),
            "access_logging": self._check_access_logging(config),
            "data_retention": self._check_data_retention_policy(config),
            "user_consent": self._check_user_consent_tracking(config),
            "data_portability": self._check_data_export_capability(config),
            "right_to_deletion": self._check_deletion_capability(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "GDPR",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.8 else "non_compliant",
            "recommendations": self._get_gdpr_recommendations(checks)
        }
    
    def _check_sox_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade SOX"""
        checks = {
            "financial_data_security": self._check_financial_data_protection(config),
            "audit_trails": self._check_comprehensive_audit_trails(config),
            "segregation_of_duties": self._check_role_separation(config),
            "change_management": self._check_change_control(config),
            "access_controls": self._check_privileged_access_controls(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "SOX",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.9 else "non_compliant",
            "recommendations": self._get_sox_recommendations(checks)
        }
    
    def _check_hipaa_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade HIPAA"""
        checks = {
            "phi_encryption": self._check_phi_encryption(config),
            "access_controls": self._check_healthcare_access_controls(config),
            "audit_logs": self._check_healthcare_audit_logs(config),
            "data_backup": self._check_data_backup_procedures(config),
            "incident_response": self._check_incident_response_plan(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "HIPAA",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.85 else "non_compliant",
            "recommendations": self._get_hipaa_recommendations(checks)
        }
    
    def _check_pci_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade PCI DSS"""
        checks = {
            "cardholder_data_protection": self._check_cardholder_data_protection(config),
            "secure_network": self._check_secure_network_config(config),
            "vulnerability_management": self._check_vulnerability_management(config),
            "strong_access_controls": self._check_strong_access_controls(config),
            "network_monitoring": self._check_network_monitoring(config),
            "security_testing": self._check_regular_security_testing(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "PCI DSS",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.95 else "non_compliant",
            "recommendations": self._get_pci_recommendations(checks)
        }
    
    def _check_iso27001_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade ISO 27001"""
        checks = {
            "isms_implementation": self._check_isms_implementation(config),
            "risk_management": self._check_risk_management_process(config),
            "security_policies": self._check_security_policies(config),
            "asset_management": self._check_asset_management(config),
            "incident_management": self._check_incident_management(config),
            "business_continuity": self._check_business_continuity(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "ISO 27001",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.8 else "non_compliant",
            "recommendations": self._get_iso27001_recommendations(checks)
        }
    
    def _check_nist_compliance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica conformidade NIST Cybersecurity Framework"""
        checks = {
            "identify": self._check_nist_identify(config),
            "protect": self._check_nist_protect(config),
            "detect": self._check_nist_detect(config),
            "respond": self._check_nist_respond(config),
            "recover": self._check_nist_recover(config)
        }
        
        compliance_score = sum(1 for check in checks.values() if check) / len(checks)
        
        return {
            "standard": "NIST CSF",
            "compliance_score": compliance_score,
            "checks": checks,
            "status": "compliant" if compliance_score >= 0.8 else "non_compliant",
            "recommendations": self._get_nist_recommendations(checks)
        }
    
    # Métodos auxiliares de verificação
    def _check_encryption_enabled(self, config: Dict[str, Any]) -> bool:
        return config.get("encryption", {}).get("enabled", False)
    
    def _check_access_logging(self, config: Dict[str, Any]) -> bool:
        return config.get("audit", {}).get("access_logging", False)
    
    def _check_data_retention_policy(self, config: Dict[str, Any]) -> bool:
        return "data_retention_days" in config.get("policies", {})
    
    def _check_user_consent_tracking(self, config: Dict[str, Any]) -> bool:
        return config.get("gdpr", {}).get("consent_tracking", False)
    
    def _check_data_export_capability(self, config: Dict[str, Any]) -> bool:
        return config.get("gdpr", {}).get("data_export", False)
    
    def _check_deletion_capability(self, config: Dict[str, Any]) -> bool:
        return config.get("gdpr", {}).get("data_deletion", False)
    
    def _check_financial_data_protection(self, config: Dict[str, Any]) -> bool:
        return config.get("sox", {}).get("financial_controls", False)
    
    def _check_comprehensive_audit_trails(self, config: Dict[str, Any]) -> bool:
        return config.get("audit", {}).get("comprehensive_trails", False)
    
    def _check_role_separation(self, config: Dict[str, Any]) -> bool:
        return config.get("access_control", {}).get("role_separation", False)
    
    def _check_change_control(self, config: Dict[str, Any]) -> bool:
        return config.get("change_management", {}).get("enabled", False)
    
    def _check_privileged_access_controls(self, config: Dict[str, Any]) -> bool:
        return config.get("access_control", {}).get("privileged_controls", False)
    
    def _check_phi_encryption(self, config: Dict[str, Any]) -> bool:
        return config.get("hipaa", {}).get("phi_encryption", False)
    
    def _check_healthcare_access_controls(self, config: Dict[str, Any]) -> bool:
        return config.get("hipaa", {}).get("access_controls", False)
    
    def _check_healthcare_audit_logs(self, config: Dict[str, Any]) -> bool:
        return config.get("hipaa", {}).get("audit_logs", False)
    
    def _check_data_backup_procedures(self, config: Dict[str, Any]) -> bool:
        return config.get("backup", {}).get("enabled", False)
    
    def _check_incident_response_plan(self, config: Dict[str, Any]) -> bool:
        return config.get("incident_response", {}).get("plan_exists", False)
    
    def _check_cardholder_data_protection(self, config: Dict[str, Any]) -> bool:
        return config.get("pci", {}).get("cardholder_protection", False)
    
    def _check_secure_network_config(self, config: Dict[str, Any]) -> bool:
        return config.get("network", {}).get("secure_config", False)
    
    def _check_vulnerability_management(self, config: Dict[str, Any]) -> bool:
        return config.get("security", {}).get("vulnerability_scanning", False)
    
    def _check_strong_access_controls(self, config: Dict[str, Any]) -> bool:
        return config.get("access_control", {}).get("strong_controls", False)
    
    def _check_network_monitoring(self, config: Dict[str, Any]) -> bool:
        return config.get("monitoring", {}).get("network_monitoring", False)
    
    def _check_regular_security_testing(self, config: Dict[str, Any]) -> bool:
        return config.get("testing", {}).get("security_testing", False)
    
    def _check_isms_implementation(self, config: Dict[str, Any]) -> bool:
        return config.get("iso27001", {}).get("isms", False)
    
    def _check_risk_management_process(self, config: Dict[str, Any]) -> bool:
        return config.get("risk_management", {}).get("process_exists", False)
    
    def _check_security_policies(self, config: Dict[str, Any]) -> bool:
        return config.get("policies", {}).get("security_policies", False)
    
    def _check_asset_management(self, config: Dict[str, Any]) -> bool:
        return config.get("asset_management", {}).get("enabled", False)
    
    def _check_incident_management(self, config: Dict[str, Any]) -> bool:
        return config.get("incident_management", {}).get("enabled", False)
    
    def _check_business_continuity(self, config: Dict[str, Any]) -> bool:
        return config.get("business_continuity", {}).get("plan_exists", False)
    
    def _check_nist_identify(self, config: Dict[str, Any]) -> bool:
        return config.get("nist", {}).get("identify", False)
    
    def _check_nist_protect(self, config: Dict[str, Any]) -> bool:
        return config.get("nist", {}).get("protect", False)
    
    def _check_nist_detect(self, config: Dict[str, Any]) -> bool:
        return config.get("nist", {}).get("detect", False)
    
    def _check_nist_respond(self, config: Dict[str, Any]) -> bool:
        return config.get("nist", {}).get("respond", False)
    
    def _check_nist_recover(self, config: Dict[str, Any]) -> bool:
        return config.get("nist", {}).get("recover", False)
    
    # Métodos de recomendações
    def _get_gdpr_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("data_encryption"):
            recommendations.append("Implementar criptografia de dados pessoais")
        if not checks.get("access_logging"):
            recommendations.append("Ativar logging de acesso a dados pessoais")
        if not checks.get("data_retention"):
            recommendations.append("Definir política de retenção de dados")
        if not checks.get("user_consent"):
            recommendations.append("Implementar rastreamento de consentimento")
        if not checks.get("data_portability"):
            recommendations.append("Implementar exportação de dados do usuário")
        if not checks.get("right_to_deletion"):
            recommendations.append("Implementar capacidade de exclusão de dados")
        return recommendations
    
    def _get_sox_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("financial_data_security"):
            recommendations.append("Implementar controles de segurança para dados financeiros")
        if not checks.get("audit_trails"):
            recommendations.append("Implementar trilhas de auditoria abrangentes")
        if not checks.get("segregation_of_duties"):
            recommendations.append("Implementar segregação de funções")
        if not checks.get("change_management"):
            recommendations.append("Implementar controle de mudanças")
        if not checks.get("access_controls"):
            recommendations.append("Implementar controles de acesso privilegiado")
        return recommendations
    
    def _get_hipaa_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("phi_encryption"):
            recommendations.append("Implementar criptografia de PHI")
        if not checks.get("access_controls"):
            recommendations.append("Implementar controles de acesso para healthcare")
        if not checks.get("audit_logs"):
            recommendations.append("Implementar logs de auditoria para healthcare")
        if not checks.get("data_backup"):
            recommendations.append("Implementar procedimentos de backup")
        if not checks.get("incident_response"):
            recommendations.append("Desenvolver plano de resposta a incidentes")
        return recommendations
    
    def _get_pci_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("cardholder_data_protection"):
            recommendations.append("Implementar proteção de dados do portador de cartão")
        if not checks.get("secure_network"):
            recommendations.append("Configurar rede segura")
        if not checks.get("vulnerability_management"):
            recommendations.append("Implementar gestão de vulnerabilidades")
        if not checks.get("strong_access_controls"):
            recommendations.append("Implementar controles de acesso robustos")
        if not checks.get("network_monitoring"):
            recommendations.append("Implementar monitoramento de rede")
        if not checks.get("security_testing"):
            recommendations.append("Implementar testes de segurança regulares")
        return recommendations
    
    def _get_iso27001_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("isms_implementation"):
            recommendations.append("Implementar SGSI (Sistema de Gestão de Segurança da Informação)")
        if not checks.get("risk_management"):
            recommendations.append("Implementar processo de gestão de riscos")
        if not checks.get("security_policies"):
            recommendations.append("Desenvolver políticas de segurança")
        if not checks.get("asset_management"):
            recommendations.append("Implementar gestão de ativos")
        if not checks.get("incident_management"):
            recommendations.append("Implementar gestão de incidentes")
        if not checks.get("business_continuity"):
            recommendations.append("Desenvolver plano de continuidade de negócios")
        return recommendations
    
    def _get_nist_recommendations(self, checks: Dict[str, bool]) -> List[str]:
        recommendations = []
        if not checks.get("identify"):
            recommendations.append("Implementar função IDENTIFY do NIST CSF")
        if not checks.get("protect"):
            recommendations.append("Implementar função PROTECT do NIST CSF")
        if not checks.get("detect"):
            recommendations.append("Implementar função DETECT do NIST CSF")
        if not checks.get("respond"):
            recommendations.append("Implementar função RESPOND do NIST CSF")
        if not checks.get("recover"):
            recommendations.append("Implementar função RECOVER do NIST CSF")
        return recommendations


class EnterpriseSecurityManager:
    """Gerenciador principal de segurança empresarial"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Componentes de segurança
        self.encryption = EncryptionManager()
        self.user_manager = UserManager(str(self.config_dir / "users.db"))
        self.access_control = AccessControlManager(str(self.config_dir / "access.db"))
        self.audit_logger = AuditLogger(str(self.config_dir / "audit"))
        self.compliance_checker = ComplianceChecker()
        
        # Configuração
        self.config = self._load_config()
        
        # Thread de monitoramento de segurança
        self.monitoring_thread = None
        self.is_monitoring = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração de segurança"""
        config_file = self.config_dir / "security_config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Configuração padrão
            default_config = {
                "encryption": {"enabled": True},
                "audit": {
                    "access_logging": True,
                    "comprehensive_trails": True
                },
                "access_control": {
                    "role_separation": True,
                    "privileged_controls": True,
                    "strong_controls": True
                },
                "monitoring": {
                    "network_monitoring": True,
                    "real_time_alerts": True
                },
                "compliance": {
                    "standards": ["gdpr", "iso27001", "nist"]
                }
            }
            
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Salva configuração de segurança"""
        config_file = self.config_dir / "security_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def initialize_security(self, admin_username: str, admin_password: str):
        """Inicializa sistema de segurança"""
        # Cria usuário administrador
        admin_user = self.user_manager.create_user(
            username=admin_username,
            email=f"{admin_username}@system.local",
            password=admin_password,
            access_level=AccessLevel.SUPERUSER
        )
        
        # Cria regras de acesso básicas
        admin_rule = AccessControlRule(
            rule_id=secrets.token_urlsafe(16),
            user_id=admin_user.user_id,
            resource_pattern="*",
            allowed_actions=["*"],
            denied_actions=[],
            conditions={}
        )
        self.access_control.add_rule(admin_rule)
        
        # Log evento de inicialização
        init_event = SecurityEvent(
            event_id=secrets.token_urlsafe(16),
            event_type="system_initialization",
            severity=SecurityLevel.HIGH,
            user_id=admin_user.user_id,
            resource="security_system",
            action="initialize",
            timestamp=datetime.now(),
            details={"admin_user_created": True}
        )
        self.audit_logger.log_event(init_event)
        
        print("✅ Security system initialized successfully")
        return admin_user
    
    def authenticate_and_authorize(self, username: str, password: str,
                                 resource: str, action: str) -> Tuple[bool, Optional[str]]:
        """Autentica usuário e autoriza ação"""
        # Autentica usuário
        user = self.user_manager.authenticate_user(username, password)
        if not user:
            # Log tentativa de login inválida
            auth_event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type="authentication_failure",
                severity=SecurityLevel.MEDIUM,
                user_id=None,
                resource="authentication_system",
                action="login",
                timestamp=datetime.now(),
                details={"username": username, "reason": "invalid_credentials"}
            )
            self.audit_logger.log_event(auth_event)
            return False, None
        
        # Verifica autorização
        if not self.access_control.check_access(user.user_id, resource, action):
            # Log tentativa de acesso negado
            authz_event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type="authorization_failure",
                severity=SecurityLevel.MEDIUM,
                user_id=user.user_id,
                resource=resource,
                action=action,
                timestamp=datetime.now(),
                details={"reason": "insufficient_privileges"}
            )
            self.audit_logger.log_event(authz_event)
            return False, user.user_id
        
        # Log acesso autorizado
        access_event = SecurityEvent(
            event_id=secrets.token_urlsafe(16),
            event_type="authorized_access",
            severity=SecurityLevel.LOW,
            user_id=user.user_id,
            resource=resource,
            action=action,
            timestamp=datetime.now()
        )
        self.audit_logger.log_event(access_event)
        
        return True, user.user_id
    
    def run_compliance_check(self, standard: ComplianceStandard) -> Dict[str, Any]:
        """Executa verificação de compliance"""
        result = self.compliance_checker.check_compliance(standard, self.config)
        
        # Log verificação de compliance
        compliance_event = SecurityEvent(
            event_id=secrets.token_urlsafe(16),
            event_type="compliance_check",
            severity=SecurityLevel.MEDIUM,
            user_id=None,
            resource="compliance_system",
            action="check",
            timestamp=datetime.now(),
            details={
                "standard": standard.value,
                "score": result.get("compliance_score", 0),
                "status": result.get("status", "unknown")
            }
        )
        self.audit_logger.log_event(compliance_event)
        
        return result
    
    def start_security_monitoring(self):
        """Inicia monitoramento de segurança em tempo real"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._security_monitor, daemon=True)
        self.monitoring_thread.start()
        
        print("🔒 Security monitoring started")
    
    def stop_security_monitoring(self):
        """Para monitoramento de segurança"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        
        print("🔒 Security monitoring stopped")
    
    def _security_monitor(self):
        """Thread de monitoramento de segurança"""
        while self.is_monitoring:
            try:
                # Verifica eventos de segurança suspeitos
                recent_events = self.audit_logger.get_events(
                    start_date=datetime.now() - timedelta(minutes=5)
                )
                
                # Detecta padrões suspeitos
                self._detect_suspicious_patterns(recent_events)
                
                time.sleep(60)  # Verifica a cada minuto
                
            except Exception as e:
                logging.error(f"Security monitoring error: {e}")
                time.sleep(60)
    
    def _detect_suspicious_patterns(self, events: List[SecurityEvent]):
        """Detecta padrões suspeitos nos eventos"""
        # Detecta múltiplas tentativas de login falhadas
        failed_logins = [e for e in events if e.event_type == "authentication_failure"]
        if len(failed_logins) >= 5:
            alert_event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type="security_alert",
                severity=SecurityLevel.HIGH,
                user_id=None,
                resource="security_monitor",
                action="pattern_detection",
                timestamp=datetime.now(),
                details={
                    "alert_type": "multiple_failed_logins",
                    "count": len(failed_logins),
                    "time_window": "5_minutes"
                },
                risk_score=0.8
            )
            self.audit_logger.log_event(alert_event)
        
        # Detecta acessos a recursos sensíveis
        sensitive_accesses = [e for e in events 
                            if e.event_type == "authorized_access" 
                            and "admin" in e.resource.lower()]
        if len(sensitive_accesses) >= 10:
            alert_event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type="security_alert",
                severity=SecurityLevel.MEDIUM,
                user_id=None,
                resource="security_monitor",
                action="pattern_detection",
                timestamp=datetime.now(),
                details={
                    "alert_type": "high_privilege_access",
                    "count": len(sensitive_accesses),
                    "time_window": "5_minutes"
                },
                risk_score=0.6
            )
            self.audit_logger.log_event(alert_event)
    
    def generate_security_report(self, output_path: str):
        """Gera relatório de segurança"""
        # Coleta dados dos últimos 30 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        events = self.audit_logger.get_events(start_date, end_date)
        
        # Agrupa eventos por tipo
        event_summary = {}
        for event in events:
            event_summary[event.event_type] = event_summary.get(event.event_type, 0) + 1
        
        # Conta eventos por severidade
        severity_summary = {}
        for event in events:
            severity_summary[event.severity.value] = severity_summary.get(event.severity.value, 0) + 1
        
        # Executa verificações de compliance
        compliance_results = {}
        for standard in [ComplianceStandard.GDPR, ComplianceStandard.ISO27001, ComplianceStandard.NIST]:
            compliance_results[standard.value] = self.run_compliance_check(standard)
        
        # Gera relatório
        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "security_events": {
                "total": len(events),
                "by_type": event_summary,
                "by_severity": severity_summary
            },
            "compliance_status": compliance_results,
            "security_metrics": {
                "average_risk_score": sum(e.risk_score for e in events) / len(events) if events else 0,
                "high_risk_events": len([e for e in events if e.risk_score > 0.7]),
                "authentication_failures": len([e for e in events if e.event_type == "authentication_failure"])
            },
            "recommendations": self._generate_security_recommendations(events, compliance_results)
        }
        
        # Salva relatório
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Security report generated: {output_path}")
        return report
    
    def _generate_security_recommendations(self, events: List[SecurityEvent], 
                                         compliance_results: Dict[str, Any]) -> List[str]:
        """Gera recomendações de segurança"""
        recommendations = []
        
        # Análise de eventos
        auth_failures = len([e for e in events if e.event_type == "authentication_failure"])
        if auth_failures > 50:
            recommendations.append("Implementar bloqueio automático após múltiplas tentativas de login")
        
        high_risk_events = len([e for e in events if e.risk_score > 0.7])
        if high_risk_events > 10:
            recommendations.append("Revisar políticas de segurança e controles de acesso")
        
        # Análise de compliance
        for standard, result in compliance_results.items():
            if result.get("compliance_score", 0) < 0.8:
                recommendations.extend(result.get("recommendations", []))
        
        return list(set(recommendations))  # Remove duplicatas


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BW Automate Enterprise Security & Compliance")
    parser.add_argument("--config-dir", "-c", default="security_config", 
                       help="Diretório de configuração de segurança")
    parser.add_argument("--init", action="store_true", 
                       help="Inicializar sistema de segurança")
    parser.add_argument("--admin-user", default="admin", 
                       help="Nome do usuário administrador")
    parser.add_argument("--admin-password", 
                       help="Senha do usuário administrador")
    parser.add_argument("--compliance-check", choices=[s.value for s in ComplianceStandard],
                       help="Executar verificação de compliance")
    parser.add_argument("--monitor", action="store_true",
                       help="Iniciar monitoramento de segurança")
    parser.add_argument("--report", help="Gerar relatório de segurança")
    
    args = parser.parse_args()
    
    # Cria gerenciador de segurança
    security_manager = EnterpriseSecurityManager(args.config_dir)
    
    if args.init:
        if not args.admin_password:
            import getpass
            args.admin_password = getpass.getpass("Admin password: ")
        
        security_manager.initialize_security(args.admin_user, args.admin_password)
    
    if args.compliance_check:
        standard = ComplianceStandard(args.compliance_check)
        result = security_manager.run_compliance_check(standard)
        print(f"\n📋 Compliance Check - {standard.value.upper()}")
        print(f"Score: {result['compliance_score']:.2%}")
        print(f"Status: {result['status']}")
        if result.get('recommendations'):
            print("\n📌 Recommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
    
    if args.report:
        security_manager.generate_security_report(args.report)
    
    if args.monitor:
        security_manager.start_security_monitoring()
        try:
            print("Security monitoring active. Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            security_manager.stop_security_monitoring()
    
    print("✅ Enterprise Security & Compliance system ready")