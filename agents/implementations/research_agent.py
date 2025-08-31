"""
Research Agent - Self-contained research and information gathering agent

This agent can be used standalone or integrated into larger systems.
It specializes in research, fact-finding, and information analysis.
"""
import asyncio
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, AgentResponse, AgentConfig, AgentStatus

class ResearchAgent(BaseAgent):
    """
    Specialized agent for research and information gathering
    
    Capabilities:
    - Deep research on any topic
    - Fact-checking and verification
    - Information synthesis
    - Source analysis
    - Data gathering
    """
    
    def __init__(self, model_service=None, logger=None):
        config = self._get_default_config()
        super().__init__(config, model_service, logger)
        
        # Research-specific settings
        self.max_sources = 10
        self.enable_web_search = True
        self.fact_check_threshold = 0.8
    
    def _get_default_config(self) -> AgentConfig:
        """Get default configuration for research agent"""
        return AgentConfig(
            agent_id="research",
            name="🔍 Research Agent",
            description="Deep research and information gathering specialist",
            version="2.0.0",
            author="JuniorGPT Team",
            model="gpt-4o-mini",
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=4096,
            thinking_style="I analyze information systematically, gathering facts and cross-referencing sources to provide comprehensive, well-researched insights.",
            triggers=[
                "research", "find", "information", "data", "facts", 
                "investigate", "study", "analyze", "sources", "evidence",
                "verify", "check", "truth", "accurate", "reliable"
            ],
            tags=["research", "information", "facts", "analysis", "investigation"],
            timeout=120,  # Research can take longer
            required_apis=["openai", "anthropic", "web_search"],
            required_models=["gpt-4o-mini", "gpt-4o"]
        )
    
    async def process(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process research request"""
        self.logger.info(f"Processing research request: {message[:100]}...")
        
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
            # Extract research parameters
            research_params = self._extract_research_parameters(message)
            
            # Generate thinking trace
            thinking_trace = self._create_research_thinking(message, research_params)
            
            # Perform research
            research_results = await self._conduct_research(message, research_params, context)
            
            # Generate comprehensive response
            response_content = await self._generate_research_response(
                message, research_results, thinking_trace
            )
            
            # Create response with artifacts
            response = AgentResponse(
                agent_id=self.config.agent_id,
                content=response_content,
                status=AgentStatus.COMPLETED,
                thinking_trace=thinking_trace,
                model_used=self.config.model
            )
            
            # Add research artifacts
            response.add_artifact("research_parameters", research_params, "Extracted research parameters")
            response.add_artifact("research_results", research_results, "Raw research findings")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Research processing failed: {e}")
            return AgentResponse(
                agent_id=self.config.agent_id,
                content=f"Research failed: {str(e)}",
                status=AgentStatus.ERROR,
                error_message=str(e),
                error_code="RESEARCH_ERROR"
            )
    
    def _extract_research_parameters(self, message: str) -> Dict[str, Any]:
        """Extract research parameters from message"""
        params = {
            "query": message,
            "depth": "standard",  # shallow, standard, deep
            "focus_areas": [],
            "time_period": None,
            "source_types": ["all"],
            "verification_required": False
        }
        
        message_lower = message.lower()
        
        # Detect depth requirements
        if any(word in message_lower for word in ["comprehensive", "detailed", "thorough", "deep"]):
            params["depth"] = "deep"
        elif any(word in message_lower for word in ["quick", "brief", "summary", "overview"]):
            params["depth"] = "shallow"
        
        # Detect verification needs
        if any(word in message_lower for word in ["verify", "check", "accurate", "fact", "truth"]):
            params["verification_required"] = True
        
        # Extract time periods
        time_patterns = [
            r"(?:in|since|from|during)\s+(\d{4})",
            r"(?:last|past)\s+(\d+)\s+(years?|months?|days?)",
            r"(recent|current|latest|modern|historical)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                params["time_period"] = match.group(1)
                break
        
        # Extract focus areas
        focus_keywords = {
            "technical": ["technical", "technology", "programming", "software", "hardware"],
            "scientific": ["scientific", "research", "study", "experiment", "data"],
            "business": ["business", "market", "industry", "company", "economic"],
            "academic": ["academic", "educational", "university", "journal", "paper"],
            "news": ["news", "current", "events", "recent", "breaking"],
        }
        
        for focus, keywords in focus_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                params["focus_areas"].append(focus)
        
        return params
    
    def _create_research_thinking(self, message: str, params: Dict[str, Any]) -> str:
        """Create research thinking trace"""
        thinking_parts = [
            f"Analyzing research request: '{message[:100]}{'...' if len(message) > 100 else ''}'",
            f"Research depth: {params['depth']}",
            f"Focus areas: {', '.join(params['focus_areas']) if params['focus_areas'] else 'General'}",
            f"Verification required: {'Yes' if params['verification_required'] else 'No'}",
            "Planning research strategy...",
        ]
        
        if params['time_period']:
            thinking_parts.append(f"Time focus: {params['time_period']}")
        
        thinking_parts.extend([
            "Gathering information from multiple angles",
            "Cross-referencing sources for accuracy",
            "Synthesizing findings into comprehensive response"
        ])
        
        return self.create_thinking_trace("\n".join(thinking_parts))
    
    async def _conduct_research(self, message: str, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Conduct the actual research"""
        results = {
            "primary_findings": [],
            "supporting_evidence": [],
            "sources": [],
            "confidence_score": 0.0,
            "research_method": params['depth']
        }
        
        try:
            # Create research prompt based on depth
            research_prompt = self._build_research_prompt(message, params)
            
            # Call AI model for research
            research_response = await self.call_model(research_prompt)
            
            # Parse and structure the research results
            results["primary_findings"] = self._extract_findings(research_response)
            results["confidence_score"] = self._calculate_confidence(research_response, params)
            
            # Add context if available
            if context and "conversation_history" in context:
                results["context_used"] = True
                # Use conversation history to refine research
            
            return results
            
        except Exception as e:
            self.logger.error(f"Research execution failed: {e}")
            results["error"] = str(e)
            return results
    
    def _build_research_prompt(self, message: str, params: Dict[str, Any]) -> str:
        """Build research prompt based on parameters"""
        prompt_parts = [
            f"You are an expert researcher conducting {params['depth']} research on the following topic:",
            f"RESEARCH QUERY: {message}",
            "",
            "Please provide a comprehensive research response that includes:",
            "1. Key findings and facts",
            "2. Multiple perspectives where relevant",
            "3. Context and background information",
            "4. Any limitations or uncertainties",
            ""
        ]
        
        if params['verification_required']:
            prompt_parts.extend([
                "IMPORTANT: This research requires high accuracy and fact-checking.",
                "Please be extra careful about claims and indicate confidence levels.",
                ""
            ])
        
        if params['focus_areas']:
            prompt_parts.extend([
                f"Focus your research on these areas: {', '.join(params['focus_areas'])}",
                ""
            ])
        
        if params['time_period']:
            prompt_parts.extend([
                f"Pay special attention to information from: {params['time_period']}",
                ""
            ])
        
        prompt_parts.extend([
            "Structure your response clearly with:",
            "- Executive summary",
            "- Detailed findings",
            "- Supporting evidence",
            "- Conclusions and implications",
            "",
            f"Research depth level: {params['depth'].upper()}",
            f"Thinking style: {self.config.thinking_style}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_findings(self, research_response: str) -> List[Dict[str, Any]]:
        """Extract structured findings from research response"""
        findings = []
        
        # Simple extraction - in a real implementation, this would be more sophisticated
        sections = research_response.split('\n\n')
        
        for i, section in enumerate(sections):
            if section.strip():
                findings.append({
                    "id": i + 1,
                    "content": section.strip(),
                    "type": "finding",
                    "confidence": 0.8  # Would be calculated based on content analysis
                })
        
        return findings
    
    def _calculate_confidence(self, research_response: str, params: Dict[str, Any]) -> float:
        """Calculate confidence score for research results"""
        confidence = 0.7  # Base confidence
        
        # Adjust based on depth
        if params['depth'] == 'deep':
            confidence += 0.15
        elif params['depth'] == 'shallow':
            confidence -= 0.1
        
        # Adjust based on verification requirements
        if params['verification_required']:
            confidence += 0.1
        
        # Analyze response for confidence indicators
        confidence_words = ["likely", "probably", "appears", "seems", "may", "might", "possibly"]
        uncertainty_count = sum(1 for word in confidence_words if word in research_response.lower())
        
        # Reduce confidence based on uncertainty markers
        confidence -= min(0.3, uncertainty_count * 0.05)
        
        return max(0.1, min(1.0, confidence))
    
    async def _generate_research_response(self, message: str, results: Dict[str, Any], thinking: str) -> str:
        """Generate final research response"""
        if "error" in results:
            return f"I encountered an issue while researching: {results['error']}"
        
        if not results["primary_findings"]:
            return "I wasn't able to find sufficient information on this topic. Could you provide more specific details or rephrase your research request?"
        
        # Build comprehensive response
        response_parts = [
            "# Research Results",
            "",
            f"**Research Query:** {message}",
            f"**Confidence Level:** {results['confidence_score']:.1%}",
            "",
            "## Key Findings",
            ""
        ]
        
        # Add findings
        for i, finding in enumerate(results["primary_findings"][:5], 1):
            response_parts.append(f"{i}. {finding['content']}")
            response_parts.append("")
        
        # Add methodology note
        response_parts.extend([
            "## Research Methodology",
            f"- Research depth: {results['research_method'].title()}",
            f"- Analysis approach: {self.config.thinking_style}",
            ""
        ])
        
        # Add limitations if confidence is low
        if results['confidence_score'] < 0.7:
            response_parts.extend([
                "## Limitations",
                "This research has moderate confidence levels. For critical decisions, please verify findings with additional sources.",
                ""
            ])
        
        return "\n".join(response_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "specializations": [
                "Information gathering",
                "Fact-checking and verification",
                "Research synthesis",
                "Source analysis",
                "Data collection",
                "Comparative analysis"
            ],
            "input_types": [
                "research_queries",
                "fact_check_requests", 
                "information_requests",
                "analysis_tasks"
            ],
            "output_formats": [
                "research_reports",
                "fact_summaries",
                "information_briefs",
                "analysis_documents"
            ],
            "quality_metrics": {
                "accuracy": "high",
                "completeness": "comprehensive", 
                "speed": "moderate",
                "depth": "variable"
            },
            "supported_domains": [
                "general_knowledge",
                "scientific_research",
                "technical_information",
                "business_intelligence",
                "academic_research"
            ]
        }
    
    def can_handle(self, message: str, context: Dict[str, Any] = None) -> float:
        """Enhanced capability detection for research tasks"""
        base_score = super().can_handle(message, context)
        
        message_lower = message.lower()
        
        # Boost score for explicit research requests
        research_indicators = [
            "research", "investigate", "find information", "look up",
            "what is", "tell me about", "explain", "analyze",
            "fact check", "verify", "sources", "evidence",
            "study", "survey", "summary", "background",
            "statistics", "data", "report"
        ]

        for indicator in research_indicators:
            if indicator in message_lower:
                base_score += 0.3

        # Question words indicate research need
        question_words = ["what", "why", "how", "when", "where", "who", "which"]
        if any(word in message_lower.split()[:3] for word in question_words):
            base_score += 0.2

        # Presence of a question mark suggests informational intent
        if "?" in message:
            base_score += 0.1

        return min(base_score, 1.0)

# Standalone execution capability
async def main():
    """Standalone execution for testing"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent without external dependencies
    agent = ResearchAgent()
    
    # Test message
    test_message = "Research the latest developments in artificial intelligence and machine learning"
    
    print(f"Testing Research Agent with: {test_message}")
    print("-" * 50)
    
    # Check if agent can handle the message
    confidence = agent.can_handle(test_message)
    print(f"Confidence: {confidence:.2f}")
    
    # Get capabilities
    capabilities = agent.get_capabilities()
    print(f"Capabilities: {json.dumps(capabilities, indent=2)}")
    
    # In a real scenario, you would need to provide a model service
    # response = await agent.execute(test_message)
    # print(f"Response: {response.to_dict()}")

if __name__ == "__main__":
    asyncio.run(main())