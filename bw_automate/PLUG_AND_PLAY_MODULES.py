#!/usr/bin/env python3
"""
PLUG-AND-PLAY INTEGRATION MODULES - BW AUTOMATE
Módulos de integração que podem ser facilmente adicionados a qualquer projeto
Sistema de plugins extensível e auto-instalável
"""

import os
import sys
import json
import logging
import subprocess
import importlib
import tempfile
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import zipfile
import urllib.request

try:
    import pkg_resources
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'setuptools'], check=True)
    import pkg_resources


class ModuleType(Enum):
    """Tipos de módulos disponíveis"""
    FRAMEWORK_INTEGRATION = "framework_integration"
    DATABASE_CONNECTOR = "database_connector"
    ANALYSIS_EXTENSION = "analysis_extension"
    VISUALIZATION_PLUGIN = "visualization_plugin"
    MONITORING_TOOL = "monitoring_tool"
    SECURITY_SCANNER = "security_scanner"
    DEPLOYMENT_HELPER = "deployment_helper"
    UTILITY_TOOL = "utility_tool"


class InstallationMethod(Enum):
    """Métodos de instalação disponíveis"""
    COPY_FILES = "copy_files"
    PIP_INSTALL = "pip_install"
    GIT_CLONE = "git_clone"
    DOWNLOAD_EXTRACT = "download_extract"
    INLINE_CODE = "inline_code"


@dataclass
class ModuleManifest:
    """Manifesto de um módulo"""
    name: str
    version: str
    description: str
    module_type: ModuleType
    author: str
    license: str
    requirements: List[str]
    python_version: str
    compatibility: List[str]  # Compatible frameworks/systems
    installation_method: InstallationMethod
    source_url: Optional[str] = None
    entry_point: Optional[str] = None
    config_template: Optional[Dict[str, Any]] = None
    documentation_url: Optional[str] = None
    examples: List[Dict[str, Any]] = None


