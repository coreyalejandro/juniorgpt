"""Service for managing agent teams"""
from typing import List, Optional, Dict, Any

from models import db, Team


class TeamService:
    """Service layer for creating and retrieving teams"""

    def create_team(self, name: str, agents: List[str], description: str = "") -> Dict[str, Any]:
        with db.get_session() as session:
            team = Team(name=name, agents=agents, description=description)
            session.add(team)
            session.flush()
            return team.to_dict()

    def update_team(self, team_id: str, name: Optional[str] = None,
                     agents: Optional[List[str]] = None,
                     description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with db.get_session() as session:
            team = Team.get_by_team_id(session, team_id)
            if not team:
                return None
            if name is not None:
                team.name = name
            if agents is not None:
                team.agents = agents
            if description is not None:
                team.description = description
            session.add(team)
            session.flush()
            return team.to_dict()

    def delete_team(self, team_id: str) -> bool:
        with db.get_session() as session:
            team = Team.get_by_team_id(session, team_id)
            if team:
                session.delete(team)
                return True
            return False

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        with db.get_session() as session:
            team = Team.get_by_team_id(session, team_id)
            return team.to_dict() if team else None

    def list_teams(self) -> List[Dict[str, Any]]:
        with db.get_session() as session:
            teams = Team.get_all(session)
            return [team.to_dict() for team in teams]
