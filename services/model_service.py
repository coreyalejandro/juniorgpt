"""
Model service for handling AI model interactions
"""
import requests
import json
import time
from typing import Dict, List, Optional, Any, Generator, Tuple
import logging
from datetime import datetime

from config import Config
from utils.security import SecurityUtils

logger = logging.getLogger('juniorgpt.model_service')

class ModelResponse:
    """Response object for model interactions"""
    
    def __init__(self, content: str, model: str, response_time: float, tokens_used: int = 0):
        self.content = content
        self.model = model
        self.response_time = response_time
        self.tokens_used = tokens_used
        self.timestamp = datetime.utcnow()
        self.success = True
        self.error = None
    
    def set_error(self, error: str):
        """Mark response as error"""
        self.success = False
        self.error = error
        self.content = f"Error: {error}"

class ModelService:
    """Service for handling AI model interactions"""
    
    def __init__(self, config: Config):
        self.config = config
        self.security = SecurityUtils()
        
        # Model configurations
        self.openai_models = {
            'gpt-4o-mini': {'max_tokens': 16384, 'context_window': 128000},
            'gpt-4o': {'max_tokens': 4096, 'context_window': 128000},
            'gpt-3.5-turbo': {'max_tokens': 4096, 'context_window': 16384}
        }
        
        self.anthropic_models = {
            'claude-3-5-sonnet': {'max_tokens': 4096, 'context_window': 200000},
            'claude-3-haiku': {'max_tokens': 4096, 'context_window': 200000},
            'claude-3-opus': {'max_tokens': 4096, 'context_window': 200000}
        }
        
        self.local_models = {}  # Will be populated from Ollama
        self._load_ollama_models()
    
    def _load_ollama_models(self):
        """Load available Ollama models"""
        try:
            response = requests.get(
                f"http://{self.config.OLLAMA_HOST}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models_data = response.json().get('models', [])
                for model in models_data:
                    self.local_models[model['name']] = {
                        'max_tokens': 4096,  # Default, can be configured
                        'context_window': 8192,
                        'size': model.get('size', 0)
                    }
                logger.info(f"Loaded {len(self.local_models)} Ollama models")
            else:
                logger.warning("Failed to load Ollama models")
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models categorized by provider"""
        return {
            'openai': list(self.openai_models.keys()),
            'anthropic': list(self.anthropic_models.keys()),
            'local': list(self.local_models.keys())
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        if model_name in self.openai_models:
            return {'provider': 'openai', **self.openai_models[model_name]}
        elif model_name in self.anthropic_models:
            return {'provider': 'anthropic', **self.anthropic_models[model_name]}
        elif model_name in self.local_models:
            return {'provider': 'local', **self.local_models[model_name]}
        return None
    
    async def generate_response(
        self,
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> ModelResponse:
        """Generate response from specified model"""
        
        # Validate input
        is_valid, error_msg = self.security.validate_message_input(prompt)
        if not is_valid:
            response = ModelResponse("", model, 0.0)
            response.set_error(error_msg)
            return response
        
        start_time = time.time()
        
        try:
            model_info = self.get_model_info(model)
            if not model_info:
                response = ModelResponse("", model, 0.0)
                response.set_error(f"Unknown model: {model}")
                return response
            
            provider = model_info['provider']
            
            if provider == 'openai':
                return await self._call_openai(prompt, model, conversation_history, temperature, max_tokens, start_time)
            elif provider == 'anthropic':
                return await self._call_anthropic(prompt, model, conversation_history, temperature, max_tokens, start_time)
            elif provider == 'local':
                return await self._call_ollama(prompt, model, temperature, max_tokens, start_time)
            else:
                response = ModelResponse("", model, 0.0)
                response.set_error(f"Unsupported provider: {provider}")
                return response
                
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Model generation error for {model}: {e}")
            response = ModelResponse("", model, response_time)
            response.set_error(str(e))
            return response
    
    async def _call_openai(
        self,
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict]],
        temperature: float,
        max_tokens: int,
        start_time: float
    ) -> ModelResponse:
        """Call OpenAI API"""
        
        if not self.config.OPENAI_API_KEY:
            response = ModelResponse("", model, 0.0)
            response.set_error("OpenAI API key not configured")
            return response
        
        # Prepare messages
        messages = []
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit history
                messages.extend([
                    {"role": "user", "content": msg.get("user", "")},
                    {"role": "assistant", "content": msg.get("assistant", "")}
                ])
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=self.config.RESPONSE_TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                tokens_used = data['usage']['total_tokens']
                
                return ModelResponse(content, model, response_time, tokens_used)
            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                if response.status_code == 429:
                    error_msg += " - Rate limit exceeded"
                elif response.status_code == 401:
                    error_msg += " - Invalid API key"
                    
                model_response = ModelResponse("", model, response_time)
                model_response.set_error(error_msg)
                return model_response
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error("Request timeout")
            return model_response
        except Exception as e:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error(f"OpenAI API error: {str(e)}")
            return model_response
    
    async def _call_anthropic(
        self,
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict]],
        temperature: float,
        max_tokens: int,
        start_time: float
    ) -> ModelResponse:
        """Call Anthropic API"""
        
        if not self.config.ANTHROPIC_API_KEY:
            response = ModelResponse("", model, 0.0)
            response.set_error("Anthropic API key not configured")
            return response
        
        # Prepare messages for Anthropic format
        messages = []
        if conversation_history:
            for msg in conversation_history[-10:]:  # Limit history
                messages.extend([
                    {"role": "user", "content": msg.get("user", "")},
                    {"role": "assistant", "content": msg.get("assistant", "")}
                ])
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.config.ANTHROPIC_API_KEY,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=self.config.RESPONSE_TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data['content'][0]['text']
                tokens_used = data['usage']['input_tokens'] + data['usage']['output_tokens']
                
                return ModelResponse(content, model, response_time, tokens_used)
            else:
                error_msg = f"Anthropic API error: {response.status_code}"
                if response.status_code == 429:
                    error_msg += " - Rate limit exceeded"
                elif response.status_code == 401:
                    error_msg += " - Invalid API key"
                    
                model_response = ModelResponse("", model, response_time)
                model_response.set_error(error_msg)
                return model_response
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error("Request timeout")
            return model_response
        except Exception as e:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error(f"Anthropic API error: {str(e)}")
            return model_response
    
    async def _call_ollama(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        start_time: float
    ) -> ModelResponse:
        """Call Ollama API"""
        
        try:
            response = requests.post(
                f"http://{self.config.OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=self.config.OLLAMA_TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('response', '')
                
                return ModelResponse(content, model, response_time)
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                model_response = ModelResponse("", model, response_time)
                model_response.set_error(error_msg)
                return model_response
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error("Ollama request timeout")
            return model_response
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error("Cannot connect to Ollama - ensure it's running")
            return model_response
        except Exception as e:
            response_time = time.time() - start_time
            model_response = ModelResponse("", model, response_time)
            model_response.set_error(f"Ollama error: {str(e)}")
            return model_response
    
    def stream_response(
        self,
        prompt: str,
        model: str,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Generator[str, None, None]:
        """Stream response from model (for real-time updates)"""
        
        # For now, implement basic streaming by yielding the complete response
        # This can be enhanced to true streaming for supported models
        
        model_info = self.get_model_info(model)
        if not model_info:
            yield f"Error: Unknown model {model}"
            return
        
        provider = model_info['provider']
        
        try:
            if provider == 'local':
                yield from self._stream_ollama(prompt, model, temperature, max_tokens)
            else:
                # For cloud models, fall back to non-streaming for now
                # Can be enhanced with proper streaming support
                import asyncio
                response = asyncio.run(self.generate_response(
                    prompt, model, conversation_history, temperature, max_tokens
                ))
                yield response.content
                
        except Exception as e:
            yield f"Streaming error: {str(e)}"
    
    def _stream_ollama(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Generator[str, None, None]:
        """Stream response from Ollama"""
        
        try:
            response = requests.post(
                f"http://{self.config.OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                stream=True,
                timeout=self.config.OLLAMA_TIMEOUT
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                                
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"Error: Ollama API returned {response.status_code}"
                
        except Exception as e:
            yield f"Streaming error: {str(e)}"