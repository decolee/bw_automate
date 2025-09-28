# Multi-stage Dockerfile for BW_AUTOMATE
# Production-ready container with minimal footprint

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG INSTALL_DEV=false

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY setup.py .
COPY README.md .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install core requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install development dependencies if needed
RUN if [ "$INSTALL_DEV" = "true" ] ; then \
    pip install --no-cache-dir pytest pytest-cov black flake8 ; \
    fi

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r bwuser && useradd -r -g bwuser bwuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/results && \
    chown -R bwuser:bwuser /app

# Switch to non-root user
USER bwuser

# Install the package
RUN pip install --no-deps -e .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "from BW_UNIFIED_CLI import BWUnifiedCLI; print('OK')" || exit 1

# Default command
CMD ["python3", "BW_UNIFIED_CLI.py", "--help"]

# Stage 3: Development stage
FROM production as development

# Switch back to root to install dev tools
USER root

# Install development tools
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    ipython \
    jupyter

# Switch back to bwuser
USER bwuser

# Set development environment variables
ENV ENVIRONMENT=development
ENV DEBUG=true

# Expose port for development server (if needed)
EXPOSE 8000

# Development command
CMD ["python3", "COMPREHENSIVE_TEST_SUITE.py"]