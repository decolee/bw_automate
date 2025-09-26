#!/usr/bin/env python3
"""
BW_AUTOMATE Backend Server
Modern Flask backend with Apple-inspired API design
Integrates all Python analyzers with clean REST endpoints
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import traceback

# Import our analyzers
try:
    from INTEGRATED_PYTHON_ANALYZER import IntegratedPythonAnalyzer, AnalysisScope
    from COMPLETE_PYTHON_CODE_ANALYZER import CompletePythonAnalyzer
    from ADVANCED_PYTHON_FEATURES_ANALYZER import AdvancedPythonFeaturesAnalyzer
except ImportError as e:
    print(f"Warning: Could not import analyzers: {e}")
    print("Some features may not be available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    static_folder='frontend/build',
    static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)

# Enable CORS for development
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Global analyzer instance
analyzer = None
current_analysis = None
analysis_progress = {}

# Initialize analyzer
def init_analyzer():
    """Initialize the integrated analyzer"""
    global analyzer
    try:
        analyzer = IntegratedPythonAnalyzer({
            'log_level': logging.INFO,
            'enable_parallel_processing': True,
            'enable_dynamic_analysis': False,  # Safe mode
            'safe_dynamic_analysis': True
        })
        logger.info("Integrated Python Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        analyzer = None

# Background analysis task
class AnalysisTask:
    def __init__(self, task_id: str, project_path: str, selected_files: List[str], options: Dict[str, Any]):
        self.task_id = task_id
        self.project_path = project_path
        self.selected_files = selected_files
        self.options = options
        self.progress = 0
        self.status = 'pending'  # pending, running, completed, error
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def run(self):
        """Execute the analysis task"""
        global analysis_progress
        
        try:
            self.status = 'running'
            self.start_time = datetime.now()
            analysis_progress[self.task_id] = self
            
            logger.info(f"Starting analysis task {self.task_id} for {self.project_path}")
            
            if not analyzer:
                raise Exception("Analyzer not initialized")
            
            # Determine analysis scope
            scope_map = {
                'basic': AnalysisScope.BASIC,
                'advanced': AnalysisScope.ADVANCED,
                'sql': AnalysisScope.SQL_DATABASE,
                'complete': AnalysisScope.COMPLETE,
                'enterprise': AnalysisScope.ENTERPRISE
            }
            scope = scope_map.get(self.options.get('scope', 'complete'), AnalysisScope.COMPLETE)
            
            # Progress callback
            def update_progress(progress):
                self.progress = progress
                analysis_progress[self.task_id] = self
            
            # Run analysis
            result = analyzer.analyze_project(self.project_path, scope)
            
            self.result = result
            self.status = 'completed'
            self.progress = 100
            self.end_time = datetime.now()
            
            logger.info(f"Analysis task {self.task_id} completed successfully")
            
        except Exception as e:
            self.status = 'error'
            self.error = str(e)
            self.end_time = datetime.now()
            logger.error(f"Analysis task {self.task_id} failed: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            analysis_progress[self.task_id] = self

# API Routes

@app.route('/')
def serve_frontend():
    """Serve the React frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # Fallback to index.html for client-side routing
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'analyzer_available': analyzer is not None,
        'version': '1.0.0'
    })

