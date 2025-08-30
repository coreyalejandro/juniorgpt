# JuniorGPT Agent Development Guide

## 🚀 Overview

JuniorGPT now uses a revolutionary plugin-based architecture where each agent is a completely self-contained application. These agents can be:

- **Used Standalone**: Run independently without JuniorGPT
- **Plug-and-Play**: Installed/removed at runtime
- **Third-Party Developed**: Created by anyone, anywhere
- **Fully Portable**: Work across different systems and environments

## 🏗️ Architecture Principles

### Self-Contained Design
Each agent is a complete application with:
- Its own dependencies and configuration
- Standardized interface for communication
- Independent execution capability
- Built-in error handling and logging

### Plugin Interface
All agents implement the `BaseAgent` interface:
- Standardized request/response format
- Capability detection system
- Health monitoring
- Performance metrics

### Dynamic Loading
Agents can be:
- Discovered automatically
- Loaded at runtime
- Hot-swapped without restart
- Installed from packages

## 🛠️ Getting Started

### 1. Install Development Tools

```bash
# Clone the repository
git clone <repository-url>
cd juniorgpt

# Install dependencies
pip install -r requirements.txt

# Make CLI tool executable
chmod +x tools/agent_cli.py
```

### 2. Create Your First Agent

```bash
# Create a new agent template
python tools/agent_cli.py create "My Awesome Agent"

# This creates a directory with:
# - agent.json (manifest)
# - my_awesome_agent_agent.py (main code)
# - README.md (documentation)
# - test_agent.py (tests)
```

### 3. Develop Your Agent

Edit the generated `my_awesome_agent_agent.py`:

```python
class MyAwesomeAgentAgent(BaseAgent):
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(
            agent_id="my_awesome_agent",
            name="🚀 My Awesome Agent",
            description="Does awesome things awesomely",
            version="1.0.0",
            author="Your Name",
            # Add your specific configuration
            triggers=["awesome", "amazing", "fantastic"],
            tags=["awesome", "utility"]
        )
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        # Your agent logic here
        thinking_trace = self.create_thinking_trace("Processing awesome request...")
        
        # Call AI model if needed
        prompt = f"Handle this awesome request: {message}"
        response_content = await self.call_model(prompt)
        
        return AgentResponse(
            agent_id=self.config.agent_id,
            content=response_content,
            status=AgentStatus.COMPLETED,
            thinking_trace=thinking_trace,
            model_used=self.config.model
        )
```

### 4. Test Your Agent

```bash
# Test locally
python tools/agent_cli.py test my_awesome_agent_agent/

# Run unit tests
cd my_awesome_agent_agent/
python -m pytest test_agent.py -v
```

### 5. Package and Deploy

```bash
# Package your agent
python tools/agent_cli.py package my_awesome_agent_agent/

# Install it
python tools/agent_cli.py install my_awesome_agent-1.0.0.zip

# List installed agents
python tools/agent_cli.py list
```

## 📋 Agent Manifest (agent.json)

Every agent must have an `agent.json` manifest:

```json
{
  "agent_id": "my_agent",
  "name": "🤖 My Agent",
  "description": "What this agent does",
  "version": "1.0.0",
  "author": "Your Name",
  "main_module": "my_agent_agent",
  "main_class": "MyAgentAgent",
  "tags": ["category", "feature"],
  "dependencies": {
    "python_packages": ["requests", "beautifulsoup4"]
  },
  "config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 60
  }
}
```

### Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `agent_id` | Yes | Unique identifier (lowercase, underscores) |
| `name` | Yes | Display name with emoji |
| `description` | Yes | What the agent does |
| `version` | Yes | Semantic version (1.0.0) |
| `author` | Yes | Developer name |
| `main_module` | Yes | Python module name |
| `main_class` | No | Main class name (auto-detected if not specified) |
| `tags` | No | Searchable tags |
| `dependencies` | No | Python packages and other requirements |
| `config` | No | Default configuration |

## 🎯 BaseAgent Interface

All agents must inherit from `BaseAgent`:

```python
from agents.base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus

class YourAgent(BaseAgent):
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(...)
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        # Required: Main processing logic
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        # Required: Return agent capabilities
        pass
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        # Optional: Custom capability detection (0.0 to 1.0)
        return super().can_handle(message, context)
```

### AgentConfig Properties

