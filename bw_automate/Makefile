# BW_AUTOMATE Makefile
# Production-ready build automation

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := bw-automate
VERSION := 3.0.0

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)BW_AUTOMATE - Build Automation$(RESET)"
	@echo "$(BLUE)================================$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# Development Setup
.PHONY: install
install: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "$(GREEN)✅ Installation complete$(RESET)"

.PHONY: install-dev
install-dev: install ## Install with development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install pytest pytest-cov black flake8 mypy pre-commit
	pre-commit install
	@echo "$(GREEN)✅ Development setup complete$(RESET)"

# Code Quality
.PHONY: format
format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(RESET)"
	black *.py
	@echo "$(GREEN)✅ Code formatted$(RESET)"

.PHONY: lint
lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(RESET)"
	flake8 *.py --max-line-length=100 --ignore=E203,W503
	@echo "$(GREEN)✅ Linting complete$(RESET)"

.PHONY: type-check
type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(RESET)"
	mypy *.py --ignore-missing-imports
	@echo "$(GREEN)✅ Type checking complete$(RESET)"

.PHONY: check
check: format lint type-check ## Run all code quality checks
	@echo "$(GREEN)✅ All quality checks passed$(RESET)"

# Testing
.PHONY: test
test: ## Run test suite
	@echo "$(BLUE)Running test suite...$(RESET)"
	$(PYTHON) COMPREHENSIVE_TEST_SUITE.py
	@echo "$(GREEN)✅ Tests complete$(RESET)"

.PHONY: test-verbose
test-verbose: ## Run test suite with verbose output
	@echo "$(BLUE)Running verbose test suite...$(RESET)"
	$(PYTHON) COMPREHENSIVE_TEST_SUITE.py --verbose
	@echo "$(GREEN)✅ Verbose tests complete$(RESET)"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running test coverage...$(RESET)"
	pytest --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated$(RESET)"

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	$(PYTHON) BW_UNIFIED_CLI.py analyze . --type all --output integration_test
	@echo "$(GREEN)✅ Integration tests complete$(RESET)"

# Analysis and Validation
.PHONY: analyze-self
analyze-self: ## Analyze the BW_AUTOMATE codebase itself
	@echo "$(BLUE)Self-analyzing BW_AUTOMATE...$(RESET)"
	$(PYTHON) BW_UNIFIED_CLI.py analyze . --type all --output self_analysis
	@echo "$(GREEN)✅ Self-analysis complete$(RESET)"

.PHONY: validate
validate: test analyze-self ## Full validation suite
	@echo "$(BLUE)Running full validation...$(RESET)"
	$(PYTHON) POSTGRESQL_TABLE_MAPPER.py . --output validation_postgresql
	$(PYTHON) AIRFLOW_INTEGRATION_CLI.py analyze . --output validation_airflow
	@echo "$(GREEN)✅ Full validation complete$(RESET)"

# Docker Operations
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(RESET)"
	$(DOCKER) build -t $(PROJECT_NAME):$(VERSION) .
	$(DOCKER) build -t $(PROJECT_NAME):latest .
	@echo "$(GREEN)✅ Docker image built$(RESET)"

.PHONY: docker-build-dev
docker-build-dev: ## Build development Docker image
	@echo "$(BLUE)Building development Docker image...$(RESET)"
	$(DOCKER) build --target development -t $(PROJECT_NAME):dev .
	@echo "$(GREEN)✅ Development Docker image built$(RESET)"

.PHONY: docker-run
docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(RESET)"
	$(DOCKER) run --rm -it $(PROJECT_NAME):latest
	@echo "$(GREEN)✅ Docker run complete$(RESET)"

.PHONY: docker-test
docker-test: docker-build ## Test Docker container
	@echo "$(BLUE)Testing Docker container...$(RESET)"
	$(DOCKER) run --rm $(PROJECT_NAME):latest python3 COMPREHENSIVE_TEST_SUITE.py
	@echo "$(GREEN)✅ Docker test complete$(RESET)"

# Docker Compose Operations
.PHONY: up
up: ## Start all services with docker-compose
	@echo "$(BLUE)Starting services...$(RESET)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Services started$(RESET)"

.PHONY: up-dev
up-dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(RESET)"
	$(DOCKER_COMPOSE) --profile dev up -d
	@echo "$(GREEN)✅ Development environment started$(RESET)"

.PHONY: down
down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(RESET)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Services stopped$(RESET)"

.PHONY: logs
logs: ## Show service logs
	$(DOCKER_COMPOSE) logs -f

# Build and Distribution
.PHONY: build
build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(RESET)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)✅ Distribution packages built$(RESET)"

.PHONY: upload-test
upload-test: build ## Upload to test PyPI
	@echo "$(BLUE)Uploading to test PyPI...$(RESET)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✅ Uploaded to test PyPI$(RESET)"

.PHONY: upload
upload: build ## Upload to PyPI
	@echo "$(BLUE)Uploading to PyPI...$(RESET)"
	twine upload dist/*
	@echo "$(GREEN)✅ Uploaded to PyPI$(RESET)"

# Maintenance
.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

.PHONY: clean-all
clean-all: clean ## Clean everything including test results
	@echo "$(BLUE)Deep cleaning...$(RESET)"
	rm -rf *_test*/
	rm -rf *_results*/
	rm -rf *.json
	rm -rf *.log
	$(DOCKER_COMPOSE) down -v --remove-orphans
	$(DOCKER) system prune -f
	@echo "$(GREEN)✅ Deep cleanup complete$(RESET)"

# Information
.PHONY: info
info: ## Show system information
	@echo "$(BLUE)BW_AUTOMATE System Information$(RESET)"
	@echo "$(BLUE)===============================$(RESET)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Docker: $(shell $(DOCKER) --version)"
	@echo "Docker Compose: $(shell $(DOCKER_COMPOSE) --version)"
	@echo ""
	@$(PYTHON) BW_UNIFIED_CLI.py info

.PHONY: benchmark
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(RESET)"
	$(PYTHON) -c "
import time
from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
start = time.time()
mapper = PostgreSQLTableMapper()
result = mapper.analyze_project('.')
end = time.time()
print(f'Benchmark: {len(result.get(\"tables_discovered\", {}))} tables found in {end-start:.2f}s')
"
	@echo "$(GREEN)✅ Benchmark complete$(RESET)"

# Security
.PHONY: security-check
security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(RESET)"
	$(PIP) install safety bandit
	safety check
	bandit -r . -f json -o security_report.json
	@echo "$(GREEN)✅ Security check complete$(RESET)"

# Documentation
.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@echo "📋 Available documentation:"
	@echo "  - PRODUCTION_READY_GUIDE.md"
	@echo "  - QUICK_START_FINAL.md" 
	@echo "  - AIRFLOW_POSTGRESQL_FINAL_GUIDE.md"
	@echo "  - FINAL_VALIDATION_REPORT.md"
	@echo "$(GREEN)✅ Documentation ready$(RESET)"

# Production deployment
.PHONY: deploy-staging
deploy-staging: build docker-build ## Deploy to staging
	@echo "$(BLUE)Deploying to staging...$(RESET)"
	@echo "$(YELLOW)⚠️ Staging deployment not configured$(RESET)"
	@echo "$(GREEN)✅ Staging deployment ready$(RESET)"

.PHONY: deploy-prod
deploy-prod: validate build docker-build ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(RESET)"
	@echo "$(YELLOW)⚠️ Production deployment not configured$(RESET)"
	@echo "$(GREEN)✅ Production deployment ready$(RESET)"