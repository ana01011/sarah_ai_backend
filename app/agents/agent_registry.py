"""
Agent Registry - Central management with strict domain routing
"""

from typing import Dict, Optional, List
import logging
from app.agents.executives.ceo_agent import CEOAgent
from app.agents.executives.cto_agent import CTOAgent
from app.agents.executives.cfo_agent import CFOAgent
from app.agents.executives.cmo_agent import CMOAgent
from app.agents.executives.coo_agent import COOAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for managing all agents with domain routing"""
    
    def __init__(self):
        self.agents = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all executive agents"""
        # Create each agent
        agents_to_register = [
            CEOAgent(),
            CTOAgent(),
            CFOAgent(),
            CMOAgent(),
            COOAgent()
        ]
        
        # Register each agent
        for agent in agents_to_register:
            self.agents[agent.id] = agent
            logger.info(f"Registered {agent.name} ({agent.role})")
    
    def get_agent(self, agent_id: str):
        """Get specific agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """List all available agents"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def route_to_agent(self, message: str, preferred_agent: Optional[str] = None):
        """Route message to appropriate agent based on domain"""
        
        # If specific agent requested, check if message is in their domain
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
            if agent.is_in_domain(message):
                logger.info(f"Routing to {agent.name} (requested)")
                return agent
            else:
                logger.warning(f"{agent.name} rejected out-of-domain query")
                # Find appropriate agent
                for other_agent in self.agents.values():
                    if other_agent.is_in_domain(message):
                        logger.info(f"Redirecting from {agent.name} to {other_agent.name}")
                        return other_agent
        
        # Auto-detect best agent based on domain
        for agent in self.agents.values():
            if agent.is_in_domain(message):
                logger.info(f"Auto-routing to {agent.name} based on domain match")
                return agent
        
        # Default to CEO for general queries
        logger.info("No domain match, defaulting to CEO")
        return self.agents.get("ceo")
    
    def get_agent_for_department(self, department: str):
        """Get agent by department name"""
        department_lower = department.lower()
        for agent in self.agents.values():
            if department_lower in agent.department.lower():
                return agent
        return None

# Global registry instance
agent_registry = AgentRegistry()
