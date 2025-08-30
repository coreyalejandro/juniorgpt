"""
Conversation model for storing chat history
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Dict, Any, List, Optional
import uuid

from .database import Base

class Conversation(Base):
    """Model for storing conversation data"""
    
    __tablename__ = 'conversations'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Conversation identification
    conversation_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # User input
    user_input = Column(Text, nullable=False)
    
    # Agent response
    agent_response = Column(Text, nullable=False)
    
    # Metadata
    agents_used = Column(JSON)  # List of agent names that participated
    model_used = Column(String(100))  # Primary model used
    response_time = Column(Float)  # Response time in seconds
    
    # Thinking trace data
    thinking_trace = Column(JSON)  # Raw thinking trace data
    
    # User feedback
    satisfaction_rating = Column(Integer)  # 1-5 rating
    user_feedback = Column(Text)  # Optional text feedback
    
    # Conversation metadata
    title = Column(String(200))  # Auto-generated or user-set title
    is_archived = Column(Boolean, default=False)
    tags = Column(JSON)  # User-defined tags
    
    # Relationships
    executions = relationship("AgentExecution", back_populates="conversation", cascade="all, delete-orphan")
    
    def __init__(self, user_input: str, agent_response: str, **kwargs):
        self.conversation_id = kwargs.get('conversation_id', str(uuid.uuid4()))
        self.user_input = user_input
        self.agent_response = agent_response
        self.agents_used = kwargs.get('agents_used', [])
        self.model_used = kwargs.get('model_used', '')
        self.response_time = kwargs.get('response_time', 0.0)
        self.thinking_trace = kwargs.get('thinking_trace', {})
        self.title = kwargs.get('title', self._generate_title(user_input))
        self.tags = kwargs.get('tags', [])
        
    def _generate_title(self, user_input: str) -> str:
        """Generate a conversation title from user input"""
        # Take first 50 characters and clean up
        title = user_input[:50].strip()
        if len(user_input) > 50:
            title += "..."
        return title
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_input': self.user_input,
            'agent_response': self.agent_response,
            'agents_used': self.agents_used or [],
            'model_used': self.model_used,
            'response_time': self.response_time,
            'thinking_trace': self.thinking_trace or {},
            'satisfaction_rating': self.satisfaction_rating,
            'user_feedback': self.user_feedback,
            'title': self.title,
            'is_archived': self.is_archived,
            'tags': self.tags or []
        }
    
    def add_rating(self, rating: int, feedback: str = None):
        """Add user satisfaction rating"""
        if 1 <= rating <= 5:
            self.satisfaction_rating = rating
            if feedback:
                self.user_feedback = feedback
    
    def add_tag(self, tag: str):
        """Add a tag to the conversation"""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the conversation"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def archive(self):
        """Archive this conversation"""
        self.is_archived = True
    
    def unarchive(self):
        """Unarchive this conversation"""
        self.is_archived = False
    
    @classmethod
    def get_by_conversation_id(cls, session, conversation_id: str) -> Optional['Conversation']:
        """Get conversation by conversation_id"""
        return session.query(cls).filter_by(conversation_id=conversation_id).first()
    
    @classmethod
    def get_recent_conversations(cls, session, limit: int = 20, include_archived: bool = False) -> List['Conversation']:
        """Get recent conversations"""
        query = session.query(cls)
        
        if not include_archived:
            query = query.filter_by(is_archived=False)
            
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def search_conversations(cls, session, query_text: str, limit: int = 20) -> List['Conversation']:
        """Search conversations by text content"""
        search_filter = f"%{query_text}%"
        return session.query(cls).filter(
            (cls.user_input.ilike(search_filter)) |
            (cls.agent_response.ilike(search_filter)) |
            (cls.title.ilike(search_filter))
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_conversations_by_tag(cls, session, tag: str, limit: int = 20) -> List['Conversation']:
        """Get conversations by tag"""
        return session.query(cls).filter(
            cls.tags.contains([tag])
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_conversation_stats(cls, session) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_conversations = session.query(cls).count()
        archived_count = session.query(cls).filter_by(is_archived=True).count()
        
        # Average response time
        avg_response_time = session.query(func.avg(cls.response_time)).scalar() or 0.0
        
        # Most used agents
        agent_usage = {}
        conversations_with_agents = session.query(cls).filter(cls.agents_used.isnot(None)).all()
        
        for conv in conversations_with_agents:
            for agent in (conv.agents_used or []):
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        # Satisfaction ratings
        ratings = session.query(cls.satisfaction_rating).filter(
            cls.satisfaction_rating.isnot(None)
        ).all()
        
        avg_rating = sum(r[0] for r in ratings) / len(ratings) if ratings else 0.0
        
        return {
            'total_conversations': total_conversations,
            'active_conversations': total_conversations - archived_count,
            'archived_conversations': archived_count,
            'average_response_time': round(avg_response_time, 2),
            'most_used_agents': sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            'average_satisfaction_rating': round(avg_rating, 2),
            'total_ratings': len(ratings)
        }
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, conversation_id={self.conversation_id}, title='{self.title}')>"