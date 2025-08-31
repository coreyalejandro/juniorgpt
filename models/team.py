"""Model for storing agent teams"""
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional
import uuid

from .database import Base


class Team(Base):
    """Represents a named collection of agents"""

    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(36), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    agents = Column(JSON)  # List of agent identifiers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __init__(self, name: str, agents: List[str], **kwargs):
        self.team_id = kwargs.get('team_id', str(uuid.uuid4()))
        self.name = name
        self.description = kwargs.get('description', '')
        self.agents = agents

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'agents': self.agents or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_team_id(cls, session, team_id: str) -> Optional['Team']:
        return session.query(cls).filter_by(team_id=team_id).first()

    @classmethod
    def get_all(cls, session) -> List['Team']:
        return session.query(cls).all()
