"""
Conversation service for managing chat history and conversations
"""
import uuid
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from models.database import db
from models.conversation import Conversation
from utils.security import SecurityUtils

logger = logging.getLogger('juniorgpt.conversation_service')

class ConversationService:
    """Service for managing conversations and chat history"""
    
    def __init__(self):
        self.security = SecurityUtils()
    
    def create_conversation(
        self,
        user_input: str,
        agent_response: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Create a new conversation or add to existing one"""
        
        # Validate input
        is_valid, error_msg = self.security.validate_message_input(user_input)
        if not is_valid:
            logger.warning(f"Invalid user input: {error_msg}")
            return None
        
        try:
            with db.get_session() as session:
                # Generate conversation ID if not provided
                if not conversation_id:
                    conversation_id = str(uuid.uuid4())
                
                # Sanitize content
                safe_user_input = self.security.sanitize_html(user_input)
                safe_agent_response = self.security.sanitize_html(agent_response)
                
                # Create conversation
                conversation = Conversation(
                    user_input=safe_user_input,
                    agent_response=safe_agent_response,
                    conversation_id=conversation_id,
                    agents_used=kwargs.get('agents_used', []),
                    model_used=kwargs.get('model_used', ''),
                    response_time=kwargs.get('response_time', 0.0),
                    thinking_trace=kwargs.get('thinking_trace', {}),
                    title=kwargs.get('title', None),
                    tags=kwargs.get('tags', [])
                )
                
                session.add(conversation)
                session.commit()
                
                logger.info(f"Created conversation: {conversation_id}")
                return conversation_id
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                return conversation.to_dict() if conversation else None
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation"""
        try:
            with db.get_session() as session:
                conversations = session.query(Conversation).filter_by(
                    conversation_id=conversation_id
                ).order_by(Conversation.created_at).limit(limit).all()
                
                return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def get_recent_conversations(
        self,
        limit: int = 20,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        try:
            with db.get_session() as session:
                conversations = Conversation.get_recent_conversations(
                    session, limit, include_archived
                )
                return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    def search_conversations(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search conversations by content"""
        if not query or not query.strip():
            return []
        
        # Validate search query
        safe_query = self.security.sanitize_html(query.strip())
        
        try:
            with db.get_session() as session:
                conversations = Conversation.search_conversations(
                    session, safe_query, limit
                )
                return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    def add_conversation_rating(
        self,
        conversation_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Add user satisfaction rating to conversation"""
        
        if not (1 <= rating <= 5):
            logger.warning(f"Invalid rating: {rating}")
            return False
        
        try:
            with db.get_session() as session:
                # Get the most recent conversation entry for this conversation_id
                conversation = session.query(Conversation).filter_by(
                    conversation_id=conversation_id
                ).order_by(Conversation.created_at.desc()).first()
                
                if conversation:
                    safe_feedback = None
                    if feedback:
                        safe_feedback = self.security.sanitize_html(feedback.strip())
                    
                    conversation.add_rating(rating, safe_feedback)
                    session.commit()
                    
                    logger.info(f"Added rating {rating} to conversation {conversation_id}")
                    return True
                else:
                    logger.warning(f"Conversation not found: {conversation_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to add rating to conversation {conversation_id}: {e}")
            return False
    
    def add_conversation_tag(self, conversation_id: str, tag: str) -> bool:
        """Add tag to conversation"""
        if not tag or not tag.strip():
            return False
        
        safe_tag = self.security.sanitize_html(tag.strip().lower())
        
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                if conversation:
                    conversation.add_tag(safe_tag)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to add tag to conversation: {e}")
            return False
    
    def remove_conversation_tag(self, conversation_id: str, tag: str) -> bool:
        """Remove tag from conversation"""
        if not tag or not tag.strip():
            return False
        
        safe_tag = self.security.sanitize_html(tag.strip().lower())
        
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                if conversation:
                    conversation.remove_tag(safe_tag)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to remove tag from conversation: {e}")
            return False
    
    def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation"""
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                if conversation:
                    conversation.archive()
                    session.commit()
                    logger.info(f"Archived conversation: {conversation_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to archive conversation: {e}")
            return False
    
    def unarchive_conversation(self, conversation_id: str) -> bool:
        """Unarchive a conversation"""
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                if conversation:
                    conversation.unarchive()
                    session.commit()
                    logger.info(f"Unarchived conversation: {conversation_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to unarchive conversation: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation (use with caution)"""
        try:
            with db.get_session() as session:
                # Delete all conversation entries with this conversation_id
                deleted_count = session.query(Conversation).filter_by(
                    conversation_id=conversation_id
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} conversation entries for {conversation_id}")
                    return True
                else:
                    logger.warning(f"No conversation found to delete: {conversation_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    def get_conversations_by_tag(
        self,
        tag: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversations by tag"""
        if not tag or not tag.strip():
            return []
        
        safe_tag = self.security.sanitize_html(tag.strip().lower())
        
        try:
            with db.get_session() as session:
                conversations = Conversation.get_conversations_by_tag(
                    session, safe_tag, limit
                )
                return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"Failed to get conversations by tag: {e}")
            return []
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            with db.get_session() as session:
                return Conversation.get_conversation_stats(session)
        except Exception as e:
            logger.error(f"Failed to get conversation statistics: {e}")
            return {}
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        if not title or not title.strip():
            return False
        
        safe_title = self.security.sanitize_html(title.strip())
        
        try:
            with db.get_session() as session:
                conversation = Conversation.get_by_conversation_id(session, conversation_id)
                if conversation:
                    conversation.title = safe_title
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update conversation title: {e}")
            return False
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Export conversation data"""
        try:
            with db.get_session() as session:
                conversations = session.query(Conversation).filter_by(
                    conversation_id=conversation_id
                ).order_by(Conversation.created_at).all()
                
                if not conversations:
                    return None
                
                # Create export structure
                export_data = {
                    'conversation_id': conversation_id,
                    'title': conversations[0].title,
                    'created_at': conversations[0].created_at.isoformat(),
                    'total_exchanges': len(conversations),
                    'exchanges': []
                }
                
                for conv in conversations:
                    export_data['exchanges'].append({
                        'timestamp': conv.created_at.isoformat(),
                        'user_input': conv.user_input,
                        'agent_response': conv.agent_response,
                        'agents_used': conv.agents_used,
                        'model_used': conv.model_used,
                        'response_time': conv.response_time,
                        'satisfaction_rating': conv.satisfaction_rating,
                        'tags': conv.tags
                    })
                
                return export_data
                
        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            return None