#!/usr/bin/env python3

with open('main.py', 'r') as f:
    lines = f.readlines()

# Find and replace the broken chat_with_memory function
new_function = '''@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Chat with working memory"""
    start = time.time()
    user_id = request.user_id or "default"

    # Initialize user memory if needed
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []

    # Check for identity question
    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers."
    else:
        # Build context-aware prompt
        prompt = ""
        
        # Add conversation history
        if USER_MEMORY[user_id]:
            prompt = "You are Sarah AI. Remember this conversation:\\n\\n"
            for exchange in USER_MEMORY[user_id][-5:]:  # Last 5 exchanges
                prompt += f"User: {exchange['user']}\\n"
                prompt += f"Sarah: {exchange['assistant']}\\n"
            prompt += "\\nContinue the conversation naturally:\\n"
        
        prompt += f"User: {request.message}\\nSarah:"

        # Generate response
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\\n\\n"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
        response_text = clean_response(response_text)

    # Store in memory
    USER_MEMORY[user_id].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })

    # Keep only last 10 exchanges
    if len(USER_MEMORY[user_id]) > 10:
        USER_MEMORY[user_id] = USER_MEMORY[user_id][-10:]

    elapsed = time.time() - start

    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(USER_MEMORY[user_id]),
        "stats": {
            "time": round(elapsed, 3),
            "context_used": len(USER_MEMORY[user_id]) > 1,
            "tokens_per_second": round(len(response_text.split())/elapsed, 1) if elapsed > 0 else 0
        }
    }

'''

# Find the chat_with_memory function and replace it
in_function = False
new_lines = []
skip_lines = 0

for i, line in enumerate(lines):
    if skip_lines > 0:
        skip_lines -= 1
        continue
        
    if '@app.post("/api/chat/with-memory")' in line:
        # Start replacing
        in_function = True
        # Add the new function
        new_lines.append(new_function)
        # Skip until we find the next function or endpoint
        for j in range(i+1, len(lines)):
            if lines[j].startswith('@app.') or (lines[j].startswith('def ') and 'chat_with_memory' not in lines[j]):
                skip_lines = j - i - 1
                break
            elif lines[j].startswith('if __name__'):
                skip_lines = j - i - 1
                break
        continue
    
    if not in_function:
        new_lines.append(line)

# Write back
with open('main.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed chat_with_memory function!")
