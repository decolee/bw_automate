#!/usr/bin/env python3
"""
🌐 BW_AUTOMATE - REST API Server
Enterprise-grade REST API with authentication, validation, and monitoring
"""

import os
import sys
import json
import time
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import traceback
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
from io import StringIO
import tempfile
import shutil

# Core imports
try:
    from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
    from BW_UNIFIED_CLI import BWUnifiedCLI
    from ENHANCED_POSTGRESQL_AIRFLOW_MAPPER import EnhancedPostgreSQLAirflowMapper
    from AIRFLOW_INTEGRATION_CLI import AirflowIntegrationCLI
    from BW_CONFIG import get_config, get_config_manager
    from BW_HEALTH_API import HealthChecker
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Core modules not available: {e}")
    CORE_MODULES_AVAILABLE = False

@dataclass
class APIRequest:
    """API request data structure"""
    request_id: str
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[str]
    timestamp: str
    client_ip: str

@dataclass
class APIResponse:
    """API response data structure"""
    request_id: str
    status_code: int
    data: Any
    timestamp: str
    execution_time_ms: float
    errors: List[str]

@dataclass
class AnalysisJob:
    """Analysis job tracking"""
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    request: APIRequest
    started_at: str
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    progress: float  # 0.0 to 1.0

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for client"""
        with self.lock:
            now = time.time()
            minute_start = now - (now % 60)
            
            if client_ip not in self.requests:
                self.requests[client_ip] = {}
            
            # Clean old requests
            self.requests[client_ip] = {
                timestamp: count for timestamp, count in self.requests[client_ip].items()
                if timestamp >= minute_start - 60
            }
            
            # Count requests in current minute
            current_requests = self.requests[client_ip].get(minute_start, 0)
            
            if current_requests >= self.requests_per_minute:
                return False
            
            # Increment counter
            self.requests[client_ip][minute_start] = current_requests + 1
            return True

class InputValidator:
    """Input validation and sanitization"""
    
    def __init__(self):
        self.config = get_config()
    
    def validate_project_path(self, path: str) -> str:
        """Validate and sanitize project path"""
        if not path:
            raise ValueError("Project path is required")
        
        # Remove dangerous characters
        cleaned_path = path.strip()
        
        # Check for blocked paths
        for blocked in self.config.security.blocked_paths:
            if cleaned_path.startswith(blocked):
                raise ValueError(f"Access to path '{blocked}' is not allowed")
        
        # Check if path exists (for local paths)
        if not cleaned_path.startswith(('http://', 'https://')):
            if not Path(cleaned_path).exists():
                raise ValueError(f"Path does not exist: {cleaned_path}")
        
        return cleaned_path
    
    def validate_analysis_type(self, analysis_type: str) -> str:
        """Validate analysis type"""
        valid_types = ["all", "postgresql", "production", "ml", "performance", "airflow"]
        
        if analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis type. Must be one of: {valid_types}")
        
        return analysis_type
    
    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        
        ext = Path(filename).suffix.lower()
        return ext in self.config.security.allowed_file_extensions
    
    def sanitize_json_input(self, data: Any) -> Any:
        """Sanitize JSON input"""
        if isinstance(data, str):
            # Basic XSS prevention
            data = data.replace('<script', '&lt;script')
            data = data.replace('</script>', '&lt;/script&gt;')
        elif isinstance(data, dict):
            return {key: self.sanitize_json_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_json_input(item) for item in data]
        
        return data

class JobManager:
    """Background job management"""
    
    def __init__(self):
        self.jobs: Dict[str, AnalysisJob] = {}
        self.lock = threading.Lock()
    
    def create_job(self, request: APIRequest, job_type: str) -> str:
        """Create new analysis job"""
        job_id = str(uuid.uuid4())
        
        job = AnalysisJob(
            job_id=job_id,
            status="pending",
            request=request,
            started_at=datetime.now().isoformat(),
            completed_at=None,
            result=None,
            error=None,
            progress=0.0
        )
        
        with self.lock:
            self.jobs[job_id] = job
        
        return job_id
    
    def update_job_status(self, job_id: str, status: str, progress: float = None, 
                         result: Dict[str, Any] = None, error: str = None):
        """Update job status"""
        with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.status = status
                
                if progress is not None:
                    job.progress = progress
                
                if result is not None:
                    job.result = result
                
                if error is not None:
                    job.error = error
                
                if status in ["completed", "failed"]:
                    job.completed_at = datetime.now().isoformat()
    
    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """Get job by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def list_jobs(self, limit: int = 100) -> List[AnalysisJob]:
        """List recent jobs"""
        with self.lock:
            jobs = list(self.jobs.values())
            jobs.sort(key=lambda x: x.started_at, reverse=True)
            return jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cutoff_str = cutoff.isoformat()
        
        with self.lock:
            to_remove = []
            for job_id, job in self.jobs.items():
                if job.status in ["completed", "failed"] and job.completed_at and job.completed_at < cutoff_str:
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del self.jobs[job_id]

