from llama_cpp import Llama
import time

print("Testing with minimal settings...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=512,  # Smaller context
    n_threads=4,  # Fewer threads
    verbose=True  # See what's happening
)

start = time.time()
response = model("Hi", max_tokens=5, temperature=0.1)
print(f"Time: {time.time() - start:.2f}s")
print(f"Response: {response['choices'][0]['text']}")
