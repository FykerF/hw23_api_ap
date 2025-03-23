#!/bin/bash
# Script to create the package structure for the URL shortener project

# Create main directories
mkdir -p api/{routes,controllers,middleware,models}
mkdir -p core
mkdir -p services
mkdir -p utils
mkdir -p tests
mkdir -p alembic/versions
mkdir -p docker
mkdir -p scripts

# Create __init__.py files for Python packages
touch api/__init__.py
touch api/routes/__init__.py
touch api/controllers/__init__.py
touch api/middleware/__init__.py
touch api/models/__init__.py
touch core/__init__.py
touch services/__init__.py
touch utils/__init__.py
touch tests/__init__.py
touch alembic/versions/__init__.py

# Make start.sh executable
chmod +x scripts/start.sh

echo "Package structure created successfully!"