```python
config = AgentConfig(
    agent_id="unique_id",           # Unique identifier
    name="🤖 Display Name",         # User-friendly name
    description="What it does",     # Brief description
    version="1.0.0",                # Semantic version
    author="Developer Name",        # Author information
    
    # Model configuration
    model="gpt-4o-mini",           # Default AI model
    temperature=0.7,               # Model temperature
    max_tokens=4096,               # Max response tokens
    
    # Behavior
    thinking_style="How I think", # Thinking approach
    triggers=["keyword", "phrase"], # Trigger words
    tags=["category", "type"],      # Classification tags
    
    # Performance
    timeout=60,                    # Execution timeout
    retry_count=3,                 # Retry attempts
    
    # Dependencies
    required_apis=["openai"],      # Required API services
    required_models=["gpt-4o"]     # Required AI models
)
```

### AgentResponse Format

```python
response = AgentResponse(
    agent_id="my_agent",
    content="The main response text",
    status=AgentStatus.COMPLETED,  # COMPLETED, ERROR, TIMEOUT
    
    # Optional metadata
    thinking_trace="My thinking process...",
    execution_time=2.5,
    tokens_used=150,
    model_used="gpt-4o-mini",
    
    # Error information (if status is ERROR)
    error_message="What went wrong",
    error_code="ERROR_TYPE",
    
    # Additional data
    metadata={"key": "value"},
    artifacts=[{
        "type": "code",
        "data": "print('hello')",
        "description": "Generated code"
    }]
)
```

## 🔍 Capability Detection

Agents use a scoring system to determine if they can handle a request:

```python
def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
    # Start with base score from triggers/tags
    base_score = super().can_handle(message, context)
    
    message_lower = message.lower()
    
    # Add specific indicators
    if "my_keyword" in message_lower:
        base_score += 0.4
    
    if message.startswith("special_prefix"):
        base_score += 0.3
    
    # Check for complex patterns
    if re.search(r"pattern_regex", message):
        base_score += 0.2
    
    # Return score between 0.0 and 1.0
    return min(base_score, 1.0)
```

### Scoring Guidelines
- **0.9-1.0**: Perfect match, this agent should definitely handle it
- **0.7-0.8**: Strong match, good candidate
- **0.5-0.6**: Moderate match, could handle it
- **0.3-0.4**: Weak match, probably not ideal
- **0.0-0.2**: No match, shouldn't handle it

## 🧠 Thinking Traces

Agents can show their thinking process:

```python
async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
    thinking_parts = [
        f"Analyzing request: '{message[:50]}...'",
        "Identifying key components...",
        "Planning solution approach...",
        "Generating response..."
    ]
    
    thinking_trace = self.create_thinking_trace("\n".join(thinking_parts))
    
    # Your processing logic...
    
    return AgentResponse(
        agent_id=self.config.agent_id,
        content=response_content,
        status=AgentStatus.COMPLETED,
        thinking_trace=thinking_trace
    )
```

## 🎨 Best Practices

### 1. Agent Design

**Do:**
- Keep agents focused on specific domains
- Use clear, descriptive names with emojis
- Provide detailed capability descriptions
- Include comprehensive error handling
- Add meaningful thinking traces

**Don't:**
- Create overly broad "do everything" agents
- Use generic names like "Helper Agent"
- Skip input validation
- Ignore error cases
- Forget to document capabilities

### 2. Performance

**Optimize for:**
- Fast startup time
- Efficient memory usage
- Quick capability detection
- Minimal dependencies

**Avoid:**
- Heavy initialization in `__init__`
- Loading large models unnecessarily
- Complex regex in `can_handle`
- Excessive API calls

### 3. User Experience

**Provide:**
- Clear, helpful responses
- Appropriate response length
- Actionable information
- Professional tone

**Avoid:**
- Overly technical jargon
- Extremely long responses
- Vague or unhelpful content
- Inconsistent formatting

### 4. Error Handling

