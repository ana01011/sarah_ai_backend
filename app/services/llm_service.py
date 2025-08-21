"""
LLM Service for model management
"""
from llama_cpp import Llama
import os
from typing import Optional

class LLMService:
    def __init__(self):
        self.model: Optional[Llama] = None
        self.model_path = os.getenv("MODEL_PATH", "openhermes-2.5-mistral-7b.Q4_K_M.gguf")
        
    def load_model(self):
        """Load the LLM model"""
        if not self.model:
            print(f"🚀 Loading model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=int(os.getenv("MODEL_CONTEXT_SIZE", 1024)),
                n_threads=int(os.getenv("MODEL_THREADS", 4)),
                n_batch=int(os.getenv("MODEL_BATCH_SIZE", 256)),
                use_mmap=True,
                verbose=False
            )
            print("✅ Model loaded successfully")
    
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.8) -> str:
        """Generate response from model"""
        if not self.model:
            self.load_model()
        
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["User:", "Human:", "\n\n"],
            echo=False
        )
        
        return response['choices'][0]['text'].strip()

# Global LLM service instance
llm_service = LLMService()
