#!/usr/bin/env python3
"""
JuniorGPT Agent CLI Tool

Command-line interface for creating, packaging, testing, and managing
self-contained agent applications.

Usage:
    python agent_cli.py create <agent_name>     # Create new agent template
    python agent_cli.py package <agent_dir>     # Package agent into distributable
    python agent_cli.py install <package>       # Install agent package
    python agent_cli.py test <agent_dir>        # Test agent locally
    python agent_cli.py list                    # List installed agents
    python agent_cli.py uninstall <agent_id>    # Uninstall agent
"""
import os
import sys
import json
import argparse
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.agent_loader import get_loader
from agents.agent_registry import get_registry
from utils.logging_config import setup_logging

def create_agent_template(agent_name: str, output_dir: str = None) -> bool:
    """
    Create a new agent template with boilerplate code
    
    Args:
        agent_name: Name of the agent to create
        output_dir: Directory to create agent in (optional)
        
    Returns:
        True if successful
    """
    if output_dir is None:
        output_dir = f"{agent_name}_agent"
    
    agent_path = Path(output_dir)
    
    # Create directory structure
    agent_path.mkdir(exist_ok=True)
    
    # Agent ID from name
    agent_id = agent_name.lower().replace(' ', '_').replace('-', '_')
    
    # Create manifest
    manifest = {
        "agent_id": agent_id,
        "name": f"🤖 {agent_name} Agent",
        "description": f"Specialized agent for {agent_name.lower()} tasks",
        "version": "1.0.0",
        "author": "Developer",
        "main_module": f"{agent_id}_agent",
        "main_class": f"{agent_name.replace(' ', '').replace('-', '')}Agent",
        "tags": [agent_name.lower()],
        "dependencies": {
            "python_packages": []
        },
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 60
        }
    }
    
    with open(agent_path / "agent.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create main agent file
    agent_code = f'''"""
{agent_name} Agent - Self-contained agent for {agent_name.lower()} tasks

This agent can be used standalone or integrated into larger systems.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the base agent framework
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus

class {manifest["main_class"]}(BaseAgent):
    """
    Specialized agent for {agent_name.lower()} tasks
    
    Capabilities:
    - Add your specific capabilities here
    - Describe what this agent can do
    - List the main features
    """
    
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(
            agent_id="{agent_id}",
            name="{manifest['name']}",
            description="{manifest['description']}",
            version="{manifest['version']}",
            author="{manifest['author']}",
            model="{manifest['config']['model']}",
            temperature={manifest['config']['temperature']},
            max_tokens={manifest['config']['max_tokens']},
            thinking_style="I approach {agent_name.lower()} tasks systematically, considering best practices and user needs.",
            triggers=[
                # Add keywords that should trigger this agent
                "{agent_name.lower()}",
                # Add more relevant triggers
            ],
            tags=["{agent_name.lower()}"],
            timeout={manifest['config']['timeout']},
            required_apis=["openai"],  # Add required APIs
            required_models=["{manifest['config']['model']}"]
        )
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process {agent_name.lower()} request"""
        self.logger.info(f"Processing {agent_name.lower()} request: {{message[:100]}}...")
        
        # Validate input
        is_valid, error_msg = self.validate_input(message, context)
        if not is_valid:
            return AgentResponse(
                agent_id=self.config.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error_message=error_msg,
                error_code="INVALID_INPUT"
            )
        
        try:
            # Create thinking trace
            thinking_trace = self.create_thinking_trace(
                f"Analyzing {agent_name.lower()} request: '{{message[:50]}}...'"
            )
            
            # Build prompt for your specific task
            prompt = self._build_prompt(message, context)
            
            # Call AI model
            response_content = await self.call_model(prompt)
            
            # Create successful response
            response = AgentResponse(
                agent_id=self.config.agent_id,
                content=response_content,
                status=AgentStatus.COMPLETED,
                thinking_trace=thinking_trace,
                model_used=self.config.model
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"{agent_name} processing failed: {{e}}")
            return AgentResponse(
                agent_id=self.config.agent_id,
                content=f"{agent_name} processing failed: {{str(e)}}",
                status=AgentStatus.ERROR,
                error_message=str(e),
                error_code="{agent_id.upper()}_ERROR"
            )
    
    def _build_prompt(self, message: str, context: Dict[str, Any] = None) -> str:
        """Build prompt for {agent_name.lower()} tasks"""
        
        prompt_parts = [
            f"You are a specialized {agent_name.lower()} assistant.",
            f"Your expertise is in: {self.config.description}",
            "",
            f"User Request: {{message}}",
            "",
            "Please provide a helpful and detailed response that:",
            f"1. Addresses the {agent_name.lower()} task directly",
            "2. Uses clear, professional language",
            "3. Includes practical information when relevant",
            "4. Follows best practices in your domain",
            "",
            f"Thinking style: {{self.config.thinking_style}}"
        ]
        
        # Add context if available
        if context and "conversation_history" in context:
            prompt_parts.extend([
                "",
                "Previous conversation context available - consider it for continuity."
            ])
        
        return "\\n".join(prompt_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {{
            "name": self.config.name,
            "description": self.config.description,
            "specializations": [
                # List your agent's specializations
                f"{{agent_name}} task processing",
                "Task-specific analysis",
                "Domain expertise",
                # Add more specific capabilities
            ],
            "input_types": [
                f"{{agent_name.lower()}}_requests",
                "general_questions",
                "task_specifications"
            ],
            "output_formats": [
                "detailed_responses",
                "structured_information",
                "actionable_guidance"
            ],
            "quality_metrics": {{
                "accuracy": "high",
                "completeness": "comprehensive",
                "speed": "fast",
                "expertise_level": "specialized"
            }}
        }}
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        """Enhanced capability detection for {agent_name.lower()} tasks"""
        base_score = super().can_handle(message, context)
        
        message_lower = message.lower()
        
        # Add specific indicators for your agent
        {agent_name.lower()}_indicators = [
            # Add specific phrases that indicate this agent should handle the task
            "{agent_name.lower()}",
            # Add more indicators
        ]
        
        for indicator in {agent_name.lower()}_indicators:
            if indicator in message_lower:
                base_score += 0.3
        
        return min(base_score, 1.0)

# Standalone execution capability
async def main():
    """Standalone execution for testing"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent without external dependencies
    agent = {manifest["main_class"]}()
    
    # Test message
    test_message = "Test message for {agent_name.lower()} agent"
    
    print(f"Testing {{agent.__class__.__name__}} with: {{test_message}}")
    print("-" * 50)
    
    # Check if agent can handle the message
    confidence = agent.can_handle(test_message)
    print(f"Confidence: {{confidence:.2f}}")
    
    # Get capabilities
    capabilities = agent.get_capabilities()
    print(f"Capabilities: {{json.dumps(capabilities, indent=2)}}")
    
    # In a real scenario, you would need to provide a model service
    # response = await agent.execute(test_message)
    # print(f"Response: {{response.to_dict()}}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(agent_path / f"{agent_id}_agent.py", 'w') as f:
        f.write(agent_code)
    
    # Create README
    readme_content = f"""# {agent_name} Agent

## Description
{manifest['description']}

## Installation
```bash
# Package the agent
python tools/agent_cli.py package {output_dir}

# Install the agent
python tools/agent_cli.py install {agent_id}-{manifest['version']}.zip
```

## Usage

### Standalone
```python
from {agent_id}_agent import {manifest['main_class']}
import asyncio

agent = {manifest['main_class']}()
response = asyncio.run(agent.execute("Your message here"))
print(response.content)
```

### Integrated
The agent will be automatically discovered when installed in the JuniorGPT system.

## Configuration
- Model: {manifest['config']['model']}
- Temperature: {manifest['config']['temperature']}
- Max Tokens: {manifest['config']['max_tokens']}
- Timeout: {manifest['config']['timeout']}s

## Development
1. Modify the agent code in `{agent_id}_agent.py`
2. Update capabilities in `get_capabilities()`
3. Add triggers in the constructor
4. Test with `python tools/agent_cli.py test {output_dir}`
5. Package with `python tools/agent_cli.py package {output_dir}`

## Version
{manifest['version']} by {manifest['author']}
"""
    
    with open(agent_path / "README.md", 'w') as f:
        f.write(readme_content)
    
    # Create test file
    test_content = f'''"""
Test suite for {agent_name} Agent
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from {agent_id}_agent import {manifest['main_class']}

@pytest.fixture
def agent():
    """Create agent instance for testing"""
    return {manifest['main_class']}()

def test_agent_config(agent):
    """Test agent configuration"""
    assert agent.config.agent_id == "{agent_id}"
    assert agent.config.name == "{manifest['name']}"
    assert agent.config.version == "{manifest['version']}"

def test_capability_detection(agent):
    """Test agent capability detection"""
    # Test positive cases
    test_messages = [
        "Help with {agent_name.lower()}",
        "I need {agent_name.lower()} assistance",
    ]
    
    for message in test_messages:
        confidence = agent.can_handle(message)
        assert confidence > 0.3, f"Agent should handle: {{message}}"
    
    # Test negative cases
    negative_messages = [
        "What's the weather?",
        "Random unrelated question",
    ]
    
    for message in negative_messages:
        confidence = agent.can_handle(message)
        assert confidence < 0.5, f"Agent should not prioritize: {{message}}"

def test_capabilities_structure(agent):
    """Test capabilities return structure"""
    caps = agent.get_capabilities()
    
    required_keys = ["name", "description", "specializations", 
                    "input_types", "output_formats"]
    
    for key in required_keys:
        assert key in caps, f"Missing capability key: {{key}}"

@pytest.mark.asyncio
async def test_input_validation(agent):
    """Test input validation"""
    # Test empty input
    response = await agent.execute("")
    assert response.status.value == "error"
    
    # Test very long input
    long_message = "x" * 20000
    response = await agent.execute(long_message)
    assert response.status.value == "error"

# Add more tests specific to your agent's functionality
'''
    
    with open(agent_path / "test_agent.py", 'w') as f:
        f.write(test_content)
    
    print(f"✅ Created agent template: {agent_path}")
    print(f"📝 Edit {agent_id}_agent.py to implement your agent")
    print(f"🧪 Test with: python tools/agent_cli.py test {output_dir}")
    print(f"📦 Package with: python tools/agent_cli.py package {output_dir}")
    
    return True

def package_agent(agent_dir: str, output_path: str = None) -> Optional[str]:
    """Package agent into distributable file"""
    loader = get_loader()
    
    try:
        package_path = loader.create_agent_package(agent_dir, output_path)
        if package_path:
            print(f"✅ Created agent package: {package_path}")
            return package_path
        else:
            print("❌ Failed to create agent package")
            return None
    except Exception as e:
        print(f"❌ Error packaging agent: {e}")
        return None

def install_agent(package_path: str, force: bool = False) -> bool:
    """Install agent package"""
    loader = get_loader()
    
    try:
        success = loader.install_agent(package_path, force=force)
        if success:
            print(f"✅ Successfully installed agent from: {package_path}")
            return True
        else:
            print(f"❌ Failed to install agent from: {package_path}")
            return False
    except Exception as e:
        print(f"❌ Error installing agent: {e}")
        return False

def test_agent(agent_dir: str) -> bool:
    """Test agent locally"""
    agent_path = Path(agent_dir)
    
    if not agent_path.exists():
        print(f"❌ Agent directory not found: {agent_dir}")
        return False
    
    # Check for manifest
    manifest_file = agent_path / "agent.json"
    if not manifest_file.exists():
        print(f"❌ Agent manifest not found: {manifest_file}")
        return False
    
    # Load manifest
    try:
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load manifest: {e}")
        return False
    
    # Check main module exists
    main_module = manifest.get('main_module')
    if not main_module:
        print("❌ No main_module specified in manifest")
        return False
    
    main_file = agent_path / f"{main_module}.py"
    if not main_file.exists():
        print(f"❌ Main module not found: {main_file}")
        return False
    
    print(f"🧪 Testing agent: {manifest.get('name', 'Unknown')}")
    print(f"📄 Version: {manifest.get('version', 'Unknown')}")
    print(f"👤 Author: {manifest.get('author', 'Unknown')}")
    
    # Try to import and test
    try:
        import sys
        import importlib.util
        
        # Add agent directory to path
        sys.path.insert(0, str(agent_path))
        
        # Import main module
        spec = importlib.util.spec_from_file_location(main_module, main_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find main class
        main_class = manifest.get('main_class')
        if main_class and hasattr(module, main_class):
            agent_class = getattr(module, main_class)
            
            # Create instance
            agent = agent_class()
            
            # Test basic functionality
            print("✅ Agent imports successfully")
            print(f"🔧 Agent ID: {agent.config.agent_id}")
            print(f"📋 Description: {agent.config.description}")
            
            # Test capability detection
            test_messages = [
                "test message",
                manifest.get('name', '').lower() + " help"
            ]
            
            for message in test_messages:
                confidence = agent.can_handle(message)
                print(f"🎯 Confidence for '{message}': {confidence:.2f}")
            
            # Test capabilities
            capabilities = agent.get_capabilities()
            print(f"⚡ Specializations: {', '.join(capabilities.get('specializations', []))}")
            
            print("✅ Agent test completed successfully")
            return True
            
        else:
            print(f"❌ Main class not found: {main_class}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

def list_agents() -> None:
    """List installed agents"""
    loader = get_loader()
    registry = get_registry()
    
    try:
        installed = loader.list_installed()
        
        if not installed:
            print("No agents installed")
            return
        
        print(f"📦 Installed Agents ({len(installed)}):")
        print("-" * 80)
        
        for agent in installed:
            status_emoji = "🟢" if agent['status'] == 'registered' else "🔴"
            running_emoji = "▶️" if agent['running'] else "⏸️"
            
            print(f"{status_emoji} {running_emoji} {agent['name']} (v{agent['version']})")
            print(f"   ID: {agent['agent_id']}")
            print(f"   Author: {agent['author']}")
            print(f"   Installed: {agent['installed_at'][:10]}")
            print(f"   Status: {agent['status']}")
            print()
        
        # Show registry statistics
        registry_stats = registry.get_statistics()
        print(f"🔧 Registry: {registry_stats['total_registered']} registered, "
              f"{registry_stats['running_instances']} running")
        
    except Exception as e:
        print(f"❌ Error listing agents: {e}")

def uninstall_agent(agent_id: str) -> bool:
    """Uninstall agent"""
    loader = get_loader()
    
    try:
        success = loader.uninstall_agent(agent_id)
        if success:
            print(f"✅ Successfully uninstalled agent: {agent_id}")
            return True
        else:
            print(f"❌ Failed to uninstall agent: {agent_id}")
            return False
    except Exception as e:
        print(f"❌ Error uninstalling agent: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="JuniorGPT Agent CLI - Create, package, and manage self-contained agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_cli.py create "My Special Agent"
  python agent_cli.py package my_special_agent/
  python agent_cli.py install my_special_agent-1.0.0.zip
  python agent_cli.py test my_special_agent/
  python agent_cli.py list
  python agent_cli.py uninstall my_special_agent
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new agent template')
    create_parser.add_argument('name', help='Agent name')
    create_parser.add_argument('-o', '--output', help='Output directory')
    
    # Package command
    package_parser = subparsers.add_parser('package', help='Package agent into distributable')
    package_parser.add_argument('agent_dir', help='Agent directory to package')
    package_parser.add_argument('-o', '--output', help='Output package path')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install agent package')
    install_parser.add_argument('package', help='Agent package file')
    install_parser.add_argument('-f', '--force', action='store_true', help='Force installation')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test agent locally')
    test_parser.add_argument('agent_dir', help='Agent directory to test')
    
    # List command
    subparsers.add_parser('list', help='List installed agents')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall agent')
    uninstall_parser.add_argument('agent_id', help='Agent ID to uninstall')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging('INFO', include_console=True)
    
    # Execute command
    try:
        if args.command == 'create':
            create_agent_template(args.name, args.output)
        elif args.command == 'package':
            package_agent(args.agent_dir, args.output)
        elif args.command == 'install':
            install_agent(args.package, args.force)
        elif args.command == 'test':
            test_agent(args.agent_dir)
        elif args.command == 'list':
            list_agents()
        elif args.command == 'uninstall':
            uninstall_agent(args.agent_id)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()