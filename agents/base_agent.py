"""
Base agent framework for creating self-contained, plug-and-play agents
"""
import abc
import json
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class AgentConfig:
    """Agent configuration"""
    agent_id: str
    name: str
    description: str
    version: str
    author: str
    
    # Model configuration
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Agent behavior
    thinking_style: str = ""
    triggers: List[str] = None
    tags: List[str] = None
    
    # Performance settings
    timeout: int = 60
    retry_count: int = 3
    
    # Dependencies
    required_apis: List[str] = None
    required_models: List[str] = None
    
    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []
        if self.tags is None:
            self.tags = []
        if self.required_apis is None:
            self.required_apis = []
        if self.required_models is None:
            self.required_models = []

@dataclass
class AgentResponse:
    """Standardized agent response"""
    agent_id: str
    content: str
    status: AgentStatus
    
    # Metadata
    thinking_trace: str = ""
    execution_time: float = 0.0
    tokens_used: int = 0
    model_used: str = ""
    
    # Error information
    error_message: str = ""
    error_code: str = ""
    
    # Additional data
    metadata: Dict[str, Any] = None
    artifacts: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.artifacts is None:
            self.artifacts = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        return result
    
    def is_success(self) -> bool:
        """Check if response is successful"""
        return self.status == AgentStatus.COMPLETED
    
    def add_artifact(self, artifact_type: str, data: Any, description: str = ""):
        """Add artifact to response"""
        self.artifacts.append({
            "type": artifact_type,
            "data": data,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        })

