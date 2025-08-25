@app.get("/api/debug/memory/{user_id}")
async def debug_memory(user_id: str):
    """Debug endpoint to check memory state"""
    return {
        "user_id": user_id,
        "memory": USER_MEMORY.get(user_id, []),
        "count": len(USER_MEMORY.get(user_id, [])),
        "last_3": USER_MEMORY.get(user_id, [])[-3:] if user_id in USER_MEMORY else []
    }

@app.post("/api/test/memory")
async def test_memory():
    """Test memory with a scripted conversation"""
    test_id = "test_user"
    
    # Clear existing memory
    USER_MEMORY[test_id] = []
    
    # Test conversation
    test_exchanges = [
        ("My name is Alice", "Nice to meet you, Alice!"),
        ("What is my name?", "Your name is Alice."),
        ("I like pizza", "Pizza is great!"),
        ("What do I like?", "You mentioned you like pizza.")
    ]
    
    for user_msg, expected in test_exchanges:
        USER_MEMORY[test_id].append({
            "user": user_msg,
            "assistant": expected,
            "timestamp": datetime.now().isoformat()
        })
    
    return {"test": "complete", "memory": USER_MEMORY[test_id]}
