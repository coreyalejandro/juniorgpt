"""
Team Orchestrator - Dynamic team formation and job assignment system

This module handles automatic team formation based on job requirements
and orchestrates multi-agent collaboration for complex tasks.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json

from .agent_registry import get_registry
from .base_agent import BaseAgent, AgentResponse, AgentStatus

logger = logging.getLogger('juniorgpt.team_orchestrator')

@dataclass
class JobRequirement:
    """Defines requirements for a job or task"""
    job_id: str
    description: str
    required_capabilities: List[str]
    preferred_capabilities: List[str] = None
    max_agents: int = 5
    timeout: int = 300
    priority: str = "normal"  # low, normal, high, critical
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferred_capabilities is None:
            self.preferred_capabilities = []
        if self.context is None:
            self.context = {}

@dataclass
class TeamConfiguration:
    """Configuration for a dynamically formed team"""
    team_id: str
    job_id: str
    agents: List[str]  # Agent IDs
    roles: Dict[str, str]  # agent_id -> role mapping
    coordination_strategy: str  # sequential, parallel, collaborative
    formed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['formed_at'] = self.formed_at.isoformat()
        return result

@dataclass
class JobExecution:
    """Tracks execution of a job by a team"""
    execution_id: str
    job_id: str
    team_id: str
    status: str  # queued, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = None
    error_message: str = ""
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}

class TeamOrchestrator:
    """
    Orchestrates team formation and job execution
    
    Features:
    - Dynamic team formation based on job requirements
    - Multiple coordination strategies
    - Load balancing across agents
    - Job queuing and prioritization
    - Real-time monitoring and recovery
    """
    
    def __init__(self):
        self.registry = get_registry()
        self.active_teams: Dict[str, TeamConfiguration] = {}
        self.job_queue: List[JobRequirement] = []
        self.running_executions: Dict[str, JobExecution] = {}
        self.agent_workloads: Dict[str, int] = {}  # agent_id -> active job count
        
        # Configuration
        self.max_concurrent_jobs = 10
        self.default_coordination_strategy = "parallel"
        
    async def submit_job(self, job: JobRequirement) -> str:
        """
        Submit a job for execution
        
        Args:
            job: Job requirements and specifications
            
        Returns:
            Execution ID for tracking
        """
        logger.info(f"Submitting job: {job.job_id}")
        
        # Form optimal team for the job
        team = await self._form_team_for_job(job)
        if not team:
            raise ValueError(f"Cannot form suitable team for job {job.job_id}")
        
        # Create execution record
        execution = JobExecution(
            execution_id=str(uuid.uuid4()),
            job_id=job.job_id,
            team_id=team.team_id,
            status="queued"
        )
        
        self.running_executions[execution.execution_id] = execution
        self.active_teams[team.team_id] = team
        
        # Execute job with team
        asyncio.create_task(self._execute_job_with_team(job, team, execution))
        
        return execution.execution_id
    
    async def _form_team_for_job(self, job: JobRequirement) -> Optional[TeamConfiguration]:
        """
        Form optimal team based on job requirements
        
        Args:
            job: Job requirements
            
        Returns:
            Team configuration or None if team cannot be formed
        """
        logger.info(f"Forming team for job: {job.job_id}")
        
        # Get all available agents
        available_agents = []
        for agent_id, agent_class in self.registry.agents.items():
            if self._is_agent_available(agent_id):
                available_agents.append(agent_id)
        
        if not available_agents:
            logger.warning("No available agents for team formation")
            return None
        
        # Score agents for this job
        agent_scores = {}
        for agent_id in available_agents:
            score = await self._score_agent_for_job(agent_id, job)
            if score > 0:
                agent_scores[agent_id] = score
        
        if not agent_scores:
            logger.warning(f"No suitable agents found for job {job.job_id}")
            return None
        
        # Select best agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agents = [agent_id for agent_id, _ in sorted_agents[:job.max_agents]]
        
        # Assign roles based on capabilities
        roles = self._assign_roles(selected_agents, job)
        
        # Determine coordination strategy
        coordination_strategy = self._determine_coordination_strategy(selected_agents, job)
        
        team = TeamConfiguration(
            team_id=str(uuid.uuid4()),
            job_id=job.job_id,
            agents=selected_agents,
            roles=roles,
            coordination_strategy=coordination_strategy,
            formed_at=datetime.utcnow()
        )
        
        logger.info(f"Formed team {team.team_id} with {len(selected_agents)} agents")
        return team
    
    def _is_agent_available(self, agent_id: str) -> bool:
        """Check if agent is available for assignment"""
        # Check current workload
        current_workload = self.agent_workloads.get(agent_id, 0)
        max_concurrent = 3  # Configurable per agent
        
        if current_workload >= max_concurrent:
            return False
        
        # Check agent health
        try:
            agent_instance = self.registry.get_agent_instance(agent_id)
            if agent_instance:
                health = agent_instance.health_check()
                return health.get('healthy', False)
        except Exception as e:
            logger.warning(f"Health check failed for agent {agent_id}: {e}")
            return False
        
        return True
    
    async def _score_agent_for_job(self, agent_id: str, job: JobRequirement) -> float:
        """
        Score an agent's suitability for a job
        
        Args:
            agent_id: Agent identifier
            job: Job requirements
            
        Returns:
            Suitability score (0.0 to 1.0)
        """
        try:
            agent_class = self.registry.get_agent_class(agent_id)
            if not agent_class:
                return 0.0
            
            # Create temporary instance for capability check
            temp_instance = agent_class()
            capabilities = temp_instance.get_capabilities()
            
            # Calculate capability match score
            capability_score = 0.0
            total_requirements = len(job.required_capabilities) + len(job.preferred_capabilities)
            
            if total_requirements == 0:
                capability_score = 0.5  # Neutral score for jobs with no specific requirements
            else:
                # Check required capabilities
                for required in job.required_capabilities:
                    if self._has_capability(capabilities, required):
                        capability_score += 1.0 / total_requirements
                
                # Check preferred capabilities (weighted less)
                for preferred in job.preferred_capabilities:
                    if self._has_capability(capabilities, preferred):
                        capability_score += 0.5 / total_requirements
            
            # Check direct message handling capability
            message_score = temp_instance.can_handle(job.description, job.context)
            
            # Combine scores
            final_score = (capability_score * 0.6) + (message_score * 0.4)
            
            # Apply load balancing penalty
            current_load = self.agent_workloads.get(agent_id, 0)
            load_penalty = min(0.3, current_load * 0.1)
            final_score = max(0.0, final_score - load_penalty)
            
            return final_score
            
        except Exception as e:
            logger.warning(f"Failed to score agent {agent_id}: {e}")
            return 0.0
    
    def _has_capability(self, capabilities: Dict[str, Any], required: str) -> bool:
        """Check if agent capabilities match requirement"""
        required_lower = required.lower()
        
        # Check specializations
        specializations = capabilities.get('specializations', [])
        if any(required_lower in spec.lower() for spec in specializations):
            return True
        
        # Check supported domains
        domains = capabilities.get('supported_domains', [])
        if any(required_lower in domain.lower() for domain in domains):
            return True
        
        # Check input/output types
        input_types = capabilities.get('input_types', [])
        output_formats = capabilities.get('output_formats', [])
        
        if any(required_lower in itype.lower() for itype in input_types):
            return True
        if any(required_lower in oformat.lower() for oformat in output_formats):
            return True
        
        return False
    
    def _assign_roles(self, agent_ids: List[str], job: JobRequirement) -> Dict[str, str]:
        """Assign roles to agents based on their capabilities"""
        roles = {}
        
        # Default role assignment strategy
        if len(agent_ids) == 1:
            roles[agent_ids[0]] = "primary"
        elif len(agent_ids) == 2:
            roles[agent_ids[0]] = "primary"
            roles[agent_ids[1]] = "support"
        else:
            # For larger teams, assign based on capabilities
            roles[agent_ids[0]] = "lead"
            for i, agent_id in enumerate(agent_ids[1:], 1):
                if i <= 2:
                    roles[agent_id] = "specialist"
                else:
                    roles[agent_id] = "support"
        
        return roles
    
    def _determine_coordination_strategy(self, agent_ids: List[str], job: JobRequirement) -> str:
        """Determine the best coordination strategy for the team"""
        # Simple heuristics for strategy selection
        if len(agent_ids) == 1:
            return "single"
        elif "analysis" in job.description.lower() or "research" in job.description.lower():
            return "collaborative"  # Multiple perspectives beneficial
        elif "urgent" in job.description.lower() or job.priority == "critical":
            return "parallel"  # Speed is important
        else:
            return self.default_coordination_strategy
    
    async def _execute_job_with_team(self, job: JobRequirement, team: TeamConfiguration, execution: JobExecution):
        """
        Execute job using the assigned team
        
        Args:
            job: Job requirements
            team: Team configuration
            execution: Execution tracking object
        """
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        
        # Update agent workloads
        for agent_id in team.agents:
            self.agent_workloads[agent_id] = self.agent_workloads.get(agent_id, 0) + 1
        
        try:
            logger.info(f"Starting job execution {execution.execution_id} with team {team.team_id}")
            
            # Execute based on coordination strategy
            if team.coordination_strategy == "single":
                results = await self._execute_single_agent(job, team)
            elif team.coordination_strategy == "sequential":
                results = await self._execute_sequential(job, team)
            elif team.coordination_strategy == "parallel":
                results = await self._execute_parallel(job, team)
            elif team.coordination_strategy == "collaborative":
                results = await self._execute_collaborative(job, team)
            else:
                raise ValueError(f"Unknown coordination strategy: {team.coordination_strategy}")
            
            # Process results
            execution.results = {
                "success": True,
                "outputs": results,
                "team_performance": self._evaluate_team_performance(team, results)
            }
            execution.status = "completed"
            
            logger.info(f"Job execution {execution.execution_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job execution {execution.execution_id} failed: {e}")
            execution.status = "failed"
            execution.error_message = str(e)
            execution.results = {"success": False, "error": str(e)}
        
        finally:
            execution.completed_at = datetime.utcnow()
            
            # Update agent workloads
            for agent_id in team.agents:
                self.agent_workloads[agent_id] = max(0, self.agent_workloads.get(agent_id, 1) - 1)
            
            # Cleanup team
            if team.team_id in self.active_teams:
                del self.active_teams[team.team_id]
    
    async def _execute_single_agent(self, job: JobRequirement, team: TeamConfiguration) -> Dict[str, Any]:
        """Execute job with single agent"""
        agent_id = team.agents[0]
        agent_instance = self.registry.get_agent_instance(agent_id)
        
        if not agent_instance:
            raise RuntimeError(f"Cannot get instance of agent {agent_id}")
        
        response = await agent_instance.execute(job.description, job.context)
        
        return {
            agent_id: {
                "response": response.to_dict(),
                "role": team.roles.get(agent_id, "primary")
            }
        }
    
    async def _execute_parallel(self, job: JobRequirement, team: TeamConfiguration) -> Dict[str, Any]:
        """Execute job with agents working in parallel"""
        tasks = []
        
        for agent_id in team.agents:
            agent_instance = self.registry.get_agent_instance(agent_id)
            if agent_instance:
                task = agent_instance.execute(job.description, job.context)
                tasks.append((agent_id, task))
        
        results = {}
        responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (agent_id, _), response in zip(tasks, responses):
            if isinstance(response, Exception):
                results[agent_id] = {
                    "error": str(response),
                    "role": team.roles.get(agent_id, "unknown")
                }
            else:
                results[agent_id] = {
                    "response": response.to_dict(),
                    "role": team.roles.get(agent_id, "unknown")
                }
        
        return results
    
    async def _execute_sequential(self, job: JobRequirement, team: TeamConfiguration) -> Dict[str, Any]:
        """Execute job with agents working sequentially"""
        results = {}
        context = job.context.copy()
        
        for agent_id in team.agents:
            agent_instance = self.registry.get_agent_instance(agent_id)
            if not agent_instance:
                continue
            
            # Add previous results to context
            if results:
                context['previous_results'] = results
            
            response = await agent_instance.execute(job.description, context)
            results[agent_id] = {
                "response": response.to_dict(),
                "role": team.roles.get(agent_id, "unknown")
            }
            
            # Pass successful results to next agent
            if response.is_success():
                context['last_successful_output'] = response.content
        
        return results
    
    async def _execute_collaborative(self, job: JobRequirement, team: TeamConfiguration) -> Dict[str, Any]:
        """Execute job with collaborative agent interaction"""
        # First, get initial responses from all agents
        initial_results = await self._execute_parallel(job, team)
        
        # Then, let agents review and refine based on others' work
        refined_context = job.context.copy()
        refined_context['peer_responses'] = {
            agent_id: result.get('response', {}).get('content', '') 
            for agent_id, result in initial_results.items()
            if 'response' in result and result['response'].get('status') == 'completed'
        }
        
        # Second round with collaborative context
        collaboration_prompt = f"Original task: {job.description}\n\nConsidering peer insights, provide your refined response."
        
        refined_tasks = []
        for agent_id in team.agents:
            agent_instance = self.registry.get_agent_instance(agent_id)
            if agent_instance:
                task = agent_instance.execute(collaboration_prompt, refined_context)
                refined_tasks.append((agent_id, task))
        
        refined_results = {}
        responses = await asyncio.gather(*[task for _, task in refined_tasks], return_exceptions=True)
        
        for (agent_id, _), response in zip(refined_tasks, responses):
            if isinstance(response, Exception):
                # Fall back to initial result if refinement fails
                refined_results[agent_id] = initial_results.get(agent_id, {"error": str(response)})
            else:
                refined_results[agent_id] = {
                    "initial_response": initial_results.get(agent_id, {}),
                    "refined_response": response.to_dict(),
                    "role": team.roles.get(agent_id, "unknown")
                }
        
        return refined_results
    
    def _evaluate_team_performance(self, team: TeamConfiguration, results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate team performance for this execution"""
        total_agents = len(team.agents)
        successful_agents = sum(1 for result in results.values() 
                               if 'response' in result and not result.get('error'))
        
        return {
            "team_size": total_agents,
            "successful_agents": successful_agents,
            "success_rate": successful_agents / total_agents if total_agents > 0 else 0,
            "coordination_strategy": team.coordination_strategy,
            "execution_time": "calculated_elsewhere"  # Would be calculated from timing
        }
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of job execution"""
        execution = self.running_executions.get(execution_id)
        if not execution:
            return None
        
        result = {
            "execution_id": execution.execution_id,
            "job_id": execution.job_id,
            "team_id": execution.team_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error_message": execution.error_message
        }
        
        if execution.results:
            result["results"] = execution.results
        
        # Add team info if available
        team = self.active_teams.get(execution.team_id)
        if team:
            result["team"] = team.to_dict()
        
        return result
    
    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all active job executions"""
        return [
            self.get_execution_status(execution_id) 
            for execution_id in self.running_executions.keys()
        ]
    
    def get_agent_workloads(self) -> Dict[str, int]:
        """Get current workload for all agents"""
        return self.agent_workloads.copy()
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.running_executions.get(execution_id)
        if not execution or execution.status not in ["queued", "running"]:
            return False
        
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        execution.error_message = "Execution cancelled by user"
        
        # Update agent workloads
        team = self.active_teams.get(execution.team_id)
        if team:
            for agent_id in team.agents:
                self.agent_workloads[agent_id] = max(0, self.agent_workloads.get(agent_id, 1) - 1)
        
        return True

# Global orchestrator instance
_global_orchestrator = None

def get_orchestrator() -> TeamOrchestrator:
    """Get global team orchestrator instance"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = TeamOrchestrator()
    return _global_orchestrator

# Convenience functions
async def submit_job(description: str, required_capabilities: List[str] = None, **kwargs) -> str:
    """
    Submit a job for execution by optimal agent team
    
    Args:
        description: Job description
        required_capabilities: Required agent capabilities
        **kwargs: Additional job parameters
        
    Returns:
        Execution ID for tracking
    """
    orchestrator = get_orchestrator()
    
    job = JobRequirement(
        job_id=str(uuid.uuid4()),
        description=description,
        required_capabilities=required_capabilities or [],
        **kwargs
    )
    
    return await orchestrator.submit_job(job)

def get_job_status(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get job execution status"""
    orchestrator = get_orchestrator()
    return orchestrator.get_execution_status(execution_id)

def list_jobs() -> List[Dict[str, Any]]:
    """List all active job executions"""
    orchestrator = get_orchestrator()
    return orchestrator.list_active_executions()