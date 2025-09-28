#!/usr/bin/env python3
"""
🏥 BW_AUTOMATE - Health Check and Monitoring API
Enterprise-grade health monitoring and REST API endpoints
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Core imports with error handling
try:
    from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
    from BW_UNIFIED_CLI import BWUnifiedCLI
    from ENHANCED_POSTGRESQL_AIRFLOW_MAPPER import EnhancedPostgreSQLAirflowMapper
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

# Optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

@dataclass
class HealthStatus:
    """Health status data structure"""
    service: str
    status: str  # "healthy", "warning", "critical"
    message: str
    timestamp: str
    details: Dict[str, Any]
    response_time_ms: float

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    uptime_seconds: float
    timestamp: str

class HealthChecker:
    """Health checking engine"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.start_time = time.time()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/health.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def check_core_modules(self) -> HealthStatus:
        """Check core module availability"""
        start_time = time.time()
        
        try:
            if not CORE_MODULES_AVAILABLE:
                return HealthStatus(
                    service="core_modules",
                    status="critical",
                    message="Core modules import failed",
                    timestamp=datetime.now().isoformat(),
                    details={"modules_available": False},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Test basic functionality
            cli = BWUnifiedCLI()
            analyzers = cli.available_analyzers
            
            available_count = sum(1 for available in analyzers.values() if available)
            total_count = len(analyzers)
            
            if available_count == total_count:
                status = "healthy"
                message = f"All {total_count} analyzers available"
            elif available_count > 0:
                status = "warning"
                message = f"{available_count}/{total_count} analyzers available"
            else:
                status = "critical"
                message = "No analyzers available"
            
            return HealthStatus(
                service="core_modules",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                details={
                    "available_analyzers": analyzers,
                    "analyzer_count": f"{available_count}/{total_count}"
                },
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"Core modules health check failed: {e}")
            return HealthStatus(
                service="core_modules",
                status="critical",
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                details={"error": str(e), "traceback": traceback.format_exc()},
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_postgresql_analyzer(self) -> HealthStatus:
        """Check PostgreSQL analyzer functionality"""
        start_time = time.time()
        
        try:
            mapper = PostgreSQLTableMapper()
            
            # Create small test project
            test_code = '''
import psycopg2
def test_function():
    conn = psycopg2.connect("postgresql://test")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
    return cursor.fetchall()
'''
            
            test_file = Path("health_test.py")
            test_file.write_text(test_code)
            
            try:
                result = mapper.analyze_project(".")
                tables_found = len(result.get("tables_discovered", {}))
                
                # Cleanup
                test_file.unlink()
                
                if tables_found > 0:
                    status = "healthy"
                    message = f"PostgreSQL analyzer working - found {tables_found} tables"
                else:
                    status = "warning"
                    message = "PostgreSQL analyzer running but found no tables"
                
                return HealthStatus(
                    service="postgresql_analyzer",
                    status=status,
                    message=message,
                    timestamp=datetime.now().isoformat(),
                    details={
                        "tables_found": tables_found,
                        "analysis_summary": result.get("analysis_summary", {})
                    },
                    response_time_ms=(time.time() - start_time) * 1000
                )
                
            except Exception as cleanup_error:
                if test_file.exists():
                    test_file.unlink()
                raise cleanup_error
                
        except Exception as e:
            self.logger.error(f"PostgreSQL analyzer health check failed: {e}")
            return HealthStatus(
                service="postgresql_analyzer",
                status="critical",
                message=f"Analyzer failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)},
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_system_resources(self) -> HealthStatus:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            if not PSUTIL_AVAILABLE:
                return HealthStatus(
                    service="system_resources",
                    status="warning",
                    message="psutil not available - limited monitoring",
                    timestamp=datetime.now().isoformat(),
                    details={"psutil_available": False},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "critical"
                message = "High resource usage detected"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = "warning"
                message = "Moderate resource usage"
            else:
                status = "healthy"
                message = "Resource usage normal"
            
            return HealthStatus(
                service="system_resources",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                },
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"System resources health check failed: {e}")
            return HealthStatus(
                service="system_resources",
                status="critical",
                message=f"Resource check failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)},
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_file_system(self) -> HealthStatus:
        """Check file system access and permissions"""
        start_time = time.time()
        
        try:
            # Check critical directories
            critical_dirs = [".", "logs"]
            issues = []
            
            for dir_path in critical_dirs:
                path = Path(dir_path)
                if not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create {dir_path}: {e}")
                        continue
                
                # Test write permissions
                test_file = path / "health_test_write.tmp"
                try:
                    test_file.write_text("health check")
                    test_file.unlink()
                except Exception as e:
                    issues.append(f"Cannot write to {dir_path}: {e}")
            
            if issues:
                status = "critical"
                message = f"File system issues: {'; '.join(issues)}"
            else:
                status = "healthy"
                message = "File system access normal"
            
            return HealthStatus(
                service="file_system",
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                details={
                    "directories_checked": critical_dirs,
                    "issues": issues,
                    "current_directory": str(Path.cwd())
                },
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            self.logger.error(f"File system health check failed: {e}")
            return HealthStatus(
                service="file_system",
                status="critical",
                message=f"File system check failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)},
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        if not PSUTIL_AVAILABLE:
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                uptime_seconds=time.time() - self.start_time,
                timestamp=datetime.now().isoformat()
            )
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024**2),
                memory_available_mb=memory.available / (1024**2),
                disk_usage_percent=disk.percent,
                uptime_seconds=time.time() - self.start_time,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                uptime_seconds=time.time() - self.start_time,
                timestamp=datetime.now().isoformat()
            )
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        
        checks = [
            self.check_core_modules(),
            self.check_postgresql_analyzer(),
            self.check_system_resources(),
            self.check_file_system()
        ]
        
        # Determine overall status
        statuses = [check.status for check in checks]
        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(checks),
            "healthy_checks": len([s for s in statuses if s == "healthy"]),
            "warning_checks": len([s for s in statuses if s == "warning"]),
            "critical_checks": len([s for s in statuses if s == "critical"]),
            "total_response_time_ms": (time.time() - start_time) * 1000,
            "checks": [asdict(check) for check in checks],
            "system_metrics": asdict(self.get_system_metrics())
        }

class HealthAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health API"""
    
    def __init__(self, *args, health_checker=None, **kwargs):
        self.health_checker = health_checker or HealthChecker()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/health':
                self._handle_health_check()
            elif path == '/health/live':
                self._handle_liveness_check()
            elif path == '/health/ready':
                self._handle_readiness_check()
            elif path == '/metrics':
                self._handle_metrics()
            elif path == '/info':
                self._handle_info()
            else:
                self._send_404()
                
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def _handle_health_check(self):
        """Handle comprehensive health check"""
        try:
            health_data = self.health_checker.run_comprehensive_health_check()
            self._send_json_response(health_data, 
                                   200 if health_data["overall_status"] == "healthy" else 503)
        except Exception as e:
            self._send_error(500, f"Health check failed: {str(e)}")
    
    def _handle_liveness_check(self):
        """Handle liveness probe (basic service availability)"""
        try:
            response = {
                "status": "alive",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.health_checker.start_time
            }
            self._send_json_response(response, 200)
        except Exception as e:
            self._send_error(500, f"Liveness check failed: {str(e)}")
    
    def _handle_readiness_check(self):
        """Handle readiness probe (service ready to accept traffic)"""
        try:
            core_check = self.health_checker.check_core_modules()
            
            if core_check.status == "healthy":
                response = {
                    "status": "ready",
                    "timestamp": datetime.now().isoformat(),
                    "core_modules": "available"
                }
                self._send_json_response(response, 200)
            else:
                response = {
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "reason": core_check.message
                }
                self._send_json_response(response, 503)
                
        except Exception as e:
            self._send_error(500, f"Readiness check failed: {str(e)}")
    
    def _handle_metrics(self):
        """Handle metrics endpoint"""
        try:
            metrics = self.health_checker.get_system_metrics()
            self._send_json_response(asdict(metrics), 200)
        except Exception as e:
            self._send_error(500, f"Metrics collection failed: {str(e)}")
    
    def _handle_info(self):
        """Handle system info endpoint"""
        try:
            info = {
                "service": "BW_AUTOMATE",
                "version": "3.0.0",
                "python_version": sys.version,
                "platform": sys.platform,
                "start_time": datetime.fromtimestamp(self.health_checker.start_time).isoformat(),
                "uptime_seconds": time.time() - self.health_checker.start_time,
                "core_modules_available": CORE_MODULES_AVAILABLE,
                "optional_dependencies": {
                    "psutil": PSUTIL_AVAILABLE,
                    "requests": REQUESTS_AVAILABLE
                }
            }
            self._send_json_response(info, 200)
        except Exception as e:
            self._send_error(500, f"Info retrieval failed: {str(e)}")
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        error_data = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(error_data, status_code)
    
    def _send_404(self):
        """Send 404 not found"""
        endpoints = ["/health", "/health/live", "/health/ready", "/metrics", "/info"]
        error_data = {
            "error": "Endpoint not found",
            "available_endpoints": endpoints,
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(error_data, 404)
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        pass  # Suppress default HTTP logs

class HealthAPIServer:
    """Health API server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.health_checker = HealthChecker()
        self.server = None
        
    def create_handler(self):
        """Create request handler with health checker"""
        def handler(*args, **kwargs):
            return HealthAPIHandler(*args, health_checker=self.health_checker, **kwargs)
        return handler
    
    def start(self):
        """Start the health API server"""
        try:
            handler = self.create_handler()
            self.server = HTTPServer((self.host, self.port), handler)
            
            print(f"🏥 BW_AUTOMATE Health API starting on http://{self.host}:{self.port}")
            print(f"📊 Health endpoints:")
            print(f"   • GET /health - Comprehensive health check")
            print(f"   • GET /health/live - Liveness probe")
            print(f"   • GET /health/ready - Readiness probe")
            print(f"   • GET /metrics - System metrics")
            print(f"   • GET /info - Service information")
            print()
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down health API server...")
            self.stop()
        except Exception as e:
            print(f"❌ Failed to start health API server: {e}")
            raise
    
    def stop(self):
        """Stop the server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("✅ Health API server stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE Health API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--check-only", action="store_true", help="Run health check and exit")
    
    args = parser.parse_args()
    
    if args.check_only:
        # Run health check and exit
        checker = HealthChecker()
        result = checker.run_comprehensive_health_check()
        
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result["overall_status"] == "healthy" else 1)
    else:
        # Start server
        server = HealthAPIServer(args.host, args.port)
        server.start()

if __name__ == "__main__":
    main()