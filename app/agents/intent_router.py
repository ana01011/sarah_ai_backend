from typing import Dict, List, Optional, Tuple
import re
from enum import Enum

class IntentType(Enum):
    GREETING = "greeting"
    QUESTION = "question"
    TASK = "task"
    CONVERSATION = "conversation"
    TECHNICAL = "technical"
    BUSINESS = "business"
    CREATIVE = "creative"
    HELP = "help"

class IntentRouter:
    """Advanced intent detection and routing"""
    
    def __init__(self):
        self.intent_patterns = {
            IntentType.GREETING: [
                r'\b(hello|hi|hey|greetings|good morning|good evening)\b',
            ],
            IntentType.QUESTION: [
                r'\b(what|when|where|who|why|how|is|are|can|could|would)\b.*\?',
            ],
            IntentType.TASK: [
                r'\b(create|make|build|generate|write|develop|design)\b',
            ],
            IntentType.TECHNICAL: [
                r'\b(code|debug|error|api|function|algorithm|database)\b',
            ],
            IntentType.BUSINESS: [
                r'\b(revenue|sales|market|strategy|customer|profit)\b',
            ],
            IntentType.CREATIVE: [
                r'\b(design|idea|brainstorm|creative|innovate|imagine)\b',
            ],
            IntentType.HELP: [
                r'\b(help|assist|support|guide|explain)\b',
            ]
        }
        
        self.agent_mapping = {
            IntentType.TECHNICAL: "cto",
            IntentType.BUSINESS: "ceo",
            IntentType.CREATIVE: "designer",
            IntentType.GREETING: "sarah",
            IntentType.QUESTION: "sarah",
            IntentType.TASK: "sarah",
            IntentType.HELP: "sarah"
        }
    
    async def detect_intent(self, message: str) -> Tuple[IntentType, float]:
        """Detect primary intent from message"""
        message_lower = message.lower()
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            if score > 0:
                intent_scores[intent_type] = score / len(patterns)
        
        if not intent_scores:
            return IntentType.CONVERSATION, 0.5
        
        # Get highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    async def route_to_agent(self, message: str) -> str:
        """Determine which agent should handle the message"""
        intent, confidence = await self.detect_intent(message)
        
        if confidence < 0.3:
            return "sarah"  # Default to Sarah for low confidence
        
        return self.agent_mapping.get(intent, "sarah")
    
    async def extract_entities(self, message: str) -> Dict:
        """Extract entities from message"""
        entities = {
            "numbers": re.findall(r'\b\d+\b', message),
            "emails": re.findall(r'\S+@\S+', message),
            "urls": re.findall(r'http[s]?://\S+', message),
            "dates": re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', message)
        }
        return entities