```python
async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
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
        # Your processing logic
        result = await self.do_processing(message)
        
        return AgentResponse(
            agent_id=self.config.agent_id,
            content=result,
            status=AgentStatus.COMPLETED
        )
        
    except TimeoutError:
        return AgentResponse(
            agent_id=self.config.agent_id,
            content="Processing timed out",
            status=AgentStatus.TIMEOUT,
            error_message="Operation exceeded time limit",
            error_code="TIMEOUT"
        )
        
    except Exception as e:
        self.logger.error(f"Processing failed: {e}")
        return AgentResponse(
            agent_id=self.config.agent_id,
            content="Processing failed",
            status=AgentStatus.ERROR,
            error_message=str(e),
            error_code="PROCESSING_ERROR"
        )
```

## 🔧 Advanced Features

### 1. Using AI Models

```python
async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
    # Build prompt
    prompt = f"""
    You are a specialized assistant for {self.config.description}.
    
    User request: {message}
    
    Please provide a helpful response that:
    1. Addresses the request directly
    2. Uses your specialized knowledge
    3. Follows best practices
    
    Thinking style: {self.config.thinking_style}
    """
    
    # Call model with specific parameters
    response_content = await self.call_model(
        prompt,
        model="gpt-4o",  # Override default model
        temperature=0.3,  # More focused
        max_tokens=2000   # Limit length
    )
    
    return AgentResponse(
        agent_id=self.config.agent_id,
        content=response_content,
        status=AgentStatus.COMPLETED
    )
```

### 2. Adding Artifacts

```python
async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
    # Generate code
    code = self.generate_code(message)
    
    response = AgentResponse(
        agent_id=self.config.agent_id,
        content="Here's the generated code:",
        status=AgentStatus.COMPLETED
    )
    
    # Add code as artifact
    response.add_artifact(
        artifact_type="code",
        data=code,
        description="Generated Python code"
    )
    
    # Add documentation
    response.add_artifact(
        artifact_type="documentation",
        data=self.generate_docs(code),
        description="Code documentation"
    )
    
    return response
```

### 3. Event Hooks

```python
def __init__(self, model_service=None, logger=None):
    super().__init__(config, model_service, logger)
    
    # Add event hooks
    self.add_hook("start", self.on_start)
    self.add_hook("complete", self.on_complete)
    self.add_hook("error", self.on_error)

async def on_start(self, message, context):
    """Called when processing starts"""
    self.logger.info(f"Starting to process: {message[:50]}...")

async def on_complete(self, response):
    """Called when processing completes successfully"""
    self.logger.info(f"Completed in {response.execution_time:.2f}s")

async def on_error(self, response):
    """Called when processing fails"""
    self.logger.error(f"Failed: {response.error_message}")
```

### 4. Health Monitoring

```python
def health_check(self) -> Dict[str, Any]:
    """Custom health check"""
    health_info = super().health_check()
    
    # Add custom health checks
    health_info["checks"].update({
        "api_connection": self.check_api_connection(),
        "model_availability": self.check_model_availability(),
        "memory_usage": psutil.Process().memory_percent()
    })
    
    # Determine overall health
    all_checks_passed = all(health_info["checks"].values())
    health_info["healthy"] = all_checks_passed
    
    return health_info

def check_api_connection(self) -> bool:
    """Check if required APIs are accessible"""
    try:
        # Test API connection
        response = requests.get("https://api.example.com/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

## 📦 Packaging and Distribution

### 1. Package Structure

```
my_agent/
├── agent.json          # Manifest
├── my_agent_agent.py   # Main code
├── README.md           # Documentation
├── test_agent.py       # Tests
├── requirements.txt    # Dependencies (optional)
└── resources/          # Additional files (optional)
    ├── templates/
    └── data/
```

### 2. Creating Packages

```bash
# Create package
python tools/agent_cli.py package my_agent/

# This creates my_agent-1.0.0.zip containing:
# - All files from the directory
# - Compressed for distribution
# - Ready for installation
```

### 3. Installing Packages

```bash
# Install locally
python tools/agent_cli.py install my_agent-1.0.0.zip

# Install with force (overwrite existing)
python tools/agent_cli.py install my_agent-1.0.0.zip --force

# List installed agents
python tools/agent_cli.py list
```

### 4. Publishing (Future Feature)

```bash
# Publish to registry (coming soon)
python tools/agent_cli.py publish my_agent-1.0.0.zip

# Install from registry
python tools/agent_cli.py install my_agent --from-registry
```

## 🧪 Testing

### 1. Unit Tests

Create `test_agent.py`:

```python
import pytest
import asyncio
from your_agent import YourAgent

@pytest.fixture
def agent():
    return YourAgent()

