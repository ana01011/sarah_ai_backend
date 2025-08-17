#!/bin/bash

echo "🤖 Setting up agent system..."

# Create directory
mkdir -p app/agents

# Create __init__.py
cat > app/agents/__init__.py << 'INIT_EOF'
"""
Intelligent Agent System for Sarah AI
"""

from .base import Agent, AgentResponse

__all__ = ['Agent', 'AgentResponse']
INIT_EOF

echo "✅ Created __init__.py"

# Add to requirements.txt if not already there
grep -q "black" requirements.txt || echo "black==23.12.1" >> requirements.txt
grep -q "autopep8" requirements.txt || echo "autopep8==2.0.4" >> requirements.txt

echo "✅ Updated requirements.txt"
echo "🎉 Agent system files created!"
echo ""
echo "Next steps:"
echo "1. Review the files in app/agents/"
echo "2. git add -A"
echo "3. git commit -m 'Add agent system'"
echo "4. git push origin master"
