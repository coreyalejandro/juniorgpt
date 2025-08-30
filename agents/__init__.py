"""
Self-contained agent framework for JuniorGPT
Each agent is a standalone application that can be used independently
"""
from .base_agent import BaseAgent, AgentResponse, AgentConfig
from .agent_registry import AgentRegistry, discover_agents
from .agent_loader import AgentLoader

__all__ = ['BaseAgent', 'AgentResponse', 'AgentConfig', 'AgentRegistry', 'discover_agents', 'AgentLoader']