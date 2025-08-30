"""
Agent service for managing AI agents and their execution
"""
import asyncio
import time
import re
from typing import Dict, List, Optional, Set, Tuple, Any
import logging
from datetime import datetime

from models.database import db
from models.agent import Agent, AgentExecution
from models.conversation import Conversation
from services.model_service import ModelService, ModelResponse
from utils.security import SecurityUtils

logger = logging.getLogger('juniorgpt.agent_service')

class AgentService:
    """Service for managing agents and their execution"""
    
    def __init__(self, model_service: ModelService):
        self.model_service = model_service
        self.security = SecurityUtils()
        
        # Define the 14 specialized agents
        self.default_agents = {
            "research": {
                "name": "🔍 Research Agent",
                "description": "Deep research and information gathering",
                "model": "gpt-4o-mini",
                "active": True,
                "thinking_style": "I analyze information systematically, gathering facts and cross-referencing sources to provide comprehensive insights.",
                "triggers": ["research", "find", "information", "data", "facts", "investigate", "study", "analyze"]
            },
            "coding": {
                "name": "💻 Coding Agent", 
                "description": "Software development and debugging",
                "model": "claude-3-5-sonnet",
                "active": True,
                "thinking_style": "I think in code structures, considering best practices, patterns, and debugging approaches to solve programming challenges.",
                "triggers": ["code", "programming", "debug", "script", "function", "algorithm", "software", "development"]
            },
            "analysis": {
                "name": "📊 Analysis Agent",
                "description": "Data analysis and insights",
                "model": "gpt-4o-mini",
                "active": True,
                "thinking_style": "I examine data patterns, identify trends, and extract meaningful insights from complex information.",
                "triggers": ["analyze", "data", "statistics", "trends", "patterns", "insights", "metrics"]
            },
            "writing": {
                "name": "✍️ Writing Agent",
                "description": "Content creation and editing",
                "model": "claude-3-5-sonnet",
                "active": True,
                "thinking_style": "I craft clear, engaging content while maintaining proper structure, tone, and style for the intended audience.",
                "triggers": ["write", "content", "article", "blog", "copy", "text", "document", "essay"]
            },
            "creative": {
                "name": "🎨 Creative Agent",
                "description": "Creative tasks and brainstorming",
                "model": "gpt-4o",
                "active": True,
                "thinking_style": "I explore creative possibilities, generate original ideas, and approach problems with innovative thinking.",
                "triggers": ["creative", "brainstorm", "ideas", "innovation", "design", "art", "story", "imagine"]
            },
            "planning": {
                "name": "📋 Planning Agent",
                "description": "Project planning and organization",
                "model": "gpt-4o-mini",
                "active": True,
                "thinking_style": "I break down complex tasks into manageable steps, create timelines, and organize resources efficiently.",
                "triggers": ["plan", "organize", "schedule", "project", "timeline", "strategy", "roadmap"]
            },
            "problem_solving": {
                "name": "🧩 Problem Solver",
                "description": "Complex problem analysis and solutions",
                "model": "gpt-4o",
                "active": True,
                "thinking_style": "I approach problems systematically, breaking them down into components and evaluating multiple solution paths.",
                "triggers": ["problem", "solve", "issue", "challenge", "troubleshoot", "fix", "solution"]
            },
            "communication": {
                "name": "💬 Communication Agent",
                "description": "Communication and interpersonal skills",
                "model": "claude-3-5-sonnet",
                "active": True,
                "thinking_style": "I focus on clear, empathetic communication while considering audience needs and cultural context.",
                "triggers": ["communicate", "message", "email", "presentation", "meeting", "discussion"]
            },
            "math": {
                "name": "🔢 Math Agent",
                "description": "Mathematical calculations and reasoning",
                "model": "gpt-4o",
                "active": True,
                "thinking_style": "I approach mathematical problems step-by-step, showing work and explaining reasoning clearly.",
                "triggers": ["math", "calculate", "equation", "formula", "statistics", "numbers", "computation"]
            },
            "learning": {
                "name": "🎓 Learning Agent",
                "description": "Educational content and explanations",
                "model": "gpt-4o-mini",
                "active": True,
                "thinking_style": "I break down complex concepts into digestible parts, providing clear explanations and examples.",
                "triggers": ["learn", "explain", "teach", "education", "tutorial", "lesson", "understand"]
            },
            "business": {
                "name": "💼 Business Agent",
                "description": "Business strategy and analysis",
                "model": "gpt-4o",
                "active": True,
                "thinking_style": "I analyze business challenges through strategic frameworks, considering market dynamics and stakeholder interests.",
                "triggers": ["business", "strategy", "market", "finance", "revenue", "profit", "customer"]
            },
            "health": {
                "name": "🏥 Health Agent",
                "description": "Health and wellness information",
                "model": "gpt-4o-mini",
                "active": True,
                "thinking_style": "I provide health information while emphasizing the importance of professional medical advice.",
                "triggers": ["health", "medical", "wellness", "fitness", "nutrition", "symptoms", "exercise"]
            },
            "legal": {
                "name": "⚖️ Legal Agent",
                "description": "Legal information and guidance",
                "model": "claude-3-5-sonnet",
                "active": True,
                "thinking_style": "I provide legal information while clearly distinguishing between general guidance and professional legal advice.",
                "triggers": ["legal", "law", "rights", "contract", "regulation", "compliance", "policy"]
            },
            "technical": {
                "name": "🔧 Technical Agent",
                "description": "Technical support and troubleshooting",
                "model": "claude-3-5-sonnet",
                "active": True,
                "thinking_style": "I diagnose technical issues systematically and provide step-by-step solutions with clear explanations.",
                "triggers": ["technical", "support", "troubleshoot", "system", "error", "configuration", "setup"]
            }
        }
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize default agents in database if they don't exist"""
        try:
            with db.get_session() as session:
                for agent_id, config in self.default_agents.items():
                    existing_agent = Agent.get_by_agent_id(session, agent_id)
                    
                    if not existing_agent:
                        agent = Agent(
                            agent_id=agent_id,
                            name=config["name"],
                            description=config["description"],
                            model=config["model"],
                            emoji=config["name"].split()[0],
                            thinking_style=config["thinking_style"],
                            active=config["active"]
                        )
                        session.add(agent)
                        logger.info(f"Created agent: {config['name']}")
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents"""
        try:
            with db.get_session() as session:
                agents = Agent.get_active_agents(session)
                return [agent.to_dict() for agent in agents]
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            return []
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        try:
            with db.get_session() as session:
                agent = Agent.get_by_agent_id(session, agent_id)
                return agent.to_dict() if agent else None
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    def auto_detect_agents(self, message: str, max_agents: int = 3) -> List[str]:
        """Automatically detect which agents should handle the message"""
        message_lower = message.lower()
        agent_scores = {}
        
        # Score agents based on keyword triggers
        for agent_id, config in self.default_agents.items():
            if not config.get("active", True):
                continue
                
            score = 0
            triggers = config.get("triggers", [])
            
            for trigger in triggers:
                if trigger in message_lower:
                    # Weight longer matches more heavily
                    score += len(trigger) * message_lower.count(trigger)
            
            if score > 0:
                agent_scores[agent_id] = score
        
        # If no specific agents detected, use general-purpose agents
        if not agent_scores:
            # Default to research and problem-solving for general queries
            return ["research", "problem_solving"][:max_agents]
        
        # Return top scoring agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, _ in sorted_agents[:max_agents]]
    
    async def process_with_agents(
        self,
        message: str,
        agent_ids: List[str],
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Process message with specified agents"""
        
        # Validate input
        is_valid, error_msg = self.security.validate_message_input(message)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "response": f"Input validation failed: {error_msg}",
                "agents_used": [],
                "thinking_traces": {},
                "response_time": 0.0
            }
        
        start_time = time.time()
        thinking_traces = {}
        agent_responses = {}
        execution_ids = []
        
        try:
            # Get conversation from database
            conversation = None
            if conversation_id:
                with db.get_session() as session:
                    conversation = Conversation.get_by_conversation_id(session, conversation_id)
            
            # Process with each agent concurrently
            tasks = []
            for agent_id in agent_ids:
                task = self._execute_agent(agent_id, message, conversation_history, conversation)
                tasks.append(task)
            
            # Wait for all agents to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_agents = []
            for i, result in enumerate(results):
                agent_id = agent_ids[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent_id} failed: {result}")
                    thinking_traces[agent_id] = {
                        "agent_name": self.default_agents[agent_id]["name"],
                        "thinking": f"Error: {str(result)}",
                        "success": False
                    }
                else:
                    execution_id, response, thinking = result
                    execution_ids.append(execution_id)
                    agent_responses[agent_id] = response
                    thinking_traces[agent_id] = {
                        "agent_name": self.default_agents[agent_id]["name"],
                        "thinking": thinking,
                        "success": True
                    }
                    successful_agents.append(agent_id)
            
            # Combine responses if multiple agents
            if len(successful_agents) == 1:
                final_response = agent_responses[successful_agents[0]]
            else:
                final_response = self._combine_agent_responses(agent_responses, successful_agents)
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "response": final_response,
                "agents_used": successful_agents,
                "thinking_traces": thinking_traces,
                "response_time": response_time,
                "execution_ids": execution_ids
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Agent processing failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "response": f"Processing failed: {str(e)}",
                "agents_used": [],
                "thinking_traces": thinking_traces,
                "response_time": response_time
            }
    
    async def _execute_agent(
        self,
        agent_id: str,
        message: str,
        conversation_history: Optional[List[Dict]],
        conversation: Optional[Conversation]
    ) -> Tuple[str, str, str]:
        """Execute a single agent"""
        
        # Get agent configuration
        agent_config = self.default_agents.get(agent_id)
        if not agent_config:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        # Get agent from database
        with db.get_session() as session:
            agent = Agent.get_by_agent_id(session, agent_id)
            if not agent:
                raise ValueError(f"Agent not found in database: {agent_id}")
            
            # Create execution record
            execution = AgentExecution(
                conversation_id=conversation.id if conversation else None,
                agent_id=agent.id,
                model_used=agent.model,
                temperature_used=agent.temperature,
                max_tokens_used=agent.max_tokens
            )
            session.add(execution)
            session.commit()
            
            execution_id = execution.execution_id
        
        try:
            # Prepare agent-specific prompt
            agent_prompt = self._create_agent_prompt(agent_config, message)
            
            # Generate thinking trace
            thinking_trace = f"Agent {agent_config['name']} is processing: {message[:100]}..."
            
            # Get response from model
            model_response = await self.model_service.generate_response(
                prompt=agent_prompt,
                model=agent_config["model"],
                conversation_history=conversation_history,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            
            if not model_response.success:
                raise Exception(model_response.error)
            
            # Update execution record
            with db.get_session() as session:
                execution = session.query(AgentExecution).filter_by(
                    execution_id=execution_id
                ).first()
                
                if execution:
                    execution.mark_completed(
                        response_time=model_response.response_time,
                        tokens_used=model_response.tokens_used,
                        thinking_trace={"thinking": thinking_trace}
                    )
                    
                    # Update agent performance
                    agent = session.query(Agent).get(execution.agent_id)
                    if agent:
                        agent.update_performance(model_response.response_time, True)
                
                session.commit()
            
            return execution_id, model_response.content, thinking_trace
            
        except Exception as e:
            # Mark execution as failed
            with db.get_session() as session:
                execution = session.query(AgentExecution).filter_by(
                    execution_id=execution_id
                ).first()
                
                if execution:
                    execution.mark_failed(str(e))
                    
                    # Update agent performance
                    agent = session.query(Agent).get(execution.agent_id)
                    if agent:
                        agent.update_performance(0.0, False)
                
                session.commit()
            
            raise e
    
    def _create_agent_prompt(self, agent_config: Dict[str, Any], message: str) -> str:
        """Create agent-specific prompt"""
        
        agent_name = agent_config["name"]
        thinking_style = agent_config.get("thinking_style", "")
        
        prompt = f"""You are {agent_name}, a specialized AI assistant.

Your thinking style: {thinking_style}

Your role is to help with: {agent_config["description"]}

Please respond to the following message with expertise in your area:

{message}

Provide a helpful, accurate, and detailed response appropriate to your specialization."""
        
        return prompt
    
    def _combine_agent_responses(
        self,
        agent_responses: Dict[str, str],
        agent_ids: List[str]
    ) -> str:
        """Combine responses from multiple agents"""
        
        if not agent_responses:
            return "No responses generated."
        
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]
        
        # Create a structured response combining all agents
        combined = "Here's a comprehensive response from multiple specialized agents:\n\n"
        
        for agent_id in agent_ids:
            if agent_id in agent_responses:
                agent_name = self.default_agents[agent_id]["name"]
                response = agent_responses[agent_id]
                
                combined += f"## {agent_name}\n\n{response}\n\n---\n\n"
        
        return combined.strip()
    
    def toggle_agent(self, agent_id: str, active: bool) -> bool:
        """Toggle agent active status"""
        try:
            with db.get_session() as session:
                agent = Agent.get_by_agent_id(session, agent_id)
                if agent:
                    if active:
                        agent.activate()
                    else:
                        agent.deactivate()
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to toggle agent {agent_id}: {e}")
            return False
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        try:
            with db.get_session() as session:
                return Agent.get_performance_stats(session)
        except Exception as e:
            logger.error(f"Failed to get agent statistics: {e}")
            return {}