class PluginInterface(ABC):
    """Interface base para todos os plugins"""
    
    @abstractmethod
    def get_manifest(self) -> ModuleManifest:
        """Retorna o manifesto do plugin"""
        pass
    
    @abstractmethod
    def install(self, target_path: str, config: Dict[str, Any] = None) -> bool:
        """Instala o plugin"""
        pass
    
    @abstractmethod
    def configure(self, project_path: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Configura o plugin para o projeto"""
        pass
    
    @abstractmethod
    def validate(self, project_path: str) -> Dict[str, Any]:
        """Valida se o plugin está funcionando corretamente"""
        pass
    
    @abstractmethod
    def uninstall(self, target_path: str) -> bool:
        """Remove o plugin"""
        pass


class DjangoIntegrationModule(PluginInterface):
    """Módulo de integração para Django"""
    
    def get_manifest(self) -> ModuleManifest:
        return ModuleManifest(
            name="django_integration",
            version="2.0.0",
            description="Complete Django ORM integration with model analysis and admin interface",
            module_type=ModuleType.FRAMEWORK_INTEGRATION,
            author="BW_AUTOMATE Team",
            license="MIT",
            requirements=["Django>=3.0", "django-extensions>=3.0"],
            python_version=">=3.8",
            compatibility=["django"],
            installation_method=InstallationMethod.INLINE_CODE,
            entry_point="django_bw_integration.py",
            config_template={
                "django_settings_module": "myproject.settings",
                "analyze_models": True,
                "analyze_migrations": True,
                "analyze_admin": True,
                "create_management_command": True,
                "create_admin_interface": True
            },
            examples=[
                {
                    "name": "Basic Analysis",
                    "code": "python manage.py bw_analyze",
                    "description": "Run basic BW_AUTOMATE analysis via Django management command"
                },
                {
                    "name": "Web Interface",
                    "code": "http://localhost:8000/admin/bw-automate/",
                    "description": "Access BW_AUTOMATE admin interface"
                }
            ]
        )
    
    def install(self, target_path: str, config: Dict[str, Any] = None) -> bool:
        """Instala integração Django"""
        try:
            project_path = Path(target_path)
            
            # 1. Cria management command
            self._create_management_command(project_path, config or {})
            
            # 2. Cria integração com admin
            self._create_admin_integration(project_path, config or {})
            
            # 3. Cria models para BW_AUTOMATE
            self._create_bw_models(project_path, config or {})
            
            # 4. Cria views e URLs
            self._create_views_and_urls(project_path, config or {})
            
            # 5. Cria templates
            self._create_templates(project_path, config or {})
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to install Django integration: {e}")
            return False
    
    def _create_management_command(self, project_path: Path, config: Dict[str, Any]):
        """Cria Django management command"""
        # Encontra o diretório de management commands
        management_dir = None
        for app_dir in project_path.rglob('management'):
            if app_dir.is_dir():
                management_dir = app_dir
                break
        
        if not management_dir:
            # Cria estrutura de management command na primeira app encontrada
            for potential_app in project_path.iterdir():
                if potential_app.is_dir() and (potential_app / 'models.py').exists():
                    management_dir = potential_app / 'management'
                    management_dir.mkdir(exist_ok=True)
                    (management_dir / '__init__.py').touch()
                    (management_dir / 'commands').mkdir(exist_ok=True)
                    (management_dir / 'commands' / '__init__.py').touch()
                    break
        
        if management_dir:
            command_file = management_dir / 'commands' / 'bw_analyze.py'
            
            command_content = f'''from django.core.management.base import BaseCommand
from django.conf import settings
import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bw_automate"))

try:
    from run_analysis import BWAutomate
    from django_bw_integration import DjangoBWAnalyzer
except ImportError as e:
    print(f"BW_AUTOMATE not found: {{e}}")
    sys.exit(1)


class Command(BaseCommand):
    help = 'Run BW_AUTOMATE analysis on Django project'
    
    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, help='Output directory for reports')
        parser.add_argument('--format', type=str, default='html', help='Output format')
        parser.add_argument('--models-only', action='store_true', help='Analyze only models')
        parser.add_argument('--migrations-only', action='store_true', help='Analyze only migrations')
    
    def handle(self, *args, **options):
        self.stdout.write('Starting BW_AUTOMATE analysis for Django project...')
        
        try:
            analyzer = DjangoBWAnalyzer()
            
            results = analyzer.analyze_django_project(
                output_dir=options.get('output', 'bw_reports'),
                format=options.get('format', 'html'),
                models_only=options.get('models_only', False),
                migrations_only=options.get('migrations_only', False)
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Analysis completed! Found {{results.get("total_tables", 0)}} tables'
                )
            )
            
            if results.get('report_path'):
                self.stdout.write(f'Report generated: {{results["report_path"]}}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Analysis failed: {{e}}')
            )
            raise
'''
            
            with open(command_file, 'w') as f:
                f.write(command_content)
    
    def _create_admin_integration(self, project_path: Path, config: Dict[str, Any]):
        """Cria integração com Django admin"""
        admin_file = project_path / 'bw_automate_admin.py'
        
        admin_content = '''from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

try:
    from django_bw_integration import DjangoBWAnalyzer
except ImportError:
    DjangoBWAnalyzer = None


class BWAutomateAdminView:
    """BW_AUTOMATE admin interface"""
    
    @method_decorator(staff_member_required)
    def analysis_view(self, request):
        """Main analysis view"""
        if request.method == 'POST':
            try:
                if DjangoBWAnalyzer:
                    analyzer = DjangoBWAnalyzer()
                    results = analyzer.analyze_django_project()
                    return JsonResponse(results)
                else:
                    return JsonResponse({'error': 'BW_AUTOMATE not available'})
            except Exception as e:
                return JsonResponse({'error': str(e)})
        
        context = {
            'title': 'BW_AUTOMATE Analysis',
            'available': DjangoBWAnalyzer is not None
        }
        return render(request, 'admin/bw_automate_analysis.html', context)
    
    def get_urls(self):
        """Get admin URLs"""
        return [
            path('bw-automate/', self.analysis_view, name='bw_automate_analysis'),
        ]


# Register with admin
bw_admin = BWAutomateAdminView()
admin.site.register_view('bw-automate/', view=bw_admin.analysis_view, name='BW_AUTOMATE Analysis')
'''
        
        with open(admin_file, 'w') as f:
            f.write(admin_content)
    
    def _create_bw_models(self, project_path: Path, config: Dict[str, Any]):
        """Cria models para armazenar resultados do BW_AUTOMATE"""
        models_file = project_path / 'bw_automate_models.py'
        
        models_content = '''from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class BWAnalysisSession(models.Model):
    """Sessão de análise do BW_AUTOMATE"""
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    project_name = models.CharField(max_length=200)
    analysis_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='running')
    total_files = models.IntegerField(default=0)
    total_tables = models.IntegerField(default=0)
    execution_time = models.FloatField(null=True, blank=True)
    report_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis {self.id} - {self.project_name} ({self.created_at})"


class DetectedTable(models.Model):
    """Tabela detectada pelo BW_AUTOMATE"""
    session = models.ForeignKey(BWAnalysisSession, on_delete=models.CASCADE, related_name='tables')
    table_name = models.CharField(max_length=200)
    database_type = models.CharField(max_length=100)
    schema_name = models.CharField(max_length=200, blank=True)
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField()
    context = models.TextField()
    operation_type = models.CharField(max_length=100)
    confidence_score = models.FloatField(default=1.0)
    
    class Meta:
        unique_together = ['session', 'table_name', 'file_path', 'line_number']
    
    def __str__(self):
        return f"{self.table_name} in {self.file_path}:{self.line_number}"


class AnalysisMetric(models.Model):
    """Métricas de análise"""
    session = models.ForeignKey(BWAnalysisSession, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=200)
    metric_value = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
'''
        
        with open(models_file, 'w') as f:
            f.write(models_content)
    
    def _create_views_and_urls(self, project_path: Path, config: Dict[str, Any]):
        """Cria views e URLs para interface web"""
        views_file = project_path / 'bw_automate_views.py'
        
        views_content = '''from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
import json
import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

try:
    from django_bw_integration import DjangoBWAnalyzer
    from bw_automate_models import BWAnalysisSession, DetectedTable
except ImportError:
    DjangoBWAnalyzer = None


@staff_member_required
def dashboard(request):
    """Dashboard principal"""
    recent_sessions = BWAnalysisSession.objects.all()[:10] if 'BWAnalysisSession' in globals() else []
    
    context = {
        'recent_sessions': recent_sessions,
        'bw_available': DjangoBWAnalyzer is not None
    }
    return render(request, 'bw_automate/dashboard.html', context)


@staff_member_required
@csrf_exempt
def run_analysis(request):
    """Executa análise via AJAX"""
    if request.method == 'POST':
        try:
            if not DjangoBWAnalyzer:
                return JsonResponse({'error': 'BW_AUTOMATE not available'})
            
            data = json.loads(request.body)
            analyzer = DjangoBWAnalyzer()
            
            results = analyzer.analyze_django_project(
                analysis_type=data.get('analysis_type', 'full'),
                save_to_db=True,
                user=request.user
            )
            
            return JsonResponse({
                'success': True,
                'session_id': results.get('session_id'),
                'total_tables': results.get('total_tables', 0),
                'total_files': results.get('total_files', 0)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Method not allowed'})


@staff_member_required
def session_detail(request, session_id):
    """Detalhes de uma sessão de análise"""
    try:
        session = BWAnalysisSession.objects.get(id=session_id)
        tables = session.tables.all()
        
        context = {
            'session': session,
            'tables': tables
        }
        return render(request, 'bw_automate/session_detail.html', context)
        
    except BWAnalysisSession.DoesNotExist:
        return render(request, 'bw_automate/error.html', {'error': 'Session not found'})
'''
        
        with open(views_file, 'w') as f:
            f.write(views_content)
    
    def _create_templates(self, project_path: Path, config: Dict[str, Any]):
        """Cria templates para interface web"""
        templates_dir = project_path / 'templates' / 'bw_automate'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Dashboard template
        dashboard_template = '''{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}BW_AUTOMATE Dashboard{% endblock %}

{% block content %}
<div class="bw-automate-dashboard">
    <h1>BW_AUTOMATE Dashboard</h1>
    
    {% if bw_available %}
        <div class="analysis-controls">
            <button id="run-analysis" class="btn btn-primary">Run New Analysis</button>
            <select id="analysis-type">
                <option value="full">Full Analysis</option>
                <option value="models">Models Only</option>
                <option value="migrations">Migrations Only</option>
            </select>
        </div>
        
        <div id="analysis-status" style="display: none;">
            <div class="spinner"></div>
            <span>Running analysis...</span>
        </div>
    {% else %}
        <div class="alert alert-warning">
            BW_AUTOMATE is not available. Please install the BW_AUTOMATE module.
        </div>
    {% endif %}
    
    <h2>Recent Analysis Sessions</h2>
    <table class="table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Type</th>
                <th>Tables Found</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for session in recent_sessions %}
            <tr>
                <td>{{ session.id }}</td>
                <td>{{ session.created_at|date:"Y-m-d H:i" }}</td>
                <td>{{ session.analysis_type }}</td>
                <td>{{ session.total_tables }}</td>
                <td>{{ session.status }}</td>
                <td>
                    <a href="{% url 'bw_session_detail' session.id %}" class="btn btn-sm btn-info">View</a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="6">No analysis sessions found</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const runBtn = document.getElementById('run-analysis');
    const statusDiv = document.getElementById('analysis-status');
    
    if (runBtn) {
        runBtn.addEventListener('click', function() {
            const analysisType = document.getElementById('analysis-type').value;
            
            statusDiv.style.display = 'block';
            runBtn.disabled = true;
            
            fetch('{% url "bw_run_analysis" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    analysis_type: analysisType
                })
            })
            .then(response => response.json())
            .then(data => {
                statusDiv.style.display = 'none';
                runBtn.disabled = false;
                
                if (data.success) {
                    alert(`Analysis completed! Found ${data.total_tables} tables in ${data.total_files} files.`);
                    location.reload();
                } else {
                    alert(`Analysis failed: ${data.error}`);
                }
            })
            .catch(error => {
                statusDiv.style.display = 'none';
                runBtn.disabled = false;
                alert(`Error: ${error}`);
            });
        });
    }
});
</script>

<style>
.bw-automate-dashboard {
    padding: 20px;
}

.analysis-controls {
    margin: 20px 0;
}

.analysis-controls button, .analysis-controls select {
    margin-right: 10px;
    padding: 8px 16px;
}

#analysis-status {
    padding: 10px;
    background: #f0f0f0;
    border-radius: 4px;
    margin: 10px 0;
}

.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #ccc;
    border-top: 2px solid #007cba;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.table {
    margin-top: 20px;
}

.btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
}

.btn-primary {
    background: #007cba;
    color: white;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-sm {
    padding: 4px 8px;
    font-size: 12px;
}

.alert {
    padding: 12px;
    border-radius: 4px;
    margin: 10px 0;
}

.alert-warning {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}
</style>
{% endblock %}
'''
        
        with open(templates_dir / 'dashboard.html', 'w') as f:
            f.write(dashboard_template)
    
    def configure(self, project_path: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Configura integração Django"""
        config = config or {}
        
        # Cria arquivo de integração principal
        integration_file = Path(project_path) / 'django_bw_integration.py'
        
        integration_content = f'''#!/usr/bin/env python3
"""
Django BW_AUTOMATE Integration
Auto-generated Django integration module
"""

import os
import django
from django.conf import settings
from django.apps import apps
import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

# Django setup
try:
    django.setup()
except:
    pass

try:
    from run_analysis import BWAutomate
    from bw_automate_models import BWAnalysisSession, DetectedTable, AnalysisMetric
except ImportError:
    BWAutomate = None
    BWAnalysisSession = None


class DjangoBWAnalyzer:
    """Django-specific BW_AUTOMATE analyzer"""
    
    def __init__(self):
        self.bw = BWAutomate() if BWAutomate else None
    
    def analyze_django_project(self, analysis_type='full', save_to_db=False, user=None, **kwargs):
        """Analyze Django project with BW_AUTOMATE"""
        
        if not self.bw:
            raise Exception("BW_AUTOMATE not available")
        
        # Create analysis session
        session = None
        if save_to_db and BWAnalysisSession:
            session = BWAnalysisSession.objects.create(
                project_name=settings.ROOT_URLCONF.split('.')[0],
                analysis_type=analysis_type,
                created_by=user,
                status='running'
            )
        
        try:
            # Configure analysis based on type
            if analysis_type == 'models':
                source_dirs = self._get_model_directories()
            elif analysis_type == 'migrations':
                source_dirs = self._get_migration_directories()
            else:
                source_dirs = ['.']
            
            # Run BW_AUTOMATE analysis
            results = self.bw.analyze_project(
                project_root=".",
                config={{
                    "source_dirs": source_dirs,
                    "django_specific": True,
                    "analyze_models": True,
                    "analyze_migrations": analysis_type in ['full', 'migrations'],
                    **kwargs
                }}
            )
            
            # Save results to database
            if save_to_db and session:
                session.total_files = results.get('total_files', 0)
                session.total_tables = results.get('total_tables', 0)
                session.status = 'completed'
                session.save()
                
                # Save detected tables
                for table_info in results.get('tables', []):
                    DetectedTable.objects.create(
                        session=session,
                        table_name=table_info.get('name', ''),
                        database_type=table_info.get('type', 'unknown'),
                        file_path=table_info.get('file', ''),
                        line_number=table_info.get('line', 0),
                        context=table_info.get('context', ''),
                        operation_type=table_info.get('operation', 'unknown')
                    )
                
                results['session_id'] = session.id
            
            return results
            
        except Exception as e:
            if save_to_db and session:
                session.status = 'failed'
                session.save()
            raise
    
    def _get_model_directories(self):
        """Get directories containing Django models"""
        dirs = []
        for app_config in apps.get_app_configs():
            app_path = Path(app_config.path)
            if (app_path / 'models.py').exists() or (app_path / 'models').exists():
                dirs.append(str(app_path.relative_to(Path.cwd())))
        return dirs or ['.']
    
    def _get_migration_directories(self):
        """Get directories containing Django migrations"""
        dirs = []
        for app_config in apps.get_app_configs():
            migrations_path = Path(app_config.path) / 'migrations'
            if migrations_path.exists():
                dirs.append(str(migrations_path.relative_to(Path.cwd())))
        return dirs or ['.']
    
    def get_django_models_info(self):
        """Get information about Django models"""
        models_info = []
        
        for model in apps.get_models():
            model_info = {{
                'app': model._meta.app_label,
                'model': model.__name__,
                'table': model._meta.db_table,
                'fields': [field.name for field in model._meta.fields],
                'relations': []
            }}
            
            # Analyze relationships
            for field in model._meta.fields:
                if hasattr(field, 'related_model') and field.related_model:
                    model_info['relations'].append({{
                        'field': field.name,
                        'related_model': field.related_model.__name__,
                        'related_table': field.related_model._meta.db_table
                    }})
            
            models_info.append(model_info)
        
        return models_info


# Auto-run analysis if called directly
if __name__ == "__main__":
    analyzer = DjangoBWAnalyzer()
    results = analyzer.analyze_django_project()
    print(f"Analysis completed! Found {{results.get('total_tables', 0)}} tables")
'''
        
        with open(integration_file, 'w') as f:
            f.write(integration_content)
        
        return {
            'success': True,
            'files_created': [
                'django_bw_integration.py',
                'bw_automate_admin.py',
                'bw_automate_models.py',
                'bw_automate_views.py'
            ],
            'next_steps': [
                "Add 'bw_automate_models' to INSTALLED_APPS in settings.py",
                "Run: python manage.py makemigrations",
                "Run: python manage.py migrate",
                "Include BW_AUTOMATE URLs in your main urls.py",
                "Run: python manage.py bw_analyze"
            ]
        }
    
    def validate(self, project_path: str) -> Dict[str, Any]:
        """Valida instalação Django"""
        validation_results = {
            'success': True,
            'checks': [],
            'errors': [],
            'warnings': []
        }
        
        project_path = Path(project_path)
        
        # Verifica se arquivos foram criados
        required_files = [
            'django_bw_integration.py',
            'bw_automate_models.py'
        ]
        
        for file_name in required_files:
            file_path = project_path / file_name
            if file_path.exists():
                validation_results['checks'].append(f"✅ {file_name} exists")
            else:
                validation_results['errors'].append(f"❌ {file_name} missing")
                validation_results['success'] = False
        
        # Verifica se Django está disponível
        try:
            import django
            validation_results['checks'].append(f"✅ Django {django.get_version()} available")
        except ImportError:
            validation_results['errors'].append("❌ Django not available")
            validation_results['success'] = False
        
        # Verifica management command
        management_cmd = None
        for cmd_file in project_path.rglob('**/management/commands/bw_analyze.py'):
            management_cmd = cmd_file
            break
        
        if management_cmd:
            validation_results['checks'].append("✅ Management command created")
        else:
            validation_results['warnings'].append("⚠ Management command not found")
        
        return validation_results
    
    def uninstall(self, target_path: str) -> bool:
        """Remove integração Django"""
        try:
            project_path = Path(target_path)
            
            files_to_remove = [
                'django_bw_integration.py',
                'bw_automate_admin.py',
                'bw_automate_models.py',
                'bw_automate_views.py'
            ]
            
            for file_name in files_to_remove:
                file_path = project_path / file_name
                if file_path.exists():
                    file_path.unlink()
            
            # Remove templates
            templates_dir = project_path / 'templates' / 'bw_automate'
            if templates_dir.exists():
                shutil.rmtree(templates_dir)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to uninstall Django integration: {e}")
            return False


class PluginManager:
    """Gerenciador de plugins"""
    
    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = Path(plugins_dir or "bw_automate_plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        self.available_modules = self._load_builtin_modules()
        self.installed_modules = self._load_installed_modules()
    
    def _load_builtin_modules(self) -> Dict[str, Type[PluginInterface]]:
        """Carrega módulos built-in"""
        return {
            'django_integration': DjangoIntegrationModule,
            # Outros módulos serão adicionados aqui
        }
    
    def _load_installed_modules(self) -> Dict[str, Dict[str, Any]]:
        """Carrega módulos instalados"""
        installed = {}
        
        manifest_file = self.plugins_dir / 'installed_modules.json'
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    installed = json.load(f)
            except:
                pass
        
        return installed
    
    def list_available_modules(self) -> List[ModuleManifest]:
        """Lista módulos disponíveis"""
        manifests = []
        
        for name, module_class in self.available_modules.items():
            try:
                module_instance = module_class()
                manifests.append(module_instance.get_manifest())
            except Exception as e:
                logging.warning(f"Failed to get manifest for {name}: {e}")
        
        return manifests
    
    def install_module(self, module_name: str, target_path: str, 
                      config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Instala um módulo"""
        if module_name not in self.available_modules:
            return {
                'success': False,
                'error': f"Module '{module_name}' not found"
            }
        
        try:
            module_class = self.available_modules[module_name]
            module_instance = module_class()
            
            # Instala o módulo
            success = module_instance.install(target_path, config)
            
            if success:
                # Configura o módulo
                config_result = module_instance.configure(target_path, config)
                
                # Salva informações da instalação
                self._save_installation_info(module_name, target_path, config)
                
                return {
                    'success': True,
                    'module': module_name,
                    'config_result': config_result,
                    'message': f"Module '{module_name}' installed successfully"
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to install module '{module_name}'"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Installation error: {e}"
            }
    
    def validate_module(self, module_name: str, target_path: str) -> Dict[str, Any]:
        """Valida um módulo instalado"""
        if module_name not in self.available_modules:
            return {
                'success': False,
                'error': f"Module '{module_name}' not found"
            }
        
        try:
            module_class = self.available_modules[module_name]
            module_instance = module_class()
            
            return module_instance.validate(target_path)
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Validation error: {e}"
            }
    
    def uninstall_module(self, module_name: str, target_path: str) -> Dict[str, Any]:
        """Remove um módulo"""
        if module_name not in self.available_modules:
            return {
                'success': False,
                'error': f"Module '{module_name}' not found"
            }
        
        try:
            module_class = self.available_modules[module_name]
            module_instance = module_class()
            
            success = module_instance.uninstall(target_path)
            
            if success:
                # Remove informações da instalação
                self._remove_installation_info(module_name, target_path)
                
                return {
                    'success': True,
                    'message': f"Module '{module_name}' uninstalled successfully"
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to uninstall module '{module_name}'"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Uninstallation error: {e}"
            }
    
    def _save_installation_info(self, module_name: str, target_path: str, config: Dict[str, Any]):
        """Salva informações da instalação"""
        installation_info = {
            'module_name': module_name,
            'target_path': target_path,
            'config': config,
            'installed_at': datetime.now().isoformat()
        }
        
        self.installed_modules[f"{module_name}_{hash(target_path)}"] = installation_info
        
        manifest_file = self.plugins_dir / 'installed_modules.json'
        with open(manifest_file, 'w') as f:
            json.dump(self.installed_modules, f, indent=2)
    
    def _remove_installation_info(self, module_name: str, target_path: str):
        """Remove informações da instalação"""
        key = f"{module_name}_{hash(target_path)}"
        if key in self.installed_modules:
            del self.installed_modules[key]
            
            manifest_file = self.plugins_dir / 'installed_modules.json'
            with open(manifest_file, 'w') as f:
                json.dump(self.installed_modules, f, indent=2)


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE Plug-and-Play Module Manager")
    parser.add_argument("command", choices=['list', 'install', 'validate', 'uninstall'], 
                       help="Command to execute")
    parser.add_argument("--module", "-m", help="Module name")
    parser.add_argument("--target", "-t", help="Target project path", default=".")
    parser.add_argument("--config", "-c", help="Configuration file (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = PluginManager()
    
    if args.command == 'list':
        modules = manager.list_available_modules()
        print("🔌 Available BW_AUTOMATE Modules:")
        print("=" * 50)
        
        for manifest in modules:
            print(f"📦 {manifest.name} v{manifest.version}")
            print(f"   {manifest.description}")
            print(f"   Type: {manifest.module_type.value}")
            print(f"   Compatible with: {', '.join(manifest.compatibility)}")
            print(f"   Requirements: {', '.join(manifest.requirements)}")
            print()
    
    elif args.command == 'install':
        if not args.module:
            print("❌ Module name required for installation")
            return
        
        config = {}
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"❌ Failed to load config file: {e}")
                return
        
        result = manager.install_module(args.module, args.target, config)
        
        if result['success']:
            print(f"✅ {result['message']}")
            if 'config_result' in result and 'next_steps' in result['config_result']:
                print("\n📋 Next Steps:")
                for step in result['config_result']['next_steps']:
                    print(f"  • {step}")
        else:
            print(f"❌ {result['error']}")
    
    elif args.command == 'validate':
        if not args.module:
            print("❌ Module name required for validation")
            return
        
        result = manager.validate_module(args.module, args.target)
        
        if result['success']:
            print(f"✅ Module '{args.module}' is valid")
            for check in result.get('checks', []):
                print(f"  {check}")
            for warning in result.get('warnings', []):
                print(f"  {warning}")
        else:
            print(f"❌ Module '{args.module}' validation failed")
            for error in result.get('errors', []):
                print(f"  {error}")
    
    elif args.command == 'uninstall':
        if not args.module:
            print("❌ Module name required for uninstallation")
            return
        
        result = manager.uninstall_module(args.module, args.target)
        
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")


if __name__ == "__main__":
    main()