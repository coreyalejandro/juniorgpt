"""
Microservice Deployer - Automatically deploy agents as independent microservices

This module handles the deployment and management of agents as standalone
microservices, enabling true modularity and independent scaling.
"""
import asyncio
import subprocess
import logging
import json
import socket
import time
import os
import signal
import yaml
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .agent_registry import get_registry
from .agent_server import create_agent_app

logger = logging.getLogger('juniorgpt.microservice_deployer')

@dataclass
class ServiceDeployment:
    """Represents a deployed agent microservice"""
    service_id: str
    agent_id: str
    port: int
    process_id: int
    endpoint: str
    status: str  # starting, running, stopped, error
    deployed_at: datetime
    config: Dict[str, Any]
    health_check_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['deployed_at'] = self.deployed_at.isoformat()
        return result

class MicroserviceDeployer:
    """
    Manages deployment of agents as independent microservices
    
    Features:
    - Automatic port allocation
    - Process management
    - Health monitoring
    - Service discovery
    - Load balancing
    - Auto-scaling
    """
    
    def __init__(self, base_port: int = 8000, max_services: int = 100):
        self.base_port = base_port
        self.max_services = max_services
        self.registry = get_registry()
        
        # Track deployed services
        self.deployments: Dict[str, ServiceDeployment] = {}
        self.port_allocations: Dict[int, str] = {}  # port -> service_id
        
        # Configuration
        self.deployment_configs = self._load_deployment_configs()
        self.default_config = {
            "memory_limit": "512m",
            "cpu_limit": "0.5",
            "restart_policy": "always",
            "health_check_interval": 30,
            "timeout": 60
        }
    
    def _load_deployment_configs(self) -> Dict[str, Any]:
        """Load deployment configurations from file"""
        config_path = Path("config/deployments.yaml")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load deployment configs: {e}")
        return {}
    
    def _find_available_port(self) -> Optional[int]:
        """Find an available port for service deployment"""
        for port in range(self.base_port, self.base_port + self.max_services):
            if port not in self.port_allocations and self._is_port_available(port):
                return port
        return None
    
    def _is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    async def deploy_agent_service(
        self, 
        agent_id: str, 
        config: Dict[str, Any] = None
    ) -> Optional[ServiceDeployment]:
        """
        Deploy an agent as a microservice
        
        Args:
            agent_id: Agent identifier to deploy
            config: Optional deployment configuration
            
        Returns:
            Service deployment info or None if failed
        """
        logger.info(f"Deploying agent {agent_id} as microservice")
        
        # Check if agent exists
        agent_class = self.registry.get_agent_class(agent_id)
        if not agent_class:
            logger.error(f"Agent {agent_id} not found in registry")
            return None
        
        # Check if already deployed
        if any(d.agent_id == agent_id for d in self.deployments.values()):
            logger.warning(f"Agent {agent_id} already deployed")
            return None
        
        # Allocate port
        port = self._find_available_port()
        if not port:
            logger.error("No available ports for deployment")
            return None
        
        # Merge configurations
        deployment_config = self.default_config.copy()
        if agent_id in self.deployment_configs:
            deployment_config.update(self.deployment_configs[agent_id])
        if config:
            deployment_config.update(config)
        
        service_id = f"{agent_id}-service-{int(time.time())}"
        endpoint = f"http://localhost:{port}"
        health_check_url = f"{endpoint}/health"
        
        try:
            # Create deployment
            deployment = ServiceDeployment(
                service_id=service_id,
                agent_id=agent_id,
                port=port,
                process_id=0,  # Will be set when process starts
                endpoint=endpoint,
                status="starting",
                deployed_at=datetime.utcnow(),
                config=deployment_config,
                health_check_url=health_check_url
            )
            
            # Start the service process
            process = await self._start_service_process(agent_id, port, deployment_config)
            if not process:
                logger.error(f"Failed to start service process for {agent_id}")
                return None
            
            deployment.process_id = process.pid
            
            # Wait for service to be ready
            if await self._wait_for_service_ready(health_check_url, timeout=30):
                deployment.status = "running"
                
                # Register deployment
                self.deployments[service_id] = deployment
                self.port_allocations[port] = service_id
                
                # Update agent registry with endpoint
                await self._register_service_endpoint(agent_id, endpoint)
                
                logger.info(f"Successfully deployed {agent_id} at {endpoint}")
                return deployment
            else:
                deployment.status = "error"
                logger.error(f"Service {service_id} failed to become ready")
                
                # Cleanup failed deployment
                try:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.poll() is None:
                        process.kill()
                except:
                    pass
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to deploy agent {agent_id}: {e}")
            return None
    
    async def _start_service_process(
        self, 
        agent_id: str, 
        port: int, 
        config: Dict[str, Any]
    ) -> Optional[subprocess.Popen]:
        """Start the agent service process"""
        
        # Create service script
        service_script = self._generate_service_script(agent_id, port, config)
        script_path = Path(f"temp/service_{agent_id}_{port}.py")
        script_path.parent.mkdir(exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(service_script)
        
        # Start process
        env = os.environ.copy()
        env['AGENT_ID'] = agent_id
        env['SERVICE_PORT'] = str(port)
        
        try:
            process = subprocess.Popen(
                ['python', str(script_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            logger.info(f"Started service process {process.pid} for agent {agent_id}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start service process: {e}")
            return None
    
    def _generate_service_script(self, agent_id: str, port: int, config: Dict[str, Any]) -> str:
        """Generate Python script for running agent service"""
        return f"""#!/usr/bin/env python3
\"\"\"
Auto-generated service script for agent: {agent_id}
Port: {port}
Generated at: {datetime.utcnow().isoformat()}
\"\"\"
import os
import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.agent_registry import get_registry
from agents.agent_server import create_agent_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_service_{agent_id}')

def main():
    try:
        # Get agent from registry
        registry = get_registry()
        
        # Discover agents if not already done
        registry.discover_agents()
        
        # Get agent instance
        agent_instance = registry.get_agent_instance('{agent_id}')
        if not agent_instance:
            logger.error("Failed to create agent instance")
            return 1
        
        # Create Flask app
        app = create_agent_app(agent_instance)
        
        # Configure app
        app.config.update({config})
        
        # Run service
        logger.info(f"Starting agent service on port {port}")
        app.run(
            host='0.0.0.0',
            port={port},
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Service failed: {{e}}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
"""
    
    async def _wait_for_service_ready(self, health_url: str, timeout: int = 30) -> bool:
        """Wait for service to be ready"""
        import httpx
        
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'ok':
                            return True
            except:
                pass
            
            await asyncio.sleep(2)
        
        return False
    
    async def _register_service_endpoint(self, agent_id: str, endpoint: str):
        """Register service endpoint in agent configuration"""
        # This would update the agent configuration to include the endpoint
        # For now, we'll update the registry metadata
        try:
            metadata = self.registry.get_agent_metadata(agent_id)
            if metadata:
                metadata['endpoint'] = endpoint
                metadata['deployment_type'] = 'microservice'
                logger.info(f"Registered endpoint {endpoint} for agent {agent_id}")
        except Exception as e:
            logger.warning(f"Failed to register endpoint: {e}")
    
    async def undeploy_service(self, service_id: str) -> bool:
        """
        Undeploy a service
        
        Args:
            service_id: Service identifier
            
        Returns:
            True if successful
        """
        deployment = self.deployments.get(service_id)
        if not deployment:
            logger.warning(f"Service {service_id} not found")
            return False
        
        logger.info(f"Undeploying service {service_id}")
        
        try:
            # Stop the process
            if deployment.process_id:
                try:
                    # Send SIGTERM to process group
                    os.killpg(os.getpgid(deployment.process_id), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    await asyncio.sleep(5)
                    
                    # Force kill if still running
                    try:
                        os.killpg(os.getpgid(deployment.process_id), signal.SIGKILL)
                    except:
                        pass
                        
                except ProcessLookupError:
                    pass  # Process already terminated
            
            # Cleanup
            if deployment.port in self.port_allocations:
                del self.port_allocations[deployment.port]
            
            del self.deployments[service_id]
            
            # Remove endpoint from registry
            await self._unregister_service_endpoint(deployment.agent_id)
            
            logger.info(f"Successfully undeployed service {service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to undeploy service {service_id}: {e}")
            return False
    
    async def _unregister_service_endpoint(self, agent_id: str):
        """Remove service endpoint from agent configuration"""
        try:
            metadata = self.registry.get_agent_metadata(agent_id)
            if metadata:
                metadata.pop('endpoint', None)
                metadata.pop('deployment_type', None)
        except Exception as e:
            logger.warning(f"Failed to unregister endpoint: {e}")
    
    async def health_check_service(self, service_id: str) -> Dict[str, Any]:
        """Perform health check on service"""
        deployment = self.deployments.get(service_id)
        if not deployment:
            return {"status": "not_found"}
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(deployment.health_check_url, timeout=10)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "service_id": service_id,
                        "endpoint": deployment.endpoint,
                        "response": response.json()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "service_id": service_id,
                        "endpoint": deployment.endpoint,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "service_id": service_id,
                "endpoint": deployment.endpoint,
                "error": str(e)
            }
    
    async def health_check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Health check all deployed services"""
        results = {}
        
        tasks = [
            (service_id, self.health_check_service(service_id))
            for service_id in self.deployments.keys()
        ]
        
        for service_id, task in tasks:
            try:
                result = await task
                results[service_id] = result
            except Exception as e:
                results[service_id] = {
                    "status": "error",
                    "service_id": service_id,
                    "error": str(e)
                }
        
        return results
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all current deployments"""
        return [deployment.to_dict() for deployment in self.deployments.values()]
    
    def get_deployment(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get specific deployment info"""
        deployment = self.deployments.get(service_id)
        return deployment.to_dict() if deployment else None
    
    async def scale_agent_services(self, agent_id: str, target_instances: int) -> List[str]:
        """
        Scale agent services to target number of instances
        
        Args:
            agent_id: Agent to scale
            target_instances: Target number of instances
            
        Returns:
            List of service IDs for the agent
        """
        # Find current instances
        current_services = [
            d for d in self.deployments.values() 
            if d.agent_id == agent_id
        ]
        current_count = len(current_services)
        
        logger.info(f"Scaling {agent_id}: {current_count} -> {target_instances}")
        
        service_ids = [s.service_id for s in current_services]
        
        if target_instances > current_count:
            # Scale up
            for _ in range(target_instances - current_count):
                deployment = await self.deploy_agent_service(agent_id)
                if deployment:
                    service_ids.append(deployment.service_id)
        elif target_instances < current_count:
            # Scale down
            services_to_remove = current_services[target_instances:]
            for service in services_to_remove:
                await self.undeploy_service(service.service_id)
                service_ids.remove(service.service_id)
        
        return service_ids
    
    async def auto_scale_based_on_load(self):
        """Automatically scale services based on load metrics"""
        # This would implement auto-scaling logic based on:
        # - CPU/memory usage
        # - Request queue length
        # - Response times
        # - Error rates
        
        for agent_id in set(d.agent_id for d in self.deployments.values()):
            # Get load metrics for agent
            load_metrics = await self._get_agent_load_metrics(agent_id)
            
            # Determine if scaling is needed
            if load_metrics.get('avg_cpu_percent', 0) > 80:
                # Scale up
                current_instances = len([d for d in self.deployments.values() if d.agent_id == agent_id])
                await self.scale_agent_services(agent_id, current_instances + 1)
            elif load_metrics.get('avg_cpu_percent', 0) < 20:
                # Scale down (but keep at least 1 instance)
                current_instances = len([d for d in self.deployments.values() if d.agent_id == agent_id])
                if current_instances > 1:
                    await self.scale_agent_services(agent_id, current_instances - 1)
    
    async def _get_agent_load_metrics(self, agent_id: str) -> Dict[str, float]:
        """Get load metrics for an agent's services"""
        services = [d for d in self.deployments.values() if d.agent_id == agent_id]
        
        if not services:
            return {}
        
        # This would collect actual metrics from the services
        # For now, return dummy metrics
        return {
            'avg_cpu_percent': 50.0,
            'avg_memory_percent': 60.0,
            'avg_response_time': 200.0,
            'total_requests': 1000,
            'error_rate': 0.1
        }
    
    def generate_docker_compose(self, output_file: str = "docker-compose.yml"):
        """Generate Docker Compose configuration for all services"""
        services = {}
        
        for deployment in self.deployments.values():
            service_name = f"agent-{deployment.agent_id}"
            services[service_name] = {
                'build': {
                    'context': '.',
                    'dockerfile': f'Dockerfile.agent.{deployment.agent_id}'
                },
                'ports': [f"{deployment.port}:{deployment.port}"],
                'environment': {
                    'AGENT_ID': deployment.agent_id,
                    'SERVICE_PORT': deployment.port
                },
                'restart': 'unless-stopped',
                'healthcheck': {
                    'test': f"curl -f {deployment.health_check_url} || exit 1",
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
            }
        
        compose_config = {
            'version': '3.8',
            'services': services
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        logger.info(f"Generated Docker Compose configuration: {output_file}")

# Global deployer instance
_global_deployer = None

def get_deployer() -> MicroserviceDeployer:
    """Get global microservice deployer instance"""
    global _global_deployer
    if _global_deployer is None:
        _global_deployer = MicroserviceDeployer()
    return _global_deployer

# Convenience functions
async def deploy_agent(agent_id: str, config: Dict[str, Any] = None) -> Optional[str]:
    """
    Deploy agent as microservice
    
    Args:
        agent_id: Agent to deploy
        config: Optional deployment config
        
    Returns:
        Service ID if successful
    """
    deployer = get_deployer()
    deployment = await deployer.deploy_agent_service(agent_id, config)
    return deployment.service_id if deployment else None

async def undeploy_agent(service_id: str) -> bool:
    """Undeploy agent service"""
    deployer = get_deployer()
    return await deployer.undeploy_service(service_id)

def list_services() -> List[Dict[str, Any]]:
    """List all deployed services"""
    deployer = get_deployer()
    return deployer.list_deployments()

async def health_check_services() -> Dict[str, Dict[str, Any]]:
    """Health check all services"""
    deployer = get_deployer()
    return await deployer.health_check_all_services()