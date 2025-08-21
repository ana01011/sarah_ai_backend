"""
Base Agent Class with Strict Domain Enforcement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseExecutiveAgent(ABC):
    """Base class for all executive agents with strict domain enforcement"""
    
    def __init__(self):
        self.id = self._get_id()
        self.name = self._get_name()
        self.role = self._get_role()
        self.department = self._get_department()
        self.avatar = self._get_avatar()
        self.description = self._get_description()
        self.specialties = self._get_specialties()
        self.level = "Executive"
        self.metrics = self._initialize_metrics()
        self.domain_keywords = self._get_domain_keywords()
        self.forbidden_domains = self._get_forbidden_domains()
    
    @abstractmethod
    def _get_id(self) -> str:
        """Return agent ID"""
        pass
    
    @abstractmethod
    def _get_name(self) -> str:
        """Return agent name"""
        pass
    
    @abstractmethod
    def _get_role(self) -> str:
        """Return agent role"""
        pass
    
    @abstractmethod
    def _get_department(self) -> str:
        """Return agent department"""
        pass
    
    @abstractmethod
    def _get_avatar(self) -> str:
        """Return agent avatar emoji"""
        pass
    
    @abstractmethod
    def _get_description(self) -> str:
        """Return agent description"""
        pass
    
    @abstractmethod
    def _get_specialties(self) -> List[str]:
        """Return agent specialties"""
        pass
    
    @abstractmethod
    def _get_domain_keywords(self) -> List[str]:
        """Return keywords that belong to this agent's domain"""
        pass
    
    @abstractmethod
    def _get_forbidden_domains(self) -> List[str]:
        """Return domains this agent should NOT discuss"""
        pass
    
    @abstractmethod
    def get_domain_prompt(self) -> str:
        """Return domain-specific prompt instructions"""
        pass
    
    def _initialize_metrics(self) -> Dict:
        """Initialize agent metrics"""
        return {
            "performance": 95,
            "efficiency": 93,
            "experience": 97,
            "availability": 94
        }
    
    def is_in_domain(self, message: str) -> bool:
        """Check if message is within agent's domain"""
        message_lower = message.lower()
        
        # Check if message contains domain keywords
        for keyword in self.domain_keywords:
            if keyword.lower() in message_lower:
                return True
        
        # Check if message is asking about forbidden domains
        for forbidden in self.forbidden_domains:
            if forbidden.lower() in message_lower:
                logger.warning(f"{self.name} received out-of-domain query about {forbidden}")
                return False
        
        return False
    
    def get_system_prompt(self, message: str) -> str:
        """Generate system prompt with strict domain enforcement"""
        
        # Check domain relevance
        if not self.is_in_domain(message) and self.id != "general":
            redirect_prompt = self._get_redirect_prompt(message)
            if redirect_prompt:
                return redirect_prompt
        
        specialties_str = ", ".join(self.specialties)
        
        base_prompt = f"""You are {self.name}, the {self.role} of the company.
Department: {self.department}
Core Specialties: {specialties_str}

STRICT DOMAIN RULES:
1. You ONLY provide expertise in {self.department} matters
2. You MUST NOT provide advice outside your domain
3. If asked about {', '.join(self.forbidden_domains[:3])}, politely redirect to the appropriate executive
4. Stay focused on your core competencies

{self.get_domain_prompt()}

If someone asks about topics outside your expertise, respond with:
"That's outside my domain as {self.role}. I recommend consulting our [appropriate executive] for expert guidance on that matter. 
However, I can help you with {self.department.lower()} related aspects if relevant."

Remember: You are a domain expert. Maintain strict boundaries while being helpful within your scope."""
        
        return base_prompt
    
    def _get_redirect_prompt(self, message: str) -> Optional[str]:
        """Get redirect prompt for out-of-domain queries"""
        message_lower = message.lower()
        
        redirects = {
            "finance": "CFO Robert Williams",
            "technology": "CTO Dr. Sarah Johnson",
            "marketing": "CMO Jessica Martinez",
            "operations": "COO David Thompson",
            "hr": "CHRO Amanda Foster",
            "security": "CISO James Wilson",
            "data": "CDO Dr. Lisa Park"
        }
        
        for domain, executive in redirects.items():
            if domain in message_lower and domain not in self.department.lower():
                return f"""You are {self.name}, the {self.role}.
The user is asking about {domain}, which is outside your domain.
Politely redirect them to {executive} while offering to help with any {self.department.lower()} aspects."""
        
        return None
    
    def get_suggestions(self) -> List[str]:
        """Get domain-specific suggestions"""
        return [
            f"📊 {self.department} overview",
            f"💡 {self.specialties[0]} insights",
            f"🎯 {self.role.split()[0]} recommendations",
            f"📈 Department performance"
        ]
    
    def to_dict(self) -> Dict:
        """Convert agent to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "avatar": self.avatar,
            "description": self.description,
            "specialties": self.specialties,
            "level": self.level,
            "metrics": self.metrics
        }
