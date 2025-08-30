"""
Agent models for tracking agent configurations and executions
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from .database import Base

class Agent(Base):
    """Model for storing agent configurations"""
    
    __tablename__ = 'agents'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Agent identification
    agent_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10))
    
    # Configuration
    description = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    thinking_style = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Performance tracking
    total_executions = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # Configuration options
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    
    def __init__(self, agent_id: str, name: str, description: str, model: str, **kwargs):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.model = model
        self.emoji = kwargs.get('emoji', '🤖')
        self.thinking_style = kwargs.get('thinking_style', '')
        self.is_active = kwargs.get('active', True)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'name': self.name,
            'emoji': self.emoji,
            'description': self.description,
            'model': self.model,
            'thinking_style': self.thinking_style,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_executions': self.total_executions,
            'average_response_time': self.average_response_time,
            'success_rate': self.success_rate,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p
        }
    
    def update_performance(self, response_time: float, success: bool):
        """Update agent performance metrics"""
        # Update execution count
        self.total_executions += 1
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            # Moving average
            self.average_response_time = (
                (self.average_response_time * (self.total_executions - 1) + response_time) 
                / self.total_executions
            )
        
        # Update success rate
        if success:
            successful_executions = int(self.success_rate * (self.total_executions - 1) / 100) + 1
        else:
            successful_executions = int(self.success_rate * (self.total_executions - 1) / 100)
            
        self.success_rate = (successful_executions / self.total_executions) * 100
    
    def activate(self):
        """Activate the agent"""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate the agent"""
        self.is_active = False
    
    @classmethod
    def get_active_agents(cls, session) -> List['Agent']:
        """Get all active agents"""
        return session.query(cls).filter_by(is_active=True).all()
    
    @classmethod
    def get_by_agent_id(cls, session, agent_id: str) -> Optional['Agent']:
        """Get agent by agent_id"""
        return session.query(cls).filter_by(agent_id=agent_id).first()
    
    @classmethod
    def get_performance_stats(cls, session) -> Dict[str, Any]:
        """Get agent performance statistics"""
        agents = session.query(cls).filter_by(is_active=True).all()
        
        stats = {
            'total_agents': len(agents),
            'total_executions': sum(agent.total_executions for agent in agents),
            'average_response_time': 0.0,
            'average_success_rate': 0.0,
            'top_performers': [],
            'model_usage': {}
        }
        
        if agents:
            # Calculate averages
            total_response_time = sum(
                agent.average_response_time * agent.total_executions 
                for agent in agents if agent.total_executions > 0
            )
            total_executions = sum(agent.total_executions for agent in agents)
            
            if total_executions > 0:
                stats['average_response_time'] = total_response_time / total_executions
                
            stats['average_success_rate'] = sum(
                agent.success_rate for agent in agents
            ) / len(agents)
            
            # Top performers (by success rate and execution count)
            top_performers = sorted(
                agents,
                key=lambda a: (a.success_rate, a.total_executions),
                reverse=True
            )[:5]
            
            stats['top_performers'] = [
                {
                    'name': agent.name,
                    'success_rate': agent.success_rate,
                    'total_executions': agent.total_executions,
                    'average_response_time': agent.average_response_time
                }
                for agent in top_performers
            ]
            
            # Model usage statistics
            model_usage = {}
            for agent in agents:
                model = agent.model
                if model in model_usage:
                    model_usage[model]['count'] += 1
                    model_usage[model]['executions'] += agent.total_executions
                else:
                    model_usage[model] = {
                        'count': 1,
                        'executions': agent.total_executions
                    }
            
            stats['model_usage'] = model_usage
        
        return stats
    
    def __repr__(self):
        return f"<Agent(id={self.id}, agent_id={self.agent_id}, name={self.name}, active={self.is_active})>"

class AgentExecution(Base):
    """Model for tracking individual agent executions"""
    
    __tablename__ = 'agent_executions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    
    # Execution details
    execution_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Performance metrics
    response_time = Column(Float)  # Time in seconds
    tokens_used = Column(Integer)
    
    # Status and results
    status = Column(String(20), default='pending')  # pending, completed, failed
    error_message = Column(Text)
    thinking_trace = Column(JSON)  # Agent's thinking process
    
    # Model specific data
    model_used = Column(String(100))
    temperature_used = Column(Float)
    max_tokens_used = Column(Integer)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="executions")
    agent = relationship("Agent", back_populates="executions")
    
    def __init__(self, conversation_id: int, agent_id: int, **kwargs):
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.model_used = kwargs.get('model_used', '')
        self.temperature_used = kwargs.get('temperature_used', 0.7)
        self.max_tokens_used = kwargs.get('max_tokens_used', 4096)
    
    def mark_completed(self, response_time: float, tokens_used: int = None, thinking_trace: Dict = None):
        """Mark execution as completed"""
        self.completed_at = datetime.utcnow()
        self.response_time = response_time
        self.tokens_used = tokens_used or 0
        self.thinking_trace = thinking_trace or {}
        self.status = 'completed'
    
    def mark_failed(self, error_message: str):
        """Mark execution as failed"""
        self.completed_at = datetime.utcnow()
        self.status = 'failed'
        self.error_message = error_message
        
        # Calculate response time even for failures
        if self.started_at:
            self.response_time = (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary"""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'conversation_id': self.conversation_id,
            'agent_id': self.agent_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'response_time': self.response_time,
            'tokens_used': self.tokens_used,
            'status': self.status,
            'error_message': self.error_message,
            'thinking_trace': self.thinking_trace or {},
            'model_used': self.model_used,
            'temperature_used': self.temperature_used,
            'max_tokens_used': self.max_tokens_used
        }
    
    @classmethod
    def get_recent_executions(cls, session, limit: int = 50) -> List['AgentExecution']:
        """Get recent executions"""
        return session.query(cls).order_by(cls.started_at.desc()).limit(limit).all()
    
    @classmethod
    def get_executions_for_conversation(cls, session, conversation_id: int) -> List['AgentExecution']:
        """Get all executions for a conversation"""
        return session.query(cls).filter_by(conversation_id=conversation_id).order_by(cls.started_at).all()
    
    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_id={self.agent_id}, status={self.status})>"