def test_config(agent):
    assert agent.config.agent_id == "your_agent"
    assert agent.config.version == "1.0.0"

def test_capability_detection(agent):
    # Test positive cases
    assert agent.can_handle("your trigger words") > 0.5
    
    # Test negative cases
    assert agent.can_handle("unrelated content") < 0.3

@pytest.mark.asyncio
async def test_processing(agent):
    response = await agent.execute("test message")
    
    assert response.is_success()
    assert len(response.content) > 0
    assert response.agent_id == "your_agent"

@pytest.mark.asyncio
async def test_error_handling(agent):
    # Test with invalid input
    response = await agent.execute("")
    assert not response.is_success()
    assert response.status == AgentStatus.ERROR
```

### 2. Integration Tests

Test with actual JuniorGPT system:

```python
def test_integration():
    from agents.agent_registry import get_registry
    
    registry = get_registry()
    
    # Register agent
    registry.register_agent(YourAgent)
    
    # Test capability detection
    capable_agents = registry.find_capable_agents("test message")
    assert any(agent_id == "your_agent" for agent_id, _ in capable_agents)
    
    # Test execution
    instance = registry.get_agent_instance("your_agent")
    assert instance is not None
```

### 3. Manual Testing

```bash
# Test locally
python tools/agent_cli.py test my_agent/

# Start interactive test
python -c "
from my_agent_agent import MyAgentAgent
import asyncio

agent = MyAgentAgent()
message = input('Enter test message: ')
response = asyncio.run(agent.execute(message))
print('Response:', response.content)
"
```

## 🚀 Deployment Options

### 1. Standalone Execution

Your agent can run independently:

```python
# standalone.py
import asyncio
from my_agent_agent import MyAgentAgent

