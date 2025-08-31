"""
Job Dispatcher - Central coordination system for job assignment and execution

This module provides a high-level interface for submitting jobs and automatically
determining the best execution strategy using teams, individual agents, or microservices.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json

from .team_orchestrator import TeamOrchestrator, JobRequirement, get_orchestrator
from .microservice_deployer import MicroserviceDeployer, get_deployer
from .agent_registry import get_registry

logger = logging.getLogger('juniorgpt.job_dispatcher')

@dataclass
class JobRequest:
    """High-level job request"""
    description: str
    requirements: List[str] = None
    preferences: Dict[str, Any] = None
    priority: str = "normal"
    execution_strategy: str = "auto"  # auto, team, single, microservice
    timeout: int = 300
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.preferences is None:
            self.preferences = {}
        if self.context is None:
            self.context = {}

@dataclass
class ExecutionPlan:
    """Execution plan determined by dispatcher"""
    plan_id: str
    strategy: str  # team, single_agent, microservice, hybrid
    agents: List[str]
    estimated_time: float
    confidence: float
    resources_required: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result

class JobDispatcher:
    """
    Central job dispatch and coordination system
    
    Features:
    - Intelligent execution strategy selection
    - Automatic resource allocation
    - Load balancing across agents and services
    - Job queuing and prioritization
    - Real-time monitoring and reporting
    """
    
    def __init__(self):
        self.registry = get_registry()
        self.orchestrator = get_orchestrator()
        self.deployer = get_deployer()
        
        # Job tracking
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Strategy weights (can be tuned based on performance)
        self.strategy_weights = {
            "team_collaboration": 0.3,
            "single_agent_efficiency": 0.2,
            "microservice_scalability": 0.3,
            "resource_availability": 0.2
        }
    
    async def submit_job(self, job_request: JobRequest) -> str:
        """
        Submit job for execution with automatic strategy selection
        
        Args:
            job_request: Job request specification
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        logger.info(f"Dispatching job {job_id}: {job_request.description[:100]}...")
        
        try:
            # Create execution plan
            execution_plan = await self._create_execution_plan(job_request)
            
            # Execute based on plan
            execution_result = await self._execute_plan(job_id, job_request, execution_plan)
            
            # Track job
            self.active_jobs[job_id] = {
                "request": asdict(job_request),
                "plan": execution_plan.to_dict(),
                "execution": execution_result,
                "status": "running",
                "started_at": datetime.utcnow().isoformat()
            }
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to dispatch job {job_id}: {e}")
            self.active_jobs[job_id] = {
                "request": asdict(job_request),
                "status": "failed",
                "error": str(e),
                "started_at": datetime.utcnow().isoformat()
            }
            raise
    
    async def _create_execution_plan(self, job_request: JobRequest) -> ExecutionPlan:
        """
        Create optimal execution plan for job
        
        Args:
            job_request: Job request
            
        Returns:
            Execution plan
        """
        logger.info("Creating execution plan...")
        
        # Analyze job characteristics
        job_analysis = self._analyze_job_complexity(job_request)
        
        # Get available resources
        available_agents = self._get_available_agents()
        available_services = self._get_available_microservices()
        
        # Evaluate execution strategies
        strategies = await self._evaluate_strategies(job_request, job_analysis, available_agents, available_services)
        
        # Select best strategy
        best_strategy = max(strategies, key=lambda s: s['score'])
        
        execution_plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            strategy=best_strategy['name'],
            agents=best_strategy['agents'],
            estimated_time=best_strategy['estimated_time'],
            confidence=best_strategy['score'],
            resources_required=best_strategy['resources'],
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Selected strategy: {execution_plan.strategy} (confidence: {execution_plan.confidence:.2f})")
        return execution_plan
    
    def _analyze_job_complexity(self, job_request: JobRequest) -> Dict[str, Any]:
        """Analyze job complexity and characteristics"""
        description = job_request.description.lower()
        
        # Complexity indicators
        complexity_score = 0
        if len(description) > 200:
            complexity_score += 1
        if any(word in description for word in ["complex", "detailed", "comprehensive", "thorough"]):
            complexity_score += 2
        if len(job_request.requirements) > 3:
            complexity_score += 1
        
        # Collaboration indicators
        collaboration_score = 0
        if any(word in description for word in ["research", "analyze", "compare", "evaluate"]):
            collaboration_score += 2
        if any(word in description for word in ["multiple", "different", "various", "perspectives"]):
            collaboration_score += 1
        
        # Time sensitivity
        urgency_score = 0
        if any(word in description for word in ["urgent", "asap", "immediately", "quickly"]):
            urgency_score += 2
        if job_request.priority in ["high", "critical"]:
            urgency_score += 1
        
        return {
            "complexity": min(complexity_score, 5),
            "collaboration_benefit": min(collaboration_score, 5),
            "urgency": min(urgency_score, 5),
            "estimated_tokens": len(description.split()) * 4,  # Rough estimate
            "requires_specialization": len(job_request.requirements) > 0
        }
    
    def _get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        return list(self.registry.agents.keys())
    
    def _get_available_microservices(self) -> List[str]:
        """Get list of available microservices"""
        deployments = self.deployer.list_deployments()
        return [d['service_id'] for d in deployments if d['status'] == 'running']
    
    async def _evaluate_strategies(
        self, 
        job_request: JobRequest, 
        job_analysis: Dict[str, Any],
        available_agents: List[str],
        available_services: List[str]
    ) -> List[Dict[str, Any]]:
        """Evaluate different execution strategies"""
        
        strategies = []
        
        # Strategy 1: Single Agent
        single_agent_strategy = await self._evaluate_single_agent_strategy(
            job_request, job_analysis, available_agents
        )
        if single_agent_strategy:
            strategies.append(single_agent_strategy)
        
        # Strategy 2: Team Collaboration
        team_strategy = await self._evaluate_team_strategy(
            job_request, job_analysis, available_agents
        )
        if team_strategy:
            strategies.append(team_strategy)
        
        # Strategy 3: Microservice
        microservice_strategy = await self._evaluate_microservice_strategy(
            job_request, job_analysis, available_services
        )
        if microservice_strategy:
            strategies.append(microservice_strategy)
        
        # Strategy 4: Hybrid (team + microservices)
        hybrid_strategy = await self._evaluate_hybrid_strategy(
            job_request, job_analysis, available_agents, available_services
        )
        if hybrid_strategy:
            strategies.append(hybrid_strategy)
        
        return strategies
    
    async def _evaluate_single_agent_strategy(
        self, 
        job_request: JobRequest, 
        job_analysis: Dict[str, Any],
        available_agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate single agent execution strategy"""
        
        # Find best agent for the job
        best_agent = None
        best_score = 0
        
        for agent_id in available_agents:
            try:
                agent_class = self.registry.get_agent_class(agent_id)
                if agent_class:
                    temp_instance = agent_class()
                    score = temp_instance.can_handle(job_request.description, job_request.context)
                    
                    if score > best_score:
                        best_score = score
                        best_agent = agent_id
            except:
                continue
        
        if not best_agent or best_score < 0.3:
            return None
        
        # Calculate strategy score
        strategy_score = best_score * 0.8  # Base agent capability
        
        # Bonus for simplicity
        if job_analysis['complexity'] <= 2:
            strategy_score += 0.2
        
        # Penalty for jobs that benefit from collaboration
        if job_analysis['collaboration_benefit'] > 3:
            strategy_score -= 0.3
        
        return {
            "name": "single_agent",
            "agents": [best_agent],
            "score": max(0, strategy_score),
            "estimated_time": 60,  # Base estimate
            "resources": {"agents": 1, "memory": "low", "cpu": "low"}
        }
    
    async def _evaluate_team_strategy(
        self, 
        job_request: JobRequest, 
        job_analysis: Dict[str, Any],
        available_agents: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate team collaboration strategy"""
        
        # Create temporary job requirement for team formation
        job_req = JobRequirement(
            job_id="temp",
            description=job_request.description,
            required_capabilities=job_request.requirements,
            max_agents=3
        )
        
        # Try to form team
        team = await self.orchestrator._form_team_for_job(job_req)
        if not team or len(team.agents) < 2:
            return None
        
        # Calculate strategy score
        strategy_score = 0.7  # Base team score
        
        # Bonus for complex jobs
        if job_analysis['complexity'] > 2:
            strategy_score += 0.2
        
        # Bonus for jobs that benefit from collaboration
        if job_analysis['collaboration_benefit'] > 2:
            strategy_score += 0.3
        
        # Penalty for urgent jobs (team coordination takes time)
        if job_analysis['urgency'] > 2:
            strategy_score -= 0.2
        
        return {
            "name": "team_collaboration",
            "agents": team.agents,
            "score": max(0, strategy_score),
            "estimated_time": 120 + (len(team.agents) * 20),  # Extra time for coordination
            "resources": {"agents": len(team.agents), "memory": "medium", "cpu": "medium"}
        }
    
    async def _evaluate_microservice_strategy(
        self, 
        job_request: JobRequest, 
        job_analysis: Dict[str, Any],
        available_services: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate microservice execution strategy"""
        
        if not available_services:
            return None
        
        # Simple heuristic: use microservice for scalable/repeatable tasks
        strategy_score = 0.5  # Base microservice score
        
        # Bonus for high-load scenarios (not directly detectable from request, so use urgency as proxy)
        if job_analysis['urgency'] > 2:
            strategy_score += 0.3
        
        # Bonus for standardized requirements
        if len(job_request.requirements) <= 2:
            strategy_score += 0.2
        
        return {
            "name": "microservice",
            "agents": available_services[:1],  # Use one service
            "score": strategy_score,
            "estimated_time": 30,  # Generally faster due to dedicated resources
            "resources": {"services": 1, "memory": "high", "cpu": "high"}
        }
    
    async def _evaluate_hybrid_strategy(
        self, 
        job_request: JobRequest, 
        job_analysis: Dict[str, Any],
        available_agents: List[str],
        available_services: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate hybrid execution strategy"""
        
        if not available_services or len(available_agents) < 2:
            return None
        
        # Hybrid is good for complex jobs that can benefit from both collaboration and scalability
        if job_analysis['complexity'] < 3 or job_analysis['collaboration_benefit'] < 2:
            return None
        
        strategy_score = 0.6  # Base hybrid score
        
        # Bonus for very complex jobs
        if job_analysis['complexity'] > 3:
            strategy_score += 0.3
        
        return {
            "name": "hybrid",
            "agents": available_agents[:2] + available_services[:1],
            "score": strategy_score,
            "estimated_time": 90,
            "resources": {"agents": 2, "services": 1, "memory": "high", "cpu": "high"}
        }
    
    async def _execute_plan(self, job_id: str, job_request: JobRequest, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute the planned strategy
        
        Args:
            job_id: Job identifier
            job_request: Original job request
            execution_plan: Execution plan
            
        Returns:
            Execution result tracking info
        """
        logger.info(f"Executing plan for job {job_id} using strategy: {execution_plan.strategy}")
        
        if execution_plan.strategy == "single_agent":
            return await self._execute_single_agent_plan(job_id, job_request, execution_plan)
        elif execution_plan.strategy == "team_collaboration":
            return await self._execute_team_plan(job_id, job_request, execution_plan)
        elif execution_plan.strategy == "microservice":
            return await self._execute_microservice_plan(job_id, job_request, execution_plan)
        elif execution_plan.strategy == "hybrid":
            return await self._execute_hybrid_plan(job_id, job_request, execution_plan)
        else:
            raise ValueError(f"Unknown execution strategy: {execution_plan.strategy}")
    
    async def _execute_single_agent_plan(self, job_id: str, job_request: JobRequest, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute single agent plan"""
        agent_id = execution_plan.agents[0]
        agent_instance = self.registry.get_agent_instance(agent_id)
        
        if not agent_instance:
            raise RuntimeError(f"Cannot get instance of agent {agent_id}")
        
        # Execute
        response = await agent_instance.execute(job_request.description, job_request.context)
        
        return {
            "execution_type": "single_agent",
            "agent_id": agent_id,
            "response": response.to_dict()
        }
    
    async def _execute_team_plan(self, job_id: str, job_request: JobRequest, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute team collaboration plan"""
        # Convert to job requirement format
        job_req = JobRequirement(
            job_id=job_id,
            description=job_request.description,
            required_capabilities=job_request.requirements,
            context=job_request.context,
            timeout=job_request.timeout
        )
        
        # Submit to orchestrator
        execution_id = await self.orchestrator.submit_job(job_req)
        
        return {
            "execution_type": "team_collaboration",
            "orchestrator_execution_id": execution_id,
            "agents": execution_plan.agents
        }
    
    async def _execute_microservice_plan(self, job_id: str, job_request: JobRequest, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute microservice plan"""
        service_id = execution_plan.agents[0]  # Service ID stored in agents field
        deployment = self.deployer.get_deployment(service_id)
        
        if not deployment:
            raise RuntimeError(f"Service {service_id} not found")
        
        # Call microservice endpoint
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{deployment['endpoint']}/process",
                json={
                    "message": job_request.description,
                    "context": job_request.context
                },
                timeout=job_request.timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Service call failed: {response.status_code}")
            
            result = response.json()
        
        return {
            "execution_type": "microservice",
            "service_id": service_id,
            "endpoint": deployment['endpoint'],
            "response": result
        }
    
    async def _execute_hybrid_plan(self, job_id: str, job_request: JobRequest, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute hybrid plan"""
        # For hybrid, we'll run both team and microservice in parallel and combine results
        
        # Split agents and services
        agents = [a for a in execution_plan.agents if not a.startswith('agent-')]
        services = [a for a in execution_plan.agents if a.startswith('agent-')]
        
        tasks = []
        
        # Team execution
        if len(agents) >= 2:
            job_req = JobRequirement(
                job_id=f"{job_id}-team",
                description=job_request.description,
                required_capabilities=job_request.requirements,
                context=job_request.context,
                max_agents=len(agents)
            )
            tasks.append(("team", self.orchestrator.submit_job(job_req)))
        
        # Service execution
        if services:
            service_id = services[0]
            deployment = self.deployer.get_deployment(service_id)
            if deployment:
                import httpx
                async def call_service():
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{deployment['endpoint']}/process",
                            json={
                                "message": job_request.description,
                                "context": job_request.context
                            },
                            timeout=job_request.timeout
                        )
                        return response.json()
                
                tasks.append(("service", call_service()))
        
        # Execute all tasks
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        hybrid_results = {}
        for (task_type, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                hybrid_results[task_type] = {"error": str(result)}
            else:
                hybrid_results[task_type] = {"result": result}
        
        return {
            "execution_type": "hybrid",
            "components": hybrid_results,
            "agents": agents,
            "services": services
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and results"""
        return self.active_jobs.get(job_id)
    
    def list_active_jobs(self) -> List[Dict[str, Any]]:
        """List all active jobs"""
        return [
            {"job_id": job_id, **info}
            for job_id, info in self.active_jobs.items()
        ]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return False
        
        # Cancel based on execution type
        execution = job_info.get("execution", {})
        execution_type = execution.get("execution_type")
        
        try:
            if execution_type == "team_collaboration":
                orchestrator_id = execution.get("orchestrator_execution_id")
                if orchestrator_id:
                    return self.orchestrator.cancel_execution(orchestrator_id)
            
            # Mark as cancelled locally
            job_info["status"] = "cancelled"
            job_info["cancelled_at"] = datetime.utcnow().isoformat()
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        return {
            "active_jobs": len(self.active_jobs),
            "available_agents": len(self._get_available_agents()),
            "running_services": len(self._get_available_microservices()),
            "strategy_weights": self.strategy_weights.copy(),
            "execution_history_length": len(self.execution_history)
        }

# Global dispatcher instance
_global_dispatcher = None

def get_dispatcher() -> JobDispatcher:
    """Get global job dispatcher instance"""
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = JobDispatcher()
    return _global_dispatcher

# Convenience functions
async def dispatch_job(description: str, **kwargs) -> str:
    """
    Dispatch job with automatic strategy selection
    
    Args:
        description: Job description
        **kwargs: Additional job parameters
        
    Returns:
        Job ID for tracking
    """
    dispatcher = get_dispatcher()
    job_request = JobRequest(description=description, **kwargs)
    return await dispatcher.submit_job(job_request)

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status"""
    dispatcher = get_dispatcher()
    return dispatcher.get_job_status(job_id)

def list_jobs() -> List[Dict[str, Any]]:
    """List all active jobs"""
    dispatcher = get_dispatcher()
    return dispatcher.list_active_jobs()