#!/usr/bin/env python3
"""
PRODUCTION DEPLOYMENT SYSTEM - BW AUTOMATE SYSTEM
Sistema completo de deployment para produção com Docker, Kubernetes, CI/CD
Suporte para AWS, GCP, Azure, monitoramento e escalabilidade automática
"""

import os
import yaml
import json
import subprocess
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import shutil
import tarfile
import zipfile

try:
    import docker
except ImportError:
    print("Installing docker for container management...")
    os.system("pip install docker")
    import docker

try:
    import kubernetes
    from kubernetes import client, config
except ImportError:
    print("Installing kubernetes for K8s management...")
    os.system("pip install kubernetes")
    import kubernetes
    from kubernetes import client, config

try:
    import boto3
except ImportError:
    print("Installing boto3 for AWS integration...")
    os.system("pip install boto3")
    import boto3

try:
    from google.cloud import container_v1
    from google.oauth2 import service_account
except ImportError:
    print("Installing google-cloud for GCP integration...")
    os.system("pip install google-cloud-container google-auth")
    try:
        from google.cloud import container_v1
        from google.oauth2 import service_account
    except:
        print("⚠ Google Cloud SDK not configured")
        container_v1 = None

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
except ImportError:
    print("Installing azure-mgmt for Azure integration...")
    os.system("pip install azure-mgmt-containerinstance azure-identity")
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.containerinstance import ContainerInstanceManagementClient
    except:
        print("⚠ Azure CLI not configured")
        DefaultAzureCredential = None


class CloudProvider(Enum):
    """Provedores de nuvem suportados"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    LOCAL = "local"


class DeploymentTarget(Enum):
    """Tipos de deployment"""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DOCKER_COMPOSE = "docker_compose"
    SERVERLESS = "serverless"
    VM = "vm"


class EnvironmentType(Enum):
    """Tipos de ambiente"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DeploymentConfig:
    """Configuração de deployment"""
    app_name: str
    version: str
    environment: EnvironmentType
    target: DeploymentTarget
    cloud_provider: CloudProvider
    region: str
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    storage_size: str = "10Gi"
    environment_vars: Dict[str, str] = None
    secrets: Dict[str, str] = None
    health_check_path: str = "/health"
    port: int = 8080


@dataclass
class CloudCredentials:
    """Credenciais de nuvem"""
    provider: CloudProvider
    credentials: Dict[str, Any]


