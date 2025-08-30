"""
Agent Registry and Discovery System

This module handles automatic discovery, registration, and management
of self-contained agents in the JuniorGPT ecosystem.
"""
import os
import json
import importlib
import inspect
import asyncio
from typing import Dict, List, Any, Type, Optional, Set
from pathlib import Path
import logging
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger('juniorgpt.agent_registry')

class AgentRegistry:
    """
    Central registry for managing self-contained agents
    
    Features:
    - Auto-discovery of agent modules
    - Dynamic loading and unloading
    - Dependency management
    - Health monitoring
    - Version management
    """
    
    def __init__(self):
        self.agents: Dict[str, Type[BaseAgent]] = {}
        self.instances: Dict[str, BaseAgent] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.load_paths: Set[str] = set()
        self.dependencies: Dict[str, List[str]] = {}
        
    def register_agent(self, agent_class: Type[BaseAgent], metadata: Dict[str, Any] = None):
        """
        Register an agent class
        
        Args:
            agent_class: Agent class inheriting from BaseAgent
            metadata: Additional metadata about the agent
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class {agent_class.__name__} must inherit from BaseAgent")
        
        # Create temporary instance to get config
        try:
            temp_instance = agent_class()
            agent_id = temp_instance.config.agent_id
            
            self.agents[agent_id] = agent_class
            self.metadata[agent_id] = {
                "class_name": agent_class.__name__,
                "module": agent_class.__module__,
                "config": temp_instance.config,
                "capabilities": temp_instance.get_capabilities(),
                "registered_at": datetime.utcnow().isoformat(),
                "status": "registered",
                **(metadata or {})
            }
            
            logger.info(f"Registered agent: {agent_id} ({agent_class.__name__})")
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_class.__name__}: {e}")
            raise
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            # Stop instance if running
            if agent_id in self.instances:
                self.stop_agent(agent_id)
            
            del self.agents[agent_id]
            del self.metadata[agent_id]
            
            logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent_class(self, agent_id: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by ID"""
        return self.agents.get(agent_id)
    
    def get_agent_instance(self, agent_id: str, **kwargs) -> Optional[BaseAgent]:
        """
        Get or create agent instance
        
        Args:
            agent_id: Agent identifier
            **kwargs: Additional arguments for agent initialization
            
        Returns:
            Agent instance or None if not found
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found in registry")
            return None
        
        # Return existing instance if available
        if agent_id in self.instances:
            return self.instances[agent_id]
        
        # Create new instance
        try:
            agent_class = self.agents[agent_id]
            instance = agent_class(**kwargs)
            self.instances[agent_id] = instance
            
            logger.info(f"Created instance of agent: {agent_id}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create instance of agent {agent_id}: {e}")
            return None
    
    def stop_agent(self, agent_id: str):
        """Stop and remove agent instance"""
        if agent_id in self.instances:
            instance = self.instances[agent_id]
            # Perform cleanup if the agent has cleanup methods
            if hasattr(instance, 'cleanup'):
                try:
                    instance.cleanup()
                except Exception as e:
                    logger.warning(f"Agent {agent_id} cleanup failed: {e}")
            
            del self.instances[agent_id]
            logger.info(f"Stopped agent instance: {agent_id}")
    
    def list_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all registered agents
        
        Args:
            status: Optional status filter
            
        Returns:
            List of agent metadata
        """
        agents = []
        for agent_id, metadata in self.metadata.items():
            if status is None or metadata.get("status") == status:
                agent_data = metadata.copy()
                agent_data["agent_id"] = agent_id
                agent_data["instance_running"] = agent_id in self.instances
                agents.append(agent_data)
        
        return sorted(agents, key=lambda x: x["config"].name)
    
    def get_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for specific agent"""
        return self.metadata.get(agent_id)
    
    def find_capable_agents(self, message: str, context: Dict[str, Any] = None, threshold: float = 0.3) -> List[tuple[str, float]]:
        """
        Find agents capable of handling a message
        
        Args:
            message: Input message
            context: Optional context
            threshold: Minimum confidence threshold
            
        Returns:
            List of (agent_id, confidence_score) tuples, sorted by confidence
        """
        capable_agents = []
        
        for agent_id, agent_class in self.agents.items():
            try:
                # Create temporary instance to check capability
                temp_instance = agent_class()
                confidence = temp_instance.can_handle(message, context)
                
                if confidence >= threshold:
                    capable_agents.append((agent_id, confidence))
                    
            except Exception as e:
                logger.warning(f"Failed to check capability for agent {agent_id}: {e}")
        
        # Sort by confidence (highest first)
        capable_agents.sort(key=lambda x: x[1], reverse=True)
        return capable_agents
    
    def auto_select_agents(self, message: str, context: Dict[str, Any] = None, max_agents: int = 3) -> List[str]:
        """
        Automatically select best agents for a message
        
        Args:
            message: Input message
            context: Optional context
            max_agents: Maximum number of agents to select
            
        Returns:
            List of selected agent IDs
        """
        capable_agents = self.find_capable_agents(message, context)
        return [agent_id for agent_id, _ in capable_agents[:max_agents]]
    
    def check_dependencies(self, agent_id: str) -> Dict[str, bool]:
        """
        Check if agent dependencies are satisfied
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        if agent_id not in self.metadata:
            return {}
        
        config = self.metadata[agent_id]["config"]
        dependency_status = {}
        
        # Check API dependencies
        for api in config.required_apis:
            dependency_status[f"api_{api}"] = self._check_api_availability(api)
        
        # Check model dependencies
        for model in config.required_models:
            dependency_status[f"model_{model}"] = self._check_model_availability(model)
        
        return dependency_status
    
    def _check_api_availability(self, api_name: str) -> bool:
        """Check if API is available (placeholder implementation)"""
        # This would check actual API availability
        # For now, return True for common APIs
        common_apis = ["openai", "anthropic", "web_search"]
        return api_name in common_apis
    
    def _check_model_availability(self, model_name: str) -> bool:
        """Check if model is available (placeholder implementation)"""
        # This would check actual model availability
        # For now, return True for common models
        common_models = ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-haiku"]
        return model_name in common_models
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all registered agents"""
        health_status = {}
        
        for agent_id in self.agents:
            try:
                instance = self.get_agent_instance(agent_id)
                if instance:
                    health_info = instance.health_check()
                    health_info["dependencies"] = self.check_dependencies(agent_id)
                    health_status[agent_id] = health_info
                else:
                    health_status[agent_id] = {
                        "agent_id": agent_id,
                        "healthy": False,
                        "error": "Failed to create instance"
                    }
                    
            except Exception as e:
                health_status[agent_id] = {
                    "agent_id": agent_id,
                    "healthy": False,
                    "error": str(e)
                }
        
        return health_status
    
    def add_search_path(self, path: str):
        """Add path for agent discovery"""
        self.load_paths.add(path)
    
    def discover_agents(self, search_paths: List[str] = None) -> int:
        """
        Discover and register agents from specified paths
        
        Args:
            search_paths: Paths to search for agent modules
            
        Returns:
            Number of agents discovered
        """
        if search_paths:
            self.load_paths.update(search_paths)
        
        discovered_count = 0
        
        for search_path in self.load_paths:
            discovered_count += self._discover_agents_in_path(search_path)
        
        return discovered_count
    
    def _discover_agents_in_path(self, search_path: str) -> int:
        """Discover agents in a specific path"""
        discovered_count = 0
        
        try:
            path = Path(search_path)
            if not path.exists():
                logger.warning(f"Search path does not exist: {search_path}")
                return 0
            
            # Look for Python files
            for py_file in path.glob("**/*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                try:
                    discovered_count += self._load_agents_from_file(py_file)
                except Exception as e:
                    logger.warning(f"Failed to load agents from {py_file}: {e}")
            
        except Exception as e:
            logger.error(f"Error discovering agents in {search_path}: {e}")
        
        return discovered_count
    
    def _load_agents_from_file(self, file_path: Path) -> int:
        """Load agents from a specific Python file"""
        discovered_count = 0
        
        try:
            # Convert file path to module name
            relative_path = file_path.relative_to(Path.cwd())
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Find agent classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != BaseAgent and 
                    issubclass(obj, BaseAgent) and 
                    obj.__module__ == module_name):
                    
                    try:
                        self.register_agent(obj)
                        discovered_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to register agent {name}: {e}")
            
        except ImportError as e:
            logger.warning(f"Failed to import module from {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading agents from {file_path}: {e}")
        
        return discovered_count
    
    def reload_agent(self, agent_id: str) -> bool:
        """Reload an agent (useful for development)"""
        if agent_id not in self.metadata:
            logger.warning(f"Agent {agent_id} not found for reload")
            return False
        
        try:
            # Stop existing instance
            if agent_id in self.instances:
                self.stop_agent(agent_id)
            
            # Reload module
            metadata = self.metadata[agent_id]
            module_name = metadata["module"]
            module = importlib.import_module(module_name)
            importlib.reload(module)
            
            # Re-register
            class_name = metadata["class_name"]
            agent_class = getattr(module, class_name)
            self.register_agent(agent_class)
            
            logger.info(f"Reloaded agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload agent {agent_id}: {e}")
            return False
    
    def export_registry(self, file_path: str):
        """Export registry metadata to JSON file"""
        export_data = {
            "agents": {},
            "exported_at": datetime.utcnow().isoformat()
        }
        
        for agent_id, metadata in self.metadata.items():
            export_data["agents"][agent_id] = {
                "class_name": metadata["class_name"],
                "module": metadata["module"],
                "config": metadata["config"].__dict__ if hasattr(metadata["config"], "__dict__") else metadata["config"],
                "capabilities": metadata["capabilities"],
                "status": metadata["status"]
            }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported registry to {file_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_agents = len(self.agents)
        running_instances = len(self.instances)
        
        # Count by status
        status_counts = {}
        for metadata in self.metadata.values():
            status = metadata.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by capabilities
        capability_counts = {}
        for metadata in self.metadata.values():
            capabilities = metadata.get("capabilities", {})
            for capability in capabilities.get("specializations", []):
                capability_counts[capability] = capability_counts.get(capability, 0) + 1
        
        return {
            "total_registered": total_agents,
            "running_instances": running_instances,
            "status_breakdown": status_counts,
            "capability_distribution": capability_counts,
            "search_paths": list(self.load_paths)
        }

# Global registry instance
_global_registry = AgentRegistry()

def get_registry() -> AgentRegistry:
    """Get the global agent registry"""
    return _global_registry

def discover_agents(search_paths: List[str] = None) -> int:
    """
    Discover agents in specified paths
    
    Args:
        search_paths: Paths to search for agents
        
    Returns:
        Number of agents discovered
    """
    registry = get_registry()
    
    if search_paths is None:
        # Default search paths
        search_paths = [
            "agents/implementations",
            "plugins/agents",
            os.path.expanduser("~/.juniorgpt/agents")
        ]
    
    for path in search_paths:
        registry.add_search_path(path)
    
    return registry.discover_agents()

def register_agent(agent_class: Type[BaseAgent], metadata: Dict[str, Any] = None):
    """Register an agent class"""
    return get_registry().register_agent(agent_class, metadata)

def get_agent_instance(agent_id: str, **kwargs) -> Optional[BaseAgent]:
    """Get agent instance"""
    return get_registry().get_agent_instance(agent_id, **kwargs)

def list_agents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all registered agents"""
    return get_registry().list_agents(status)

def find_capable_agents(message: str, context: Dict[str, Any] = None, threshold: float = 0.3) -> List[tuple[str, float]]:
    """Find agents capable of handling a message"""
    return get_registry().find_capable_agents(message, context, threshold)