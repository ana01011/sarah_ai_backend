#!/bin/bash

echo "🧠 Testing Fixed Memory System"
echo "=============================="

USER_ID="memory_test_$(date +%s)"

# Test 1: Introduction
echo -e "\n1️⃣ Introducing myself..."
response1=$(curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Hi! My name is Alex and I am 28 years old. I work as a data scientist.\",
    \"user_id\": \"$USER_ID\"
  }")
echo "Response: $(echo $response1 | jq -r .response)"

# Test 2: Name recall
echo -e "\n2️⃣ Testing name recall..."
response2=$(curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What is my name?\",
    \"user_id\": \"$USER_ID\"
  }")
echo "Response: $(echo $response2 | jq -r .response)"
echo "Memory used: $(echo $response2 | jq -r .stats.context_used)"

# Test 3: Age recall
echo -e "\n3️⃣ Testing age recall..."
response3=$(curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"How old am I?\",
    \"user_id\": \"$USER_ID\"
  }")
echo "Response: $(echo $response3 | jq -r .response)"

# Test 4: Job recall
echo -e "\n4️⃣ Testing job recall..."
response4=$(curl -s -X POST http://localhost:8000/api/chat/with-memory \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What do I do for work?\",
    \"user_id\": \"$USER_ID\"
  }")
echo "Response: $(echo $response4 | jq -r .response)"

# Check full memory
echo -e "\n5️⃣ Checking stored memory..."
curl -s http://localhost:8000/api/memory/$USER_ID | jq .

echo -e "\n✅ Test Complete!"
