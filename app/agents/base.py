"""
Base Agent class with core functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AgentResponse(BaseModel):
    """Structured response from an agent"""
    agent: str
    role: str
    response: str
    confidence: float
    tools_used: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()
    suggestions: List[str] = []

class Agent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description
        self.tools = {}
        self.context = []
        self.max_context = 10
        
    @abstractmethod
    async def process(self, message: str, **kwargs) -> AgentResponse:
        """Process a message and return a response"""
        pass
    
    def add_tool(self, name: str, func: callable):
        """Register a tool for this agent"""
        self.tools[name] = func
        logger.info(f"Added tool '{name}' to agent '{self.name}'")
    
    def add_context(self, message: str, response: str):
        """Add to conversation context"""
        self.context.append({
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.context) > self.max_context:
            self.context.pop(0)
    
    def get_context_string(self) -> str:
        """Get formatted context for prompt"""
        if not self.context:
            return ""
        
        context_str = "Previous conversation:\n"
        for ctx in self.context[-3:]:  # Last 3 exchanges
            context_str += f"User: {ctx['message']}\n"
            context_str += f"Assistant: {ctx['response']}\n"
        return context_str
    
    def format_prompt(self, message: str) -> str:
        """Format prompt with agent personality and context"""
        context = self.get_context_string()
        
        return f"""<|im_start|>system
You are {self.name}, a specialized {self.role}.
{self.description}

Available tools: {', '.join(self.tools.keys()) if self.tools else 'None'}

{context}
<|im_end|>
<|im_start|>user
{message}
<|im_end|>
<|im_start|>assistant
"""
