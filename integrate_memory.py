#!/usr/bin/env python3
import sys

# Read the current main.py
with open('main.py', 'r') as f:
    lines = f.readlines()

# Find where to insert the enhanced memory code
insert_index = 0
for i, line in enumerate(lines):
    if 'USER_MEMORY = {}' in line:
        insert_index = i + 1
        break

# Insert the enhanced memory system
enhanced_code = open('enhanced_memory_system.py', 'r').read()

# Find and replace the chat_with_memory function
new_lines = []
skip_old_function = False
for i, line in enumerate(lines):
    if '@app.post("/api/chat/with-memory")' in line:
        skip_old_function = True
        # Insert new function
        new_lines.append('@app.post("/api/chat/with-memory")\n')
        new_lines.append('async def chat_with_memory(request: ChatRequest):\n')
        new_lines.append('    """Enhanced chat with robust memory and context"""\n')
        new_lines.append('    return await chat_with_enhanced_memory(request)\n')
        new_lines.append('\n')
        continue
    
    if skip_old_function:
        # Skip until we find the next function or endpoint
        if line.startswith('@app.') or line.startswith('def ') and 'chat_with_memory' not in line:
            skip_old_function = False
            new_lines.append(line)
        continue
    else:
        new_lines.append(line)

# Write back
with open('main.py', 'w') as f:
    f.writelines(new_lines)

print("Enhanced memory system integrated!")