async def main():
    agent = MyAgentAgent()
    
    while True:
        message = input("\nYour message: ")
        if message.lower() == 'quit':
            break
            
        response = await agent.execute(message)
        print(f"\nAgent: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Web API

Create a simple web service:

```python
from flask import Flask, request, jsonify
from my_agent_agent import MyAgentAgent
import asyncio

app = Flask(__name__)
agent = MyAgentAgent()

@app.route('/api/process', methods=['POST'])
def process():
    message = request.json.get('message')
    
    # Run async in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        response = loop.run_until_complete(agent.execute(message))
        return jsonify(response.to_dict())
    finally:
        loop.close()

if __name__ == '__main__':
    app.run(port=5000)
```

### 3. Integration with JuniorGPT

Install and let the system discover it:

```bash
# Package and install
python tools/agent_cli.py package my_agent/
python tools/agent_cli.py install my_agent-1.0.0.zip

# Start JuniorGPT
python app_plugin.py

# Your agent is now available in the system!
```

## 📚 Examples

### 1. Simple Utility Agent

```python
class UtilityAgent(BaseAgent):
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(
            agent_id="utility",
            name="🔧 Utility Agent",
            description="General utility and helper functions",
            version="1.0.0",
            author="Example Author",
            triggers=["utility", "helper", "tool", "convert"],
            tags=["utility", "helper"]
        )
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        thinking = "Analyzing utility request..."
        
        # Simple utility functions
        if "convert" in message.lower():
            result = self.handle_conversion(message)
        elif "calculate" in message.lower():
            result = self.handle_calculation(message)
        else:
            result = "I can help with conversions, calculations, and other utilities."
        
        return AgentResponse(
            agent_id=self.config.agent_id,
            content=result,
            status=AgentStatus.COMPLETED,
            thinking_trace=self.create_thinking_trace(thinking)
        )
    
    def handle_conversion(self, message: str) -> str:
        # Simple conversion logic
        return "Conversion functionality would go here"
    
    def handle_calculation(self, message: str) -> str:
        # Simple calculation logic
        return "Calculation functionality would go here"
```

### 2. AI-Powered Agent

```python
class AIWriterAgent(BaseAgent):
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(
            agent_id="ai_writer",
            name="✍️ AI Writer Agent",
            description="Creative and professional writing assistance",
            version="1.0.0",
            author="Example Author",
            model="claude-3-5-sonnet",
            temperature=0.8,  # More creative
            triggers=["write", "draft", "compose", "create text"],
            tags=["writing", "creative", "content"]
        )
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        thinking_trace = self.create_thinking_trace(
            f"Analyzing writing request: {message[:50]}...\n"
            "Determining writing style and format needed...\n"
            "Crafting response with appropriate tone..."
        )
        
        prompt = f"""
        You are a professional writer specializing in creating high-quality content.
        
        Writing request: {message}
        
        Please create content that is:
        1. Well-structured and organized
        2. Engaging and appropriate for the audience
        3. Professional yet accessible
        4. Tailored to the specific request
        
        Consider the context and purpose of the writing.
        """
        
        content = await self.call_model(prompt)
        
        return AgentResponse(
            agent_id=self.config.agent_id,
            content=content,
            status=AgentStatus.COMPLETED,
            thinking_trace=thinking_trace,
            model_used=self.config.model
        )
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        base_score = super().can_handle(message, context)
        
        writing_indicators = [
            "write", "draft", "compose", "create",
            "blog post", "article", "essay", "letter",
            "email", "content", "copy"
        ]
        
        message_lower = message.lower()
        for indicator in writing_indicators:
            if indicator in message_lower:
                base_score += 0.3
        
        return min(base_score, 1.0)
```

## 🔍 Troubleshooting

### Common Issues

**1. Agent Not Loading**
```bash
# Check manifest syntax
python -m json.tool agent.json

# Check main module
python tools/agent_cli.py test my_agent/

# Check dependencies
pip install -r requirements.txt
```

**2. Import Errors**
```python
# Ensure proper imports in agent file
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus
```

**3. Capability Detection Not Working**
```python
def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
    # Debug capability detection
    base_score = super().can_handle(message, context)
    print(f"Base score for '{message}': {base_score}")
    
    # Add your custom logic
    # ...
    
    print(f"Final score: {final_score}")
    return final_score
```

**4. Model Service Not Available**
```python
async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
    if not self.model_service:
        # Fallback logic when no model service
        return AgentResponse(
            agent_id=self.config.agent_id,
            content="Model service not available - using fallback response",
            status=AgentStatus.COMPLETED
        )
```

### Debug Tools

**Enable Verbose Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test Individual Components**
```python
# Test capability detection
agent = MyAgent()
print(agent.can_handle("test message"))

# Test configuration
print(agent.config.__dict__)

# Test capabilities
print(agent.get_capabilities())
```

**Profile Performance**
```python
import time

start = time.time()
response = await agent.execute(message)
print(f"Execution time: {time.time() - start:.2f}s")
```

## 📞 Support and Community

### Getting Help
- Check the troubleshooting section above
- Review existing agent examples
- Test with the CLI tool first
- Check logs for error messages

### Contributing
- Follow the coding standards
- Add comprehensive tests
- Update documentation
- Submit clear pull requests

### Sharing Agents
- Package agents properly
- Include clear documentation
- Add usage examples
- Test thoroughly before sharing

---

## 🎯 Quick Reference

### CLI Commands
```bash
# Create new agent
python tools/agent_cli.py create "Agent Name"

# Test agent
python tools/agent_cli.py test agent_directory/

# Package agent
python tools/agent_cli.py package agent_directory/

# Install agent
python tools/agent_cli.py install agent-1.0.0.zip

# List agents
python tools/agent_cli.py list

# Uninstall agent
python tools/agent_cli.py uninstall agent_id
```

### Required Imports
```python
from agents.base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus
from typing import Dict, List, Any, Optional
import asyncio
```

### Minimal Agent Template
```python
class MinimalAgent(BaseAgent):
    def __init__(self, model_service=None, logger=None):
        config = AgentConfig(
            agent_id="minimal",
            name="🤖 Minimal Agent",
            description="Minimal example agent",
            version="1.0.0",
            author="Developer"
        )
        super().__init__(config, model_service, logger)
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        return AgentResponse(
            agent_id=self.config.agent_id,
            content=f"Processed: {message}",
            status=AgentStatus.COMPLETED
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.config.name,
            "description": self.config.description,
            "specializations": ["minimal processing"]
        }
```

### File Structure
```
my_agent/
├── agent.json              # Required manifest
├── my_agent_agent.py       # Required main module
├── README.md               # Recommended documentation
├── test_agent.py           # Recommended tests
└── requirements.txt        # Optional dependencies
```

Now you're ready to create amazing self-contained agents for JuniorGPT! 🚀