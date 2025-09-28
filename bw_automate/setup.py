#!/usr/bin/env python3
"""
BW_AUTOMATE - Enterprise PostgreSQL and Airflow Code Analysis System
Setup script for production deployment
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
def read_requirements():
    """Read requirements.txt and return list of requirements"""
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    requirements = []
    optional_requirements = {}
    current_section = 'core'
    
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        if 'Optional:' in line:
            current_section = line.split('Optional:')[1].strip().lower().replace(' ', '_')
            optional_requirements[current_section] = []
            continue
        if 'Development Dependencies' in line:
            current_section = 'dev'
            optional_requirements[current_section] = []
            continue
        
        if current_section == 'core':
            requirements.append(line)
        else:
            if current_section not in optional_requirements:
                optional_requirements[current_section] = []
            optional_requirements[current_section].append(line)
    
    return requirements, optional_requirements

core_requirements, extras_require = read_requirements()

setup(
    name="bw-automate",
    version="3.0.0",
    author="BW Development Team",
    author_email="dev@bw-automate.com",
    description="Enterprise PostgreSQL and Airflow Code Analysis System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/decolee/bw_automate",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Software Development :: Code Generators",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=core_requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "bw-automate=BW_UNIFIED_CLI:main",
            "bw-postgresql=POSTGRESQL_TABLE_MAPPER:main",
            "bw-airflow=AIRFLOW_INTEGRATION_CLI:main",
            "bw-test=COMPREHENSIVE_TEST_SUITE:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
    },
    project_urls={
        "Bug Reports": "https://github.com/decolee/bw_automate/issues",
        "Source": "https://github.com/decolee/bw_automate",
        "Documentation": "https://github.com/decolee/bw_automate/blob/master/PRODUCTION_READY_GUIDE.md",
    },
)