class DockerManager:
    """Gerenciador de containers Docker"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logging.error(f"Failed to connect to Docker: {e}")
            self.client = None
    
    def build_image(self, dockerfile_path: str, image_name: str, tag: str = "latest") -> bool:
        """Constrói imagem Docker"""
        if not self.client:
            logging.error("Docker client not available")
            return False
        
        try:
            image, logs = self.client.images.build(
                path=str(Path(dockerfile_path).parent),
                dockerfile=Path(dockerfile_path).name,
                tag=f"{image_name}:{tag}",
                rm=True
            )
            
            print(f"✅ Docker image built: {image_name}:{tag}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to build Docker image: {e}")
            return False
    
    def push_image(self, image_name: str, tag: str = "latest", registry: str = None) -> bool:
        """Envia imagem para registry"""
        if not self.client:
            return False
        
        try:
            full_name = f"{registry}/{image_name}:{tag}" if registry else f"{image_name}:{tag}"
            
            # Tag para registry se necessário
            if registry:
                image = self.client.images.get(f"{image_name}:{tag}")
                image.tag(full_name)
            
            # Push
            for line in self.client.images.push(full_name, stream=True, decode=True):
                if 'status' in line:
                    print(f"📤 {line['status']}")
            
            print(f"✅ Image pushed: {full_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to push image: {e}")
            return False
    
    def run_container(self, image_name: str, tag: str = "latest", 
                     name: str = None, ports: Dict[int, int] = None,
                     environment: Dict[str, str] = None) -> bool:
        """Executa container"""
        if not self.client:
            return False
        
        try:
            container = self.client.containers.run(
                f"{image_name}:{tag}",
                name=name,
                ports=ports,
                environment=environment,
                detach=True,
                remove=True
            )
            
            print(f"✅ Container started: {container.name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to run container: {e}")
            return False


class KubernetesManager:
    """Gerenciador de deployment Kubernetes"""
    
    def __init__(self, kubeconfig_path: str = None):
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
        except Exception as e:
            logging.error(f"Failed to initialize Kubernetes client: {e}")
            self.v1 = None
            self.apps_v1 = None
            self.networking_v1 = None
    
    def create_namespace(self, namespace: str) -> bool:
        """Cria namespace"""
        if not self.v1:
            return False
        
        try:
            # Verifica se namespace já existe
            try:
                self.v1.read_namespace(namespace)
                print(f"📁 Namespace '{namespace}' already exists")
                return True
            except client.exceptions.ApiException as e:
                if e.status != 404:
                    raise
            
            # Cria namespace
            namespace_obj = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace)
            )
            
            self.v1.create_namespace(namespace_obj)
            print(f"✅ Namespace created: {namespace}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create namespace: {e}")
            return False
    
    def create_deployment(self, config: DeploymentConfig, image_name: str, 
                         namespace: str = "default") -> bool:
        """Cria deployment Kubernetes"""
        if not self.apps_v1:
            return False
        
        try:
            # Define deployment
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=config.app_name,
                    namespace=namespace,
                    labels={"app": config.app_name, "version": config.version}
                ),
                spec=client.V1DeploymentSpec(
                    replicas=config.replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": config.app_name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": config.app_name, "version": config.version}
                        ),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=config.app_name,
                                    image=image_name,
                                    ports=[client.V1ContainerPort(container_port=config.port)],
                                    resources=client.V1ResourceRequirements(
                                        limits={
                                            "cpu": config.cpu_limit,
                                            "memory": config.memory_limit
                                        }
                                    ),
                                    env=[
                                        client.V1EnvVar(name=k, value=v)
                                        for k, v in (config.environment_vars or {}).items()
                                    ],
                                    liveness_probe=client.V1Probe(
                                        http_get=client.V1HTTPGetAction(
                                            path=config.health_check_path,
                                            port=config.port
                                        ),
                                        initial_delay_seconds=30,
                                        period_seconds=10
                                    ),
                                    readiness_probe=client.V1Probe(
                                        http_get=client.V1HTTPGetAction(
                                            path=config.health_check_path,
                                            port=config.port
                                        ),
                                        initial_delay_seconds=5,
                                        period_seconds=5
                                    )
                                )
                            ]
                        )
                    )
                )
            )
            
            # Cria deployment
            self.apps_v1.create_namespaced_deployment(namespace, deployment)
            print(f"✅ Deployment created: {config.app_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create deployment: {e}")
            return False
    
    def create_service(self, config: DeploymentConfig, namespace: str = "default", 
                      service_type: str = "LoadBalancer") -> bool:
        """Cria service Kubernetes"""
        if not self.v1:
            return False
        
        try:
            service = client.V1Service(
                metadata=client.V1ObjectMeta(
                    name=f"{config.app_name}-service",
                    namespace=namespace,
                    labels={"app": config.app_name}
                ),
                spec=client.V1ServiceSpec(
                    selector={"app": config.app_name},
                    ports=[
                        client.V1ServicePort(
                            port=80,
                            target_port=config.port,
                            protocol="TCP"
                        )
                    ],
                    type=service_type
                )
            )
            
            self.v1.create_namespaced_service(namespace, service)
            print(f"✅ Service created: {config.app_name}-service")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create service: {e}")
            return False
    
    def create_ingress(self, config: DeploymentConfig, domain: str, 
                      namespace: str = "default", tls: bool = True) -> bool:
        """Cria ingress Kubernetes"""
        if not self.networking_v1:
            return False
        
        try:
            ingress_rules = [
                client.V1IngressRule(
                    host=domain,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name=f"{config.app_name}-service",
                                        port=client.V1ServiceBackendPort(number=80)
                                    )
                                )
                            )
                        ]
                    )
                )
            ]
            
            ingress_spec = client.V1IngressSpec(rules=ingress_rules)
            
            if tls:
                ingress_spec.tls = [
                    client.V1IngressTLS(
                        hosts=[domain],
                        secret_name=f"{config.app_name}-tls"
                    )
                ]
            
            ingress = client.V1Ingress(
                metadata=client.V1ObjectMeta(
                    name=f"{config.app_name}-ingress",
                    namespace=namespace,
                    annotations={
                        "kubernetes.io/ingress.class": "nginx",
                        "cert-manager.io/cluster-issuer": "letsencrypt-prod" if tls else ""
                    }
                ),
                spec=ingress_spec
            )
            
            self.networking_v1.create_namespaced_ingress(namespace, ingress)
            print(f"✅ Ingress created: {config.app_name}-ingress")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create ingress: {e}")
            return False


class CloudDeploymentManager:
    """Gerenciador de deployment em nuvem"""
    
    def __init__(self, credentials: CloudCredentials):
        self.credentials = credentials
        self.provider = credentials.provider
        
        # Inicializa clientes específicos da nuvem
        if self.provider == CloudProvider.AWS:
            self._init_aws_client()
        elif self.provider == CloudProvider.GCP:
            self._init_gcp_client()
        elif self.provider == CloudProvider.AZURE:
            self._init_azure_client()
    
    def _init_aws_client(self):
        """Inicializa cliente AWS"""
        try:
            self.aws_session = boto3.Session(
                aws_access_key_id=self.credentials.credentials.get('access_key_id'),
                aws_secret_access_key=self.credentials.credentials.get('secret_access_key'),
                region_name=self.credentials.credentials.get('region', 'us-east-1')
            )
            
            self.ecs_client = self.aws_session.client('ecs')
            self.ecr_client = self.aws_session.client('ecr')
            self.eks_client = self.aws_session.client('eks')
            
            print("✅ AWS clients initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize AWS clients: {e}")
    
    def _init_gcp_client(self):
        """Inicializa cliente GCP"""
        try:
            if container_v1:
                credentials_info = self.credentials.credentials
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                self.gcp_client = container_v1.ClusterManagerClient(credentials=credentials)
                print("✅ GCP client initialized")
            else:
                print("⚠ GCP client not available")
                
        except Exception as e:
            logging.error(f"Failed to initialize GCP client: {e}")
    
    def _init_azure_client(self):
        """Inicializa cliente Azure"""
        try:
            if DefaultAzureCredential:
                credential = DefaultAzureCredential()
                subscription_id = self.credentials.credentials.get('subscription_id')
                self.azure_client = ContainerInstanceManagementClient(credential, subscription_id)
                print("✅ Azure client initialized")
            else:
                print("⚠ Azure client not available")
                
        except Exception as e:
            logging.error(f"Failed to initialize Azure client: {e}")
    
    def deploy_to_aws_ecs(self, config: DeploymentConfig, image_uri: str) -> bool:
        """Deploy para AWS ECS"""
        try:
            # Cria task definition
            task_definition = {
                'family': config.app_name,
                'networkMode': 'awsvpc',
                'requiresCompatibilities': ['FARGATE'],
                'cpu': '256',
                'memory': '512',
                'executionRoleArn': f"arn:aws:iam::{self.credentials.credentials.get('account_id')}:role/ecsTaskExecutionRole",
                'containerDefinitions': [
                    {
                        'name': config.app_name,
                        'image': image_uri,
                        'portMappings': [
                            {
                                'containerPort': config.port,
                                'protocol': 'tcp'
                            }
                        ],
                        'environment': [
                            {'name': k, 'value': v}
                            for k, v in (config.environment_vars or {}).items()
                        ],
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': f'/ecs/{config.app_name}',
                                'awslogs-region': self.credentials.credentials.get('region', 'us-east-1'),
                                'awslogs-stream-prefix': 'ecs'
                            }
                        }
                    }
                ]
            }
            
            # Registra task definition
            response = self.ecs_client.register_task_definition(**task_definition)
            task_definition_arn = response['taskDefinition']['taskDefinitionArn']
            
            # Cria ou atualiza service
            cluster_name = f"{config.app_name}-cluster"
            service_name = f"{config.app_name}-service"
            
            service_spec = {
                'cluster': cluster_name,
                'serviceName': service_name,
                'taskDefinition': task_definition_arn,
                'desiredCount': config.replicas,
                'launchType': 'FARGATE',
                'networkConfiguration': {
                    'awsvpcConfiguration': {
                        'subnets': self.credentials.credentials.get('subnets', []),
                        'securityGroups': self.credentials.credentials.get('security_groups', []),
                        'assignPublicIp': 'ENABLED'
                    }
                }
            }
            
            try:
                self.ecs_client.create_service(**service_spec)
                print(f"✅ ECS service created: {service_name}")
            except self.ecs_client.exceptions.ServiceNotFoundException:
                self.ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_name,
                    taskDefinition=task_definition_arn,
                    desiredCount=config.replicas
                )
                print(f"✅ ECS service updated: {service_name}")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to deploy to AWS ECS: {e}")
            return False


class CICDPipeline:
    """Pipeline de CI/CD"""
    
    def __init__(self, project_root: str, config_dir: str = None):
        self.project_root = Path(project_root)
        self.config_dir = Path(config_dir or self.project_root / ".bw_automate")
        self.config_dir.mkdir(exist_ok=True)
        
        self.docker_manager = DockerManager()
        self.k8s_manager = None
        self.cloud_manager = None
    
    def generate_dockerfile(self, config: DeploymentConfig, python_version: str = "3.9") -> str:
        """Gera Dockerfile otimizado"""
        dockerfile_content = f"""# Multi-stage build for BW Automate
