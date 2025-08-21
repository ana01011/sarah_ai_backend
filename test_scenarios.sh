#!/bin/bash

echo "🎭 TESTING DIFFERENT CONVERSATION SCENARIOS"
echo "=========================================="

# Scenario 1: Personal Assistant
echo -e "\n📝 Scenario 1: Personal Assistant"
USER1="personal_$(date +%s)"

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I need to buy milk, eggs, and bread tomorrow\", \"user_id\": \"$USER1\"}" | jq -r .response

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What did I say I need to buy?\", \"user_id\": \"$USER1\"}" | jq -r .response

# Scenario 2: Learning Assistant
echo -e "\n📚 Scenario 2: Learning Assistant"
USER2="learner_$(date +%s)"

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I'm learning Python and I'm currently stuck on decorators\", \"user_id\": \"$USER2\"}" | jq -r .response

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What programming concept am I struggling with?\", \"user_id\": \"$USER2\"}" | jq -r .response

# Scenario 3: Project Assistant
echo -e "\n💼 Scenario 3: Project Assistant"
USER3="project_$(date +%s)"

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"I'm working on a React app with TypeScript for an e-commerce platform\", \"user_id\": \"$USER3\"}" | jq -r .response

curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What technology stack am I using for my project?\", \"user_id\": \"$USER3\"}" | jq -r .response

echo -e "\n✅ All scenarios tested!"
