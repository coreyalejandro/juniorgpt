"""
Agent Loader - Dynamic loading and management of plug-and-play agents

This module provides utilities for loading, installing, and managing
self-contained agent applications.
"""
import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from .agent_registry import get_registry, AgentRegistry
from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger('juniorgpt.agent_loader')

class AgentPackage:
    """Represents a packaged agent application"""
    
    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        self.manifest = {}
        self.extracted_path = None
        
        self._load_manifest()
    
    def _load_manifest(self):
        """Load agent package manifest"""
        if self.package_path.is_file() and self.package_path.suffix == '.zip':
            # Load from zip file
            with zipfile.ZipFile(self.package_path, 'r') as zip_file:
                if 'agent.json' in zip_file.namelist():
                    with zip_file.open('agent.json') as f:
                        self.manifest = json.load(f)
                else:
                    raise ValueError("Invalid agent package: missing agent.json manifest")
        elif self.package_path.is_dir():
            # Load from directory
            manifest_file = self.package_path / 'agent.json'
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    self.manifest = json.load(f)
            else:
                raise ValueError("Invalid agent package: missing agent.json manifest")
        else:
            raise ValueError(f"Invalid package path: {self.package_path}")
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate agent package"""
        errors = []
        
        # Check required manifest fields
        required_fields = ['agent_id', 'name', 'version', 'main_module', 'author']
        for field in required_fields:
            if field not in self.manifest:
                errors.append(f"Missing required field: {field}")
        
        # Check for main module
        if 'main_module' in self.manifest:
            main_module = self.manifest['main_module']
            if self.package_path.is_dir():
                main_file = self.package_path / f"{main_module}.py"
                if not main_file.exists():
                    errors.append(f"Main module not found: {main_module}.py")
        
        # Check dependencies
        if 'dependencies' in self.manifest:
            deps = self.manifest['dependencies']
            if 'python_packages' in deps:
                # Could check if packages are installable
                pass
        
        return len(errors) == 0, errors
    
    def extract(self, target_dir: str) -> str:
        """Extract package to target directory"""
        target_path = Path(target_dir) / self.manifest['agent_id']
        
        if self.package_path.is_file():
            # Extract zip file
            with zipfile.ZipFile(self.package_path, 'r') as zip_file:
                zip_file.extractall(target_path)
        else:
            # Copy directory
            shutil.copytree(self.package_path, target_path, dirs_exist_ok=True)
        
        self.extracted_path = target_path
        return str(target_path)
    
    def get_info(self) -> Dict[str, Any]:
        """Get package information"""
        return {
            "agent_id": self.manifest.get('agent_id'),
            "name": self.manifest.get('name'),
            "version": self.manifest.get('version'),
            "author": self.manifest.get('author'),
            "description": self.manifest.get('description', ''),
            "tags": self.manifest.get('tags', []),
            "dependencies": self.manifest.get('dependencies', {}),
            "package_path": str(self.package_path)
        }

class AgentLoader:
    """
    Dynamic agent loader and manager
    
    Handles:
    - Installing agent packages
    - Loading agents from packages
    - Managing agent dependencies
    - Uninstalling agents
    """
    
    def __init__(self, install_dir: str = None):
        self.install_dir = Path(install_dir or os.path.expanduser("~/.juniorgpt/agents"))
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry = get_registry()
        self.installed_agents = {}
        
        self._load_installed_agents()
    
    def _load_installed_agents(self):
        """Load information about installed agents"""
        installed_file = self.install_dir / "installed.json"
        if installed_file.exists():
            try:
                with open(installed_file, 'r') as f:
                    self.installed_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load installed agents info: {e}")
                self.installed_agents = {}
    
    def _save_installed_agents(self):
        """Save information about installed agents"""
        installed_file = self.install_dir / "installed.json"
        try:
            with open(installed_file, 'w') as f:
                json.dump(self.installed_agents, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save installed agents info: {e}")
    
    def install_agent(self, package_path: str, force: bool = False) -> bool:
        """
        Install an agent package
        
        Args:
            package_path: Path to agent package (zip file or directory)
            force: Force installation even if agent exists
            
        Returns:
            True if installation successful
        """
        try:
            # Load and validate package
            package = AgentPackage(package_path)
            is_valid, errors = package.validate()
            
            if not is_valid:
                logger.error(f"Invalid agent package: {', '.join(errors)}")
                return False
            
            agent_id = package.manifest['agent_id']
            
            # Check if agent already installed
            if agent_id in self.installed_agents and not force:
                logger.warning(f"Agent {agent_id} already installed. Use force=True to overwrite.")
                return False
            
            # Extract package
            logger.info(f"Installing agent: {agent_id}")
            extracted_path = package.extract(str(self.install_dir))
            
            # Install Python dependencies if specified
            if 'dependencies' in package.manifest:
                success = self._install_dependencies(package.manifest['dependencies'], extracted_path)
                if not success:
                    logger.error(f"Failed to install dependencies for {agent_id}")
                    return False
            
            # Load and register agent
            success = self._load_agent_from_path(extracted_path, package.manifest)
            if not success:
                logger.error(f"Failed to load agent {agent_id}")
                return False
            
            # Update installed agents registry
            self.installed_agents[agent_id] = {
                "name": package.manifest['name'],
                "version": package.manifest['version'],
                "author": package.manifest['author'],
                "installed_at": datetime.utcnow().isoformat(),
                "extracted_path": extracted_path,
                "original_package": str(package.package_path),
                "manifest": package.manifest
            }
            
            self._save_installed_agents()
            
            logger.info(f"Successfully installed agent: {agent_id} v{package.manifest['version']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install agent package {package_path}: {e}")
            return False
    
    def _install_dependencies(self, dependencies: Dict[str, Any], agent_path: str) -> bool:
        """Install agent dependencies"""
        if 'python_packages' in dependencies:
            packages = dependencies['python_packages']
            if packages:
                logger.info(f"Installing Python packages: {', '.join(packages)}")
                try:
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install', '--user', *packages
                    ])
                    return True
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install Python packages: {e}")
                    return False
        
        return True
    
    def _load_agent_from_path(self, agent_path: str, manifest: Dict[str, Any]) -> bool:
        """Load agent from extracted path"""
        try:
            agent_path = Path(agent_path)
            main_module = manifest['main_module']
            
            # Add agent path to Python path
            if str(agent_path) not in sys.path:
                sys.path.insert(0, str(agent_path))
            
            # Import main module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                main_module, 
                agent_path / f"{main_module}.py"
            )
            
            if spec is None:
                logger.error(f"Could not load spec for {main_module}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find agent class
            agent_class = None
            main_class = manifest.get('main_class')
            
            if main_class:
                # Use specified main class
                agent_class = getattr(module, main_class, None)
            else:
                # Find first BaseAgent subclass
                import inspect
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj != BaseAgent and issubclass(obj, BaseAgent):
                        agent_class = obj
                        break
            
            if agent_class is None:
                logger.error(f"No agent class found in {main_module}")
                return False
            
            # Register agent
            self.registry.register_agent(agent_class, {
                "source": "installed_package",
                "package_path": str(agent_path),
                "manifest": manifest
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load agent from {agent_path}: {e}")
            return False
    
    def uninstall_agent(self, agent_id: str) -> bool:
        """
        Uninstall an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if uninstallation successful
        """
        if agent_id not in self.installed_agents:
            logger.warning(f"Agent {agent_id} not found in installed agents")
            return False
        
        try:
            # Stop agent if running
            self.registry.stop_agent(agent_id)
            
            # Unregister from registry
            self.registry.unregister_agent(agent_id)
            
            # Remove files
            agent_info = self.installed_agents[agent_id]
            extracted_path = Path(agent_info['extracted_path'])
            
            if extracted_path.exists():
                shutil.rmtree(extracted_path)
                logger.info(f"Removed agent files: {extracted_path}")
            
            # Update installed agents registry
            del self.installed_agents[agent_id]
            self._save_installed_agents()
            
            logger.info(f"Successfully uninstalled agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall agent {agent_id}: {e}")
            return False
    
    def list_installed(self) -> List[Dict[str, Any]]:
        """List installed agents"""
        installed = []
        
        for agent_id, info in self.installed_agents.items():
            agent_data = info.copy()
            agent_data['agent_id'] = agent_id
            agent_data['status'] = 'registered' if agent_id in self.registry.agents else 'not_loaded'
            agent_data['running'] = agent_id in self.registry.instances
            installed.append(agent_data)
        
        return sorted(installed, key=lambda x: x['name'])
    
    def update_agent(self, agent_id: str, package_path: str) -> bool:
        """
        Update an existing agent
        
        Args:
            agent_id: Agent identifier
            package_path: Path to new package version
            
        Returns:
            True if update successful
        """
        if agent_id not in self.installed_agents:
            logger.warning(f"Agent {agent_id} not installed, use install_agent instead")
            return False
        
        try:
            # Validate new package
            package = AgentPackage(package_path)
            is_valid, errors = package.validate()
            
            if not is_valid:
                logger.error(f"Invalid agent package: {', '.join(errors)}")
                return False
            
            if package.manifest['agent_id'] != agent_id:
                logger.error(f"Agent ID mismatch: expected {agent_id}, got {package.manifest['agent_id']}")
                return False
            
            # Stop current agent
            self.registry.stop_agent(agent_id)
            
            # Backup current installation
            current_info = self.installed_agents[agent_id]
            current_path = Path(current_info['extracted_path'])
            backup_path = current_path.with_suffix('.backup')
            
            if current_path.exists():
                shutil.move(current_path, backup_path)
            
            try:
                # Install new version
                success = self.install_agent(package_path, force=True)
                
                if success:
                    # Remove backup
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                    logger.info(f"Successfully updated agent: {agent_id}")
                    return True
                else:
                    # Restore backup
                    if backup_path.exists():
                        shutil.move(backup_path, current_path)
                    logger.error(f"Update failed, restored previous version: {agent_id}")
                    return False
                    
            except Exception as e:
                # Restore backup on error
                if backup_path.exists():
                    shutil.move(backup_path, current_path)
                raise e
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            return False
    
    def create_agent_package(self, agent_dir: str, output_path: str = None) -> Optional[str]:
        """
        Create an agent package from a directory
        
        Args:
            agent_dir: Directory containing agent files
            output_path: Output path for package (optional)
            
        Returns:
            Path to created package or None if failed
        """
        try:
            agent_path = Path(agent_dir)
            if not agent_path.exists():
                logger.error(f"Agent directory does not exist: {agent_dir}")
                return None
            
            # Check for manifest
            manifest_file = agent_path / 'agent.json'
            if not manifest_file.exists():
                logger.error(f"Agent manifest not found: {manifest_file}")
                return None
            
            # Load manifest
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Determine output path
            if output_path is None:
                agent_id = manifest['agent_id']
                version = manifest['version']
                output_path = f"{agent_id}-{version}.zip"
            
            # Create zip package
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in agent_path.rglob('*'):
                    if file_path.is_file():
                        # Skip hidden files and __pycache__
                        if (file_path.name.startswith('.') or 
                            '__pycache__' in str(file_path)):
                            continue
                        
                        arcname = file_path.relative_to(agent_path)
                        zip_file.write(file_path, arcname)
            
            logger.info(f"Created agent package: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create agent package: {e}")
            return None
    
    def load_all_installed(self) -> int:
        """Load all installed agents into registry"""
        loaded_count = 0
        
        for agent_id, info in self.installed_agents.items():
            if agent_id not in self.registry.agents:
                try:
                    extracted_path = info['extracted_path']
                    manifest = info['manifest']
                    
                    success = self._load_agent_from_path(extracted_path, manifest)
                    if success:
                        loaded_count += 1
                        logger.info(f"Loaded installed agent: {agent_id}")
                    else:
                        logger.warning(f"Failed to load installed agent: {agent_id}")
                        
                except Exception as e:
                    logger.error(f"Error loading installed agent {agent_id}: {e}")
        
        return loaded_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get loader statistics"""
        return {
            "install_directory": str(self.install_dir),
            "total_installed": len(self.installed_agents),
            "loaded_agents": len([aid for aid in self.installed_agents.keys() 
                                if aid in self.registry.agents]),
            "running_agents": len([aid for aid in self.installed_agents.keys() 
                                 if aid in self.registry.instances])
        }

# Global loader instance
_global_loader = None

def get_loader() -> AgentLoader:
    """Get the global agent loader"""
    global _global_loader
    if _global_loader is None:
        _global_loader = AgentLoader()
    return _global_loader