class BaseAgent(abc.ABC):
    """
    Base class for all self-contained agents
    
    Each agent should inherit from this class and implement the required methods.
    Agents can be run standalone or integrated into larger systems.
    
    Key Features:
    - Absolute modularity and independence
    - Microservice deployment ready
    - Team collaboration capable
    - Health monitoring and metrics
    - Standardized interfaces
    """
    
    def __init__(self, config: AgentConfig = None, model_service=None, logger=None):
        # Handle case where no config is provided (for abstract instantiation)
        if config is None:
            config = self._get_default_config()
        
        self.config = config
        self.model_service = model_service
        self.logger = logger or logging.getLogger(f"agent.{config.agent_id}")
        
        self.status = AgentStatus.IDLE
        self.execution_id = None
        self.start_time = None
        
        # Event hooks
        self.on_start_hooks = []
        self.on_complete_hooks = []
        self.on_error_hooks = []
        
        # Collaboration context for team work
        self.team_context = {}
        self.peer_agents = []
        
        # Performance metrics
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_response_time": 0.0,
            "last_execution_time": None
        }
        
        # Validate configuration
        self._validate_config()
    
    def _get_default_config(self) -> AgentConfig:
        """Get default configuration for agent (override in subclasses)"""
        return AgentConfig(
            agent_id="base_agent",
            name="Base Agent",
            description="Base agent implementation",
            version="1.0.0",
            author="JuniorGPT"
        )
    
    def _validate_config(self):
        """Validate agent configuration"""
        required_fields = ['agent_id', 'name', 'description', 'version']
        for field in required_fields:
            if not getattr(self.config, field):
                raise ValueError(f"Agent config missing required field: {field}")
    
    @abc.abstractmethod
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process a message and return response
        
        Args:
            message: User input message
            context: Optional context data (conversation history, metadata, etc.)
            
        Returns:
            AgentResponse object
        """
        pass
    
    @abc.abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return agent capabilities and metadata
        
        Returns:
            Dictionary describing what the agent can do
        """
        pass
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if agent can handle the message
        
        Args:
            message: User input message
            context: Optional context data
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        message_lower = message.lower()
        score = 0.0
        
        # Check triggers
        for trigger in self.config.triggers:
            if trigger.lower() in message_lower:
                score += 0.2
        
        # Check tags
        for tag in self.config.tags:
            if tag.lower() in message_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    async def execute(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Execute agent with full lifecycle management
        
        Args:
            message: User input message
            context: Optional context data
            
        Returns:
            AgentResponse object
        """
        self.execution_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.status = AgentStatus.PROCESSING
        
        self.logger.info(f"Starting execution {self.execution_id} for agent {self.config.agent_id}")
        
        # Run start hooks
        await self._run_hooks(self.on_start_hooks, message, context)
        
        try:
            # Set timeout
            response = await asyncio.wait_for(
                self.process(message, context or {}),
                timeout=self.config.timeout
            )
            
            # Update response metadata
            response.execution_time = time.time() - self.start_time
            response.agent_id = self.config.agent_id
            
            # Update performance metrics
            self._update_metrics(response.execution_time, response.status == AgentStatus.COMPLETED)
            
            if response.status == AgentStatus.COMPLETED:
                self.status = AgentStatus.COMPLETED
                await self._run_hooks(self.on_complete_hooks, response)
            else:
                self.status = response.status
                await self._run_hooks(self.on_error_hooks, response)
            
            self.logger.info(f"Completed execution {self.execution_id} in {response.execution_time:.2f}s")
            
            return response
            
        except asyncio.TimeoutError:
            execution_time = time.time() - self.start_time
            self.status = AgentStatus.TIMEOUT
            
            response = AgentResponse(
                agent_id=self.config.agent_id,
                content="",
                status=AgentStatus.TIMEOUT,
                execution_time=execution_time,
                error_message=f"Agent execution timed out after {self.config.timeout}s",
                error_code="TIMEOUT"
            )
            
            await self._run_hooks(self.on_error_hooks, response)
            self.logger.error(f"Execution {self.execution_id} timed out after {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            execution_time = time.time() - self.start_time
            self.status = AgentStatus.ERROR
            
            response = AgentResponse(
                agent_id=self.config.agent_id,
                content="",
                status=AgentStatus.ERROR,
                execution_time=execution_time,
                error_message=str(e),
                error_code="EXECUTION_ERROR"
            )
            
            await self._run_hooks(self.on_error_hooks, response)
            self.logger.error(f"Execution {self.execution_id} failed: {e}")
            
            return response
    
    async def _run_hooks(self, hooks: List[Callable], *args):
        """Run event hooks"""
        for hook in hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(*args)
                else:
                    hook(*args)
            except Exception as e:
                self.logger.warning(f"Hook execution failed: {e}")
    
    def add_hook(self, event: str, hook: Callable):
        """Add event hook"""
        if event == "start":
            self.on_start_hooks.append(hook)
        elif event == "complete":
            self.on_complete_hooks.append(hook)
        elif event == "error":
            self.on_error_hooks.append(hook)
        else:
            raise ValueError(f"Unknown event type: {event}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform agent health check"""
        health_info = {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "version": self.config.version,
            "status": self.status.value,
            "healthy": True,
            "checks": {}
        }
        
        # Check dependencies
        for api in self.config.required_apis:
            # This would be implemented by specific agent subclasses
            health_info["checks"][f"api_{api}"] = True
        
        return health_info
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_id": self.config.agent_id,
            "status": self.status.value,
            "execution_id": self.execution_id,
            "uptime": time.time() - (self.start_time or time.time()),
            "config": asdict(self.config),
            "performance": self.execution_metrics.copy(),
            "team_context": bool(self.team_context),
            "peer_agents_count": len(self.peer_agents)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "config": asdict(self.config),
            "status": self.status.value,
            "capabilities": self.get_capabilities(),
            "health": self.health_check(),
            "metrics": self.get_metrics()
        }
    
    def create_thinking_trace(self, thinking: str) -> str:
        """Create formatted thinking trace"""
        return f"[{self.config.name}] {thinking}"
    
    async def call_model(self, prompt: str, **kwargs) -> str:
        """Call AI model through model service"""
        if not self.model_service:
            raise RuntimeError("Model service not available")
        
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        response = await self.model_service.generate_response(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response.success:
            return response.content
        else:
            raise RuntimeError(f"Model call failed: {response.error}")
    
    def validate_input(self, message: str, context: Dict[str, Any] = None) -> tuple[bool, str]:
        """Validate input message"""
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message) > 10000:
            return False, "Message too long (max 10,000 characters)"
        
        return True, "Valid"
    
    @classmethod
    def from_config_file(cls, config_path: str, **kwargs):
        """Create agent from configuration file"""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config = AgentConfig(**config_data)
        return cls(config, **kwargs)
    
    def save_config(self, config_path: str):
        """Save agent configuration to file"""
        with open(config_path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def __str__(self) -> str:
        return f"{self.config.name} (v{self.config.version}) - {self.config.description}"
    
    def _update_metrics(self, execution_time: float, success: bool):
        """Update performance metrics"""
        self.execution_metrics["total_executions"] += 1
        if success:
            self.execution_metrics["successful_executions"] += 1
        
        # Update average response time
        total = self.execution_metrics["total_executions"]
        current_avg = self.execution_metrics["average_response_time"]
        self.execution_metrics["average_response_time"] = ((current_avg * (total - 1)) + execution_time) / total
        self.execution_metrics["last_execution_time"] = datetime.utcnow().isoformat()
    
    def set_team_context(self, team_id: str, role: str, peer_agents: List[str]):
        """Set team collaboration context"""
        self.team_context = {
            "team_id": team_id,
            "role": role,
            "joined_at": datetime.utcnow().isoformat()
        }
        self.peer_agents = peer_agents.copy()
        self.logger.info(f"Agent assigned to team {team_id} as {role}")
    
    def clear_team_context(self):
        """Clear team collaboration context"""
        self.team_context = {}
        self.peer_agents = []
    
    def is_team_member(self) -> bool:
        """Check if agent is part of a team"""
        return bool(self.team_context)
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """Get configuration for microservice deployment"""
        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "model": self.config.model,
            "timeout": self.config.timeout,
            "required_apis": self.config.required_apis.copy(),
            "required_models": self.config.required_models.copy(),
            "deployment_ready": self._is_deployment_ready()
        }
    
    def _is_deployment_ready(self) -> bool:
        """Check if agent is ready for independent deployment"""
        try:
            # Check if agent can handle basic operations
            capabilities = self.get_capabilities()
            health = self.health_check()
            return capabilities is not None and health.get('healthy', False)
        except:
            return False
    
    async def collaborate_with_peers(self, message: str, peer_responses: Dict[str, str]) -> AgentResponse:
        """Collaborate with peer agents (override for custom collaboration)"""
        # Default collaboration: incorporate peer insights into context
        enhanced_context = {
            "peer_responses": peer_responses,
            "collaboration_mode": True,
            "team_context": self.team_context
        }
        
        # Enhance message with collaboration context
        collaboration_message = f"Original request: {message}\n\nPeer insights available for consideration."
        
        return await self.process(collaboration_message, enhanced_context)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.config.agent_id}, status={self.status.value})>"