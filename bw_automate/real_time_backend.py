#!/usr/bin/env python3
"""
Real-Time Analysis Backend with WebSocket Support
Provides real-time progress updates and streaming analysis results
"""

import os
import sys
import json
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
from queue import Queue, Empty

# Add our modules to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import our performance optimizer
try:
    from PERFORMANCE_OPTIMIZER import ParallelAnalyzer, CacheManager
    from INTEGRATED_PYTHON_ANALYZER import IntegratedPythonAnalyzer
    from COMPLETE_PYTHON_CODE_ANALYZER import CompletePythonAnalyzer
except ImportError as e:
    print(f"Warning: Could not import analyzers: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bw_automate_realtime_secret'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state management
active_analyses = {}
analysis_results_cache = {}

class RealTimeAnalysisManager:
    def __init__(self):
        self.parallel_analyzer = ParallelAnalyzer(max_workers=8)
        self.cache_manager = CacheManager()
        self.active_sessions = {}
        
    def start_analysis(self, session_id: str, directory: str, options: Dict):
        """Start real-time analysis with progress updates"""
        if session_id in self.active_sessions:
            return False, "Analysis already running for this session"
        
        # Create analysis session
        session = {
            'id': session_id,
            'directory': directory,
            'options': options,
            'start_time': datetime.now(),
            'status': 'starting',
            'progress': 0,
            'current_file': '',
            'total_files': 0,
            'processed_files': 0,
            'results': {},
            'metrics': {},
            'cancelled': False
        }
        
        self.active_sessions[session_id] = session
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(
            target=self._run_analysis,
            args=(session_id,),
            daemon=True
        )
        analysis_thread.start()
        
        return True, "Analysis started"
    
    def _run_analysis(self, session_id: str):
        """Run analysis with real-time updates"""
        session = self.active_sessions[session_id]
        
        try:
            directory = session['directory']
            
            # Progress callback for real-time updates
            def progress_callback(progress_data):
                if session['cancelled']:
                    return False  # Signal to stop
                
                session.update({
                    'progress': progress_data['progress_percent'],
                    'current_file': progress_data['current_file'],
                    'total_files': progress_data['total'],
                    'processed_files': progress_data['processed'],
                    'status': 'analyzing'
                })
                
                # Emit progress update
                socketio.emit('analysis_progress', {
                    'session_id': session_id,
                    'progress': progress_data['progress_percent'],
                    'current_file': progress_data['current_file'],
                    'processed': progress_data['processed'],
                    'total': progress_data['total'],
                    'status': 'analyzing'
                }, room=session_id)
                
                return True
            
            # File result callback for streaming results
            def result_callback(file_path: str, result: Dict):
                if session['cancelled']:
                    return
                
                session['results'][file_path] = result
                
                # Emit individual file result
                socketio.emit('file_result', {
                    'session_id': session_id,
                    'file_path': file_path,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
            
            # Use our integrated analyzer
            analyzer = IntegratedPythonAnalyzer()
            
            # Modified analyzer to support callbacks
            results = self._analyze_with_callbacks(
                analyzer, directory, progress_callback, result_callback
            )
            
            if not session['cancelled']:
                session.update({
                    'status': 'completed',
                    'progress': 100,
                    'end_time': datetime.now(),
                    'final_results': results
                })
                
                # Emit completion
                socketio.emit('analysis_complete', {
                    'session_id': session_id,
                    'results': results,
                    'metrics': session.get('metrics', {}),
                    'duration': (session['end_time'] - session['start_time']).total_seconds()
                }, room=session_id)
            
        except Exception as e:
            logging.error(f"Analysis error for session {session_id}: {e}")
            session.update({
                'status': 'error',
                'error': str(e)
            })
            
            socketio.emit('analysis_error', {
                'session_id': session_id,
                'error': str(e)
            }, room=session_id)
    
    def _analyze_with_callbacks(self, analyzer, directory, progress_callback, result_callback):
        """Analyze directory with real-time callbacks"""
        directory_path = Path(directory)
        python_files = list(directory_path.rglob("*.py"))
        total_files = len(python_files)
        
        results = {
            'project_path': directory,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files': total_files,
            'file_results': {}
        }
        
        for i, file_path in enumerate(python_files):
            if self.active_sessions.get(self.get_session_for_file(str(file_path)), {}).get('cancelled'):
                break
            
            try:
                # Analyze single file
                file_result = analyzer.analyze_file(str(file_path))
                results['file_results'][str(file_path)] = file_result
                
                # Call callbacks
                result_callback(str(file_path), file_result)
                progress_callback({
                    'processed': i + 1,
                    'total': total_files,
                    'current_file': str(file_path),
                    'progress_percent': ((i + 1) / total_files) * 100
                })
                
                # Small delay to allow real-time updates
                time.sleep(0.01)
                
            except Exception as e:
                logging.error(f"Error analyzing {file_path}: {e}")
                continue
        
        return results
    
    def get_session_for_file(self, file_path: str) -> Optional[str]:
        """Get session ID for a file path"""
        for session_id, session in self.active_sessions.items():
            if file_path.startswith(session['directory']):
                return session_id
        return None
    
    def cancel_analysis(self, session_id: str) -> bool:
        """Cancel ongoing analysis"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['cancelled'] = True
            self.active_sessions[session_id]['status'] = 'cancelled'
            
            socketio.emit('analysis_cancelled', {
                'session_id': session_id
            }, room=session_id)
            
            return True
        return False
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current session status"""
        return self.active_sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up completed session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

# Global analysis manager
analysis_manager = RealTimeAnalysisManager()

@app.route('/api/analysis/start', methods=['POST'])
def start_analysis():
    """Start real-time analysis"""
    try:
        data = request.get_json()
        directory = data.get('directory')
        options = data.get('options', {})
        
        if not directory or not os.path.exists(directory):
            return jsonify({'error': 'Invalid directory'}), 400
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        success, message = analysis_manager.start_analysis(session_id, directory, options)
        
        if success:
            return jsonify({
                'session_id': session_id,
                'status': 'started',
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error starting analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<session_id>/status', methods=['GET'])
def get_analysis_status(session_id):
    """Get analysis status"""
    try:
        status = analysis_manager.get_session_status(session_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<session_id>/cancel', methods=['POST'])
def cancel_analysis(session_id):
    """Cancel analysis"""
    try:
        success = analysis_manager.cancel_analysis(session_id)
        if success:
            return jsonify({'status': 'cancelled'})
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/directories', methods=['GET'])
def list_directories():
    """List available directories for analysis"""
    try:
        path = request.args.get('path', '.')
        path_obj = Path(path).resolve()
        
        if not path_obj.exists() or not path_obj.is_dir():
            return jsonify({'error': 'Invalid path'}), 400
        
        directories = []
        files = []
        
        try:
            for item in path_obj.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory'
                    })
                elif item.is_file() and item.suffix == '.py':
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'file',
                        'size': item.stat().st_size
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied'}), 403
        
        return jsonify({
            'current_path': str(path_obj),
            'parent_path': str(path_obj.parent) if path_obj.parent != path_obj else None,
            'directories': sorted(directories, key=lambda x: x['name'].lower()),
            'files': sorted(files, key=lambda x: x['name'].lower())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Connected to BW_AUTOMATE Real-Time Server'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_analysis')
def handle_join_analysis(data):
    """Join analysis session room"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_analysis', {'session_id': session_id})

@socketio.on('leave_analysis')
def handle_leave_analysis(data):
    """Leave analysis session room"""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        emit('left_analysis', {'session_id': session_id})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_analyses': len(analysis_manager.active_sessions),
        'version': '2.0.0'
    })

@app.route('/')
def serve_frontend():
    """Serve frontend for development"""
    return jsonify({
        'message': 'BW_AUTOMATE Real-Time Backend',
        'version': '2.0.0',
        'endpoints': {
            '/api/analysis/start': 'POST - Start analysis',
            '/api/analysis/<id>/status': 'GET - Get analysis status',
            '/api/analysis/<id>/cancel': 'POST - Cancel analysis',
            '/api/directories': 'GET - List directories',
            '/api/health': 'GET - Health check'
        },
        'websocket_events': {
            'join_analysis': 'Join analysis session',
            'leave_analysis': 'Leave analysis session',
            'analysis_progress': 'Receive progress updates',
            'file_result': 'Receive individual file results',
            'analysis_complete': 'Analysis completion notification',
            'analysis_error': 'Error notifications'
        }
    })

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting BW_AUTOMATE Real-Time Backend Server...")
    print("   Real-time analysis with WebSocket support")
    print("   Performance optimization with caching")
    print("   Apple-inspired API design")
    print()
    
    # Clean up old cache on startup
    analysis_manager.cache_manager.cleanup_old_cache(max_age_days=7)
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True
    )