@app.route('/api/files/tree', methods=['POST'])
def get_file_tree():
    """Get file tree for a directory"""
    try:
        data = request.get_json()
        path = data.get('path')
        
        if not path or not os.path.exists(path):
            return jsonify({
                'success': False,
                'error': 'Invalid path'
            }), 400
        
        def build_tree(dir_path, max_depth=3, current_depth=0):
            """Build file tree recursively"""
            if current_depth >= max_depth:
                return []
            
            items = []
            try:
                for item in sorted(os.listdir(dir_path)):
                    if item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(dir_path, item)
                    
                    if os.path.isdir(item_path):
                        # Skip common non-source directories
                        if item in ['__pycache__', 'node_modules', '.git', 'venv', 'env', '.venv']:
                            continue
                        
                        children = build_tree(item_path, max_depth, current_depth + 1)
                        items.append({
                            'name': item,
                            'path': item_path,
                            'type': 'folder',
                            'children': children
                        })
                    else:
                        # Only include relevant file types
                        if item.endswith(('.py', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.txt', '.md')):
                            items.append({
                                'name': item,
                                'path': item_path,
                                'type': 'file',
                                'size': os.path.getsize(item_path)
                            })
            except PermissionError:
                pass
            
            return items
        
        tree = build_tree(path)
        
        return jsonify({
            'success': True,
            'tree': tree,
            'path': path
        })
        
    except Exception as e:
        logger.error(f"Error building file tree: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/select-folder', methods=['POST'])
def select_folder():
    """Open native folder selection dialog"""
    try:
        # For development, return a mock folder path
        # In production, this would integrate with the OS file dialog
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        folder_path = filedialog.askdirectory(
            title="Select Python Project Folder",
            initialdir=os.path.expanduser("~")
        )
        
        root.destroy()
        
        if folder_path:
            return jsonify({
                'success': True,
                'folderPath': folder_path
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No folder selected'
            })
            
    except Exception as e:
        logger.error(f"Error selecting folder: {e}")
        return jsonify({
            'success': False,
            'error': 'Could not open folder dialog. Please ensure GUI support is available.'
        }), 500

@app.route('/api/analysis/start', methods=['POST'])
def start_analysis():
    """Start code analysis"""
    try:
        data = request.get_json()
        project_path = data.get('projectPath')
        selected_files = data.get('selectedFiles', [])
        options = data.get('options', {})
        
        if not project_path:
            return jsonify({
                'success': False,
                'error': 'Project path is required'
            }), 400
        
        if not selected_files:
            return jsonify({
                'success': False,
                'error': 'No files selected for analysis'
            }), 400
        
        if not analyzer:
            return jsonify({
                'success': False,
                'error': 'Analyzer not available'
            }), 500
        
        # Generate task ID
        task_id = f"analysis_{int(time.time())}"
        
        # Create analysis task
        task = AnalysisTask(task_id, project_path, selected_files, options)
        
        # Start analysis in background thread
        def run_analysis():
            task.run()
        
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'taskId': task_id,
            'message': 'Analysis started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analysis/progress/<task_id>', methods=['GET'])
def get_analysis_progress(task_id):
    """Get analysis progress"""
    try:
        if task_id not in analysis_progress:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
        
        task = analysis_progress[task_id]
        
        response_data = {
            'success': True,
            'taskId': task_id,
            'status': task.status,
            'progress': task.progress
        }
        
        if task.status == 'completed' and task.result:
            # Convert result to serializable format
            result_dict = {}
            try:
                if hasattr(task.result, '__dict__'):
                    from dataclasses import asdict
                    result_dict = asdict(task.result)
                else:
                    result_dict = task.result
                
                # Clean up non-serializable objects
                def clean_for_json(obj):
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    elif hasattr(obj, 'value'):  # Enum
                        return obj.value
                    elif not isinstance(obj, (str, int, float, bool, type(None))):
                        return str(obj)
                    return obj
                
                result_dict = clean_for_json(result_dict)
                response_data['result'] = result_dict
                
            except Exception as e:
                logger.error(f"Error serializing result: {e}")
                response_data['result'] = {'error': 'Failed to serialize results'}
        
        elif task.status == 'error':
            response_data['error'] = task.error
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting analysis progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analysis/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id):
    """Get full analysis results"""
    try:
        if task_id not in analysis_progress:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
        
        task = analysis_progress[task_id]
        
        if task.status != 'completed':
            return jsonify({
                'success': False,
                'error': f'Analysis not completed. Status: {task.status}'
            }), 400
        
        if not task.result:
            return jsonify({
                'success': False,
                'error': 'No results available'
            }), 404
        
        # Export results to JSON file
        results_dir = Path('user_projects') / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = results_dir / f"analysis_{task_id}.json"
        analyzer.export_results(task.result, str(output_file))
        
        return jsonify({
            'success': True,
            'taskId': task_id,
            'resultsFile': str(output_file),
            'downloadUrl': f'/api/download/results/{task_id}'
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/results/<task_id>', methods=['GET'])
def download_results(task_id):
    """Download analysis results as JSON"""
    try:
        results_dir = Path('user_projects') / 'results'
        results_file = results_dir / f"analysis_{task_id}.json"
        
        if not results_file.exists():
            return jsonify({
                'success': False,
                'error': 'Results file not found'
            }), 404
        
        return send_from_directory(
            results_dir,
            f"analysis_{task_id}.json",
            as_attachment=True,
            download_name=f"bw_automate_analysis_{task_id}.json"
        )
        
    except Exception as e:
        logger.error(f"Error downloading results: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projects/recent', methods=['GET'])
def get_recent_projects():
    """Get recently analyzed projects"""
    try:
        # Load from user preferences/history
        history_file = Path('user_projects') / 'history.json'
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = {'recent_projects': []}
        
        return jsonify({
            'success': True,
            'projects': history.get('recent_projects', [])
        })
        
    except Exception as e:
        logger.error(f"Error getting recent projects: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyzer/info', methods=['GET'])
def get_analyzer_info():
    """Get analyzer capabilities and information"""
    try:
        info = {
            'available': analyzer is not None,
            'version': '1.0.0',
            'capabilities': {
                'basic_analysis': True,
                'advanced_features': True,
                'sql_analysis': True,
                'security_analysis': True,
                'performance_analysis': True,
                'dependency_analysis': True
            },
            'supported_python_versions': ['3.6', '3.7', '3.8', '3.9', '3.10', '3.11', '3.12'],
            'supported_file_types': ['.py', '.pyi'],
            'analysis_scopes': ['basic', 'advanced', 'sql', 'complete', 'enterprise']
        }
        
        return jsonify({
            'success': True,
            'analyzer': info
        })
        
    except Exception as e:
        logger.error(f"Error getting analyzer info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

def create_user_directories():
    """Create necessary user directories"""
    directories = [
        'user_projects',
        'user_projects/results',
        'user_projects/cache',
        'frontend/build'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main server function"""
    logger.info("Starting BW_AUTOMATE Backend Server...")
    
    # Create necessary directories
    create_user_directories()
    
    # Initialize analyzer
    init_analyzer()
    
    # Get configuration
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Server starting on http://{host}:{port}")
    logger.info(f"Frontend served from: {app.static_folder}")
    logger.info(f"Analyzer available: {analyzer is not None}")
    
    if debug:
        logger.warning("Debug mode enabled - do not use in production!")
    
    # Start server
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()