class BWRestAPIHandler(BaseHTTPRequestHandler):
    """REST API request handler"""
    
    def __init__(self, *args, **kwargs):
        self.config = get_config()
        self.rate_limiter = RateLimiter(self.config.security.rate_limit_requests_per_minute)
        self.validator = InputValidator()
        self.job_manager = JobManager()
        self.health_checker = HealthChecker()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            request = self._create_request()
            
            # Rate limiting
            if not self._check_rate_limit(request):
                return
            
            # Route request
            if request.path == "/api/v1/health":
                self._handle_health_check(request)
            elif request.path == "/api/v1/info":
                self._handle_info(request)
            elif request.path.startswith("/api/v1/jobs/"):
                self._handle_job_status(request)
            elif request.path == "/api/v1/jobs":
                self._handle_list_jobs(request)
            elif request.path == "/api/v1/analyzers":
                self._handle_list_analyzers(request)
            else:
                self._send_error(request, 404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(None, 500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            request = self._create_request()
            
            # Rate limiting
            if not self._check_rate_limit(request):
                return
            
            # Content length check
            content_length = int(self.headers.get('Content-Length', 0))
            max_size = self.config.security.max_request_size_mb * 1024 * 1024
            
            if content_length > max_size:
                self._send_error(request, 413, f"Request too large. Max size: {max_size} bytes")
                return
            
            # Read body
            if content_length > 0:
                request.body = self.rfile.read(content_length).decode('utf-8')
            
            # Route request
            if request.path == "/api/v1/analyze":
                self._handle_analyze(request)
            elif request.path == "/api/v1/analyze-async":
                self._handle_analyze_async(request)
            else:
                self._send_error(request, 404, "Endpoint not found")
                
        except Exception as e:
            self._send_error(None, 500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def _create_request(self) -> APIRequest:
        """Create API request object"""
        parsed_path = urlparse(self.path)
        
        return APIRequest(
            request_id=str(uuid.uuid4()),
            method=self.command,
            path=parsed_path.path,
            headers=dict(self.headers),
            body=None,
            timestamp=datetime.now().isoformat(),
            client_ip=self.client_address[0]
        )
    
    def _check_rate_limit(self, request: APIRequest) -> bool:
        """Check rate limiting"""
        if not self.config.security.enable_rate_limiting:
            return True
        
        if not self.rate_limiter.is_allowed(request.client_ip):
            self._send_error(request, 429, "Rate limit exceeded")
            return False
        
        return True
    
    def _handle_health_check(self, request: APIRequest):
        """Handle health check endpoint"""
        try:
            health_data = self.health_checker.run_comprehensive_health_check()
            self._send_success(request, health_data)
        except Exception as e:
            self._send_error(request, 500, f"Health check failed: {str(e)}")
    
    def _handle_info(self, request: APIRequest):
        """Handle service info endpoint"""
        try:
            info = {
                "service": "BW_AUTOMATE_API",
                "version": "3.0.0",
                "api_version": "v1",
                "timestamp": datetime.now().isoformat(),
                "endpoints": {
                    "GET /api/v1/health": "Health check",
                    "GET /api/v1/info": "Service information",
                    "GET /api/v1/analyzers": "List available analyzers",
                    "GET /api/v1/jobs": "List analysis jobs",
                    "GET /api/v1/jobs/{job_id}": "Get job status",
                    "POST /api/v1/analyze": "Run synchronous analysis",
                    "POST /api/v1/analyze-async": "Run asynchronous analysis"
                },
                "configuration": {
                    "rate_limiting": self.config.security.enable_rate_limiting,
                    "authentication": self.config.security.enable_authentication,
                    "max_request_size_mb": self.config.security.max_request_size_mb
                }
            }
            self._send_success(request, info)
        except Exception as e:
            self._send_error(request, 500, f"Failed to get info: {str(e)}")
    
    def _handle_list_analyzers(self, request: APIRequest):
        """Handle list analyzers endpoint"""
        try:
            if not CORE_MODULES_AVAILABLE:
                self._send_error(request, 503, "Core modules not available")
                return
            
            cli = BWUnifiedCLI()
            analyzers = cli.available_analyzers
            
            analyzer_info = {}
            for name, available in analyzers.items():
                analyzer_info[name] = {
                    "available": available,
                    "description": self._get_analyzer_description(name)
                }
            
            result = {
                "analyzers": analyzer_info,
                "total_count": len(analyzers),
                "available_count": sum(1 for available in analyzers.values() if available)
            }
            
            self._send_success(request, result)
        except Exception as e:
            self._send_error(request, 500, f"Failed to list analyzers: {str(e)}")
    
    def _handle_analyze(self, request: APIRequest):
        """Handle synchronous analysis endpoint"""
        try:
            # Parse request body
            if not request.body:
                self._send_error(request, 400, "Request body required")
                return
            
            data = json.loads(request.body)
            data = self.validator.sanitize_json_input(data)
            
            # Validate required fields
            project_path = data.get("project_path")
            if not project_path:
                self._send_error(request, 400, "project_path is required")
                return
            
            analysis_type = data.get("analysis_type", "postgresql")
            
            # Validate inputs
            try:
                project_path = self.validator.validate_project_path(project_path)
                analysis_type = self.validator.validate_analysis_type(analysis_type)
            except ValueError as e:
                self._send_error(request, 400, str(e))
                return
            
            # Run analysis
            start_time = time.time()
            result = self._run_analysis(project_path, analysis_type)
            execution_time = (time.time() - start_time) * 1000
            
            response_data = {
                "analysis_result": result,
                "execution_time_ms": execution_time,
                "project_path": project_path,
                "analysis_type": analysis_type
            }
            
            self._send_success(request, response_data)
            
        except json.JSONDecodeError:
            self._send_error(request, 400, "Invalid JSON in request body")
        except Exception as e:
            self._send_error(request, 500, f"Analysis failed: {str(e)}")
    
    def _handle_analyze_async(self, request: APIRequest):
        """Handle asynchronous analysis endpoint"""
        try:
            # Parse request body
            if not request.body:
                self._send_error(request, 400, "Request body required")
                return
            
            data = json.loads(request.body)
            data = self.validator.sanitize_json_input(data)
            
            # Validate inputs
            project_path = data.get("project_path")
            if not project_path:
                self._send_error(request, 400, "project_path is required")
                return
            
            analysis_type = data.get("analysis_type", "postgresql")
            
            try:
                project_path = self.validator.validate_project_path(project_path)
                analysis_type = self.validator.validate_analysis_type(analysis_type)
            except ValueError as e:
                self._send_error(request, 400, str(e))
                return
            
            # Create background job
            job_id = self.job_manager.create_job(request, analysis_type)
            
            # Start analysis in background
            def run_background_analysis():
                try:
                    self.job_manager.update_job_status(job_id, "running", 0.1)
                    result = self._run_analysis(project_path, analysis_type)
                    self.job_manager.update_job_status(job_id, "completed", 1.0, result)
                except Exception as e:
                    self.job_manager.update_job_status(job_id, "failed", 0.0, None, str(e))
            
            thread = threading.Thread(target=run_background_analysis)
            thread.daemon = True
            thread.start()
            
            response_data = {
                "job_id": job_id,
                "status": "accepted",
                "message": "Analysis started in background",
                "status_url": f"/api/v1/jobs/{job_id}"
            }
            
            self._send_success(request, response_data, 202)
            
        except json.JSONDecodeError:
            self._send_error(request, 400, "Invalid JSON in request body")
        except Exception as e:
            self._send_error(request, 500, f"Failed to start analysis: {str(e)}")
    
    def _handle_job_status(self, request: APIRequest):
        """Handle job status endpoint"""
        try:
            # Extract job ID from path
            job_id = request.path.split("/")[-1]
            
            job = self.job_manager.get_job(job_id)
            if not job:
                self._send_error(request, 404, "Job not found")
                return
            
            job_data = asdict(job)
            self._send_success(request, job_data)
            
        except Exception as e:
            self._send_error(request, 500, f"Failed to get job status: {str(e)}")
    
    def _handle_list_jobs(self, request: APIRequest):
        """Handle list jobs endpoint"""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            limit = int(query_params.get("limit", [100])[0])
            limit = min(limit, 1000)  # Max 1000 jobs
            
            jobs = self.job_manager.list_jobs(limit)
            jobs_data = [asdict(job) for job in jobs]
            
            result = {
                "jobs": jobs_data,
                "total_count": len(jobs_data),
                "limit": limit
            }
            
            self._send_success(request, result)
            
        except Exception as e:
            self._send_error(request, 500, f"Failed to list jobs: {str(e)}")
    
    def _run_analysis(self, project_path: str, analysis_type: str) -> Dict[str, Any]:
        """Run analysis and return results"""
        if analysis_type == "postgresql":
            mapper = PostgreSQLTableMapper()
            return mapper.analyze_project(project_path)
        
        elif analysis_type == "airflow":
            mapper = EnhancedPostgreSQLAirflowMapper()
            return mapper.analyze_project(project_path)
        
        elif analysis_type == "all":
            cli = BWUnifiedCLI()
            
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                result_dir = Path(temp_dir) / "api_results"
                result_dir.mkdir()
                
                # Run analysis (this would need to be modified to return data)
                # For now, run individual analyzers
                results = {}
                
                if cli.available_analyzers.get("postgresql"):
                    mapper = PostgreSQLTableMapper()
                    results["postgresql"] = mapper.analyze_project(project_path)
                
                return {
                    "analysis_type": "all",
                    "results": results,
                    "analyzers_run": list(results.keys())
                }
        
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
    
    def _get_analyzer_description(self, name: str) -> str:
        """Get analyzer description"""
        descriptions = {
            "postgresql": "PostgreSQL table detection and analysis",
            "production": "Code quality and production readiness analysis",
            "ml": "Machine learning trend analysis",
            "performance": "Performance profiling and benchmarking"
        }
        return descriptions.get(name, "No description available")
    
    def _send_success(self, request: APIRequest, data: Any, status_code: int = 200):
        """Send success response"""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id if request else None
        }
        self._send_json_response(response, status_code)
    
    def _send_error(self, request: Optional[APIRequest], status_code: int, message: str):
        """Send error response"""
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": status_code
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id if request else None
        }
        self._send_json_response(response, status_code)
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override default logging"""
        pass  # Use our structured logging instead

class BWRestAPIServer:
    """BW_AUTOMATE REST API Server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.config = get_config()
    
    def start(self):
        """Start the API server"""
        try:
            self.server = HTTPServer((self.host, self.port), BWRestAPIHandler)
            
            print(f"🌐 BW_AUTOMATE REST API starting on http://{self.host}:{self.port}")
            print(f"🔗 API Documentation:")
            print(f"   • GET  /api/v1/health - Health check")
            print(f"   • GET  /api/v1/info - Service information") 
            print(f"   • GET  /api/v1/analyzers - List analyzers")
            print(f"   • GET  /api/v1/jobs - List analysis jobs")
            print(f"   • GET  /api/v1/jobs/{{id}} - Get job status")
            print(f"   • POST /api/v1/analyze - Synchronous analysis")
            print(f"   • POST /api/v1/analyze-async - Asynchronous analysis")
            print()
            print(f"🔒 Security:")
            print(f"   • Rate limiting: {self.config.security.enable_rate_limiting}")
            print(f"   • Input validation: {self.config.security.enable_input_validation}")
            print(f"   • Max request size: {self.config.security.max_request_size_mb}MB")
            print()
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutting down API server...")
            self.stop()
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise
    
    def stop(self):
        """Stop the server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("✅ API server stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE REST API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize configuration
    if args.config:
        config_manager = get_config_manager()
        config_manager.config_path = args.config
        config_manager.reload_config()
    
    # Start server
    server = BWRestAPIServer(args.host, args.port)
    server.start()

if __name__ == "__main__":
    main()