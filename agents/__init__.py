"""
JuniorGPT Agent System

A comprehensive framework for modular, independent AI agents that can work
individually or collaborate in teams to solve complex tasks.

Key Components:
- BaseAgent: Foundation class for all agents
- AgentRegistry: Discovery and management system
- TeamOrchestrator: Dynamic team formation and coordination
- MicroserviceDeployer: Independent service deployment
- JobDispatcher: High-level job assignment and execution
"""

from .base_agent import BaseAgent, AgentConfig, AgentResponse, AgentStatus
from .agent_registry import (
    get_registry, 
    discover_agents, 
    register_agent, 
    get_agent_instance,
    list_agents,
    find_capable_agents
)
from .team_orchestrator import (
    get_orchestrator,
    submit_job as submit_team_job,
    get_job_status as get_team_job_status,
    list_jobs as list_team_jobs,
    JobRequirement,
    TeamConfiguration
)
from .microservice_deployer import (
    get_deployer,
    deploy_agent,
    undeploy_agent,
    list_services,
    health_check_services
)
from .job_dispatcher import (
    get_dispatcher,
    dispatch_job,
    get_job_status,
    list_jobs,
    JobRequest,
    ExecutionPlan
)

# Import agent implementations
from .implementations.coding_agent import CodingAgent
from .implementations.research_agent import ResearchAgent

__version__ = "2.0.0"
__author__ = "JuniorGPT Team"

__all__ = [
    # Core classes
    "BaseAgent",
    "AgentConfig", 
    "AgentResponse",
    "AgentStatus",
    
    # Registry functions
    "get_registry",
    "discover_agents",
    "register_agent", 
    "get_agent_instance",
    "list_agents",
    "find_capable_agents",
    
    # Team orchestration
    "get_orchestrator",
    "submit_team_job",
    "get_team_job_status", 
    "list_team_jobs",
    "JobRequirement",
    "TeamConfiguration",
    
    # Microservice deployment
    "get_deployer",
    "deploy_agent",
    "undeploy_agent",
    "list_services",
    "health_check_services",
    
    # Job dispatching
    "get_dispatcher",
    "dispatch_job",
    "get_job_status",
    "list_jobs",
    "JobRequest",
    "ExecutionPlan",
    
    # Agent implementations
    "CodingAgent",
    "ResearchAgent"
]

def initialize_system():
    """
    Initialize the agent system with automatic discovery and setup
    
    This function should be called at application startup to:
    1. Discover and register all available agents
    2. Initialize core services
    3. Prepare the system for job execution
    """
    # Discover agents
    discovered_count = discover_agents()
    print(f"Discovered {discovered_count} agents")
    
    # Initialize services
    registry = get_registry()
    orchestrator = get_orchestrator()
    deployer = get_deployer()
    dispatcher = get_dispatcher()
    
    print("JuniorGPT Agent System initialized successfully")
    
    return {
        "agents_discovered": discovered_count,
        "registry": registry,
        "orchestrator": orchestrator,
        "deployer": deployer,
        "dispatcher": dispatcher
    }

async def quick_start_example():
    """
    Quick start example demonstrating the agent system capabilities
    """
    print("JuniorGPT Agent System - Quick Start Example")
    print("=" * 50)
    
    # Initialize system
    init_result = initialize_system()
    
    # List available agents
    agents = list_agents()
    print(f"\nAvailable Agents ({len(agents)}):")
    for agent in agents[:5]:  # Show first 5
        print(f"  - {agent['config'].name}: {agent['config'].description}")
    
    # Example 1: Simple job dispatch
    print("\nExample 1: Simple Job Dispatch")
    try:
        job_id = await dispatch_job(
            "Write a Python function to calculate factorial",
            requirements=["programming", "python"]
        )
        print(f"Job dispatched with ID: {job_id}")
        
        # Check status
        status = get_job_status(job_id)
        print(f"Job status: {status['status'] if status else 'Not found'}")
        
    except Exception as e:
        print(f"Job dispatch failed: {e}")
    
    # Example 2: Deploy agent as microservice
    print("\nExample 2: Microservice Deployment")
    try:
        service_id = await deploy_agent("coding")
        if service_id:
            print(f"Coding agent deployed as service: {service_id}")
        else:
            print("Failed to deploy coding agent")
    except Exception as e:
        print(f"Deployment failed: {e}")
    
    # Example 3: Team collaboration
    print("\nExample 3: Team Collaboration")
    try:
        team_job_id = await submit_team_job(
            "Research and analyze the latest trends in AI development, then create a comprehensive report",
            required_capabilities=["research", "analysis", "writing"]
        )
        print(f"Team job submitted with ID: {team_job_id}")
    except Exception as e:
        print(f"Team job failed: {e}")
    
    print("\nQuick start example completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(quick_start_example())