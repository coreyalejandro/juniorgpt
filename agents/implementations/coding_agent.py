"""
Coding Agent - Self-contained software development agent

This agent specializes in programming, debugging, code review, and software development tasks.
Can be used standalone or integrated into larger systems.
"""
import asyncio
import re
import json
import ast
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus

class CodingAgent(BaseAgent):
    """
    Specialized agent for software development and programming tasks
    
    Capabilities:
    - Code generation and completion
    - Debugging and error analysis
    - Code review and optimization
    - Architecture recommendations
    - Documentation generation
    - Testing strategies
    """
    
    def __init__(self, model_service=None, logger=None):
        config = self._get_default_config()
        super().__init__(config, model_service, logger)
        
        # Coding-specific settings
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "c++", "c#", "go",
            "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql"
        ]
        self.code_quality_checks = True
        self.security_analysis = True
        self.performance_optimization = True
    
    def _get_default_config(self) -> AgentConfig:
        """Get default configuration for coding agent"""
        return AgentConfig(
            agent_id="coding",
            name="💻 Coding Agent",
            description="Software development and programming specialist",
            version="2.0.0",
            author="JuniorGPT Team",
            model="claude-3-5-sonnet",
            temperature=0.2,  # Lower temperature for more consistent code
            max_tokens=6000,  # More tokens for code generation
            thinking_style="I think in code structures, considering best practices, design patterns, and debugging approaches to solve programming challenges efficiently.",
            triggers=[
                "code", "programming", "debug", "script", "function", "algorithm",
                "software", "development", "bug", "error", "implement", "build",
                "create", "write code", "fix", "optimize", "refactor", "test"
            ],
            tags=["programming", "software", "development", "debugging", "coding"],
            timeout=90,
            required_apis=["anthropic", "openai"],
            required_models=["claude-3-5-sonnet", "gpt-4o"]
        )
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process coding request"""
        self.logger.info(f"Processing coding request: {message[:100]}...")
        
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
            # Analyze coding task
            task_analysis = self._analyze_coding_task(message)
            
            # Generate thinking trace
            thinking_trace = self._create_coding_thinking(message, task_analysis)
            
            # Execute coding task
            coding_result = await self._execute_coding_task(message, task_analysis, context)
            
            # Generate response with code
            response_content = await self._generate_coding_response(
                message, coding_result, thinking_trace
            )
            
            # Create response with artifacts
            response = AgentResponse(
                agent_id=self.config.agent_id,
                content=response_content,
                status=AgentStatus.COMPLETED,
                thinking_trace=thinking_trace,
                model_used=self.config.model
            )
            
            # Add coding artifacts
            response.add_artifact("task_analysis", task_analysis, "Coding task analysis")
            response.add_artifact("code_result", coding_result, "Generated code and analysis")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Coding processing failed: {e}")
            return AgentResponse(
                agent_id=self.config.agent_id,
                content=f"Coding task failed: {str(e)}",
                status=AgentStatus.ERROR,
                error_message=str(e),
                error_code="CODING_ERROR"
            )
    
    def _analyze_coding_task(self, message: str) -> Dict[str, Any]:
        """Analyze the coding task requirements"""
        analysis = {
            "task_type": "general",
            "language": "python",  # default
            "complexity": "medium",
            "requires_testing": False,
            "requires_documentation": False,
            "has_existing_code": False,
            "error_analysis": False,
            "code_review": False
        }
        
        message_lower = message.lower()
        
        # Detect task type
        task_types = {
            "debug": ["debug", "fix", "error", "bug", "issue", "problem", "broken"],
            "implement": ["implement", "create", "build", "write", "develop", "generate"],
            "optimize": ["optimize", "improve", "refactor", "enhance", "performance"],
            "review": ["review", "check", "analyze", "evaluate", "assess"],
            "test": ["test", "testing", "unit test", "pytest", "junit"],
            "explain": ["explain", "understand", "how does", "what is", "documentation"]
        }
        
        for task_type, keywords in task_types.items():
            if any(keyword in message_lower for keyword in keywords):
                analysis["task_type"] = task_type
                break
        
        # Detect programming language
        for lang in self.supported_languages:
            if lang in message_lower:
                analysis["language"] = lang
                break
        
        # Detect complexity
        complexity_indicators = {
            "simple": ["simple", "basic", "easy", "quick", "small"],
            "medium": ["function", "class", "module", "script"],
            "complex": ["system", "application", "framework", "architecture", "complex", "advanced"]
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                analysis["complexity"] = level
        
        # Detect additional requirements
        if any(word in message_lower for word in ["test", "testing", "unit test"]):
            analysis["requires_testing"] = True
        
        if any(word in message_lower for word in ["document", "documentation", "comments", "docstring"]):
            analysis["requires_documentation"] = True
        
        if "```" in message or "def " in message or "function" in message:
            analysis["has_existing_code"] = True
        
        if any(word in message_lower for word in ["error", "exception", "traceback", "fails"]):
            analysis["error_analysis"] = True
        
        if any(word in message_lower for word in ["review", "check", "analyze code"]):
            analysis["code_review"] = True
        
        return analysis
    
    def _create_coding_thinking(self, message: str, analysis: Dict[str, Any]) -> str:
        """Create coding thinking trace"""
        thinking_parts = [
            f"Analyzing coding request: '{message[:100]}{'...' if len(message) > 100 else ''}'",
            f"Task type: {analysis['task_type'].title()}",
            f"Language: {analysis['language'].title()}",
            f"Complexity: {analysis['complexity'].title()}",
            ""
        ]
        
        if analysis['has_existing_code']:
            thinking_parts.append("Existing code detected - analyzing structure and logic")
        
        if analysis['error_analysis']:
            thinking_parts.append("Error analysis required - identifying root causes")
        
        if analysis['code_review']:
            thinking_parts.append("Code review mode - checking quality, security, and best practices")
        
        thinking_parts.extend([
            "Planning solution architecture...",
            "Considering best practices and design patterns",
            "Ensuring code quality and maintainability"
        ])
        
        if analysis['requires_testing']:
            thinking_parts.append("Including test cases for verification")
        
        if analysis['requires_documentation']:
            thinking_parts.append("Adding comprehensive documentation")
        
        return self.create_thinking_trace("\n".join(thinking_parts))
    
    async def _execute_coding_task(self, message: str, analysis: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the coding task"""
        result = {
            "code": "",
            "explanation": "",
            "tests": "",
            "documentation": "",
            "quality_analysis": {},
            "security_notes": [],
            "performance_notes": []
        }
        
        try:
            # Build coding prompt
            coding_prompt = self._build_coding_prompt(message, analysis)
            
            # Generate code
            coding_response = await self.call_model(coding_prompt)
            
            # Parse response for different components
            result = self._parse_coding_response(coding_response, analysis)
            
            # Perform quality checks if enabled
            if self.code_quality_checks and result["code"]:
                result["quality_analysis"] = self._analyze_code_quality(result["code"], analysis["language"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Coding task execution failed: {e}")
            result["error"] = str(e)
            return result
    
    def _build_coding_prompt(self, message: str, analysis: Dict[str, Any]) -> str:
        """Build coding prompt based on task analysis"""
        prompt_parts = [
            f"You are an expert {analysis['language'].title()} developer working on the following task:",
            f"TASK: {message}",
            "",
            f"Programming Language: {analysis['language'].title()}",
            f"Complexity Level: {analysis['complexity'].title()}",
            f"Task Type: {analysis['task_type'].title()}",
            "",
            "Please provide:"
        ]
        
        if analysis['task_type'] == 'implement':
            prompt_parts.extend([
                "1. Clean, well-structured code implementation",
                "2. Clear comments explaining the logic",
                "3. Error handling where appropriate"
            ])
        elif analysis['task_type'] == 'debug':
            prompt_parts.extend([
                "1. Analysis of the problem/error",
                "2. Root cause identification", 
                "3. Fixed code with explanations",
                "4. Prevention strategies"
            ])
        elif analysis['task_type'] == 'review':
            prompt_parts.extend([
                "1. Code quality assessment",
                "2. Security analysis",
                "3. Performance considerations",
                "4. Improvement suggestions"
            ])
        else:
            prompt_parts.extend([
                "1. Appropriate code solution",
                "2. Clear explanations",
                "3. Best practices implementation"
            ])
        
        if analysis['requires_testing']:
            prompt_parts.append("4. Unit tests with good coverage")
        
        if analysis['requires_documentation']:
            prompt_parts.append("5. Comprehensive documentation")
        
        prompt_parts.extend([
            "",
            "Code Quality Requirements:",
            "- Follow language best practices and conventions",
            "- Include appropriate error handling",
            "- Use clear, descriptive variable names",
            "- Add comments for complex logic",
            "- Consider performance and security",
            "",
            f"Thinking approach: {self.config.thinking_style}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_coding_response(self, response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the AI response to extract different components"""
        result = {
            "code": "",
            "explanation": "",
            "tests": "",
            "documentation": "",
            "quality_analysis": {},
            "security_notes": [],
            "performance_notes": []
        }
        
        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            # First code block is usually the main code
            result["code"] = code_blocks[0].strip()
            
            # If there are multiple blocks, second might be tests
            if len(code_blocks) > 1:
                result["tests"] = code_blocks[1].strip()
        
        # Extract explanation (text before first code block or after last)
        if '```' in response:
            parts = response.split('```')
            if len(parts) > 0:
                result["explanation"] = parts[0].strip()
        else:
            result["explanation"] = response.strip()
        
        # Look for specific sections in the response
        sections = {
            "documentation": ["documentation", "docs", "readme"],
            "security": ["security", "vulnerability", "secure"],
            "performance": ["performance", "optimization", "efficiency"]
        }
        
        response_lower = response.lower()
        for section, keywords in sections.items():
            for keyword in keywords:
                if keyword in response_lower:
                    # Extract relevant section (simplified)
                    section_start = response_lower.find(keyword)
                    section_end = response_lower.find('\n\n', section_start)
                    if section_end == -1:
                        section_end = len(response)
                    
                    section_content = response[section_start:section_end].strip()
                    
                    if section == "security":
                        result["security_notes"].append(section_content)
                    elif section == "performance":
                        result["performance_notes"].append(section_content)
                    else:
                        result[section] = section_content
        
        return result
    
    def _analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Perform basic code quality analysis"""
        analysis = {
            "language": language,
            "lines_of_code": len(code.split('\n')),
            "has_comments": False,
            "has_error_handling": False,
            "function_count": 0,
            "class_count": 0,
            "complexity_estimate": "low"
        }
        
        # Basic analysis for Python (can be extended for other languages)
        if language.lower() == "python":
            try:
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        analysis["function_count"] += 1
                    elif isinstance(node, ast.ClassDef):
                        analysis["class_count"] += 1
                    elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                        analysis["has_error_handling"] = True
                        
            except SyntaxError:
                analysis["syntax_error"] = True
        
        # Check for comments
        analysis["has_comments"] = "#" in code or '"""' in code or "'''" in code
        
        # Estimate complexity based on code length and structure
        if analysis["lines_of_code"] > 50 or analysis["function_count"] > 3:
            analysis["complexity_estimate"] = "medium"
        if analysis["lines_of_code"] > 100 or analysis["class_count"] > 2:
            analysis["complexity_estimate"] = "high"
        
        return analysis
    
    async def _generate_coding_response(self, message: str, result: Dict[str, Any], thinking: str) -> str:
        """Generate final coding response"""
        if "error" in result:
            return f"I encountered an issue while processing your coding request: {result['error']}"
        
        if not result["code"] and not result["explanation"]:
            return "I wasn't able to generate a code solution. Could you provide more specific requirements or clarify your request?"
        
        response_parts = []
        
        # Add explanation if available
        if result["explanation"]:
            response_parts.extend([
                "## Solution Explanation",
                result["explanation"],
                ""
            ])
        
        # Add main code
        if result["code"]:
            response_parts.extend([
                "## Code Implementation",
                "```" + (result.get("language", "python")),
                result["code"],
                "```",
                ""
            ])
        
        # Add tests if available
        if result["tests"]:
            response_parts.extend([
                "## Test Cases",
                "```" + (result.get("language", "python")),
                result["tests"],
                "```",
                ""
            ])
        
        # Add quality analysis if available
        if result["quality_analysis"]:
            qa = result["quality_analysis"]
            response_parts.extend([
                "## Code Quality Analysis",
                f"- Lines of code: {qa.get('lines_of_code', 'N/A')}",
                f"- Functions: {qa.get('function_count', 0)}",
                f"- Classes: {qa.get('class_count', 0)}",
                f"- Has error handling: {'Yes' if qa.get('has_error_handling') else 'No'}",
                f"- Has comments: {'Yes' if qa.get('has_comments') else 'No'}",
                f"- Complexity: {qa.get('complexity_estimate', 'Unknown').title()}",
                ""
            ])
        
        # Add security notes if available
        if result["security_notes"]:
            response_parts.extend([
                "## Security Considerations",
                *[f"- {note}" for note in result["security_notes"]],
                ""
            ])
        
        # Add performance notes if available
        if result["performance_notes"]:
            response_parts.extend([
                "## Performance Notes",
                *[f"- {note}" for note in result["performance_notes"]],
                ""
            ])
        
        # Add documentation if available
        if result["documentation"]:
            response_parts.extend([
                "## Documentation",
                result["documentation"],
                ""
            ])
        
        return "\n".join(response_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "specializations": [
                "Code generation and completion",
                "Debugging and error analysis", 
                "Code review and optimization",
                "Architecture recommendations",
                "Testing strategies",
                "Documentation generation"
            ],
            "supported_languages": self.supported_languages,
            "input_types": [
                "code_requests",
                "debugging_tasks",
                "code_review_requests",
                "implementation_specifications"
            ],
            "output_formats": [
                "source_code",
                "code_explanations",
                "test_cases",
                "documentation",
                "quality_reports"
            ],
            "quality_features": {
                "syntax_validation": True,
                "best_practices": True,
                "security_analysis": self.security_analysis,
                "performance_optimization": self.performance_optimization,
                "code_quality_checks": self.code_quality_checks
            },
            "complexity_levels": ["simple", "medium", "complex"]
        }
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        """Enhanced capability detection for coding tasks"""
        base_score = super().can_handle(message, context)
        
        message_lower = message.lower()
        
        # Boost score for code-related content
        if "```" in message or "def " in message or "function" in message:
            base_score += 0.4
        
        # Language-specific indicators
        for lang in self.supported_languages:
            if lang in message_lower:
                base_score += 0.3
                break
        
        # Coding task indicators
        coding_indicators = [
            "write code", "implement", "create function", "debug",
            "fix error", "programming", "software", "algorithm"
        ]
        
        for indicator in coding_indicators:
            if indicator in message_lower:
                base_score += 0.3
        
        return min(base_score, 1.0)

# Standalone execution capability
async def main():
    """Standalone execution for testing"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent without external dependencies
    agent = CodingAgent()
    
    # Test message
    test_message = "Write a Python function to calculate the Fibonacci sequence with error handling"
    
    print(f"Testing Coding Agent with: {test_message}")
    print("-" * 50)
    
    # Check if agent can handle the message
    confidence = agent.can_handle(test_message)
    print(f"Confidence: {confidence:.2f}")
    
    # Get capabilities
    capabilities = agent.get_capabilities()
    print(f"Capabilities: {json.dumps(capabilities, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())