import requests
import os
import json
from typing import Optional, Dict, Any, List, Generator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API."""
    
    def __init__(self, base_url: str = None, default_model: str = None, timeout: int = 30):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = default_model or os.getenv("OLLAMA_MODEL", "llama2")
        self.timeout = timeout
        
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def generate_response(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response using Ollama.
        
        Args:
            prompt: The input prompt
            model: Optional model name (uses default if not provided)
            
        Returns:
            Dict containing response, model, and metadata
        """
        model_name = model or self.default_model
        
        # Check if Ollama is available
        if not self.is_available():
            return self._get_fallback_response(prompt, model_name, "Ollama service unavailable")
        
        # Check if requested model is available
        available_models = self.get_available_models()
        if available_models and model_name not in available_models:
            logger.warning(f"Model {model_name} not available. Available models: {available_models}")
            # Try to use the first available model as fallback
            if available_models:
                model_name = available_models[0]
                logger.info(f"Using fallback model: {model_name}")
            else:
                return self._get_fallback_response(prompt, model_name, "No models available")
        
        try:
            start_time = datetime.now()
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", "").strip(),
                    "model": model_name,
                    "timestamp": end_time,
                    "duration_ms": duration_ms,
                    "success": True
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(
                    prompt, 
                    model_name, 
                    f"API error: {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            return self._get_fallback_response(prompt, model_name, "Request timeout")
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return self._get_fallback_response(prompt, model_name, str(e))
    
    def generate_response_stream(self, prompt: str, model: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response using Ollama.
        
        Args:
            prompt: The input prompt
            model: Optional model name (uses default if not provided)
            
        Yields:
            Dict containing token, model, and metadata for each chunk
        """
        model_name = model or self.default_model
        
        # Check if Ollama is available
        if not self.is_available():
            yield self._get_fallback_stream_response(prompt, model_name, "Ollama service unavailable")
            return
        
        # Check if requested model is available
        available_models = self.get_available_models()
        if available_models and model_name not in available_models:
            logger.warning(f"Model {model_name} not available. Available models: {available_models}")
            # Try to use the first available model as fallback
            if available_models:
                model_name = available_models[0]
                logger.info(f"Using fallback model: {model_name}")
            else:
                yield self._get_fallback_stream_response(prompt, model_name, "No models available")
                return
        
        try:
            start_time = datetime.now()
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            token = chunk_data.get("response", "")
                            done = chunk_data.get("done", False)
                            
                            if token:
                                full_response += token
                                yield {
                                    "token": token,
                                    "model": model_name,
                                    "timestamp": datetime.now().isoformat(),
                                    "done": done,
                                    "success": True
                                }
                            
                            if done:
                                end_time = datetime.now()
                                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                                yield {
                                    "token": "",
                                    "model": model_name,
                                    "timestamp": end_time.isoformat(),
                                    "done": True,
                                    "success": True,
                                    "duration_ms": duration_ms,
                                    "full_response": full_response.strip()
                                }
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse streaming response: {e}")
                            continue
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                yield self._get_fallback_stream_response(prompt, model_name, f"API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            yield self._get_fallback_stream_response(prompt, model_name, "Request timeout")
            
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield self._get_fallback_stream_response(prompt, model_name, str(e))
    
    def _get_fallback_response(self, prompt: str, model: str, error_reason: str) -> Dict[str, Any]:
        """Generate a fallback response when Ollama is unavailable."""
        logger.info(f"Using fallback response due to: {error_reason}")
        
        # Simple fallback responses based on prompt content
        fallback_responses = {
            "hello": "Hello! I'm a fallback response since the LLM service is currently unavailable.",
            "what": "I'm sorry, I cannot provide a detailed answer right now as the LLM service is unavailable. This is a fallback response.",
            "how": "I'd love to help explain that, but the LLM service is currently unavailable. This is a fallback response.",
            "why": "That's an interesting question! Unfortunately, the LLM service is unavailable right now, so this is a fallback response.",
            "explain": "I'd be happy to explain that topic, but the LLM service is currently unavailable. This is a fallback response."
        }
        
        # Find appropriate fallback based on prompt content
        prompt_lower = prompt.lower()
        fallback_text = "I apologize, but the LLM service is currently unavailable. This is a fallback response to your prompt."
        
        for keyword, response in fallback_responses.items():
            if keyword in prompt_lower:
                fallback_text = response
                break
        
        return {
            "response": fallback_text,
            "model": f"{model} (fallback)",
            "timestamp": datetime.now(),
            "duration_ms": 0,
            "success": False,
            "error_reason": error_reason
        }
    
    def _get_fallback_stream_response(self, prompt: str, model: str, error_reason: str) -> Dict[str, Any]:
        """Generate a fallback streaming response when Ollama is unavailable."""
        logger.info(f"Using fallback streaming response due to: {error_reason}")
        
        # Simple fallback responses based on prompt content
        fallback_responses = {
            "hello": "Hello! I'm a fallback response since the LLM service is currently unavailable.",
            "what": "I'm sorry, I cannot provide a detailed answer right now as the LLM service is unavailable. This is a fallback response.",
            "how": "I'd love to help explain that, but the LLM service is currently unavailable. This is a fallback response.",
            "why": "That's an interesting question! Unfortunately, the LLM service is unavailable right now, so this is a fallback response.",
            "explain": "I'd be happy to explain that topic, but the LLM service is currently unavailable. This is a fallback response."
        }
        
        # Find appropriate fallback based on prompt content
        prompt_lower = prompt.lower()
        fallback_text = "I apologize, but the LLM service is currently unavailable. This is a fallback response to your prompt."
        
        for keyword, response in fallback_responses.items():
            if keyword in prompt_lower:
                fallback_text = response
                break
        
        return {
            "token": fallback_text,
            "model": f"{model} (fallback)",
            "timestamp": datetime.now().isoformat(),
            "done": True,
            "success": False,
            "error_reason": error_reason,
            "duration_ms": 0,
            "full_response": fallback_text
        }
