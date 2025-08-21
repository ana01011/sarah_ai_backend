#!/bin/bash

# Create all directories
mkdir -p app/{core,models,database,services,agents,api,middleware,utils,background}
mkdir -p app/database/{repositories,migrations}
mkdir -p app/services/{auth,user,chat,memory,agent}
mkdir -p app/agents/{base,personalities}
mkdir -p app/api/v1/routers
mkdir -p app/utils/{extractors,validators,helpers}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p scripts/{setup,migration,deployment}
mkdir -p configs
mkdir -p logs

# Create __init__.py files
find app -type d -exec touch {}/__init__.py \;

echo "✅ Directory structure created"
