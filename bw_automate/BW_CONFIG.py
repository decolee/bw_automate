#!/usr/bin/env python3
"""
⚙️ BW_AUTOMATE - Configuration Management System
Enterprise-grade configuration with environment support and validation
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

# Optional dependencies with fallbacks
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if present
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "bw_automate"
    username: str = "bw_user"
    password: str = ""
    ssl_mode: str = "prefer"
    connection_timeout: int = 30
    pool_size: int = 5
    max_connections: int = 20

@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    max_file_size_mb: int = 100
    max_files_per_analysis: int = 10000
    confidence_threshold: float = 0.8
    enable_cross_file_analysis: bool = True
    enable_airflow_detection: bool = True
    enable_ml_patterns: bool = True
    timeout_seconds: int = 300
    parallel_processing: bool = True
    max_workers: int = 4

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_authentication: bool = False
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 100
    enable_audit_logging: bool = True
    enable_input_validation: bool = True
    max_request_size_mb: int = 50
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.py', '.sql', '.yaml', '.yml', '.json'])
    blocked_paths: List[str] = field(default_factory=lambda: ['/etc', '/root', '/var/log'])

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/bw_automate.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    enable_json_format: bool = False

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    enable_metrics: bool = True
    metrics_port: int = 8080
    enable_alerts: bool = False
    alert_email: str = ""
    alert_webhook_url: str = ""

@dataclass
class CacheConfig:
    """Cache configuration"""
    enable_cache: bool = True
    cache_type: str = "memory"  # memory, redis, file
    cache_ttl_seconds: int = 3600
    max_cache_size_mb: int = 100
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

@dataclass
class BWConfig:
    """Main BW_AUTOMATE configuration"""
    environment: str = "development"
    debug: bool = False
    version: str = "3.0.0"
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # Runtime settings
    startup_time: str = field(default_factory=lambda: datetime.now().isoformat())
    config_loaded_from: str = "default"

class ConfigManager:
    """Configuration management system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = self._setup_logging()
        self.config: BWConfig = BWConfig()
        self.config_path = config_path or self._find_config_file()
        
        # Load configuration
        self._load_configuration()
        
        # Setup logging with loaded config
        self._setup_logging_from_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup basic logging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_locations = [
            "bw_config.yaml",
            "bw_config.yml", 
            "bw_config.json",
            "config/bw_config.yaml",
            "config/bw_config.yml",
            "config/bw_config.json",
            "/etc/bw_automate/config.yaml",
            "/etc/bw_automate/config.yml"
        ]
        
        for location in possible_locations:
            if Path(location).exists():
                self.logger.info(f"Found config file: {location}")
                return location
        
        self.logger.info("No config file found, using defaults")
        return None
    
    def _load_configuration(self):
        """Load configuration from various sources"""
        # 1. Start with defaults (already loaded)
        
        # 2. Load from file if available
        if self.config_path:
            self._load_from_file(self.config_path)
        
        # 3. Override with environment variables
        self._load_from_environment()
        
        # 4. Validate configuration
        self._validate_configuration()
    
    def _load_from_file(self, file_path: str):
        """Load configuration from file"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"Config file not found: {file_path}")
                return
            
            content = path.read_text()
            
            if file_path.endswith(('.yaml', '.yml')):
                data = yaml.safe_load(content)
            elif file_path.endswith('.json'):
                data = json.loads(content)
            else:
                self.logger.error(f"Unsupported config file format: {file_path}")
                return
            
            # Merge configuration
            self._merge_config_data(data)
            self.config.config_loaded_from = file_path
            
            self.logger.info(f"Configuration loaded from: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {file_path}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database
            "BW_DB_HOST": ("database", "host"),
            "BW_DB_PORT": ("database", "port", int),
            "BW_DB_NAME": ("database", "database"),
            "BW_DB_USER": ("database", "username"),
            "BW_DB_PASSWORD": ("database", "password"),
            "BW_DB_SSL_MODE": ("database", "ssl_mode"),
            
            # Analysis
            "BW_MAX_FILE_SIZE_MB": ("analysis", "max_file_size_mb", int),
            "BW_MAX_FILES": ("analysis", "max_files_per_analysis", int),
            "BW_CONFIDENCE_THRESHOLD": ("analysis", "confidence_threshold", float),
            "BW_ANALYSIS_TIMEOUT": ("analysis", "timeout_seconds", int),
            "BW_MAX_WORKERS": ("analysis", "max_workers", int),
            
            # Security
            "BW_ENABLE_AUTH": ("security", "enable_authentication", bool),
            "BW_ENABLE_RATE_LIMIT": ("security", "enable_rate_limiting", bool),
            "BW_RATE_LIMIT": ("security", "rate_limit_requests_per_minute", int),
            "BW_MAX_REQUEST_SIZE_MB": ("security", "max_request_size_mb", int),
            
            # Logging
            "BW_LOG_LEVEL": ("logging", "level"),
            "BW_LOG_FILE": ("logging", "file_path"),
            "BW_LOG_MAX_SIZE_MB": ("logging", "max_file_size_mb", int),
            
            # Monitoring
            "BW_ENABLE_HEALTH_CHECKS": ("monitoring", "enable_health_checks", bool),
            "BW_HEALTH_CHECK_INTERVAL": ("monitoring", "health_check_interval_seconds", int),
            "BW_METRICS_PORT": ("monitoring", "metrics_port", int),
            "BW_ALERT_EMAIL": ("monitoring", "alert_email"),
            
            # Cache
            "BW_ENABLE_CACHE": ("cache", "enable_cache", bool),
            "BW_CACHE_TYPE": ("cache", "cache_type"),
            "BW_CACHE_TTL": ("cache", "cache_ttl_seconds", int),
            "BW_REDIS_HOST": ("cache", "redis_host"),
            "BW_REDIS_PORT": ("cache", "redis_port", int),
            
            # General
            "BW_ENVIRONMENT": ("environment",),
            "BW_DEBUG": ("debug", None, bool),
        }
        
        env_loaded = []
        
        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert type if specified
                    if len(mapping) > 2:
                        converter = mapping[2]
                        if converter == bool:
                            value = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            value = converter(value)
                    
                    # Set value in config
                    if len(mapping) == 1:
                        # Root level setting
                        setattr(self.config, mapping[0], value)
                    else:
                        # Nested setting
                        section = getattr(self.config, mapping[0])
                        setattr(section, mapping[1], value)
                    
                    env_loaded.append(env_var)
                    
                except Exception as e:
                    self.logger.error(f"Failed to load {env_var}={value}: {e}")
        
        if env_loaded:
            self.logger.info(f"Loaded {len(env_loaded)} settings from environment variables")
    
    def _merge_config_data(self, data: Dict[str, Any]):
        """Merge configuration data into existing config"""
        def merge_dict(target, source):
            for key, value in source.items():
                if hasattr(target, key):
                    current_value = getattr(target, key)
                    if hasattr(current_value, '__dict__') and isinstance(value, dict):
                        # Nested object - recurse
                        merge_dict(current_value, value)
                    else:
                        # Simple value - set directly
                        setattr(target, key, value)
                else:
                    self.logger.warning(f"Unknown config key: {key}")
        
        merge_dict(self.config, data)
    
    def _validate_configuration(self):
        """Validate configuration values"""
        errors = []
        
        # Validate database config
        if self.config.database.port < 1 or self.config.database.port > 65535:
            errors.append("Database port must be between 1-65535")
        
        # Validate analysis config
        if self.config.analysis.confidence_threshold < 0 or self.config.analysis.confidence_threshold > 1:
            errors.append("Confidence threshold must be between 0-1")
        
        if self.config.analysis.max_workers < 1:
            errors.append("Max workers must be at least 1")
        
        # Validate security config
        if self.config.security.rate_limit_requests_per_minute < 1:
            errors.append("Rate limit must be at least 1 request per minute")
        
        # Validate monitoring config
        if self.config.monitoring.metrics_port < 1 or self.config.monitoring.metrics_port > 65535:
            errors.append("Metrics port must be between 1-65535")
        
        # Log validation results
        if errors:
            for error in errors:
                self.logger.error(f"Configuration validation error: {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        else:
            self.logger.info("Configuration validation passed")
    
    def _setup_logging_from_config(self):
        """Setup logging based on loaded configuration"""
        try:
            # Create logs directory if needed
            log_path = Path(self.config.logging.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            handlers = []
            
            if self.config.logging.enable_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(self.config.logging.format))
                handlers.append(console_handler)
            
            if self.config.logging.enable_file:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.config.logging.file_path,
                    maxBytes=self.config.logging.max_file_size_mb * 1024 * 1024,
                    backupCount=self.config.logging.backup_count
                )
                file_handler.setFormatter(logging.Formatter(self.config.logging.format))
                handlers.append(file_handler)
            
            # Configure root logger
            logging.basicConfig(
                level=getattr(logging, self.config.logging.level.upper()),
                handlers=handlers,
                force=True
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("Logging configured successfully")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        db = self.config.database
        return f"postgresql://{db.username}:{db.password}@{db.host}:{db.port}/{db.database}?sslmode={db.ssl_mode}"
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return asdict(self.config)
    
    def save_config(self, file_path: str, format: str = "yaml"):
        """Save current configuration to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.get_config_dict()
            
            if format.lower() in ("yaml", "yml"):
                with open(path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
            elif format.lower() == "json":
                with open(path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Configuration saved to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration from all sources"""
        self.logger.info("Reloading configuration...")
        self.config = BWConfig()  # Reset to defaults
        self._load_configuration()
        self._setup_logging_from_config()
        self.logger.info("Configuration reloaded successfully")

# Global configuration instance
_config_manager: Optional[ConfigManager] = None

def get_config() -> BWConfig:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def reload_config():
    """Reload global configuration"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_config()

def main():
    """Main entry point for config management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE Configuration Manager")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--save", help="Save configuration to file")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize config manager
    config_manager = ConfigManager(args.config)
    
    if args.show:
        print("Current Configuration:")
        print("=" * 50)
        if args.format == "json":
            print(json.dumps(config_manager.get_config_dict(), indent=2))
        else:
            print(yaml.dump(config_manager.get_config_dict(), default_flow_style=False, indent=2))
    
    if args.validate:
        try:
            config_manager._validate_configuration()
            print("✅ Configuration validation passed")
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return 1
    
    if args.save:
        try:
            config_manager.save_config(args.save, args.format)
            print(f"✅ Configuration saved to: {args.save}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())