FROM python:{python_version}-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:{python_version}-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash bw_automate

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/bw_automate/.local

# Set up application
WORKDIR /app
COPY --chown=bw_automate:bw_automate . .

# Switch to non-root user
USER bw_automate

# Add local Python packages to PATH
ENV PATH=/home/bw_automate/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{config.port}{config.health_check_path} || exit 1

# Expose port
EXPOSE {config.port}

# Start application
CMD ["python", "run_analysis.py", "--server", "--port", "{config.port}"]
"""
        
        dockerfile_path = self.project_root / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"✅ Dockerfile generated: {dockerfile_path}")
        return str(dockerfile_path)
    
    def generate_docker_compose(self, config: DeploymentConfig) -> str:
        """Gera docker-compose.yml"""
        compose_content = {
            'version': '3.8',
            'services': {
                config.app_name: {
                    'build': '.',
                    'ports': [f"{config.port}:{config.port}"],
                    'environment': config.environment_vars or {},
                    'restart': 'unless-stopped',
                    'healthcheck': {
                        'test': f"curl -f http://localhost:{config.port}{config.health_check_path} || exit 1",
                        'interval': '30s',
                        'timeout': '30s',
                        'retries': 3,
                        'start_period': '40s'
                    }
                },
                'redis': {
                    'image': 'redis:alpine',
                    'restart': 'unless-stopped',
                    'ports': ['6379:6379']
                },
                'postgres': {
                    'image': 'postgres:13',
                    'environment': {
                        'POSTGRES_DB': 'bw_automate',
                        'POSTGRES_USER': 'bw_automate',
                        'POSTGRES_PASSWORD': 'password'
                    },
                    'volumes': ['postgres_data:/var/lib/postgresql/data'],
                    'restart': 'unless-stopped',
                    'ports': ['5432:5432']
                }
            },
            'volumes': {
                'postgres_data': {}
            }
        }
        
        compose_path = self.project_root / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose_content, f, default_flow_style=False)
        
        print(f"✅ Docker Compose file generated: {compose_path}")
        return str(compose_path)
    
    def generate_kubernetes_manifests(self, config: DeploymentConfig, image_name: str) -> str:
        """Gera manifests Kubernetes"""
        k8s_dir = self.config_dir / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)
        
        # Deployment
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': config.app_name,
                'labels': {'app': config.app_name}
            },
            'spec': {
                'replicas': config.replicas,
                'selector': {'matchLabels': {'app': config.app_name}},
                'template': {
                    'metadata': {'labels': {'app': config.app_name}},
                    'spec': {
                        'containers': [{
                            'name': config.app_name,
                            'image': image_name,
                            'ports': [{'containerPort': config.port}],
                            'resources': {
                                'limits': {
                                    'cpu': config.cpu_limit,
                                    'memory': config.memory_limit
                                }
                            },
                            'env': [
                                {'name': k, 'value': v}
                                for k, v in (config.environment_vars or {}).items()
                            ],
                            'livenessProbe': {
                                'httpGet': {
                                    'path': config.health_check_path,
                                    'port': config.port
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': config.health_check_path,
                                    'port': config.port
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        # Service
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{config.app_name}-service",
                'labels': {'app': config.app_name}
            },
            'spec': {
                'selector': {'app': config.app_name},
                'ports': [{
                    'port': 80,
                    'targetPort': config.port,
                    'protocol': 'TCP'
                }],
                'type': 'LoadBalancer'
            }
        }
        
        # Ingress
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f"{config.app_name}-ingress",
                'annotations': {
                    'kubernetes.io/ingress.class': 'nginx',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod'
                }
            },
            'spec': {
                'tls': [{
                    'hosts': [f"{config.app_name}.example.com"],
                    'secretName': f"{config.app_name}-tls"
                }],
                'rules': [{
                    'host': f"{config.app_name}.example.com",
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': f"{config.app_name}-service",
                                    'port': {'number': 80}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        # Salva manifests
        with open(k8s_dir / "deployment.yaml", 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)
        
        with open(k8s_dir / "service.yaml", 'w') as f:
            yaml.dump(service, f, default_flow_style=False)
        
        with open(k8s_dir / "ingress.yaml", 'w') as f:
            yaml.dump(ingress, f, default_flow_style=False)
        
        print(f"✅ Kubernetes manifests generated: {k8s_dir}")
        return str(k8s_dir)
    
    def generate_github_actions(self, config: DeploymentConfig, image_registry: str) -> str:
        """Gera workflow GitHub Actions"""
        workflows_dir = self.project_root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        workflow = {
            'name': 'BW Automate CI/CD',
            'on': {
                'push': {'branches': ['main', 'develop']},
                'pull_request': {'branches': ['main']}
            },
            'env': {
                'REGISTRY': image_registry,
                'IMAGE_NAME': config.app_name
            },
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {'uses': 'actions/checkout@v3'},
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v4',
                            'with': {'python-version': '3.9'}
                        },
                        {
                            'name': 'Install dependencies',
                            'run': 'pip install -r requirements.txt'
                        },
                        {
                            'name': 'Run tests',
                            'run': 'python -m pytest tests/ -v'
                        },
                        {
                            'name': 'Run analysis',
                            'run': 'python run_analysis.py --validate'
                        }
                    ]
                },
                'build-and-deploy': {
                    'needs': 'test',
                    'runs-on': 'ubuntu-latest',
                    'if': "github.ref == 'refs/heads/main'",
                    'steps': [
                        {'uses': 'actions/checkout@v3'},
                        {
                            'name': 'Set up Docker Buildx',
                            'uses': 'docker/setup-buildx-action@v2'
                        },
                        {
                            'name': 'Login to Container Registry',
                            'uses': 'docker/login-action@v2',
                            'with': {
                                'registry': '${{ env.REGISTRY }}',
                                'username': '${{ secrets.REGISTRY_USERNAME }}',
                                'password': '${{ secrets.REGISTRY_PASSWORD }}'
                            }
                        },
                        {
                            'name': 'Extract metadata',
                            'id': 'meta',
                            'uses': 'docker/metadata-action@v4',
                            'with': {
                                'images': '${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}',
                                'tags': 'type=ref,event=branch\ntype=sha'
                            }
                        },
                        {
                            'name': 'Build and push Docker image',
                            'uses': 'docker/build-push-action@v4',
                            'with': {
                                'context': '.',
                                'push': True,
                                'tags': '${{ steps.meta.outputs.tags }}',
                                'labels': '${{ steps.meta.outputs.labels }}',
                                'cache-from': 'type=gha',
                                'cache-to': 'type=gha,mode=max'
                            }
                        },
                        {
                            'name': 'Deploy to Kubernetes',
                            'run': 'kubectl apply -f .bw_automate/kubernetes/',
                            'env': {
                                'KUBECONFIG': '${{ secrets.KUBECONFIG }}'
                            }
                        }
                    ]
                }
            }
        }
        
        workflow_path = workflows_dir / "ci-cd.yml"
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False)
        
        print(f"✅ GitHub Actions workflow generated: {workflow_path}")
        return str(workflow_path)
    
    def generate_requirements_txt(self) -> str:
        """Gera requirements.txt baseado nos imports do projeto"""
        requirements = [
            "fastapi>=0.68.0",
            "uvicorn[standard]>=0.15.0",
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=1.4.0",
            "pandas>=1.3.0",
            "plotly>=5.0.0",
            "dash>=2.0.0",
            "redis>=4.0.0",
            "celery>=5.2.0",
            "prometheus-client>=0.14.0",
            "pydantic>=1.8.0",
            "python-multipart>=0.0.5",
            "jinja2>=3.0.0",
            "cryptography>=3.4.0",
            "bcrypt>=3.2.0",
            "PyJWT>=2.3.0",
            "requests>=2.26.0",
            "pyyaml>=5.4.0",
            "python-dotenv>=0.19.0"
        ]
        
        requirements_path = self.project_root / "requirements.txt"
        with open(requirements_path, 'w') as f:
            f.write('\n'.join(requirements))
        
        print(f"✅ Requirements file generated: {requirements_path}")
        return str(requirements_path)
    
    def deploy(self, config: DeploymentConfig, 
              cloud_credentials: CloudCredentials = None) -> bool:
        """Executa deployment completo"""
        try:
            print(f"🚀 Starting deployment for {config.app_name} v{config.version}")
            
            # Gera arquivos de configuração
            self.generate_requirements_txt()
            dockerfile_path = self.generate_dockerfile(config)
            
            # Constrói imagem Docker
            image_name = f"{config.app_name}"
            if not self.docker_manager.build_image(dockerfile_path, image_name, config.version):
                return False
            
            # Deploy baseado no target
            if config.target == DeploymentTarget.DOCKER:
                return self._deploy_docker(config, image_name)
            elif config.target == DeploymentTarget.DOCKER_COMPOSE:
                return self._deploy_docker_compose(config)
            elif config.target == DeploymentTarget.KUBERNETES:
                return self._deploy_kubernetes(config, image_name)
            else:
                print(f"❌ Deployment target {config.target.value} not supported")
                return False
                
        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            return False
    
    def _deploy_docker(self, config: DeploymentConfig, image_name: str) -> bool:
        """Deploy local com Docker"""
        ports = {config.port: config.port}
        return self.docker_manager.run_container(
            image_name, config.version, 
            name=f"{config.app_name}-{config.environment.value}",
            ports=ports,
            environment=config.environment_vars
        )
    
    def _deploy_docker_compose(self, config: DeploymentConfig) -> bool:
        """Deploy com Docker Compose"""
        compose_path = self.generate_docker_compose(config)
        
        try:
            result = subprocess.run([
                "docker-compose", "-f", compose_path, "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Docker Compose deployment successful")
                return True
            else:
                print(f"❌ Docker Compose deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Docker Compose deployment error: {e}")
            return False
    
    def _deploy_kubernetes(self, config: DeploymentConfig, image_name: str) -> bool:
        """Deploy com Kubernetes"""
        if not self.k8s_manager:
            self.k8s_manager = KubernetesManager()
        
        if not self.k8s_manager.v1:
            print("❌ Kubernetes client not available")
            return False
        
        namespace = f"{config.app_name}-{config.environment.value}"
        
        # Cria namespace
        if not self.k8s_manager.create_namespace(namespace):
            return False
        
        # Cria deployment
        full_image_name = f"{image_name}:{config.version}"
        if not self.k8s_manager.create_deployment(config, full_image_name, namespace):
            return False
        
        # Cria service
        if not self.k8s_manager.create_service(config, namespace):
            return False
        
        print("✅ Kubernetes deployment successful")
        return True


class ProductionDeploymentSystem:
    """Sistema principal de deployment para produção"""
    
    def __init__(self, project_root: str, config_dir: str = None):
        self.project_root = Path(project_root)
        self.config_dir = Path(config_dir or self.project_root / ".bw_automate")
        self.config_dir.mkdir(exist_ok=True)
        
        self.cicd_pipeline = CICDPipeline(project_root, str(self.config_dir))
        
        # Configuração
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração de deployment"""
        config_file = self.config_dir / "deployment_config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "environments": {
                    "development": {
                        "cloud_provider": "local",
                        "target": "docker",
                        "replicas": 1,
                        "resources": {
                            "cpu_limit": "500m",
                            "memory_limit": "512Mi"
                        }
                    },
                    "staging": {
                        "cloud_provider": "aws",
                        "target": "kubernetes",
                        "replicas": 2,
                        "resources": {
                            "cpu_limit": "1000m",
                            "memory_limit": "1Gi"
                        }
                    },
                    "production": {
                        "cloud_provider": "aws",
                        "target": "kubernetes",
                        "replicas": 3,
                        "resources": {
                            "cpu_limit": "2000m",
                            "memory_limit": "2Gi"
                        }
                    }
                },
                "image_registry": "your-registry.com",
                "monitoring": {
                    "prometheus": True,
                    "grafana": True,
                    "alertmanager": True
                },
                "security": {
                    "vulnerability_scanning": True,
                    "secrets_management": True,
                    "network_policies": True
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def setup_production_environment(self, app_name: str, version: str,
                                   environment: EnvironmentType = EnvironmentType.PRODUCTION) -> DeploymentConfig:
        """Configura ambiente de produção"""
        env_config = self.config["environments"][environment.value]
        
        config = DeploymentConfig(
            app_name=app_name,
            version=version,
            environment=environment,
            target=DeploymentTarget(env_config["target"]),
            cloud_provider=CloudProvider(env_config["cloud_provider"]),
            region="us-east-1",  # TODO: Configurável
            replicas=env_config["replicas"],
            cpu_limit=env_config["resources"]["cpu_limit"],
            memory_limit=env_config["resources"]["memory_limit"],
            environment_vars={
                "ENVIRONMENT": environment.value,
                "LOG_LEVEL": "INFO" if environment == EnvironmentType.PRODUCTION else "DEBUG",
                "REDIS_URL": "redis://redis:6379",
                "DATABASE_URL": "postgresql://bw_automate:password@postgres:5432/bw_automate"
            }
        )
        
        return config
    
    def deploy_to_production(self, app_name: str, version: str) -> bool:
        """Deploy completo para produção"""
        print(f"🚀 Deploying {app_name} v{version} to PRODUCTION")
        
        # Configuração de produção
        config = self.setup_production_environment(app_name, version, EnvironmentType.PRODUCTION)
        
        # Gera todos os arquivos necessários
        self.cicd_pipeline.generate_requirements_txt()
        self.cicd_pipeline.generate_dockerfile(config)
        self.cicd_pipeline.generate_docker_compose(config)
        self.cicd_pipeline.generate_kubernetes_manifests(config, f"{app_name}:{version}")
        self.cicd_pipeline.generate_github_actions(config, self.config["image_registry"])
        
        # Executa deployment
        success = self.cicd_pipeline.deploy(config)
        
        if success:
            print("✅ Production deployment completed successfully!")
            self._post_deployment_tasks(config)
        else:
            print("❌ Production deployment failed!")
        
        return success
    
    def _post_deployment_tasks(self, config: DeploymentConfig):
        """Tarefas pós-deployment"""
        print("📋 Running post-deployment tasks...")
        
        # TODO: Implementar verificações de saúde
        # TODO: Configurar monitoramento
        # TODO: Enviar notificações
        
        print("✅ Post-deployment tasks completed")
    
    def rollback_deployment(self, app_name: str, target_version: str) -> bool:
        """Rollback para versão anterior"""
        print(f"🔄 Rolling back {app_name} to version {target_version}")
        
        # TODO: Implementar rollback automático
        
        return True


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BW Automate Production Deployment System")
    parser.add_argument("--project-root", "-p", default=".", help="Project root directory")
    parser.add_argument("--app-name", "-n", default="bw-automate", help="Application name")
    parser.add_argument("--version", "-v", default="1.0.0", help="Application version")
    parser.add_argument("--environment", "-e", choices=[env.value for env in EnvironmentType],
                       default="development", help="Target environment")
    parser.add_argument("--target", "-t", choices=[target.value for target in DeploymentTarget],
                       default="docker", help="Deployment target")
    parser.add_argument("--deploy", action="store_true", help="Execute deployment")
    parser.add_argument("--generate-only", action="store_true", help="Generate files only")
    
    args = parser.parse_args()
    
    # Cria sistema de deployment
    deployment_system = ProductionDeploymentSystem(args.project_root)
    
    if args.deploy:
        if args.environment == "production":
            success = deployment_system.deploy_to_production(args.app_name, args.version)
        else:
            config = deployment_system.setup_production_environment(
                args.app_name, args.version, EnvironmentType(args.environment)
            )
            config.target = DeploymentTarget(args.target)
            
            success = deployment_system.cicd_pipeline.deploy(config)
        
        if success:
            print("🎉 Deployment completed successfully!")
        else:
            print("💥 Deployment failed!")
    
    elif args.generate_only:
        config = deployment_system.setup_production_environment(
            args.app_name, args.version, EnvironmentType(args.environment)
        )
        config.target = DeploymentTarget(args.target)
        
        deployment_system.cicd_pipeline.generate_requirements_txt()
        deployment_system.cicd_pipeline.generate_dockerfile(config)
        deployment_system.cicd_pipeline.generate_docker_compose(config)
        deployment_system.cicd_pipeline.generate_kubernetes_manifests(config, f"{args.app_name}:{args.version}")
        deployment_system.cicd_pipeline.generate_github_actions(config, "your-registry.com")
        
        print("✅ Configuration files generated!")
    
    else:
        print("Use --deploy or --generate-only to perform actions")
    
    print("🚀 Production Deployment System ready")