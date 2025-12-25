import abc
import os
import sys
import asyncio
import time
from typing import List, Dict, Optional, Any
import httpx

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config
from services.shared.circuit_breaker import CircuitBreaker
from services.shared.settings_service import get_settings_service
from services.shared.provider_metrics import get_provider_metrics

settings_service = get_settings_service()
provider_metrics = get_provider_metrics()

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        pass

class GrokProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        # Grok is often compatible with OpenAI client
        # We use the openai library if available, else fallback to httpx
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.grok.x.ai/v1" 
            )
            self.use_sdk = True
        except ImportError:
            self.client = httpx.AsyncClient(headers={"Authorization": f"Bearer {api_key}"})
            self.use_sdk = False

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        if self.use_sdk:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=10.0
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Grok SDK Error: {e}")
                raise e
        else:
            # Fallback HTTP
            url = "https://api.grok.x.ai/v1/chat/completions" 
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            }
            response = await self.client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        # Use v1 endpoint instead of v1beta
        self.url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        print(f"[GeminiProvider] Initialized with api_key={api_key[:10] if api_key and api_key != 'dummy' else api_key}...")

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        # Google Gemini REST API
        async with httpx.AsyncClient(verify=False) as client:
            payload = {
                "contents": [{
                    "parts": [{"text": f"{system_instruction}\n\nUser Query: {prompt}"}]
                }]
            }
            response = await client.post(self.url, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            # Handle safety ratings or empty content
            if 'candidates' in data and data['candidates']:
                content = data['candidates'][0].get('content')
                if content and 'parts' in content:
                    return content['parts'][0]['text']
            raise Exception("No content returned from Gemini (possibly blocked by safety filters)")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        if not self.api_key or self.api_key in ("", "dummy"):
            raise ValueError(f"Missing OPENAI_API_KEY (got: {self.api_key})")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            choices = data.get('choices')
            if not choices:
                raise Exception("OpenAI response missing choices")
            return choices[0]['message']['content']

class LocalLLMProvider(LLMProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            }
            # Assuming OpenAI compatible local server (like vLLM or Ollama)
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        if not self.api_key or self.api_key in ("", "dummy"):
            raise ValueError(f"Missing GROQ_API_KEY (got: {self.api_key})")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        # Disable SSL verification for Groq (same as other services in this project)
        async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            choices = data.get('choices')
            if not choices:
                raise Exception("Groq response missing choices")
            return choices[0]['message']['content']

class HuggingFaceProvider(LLMProvider):
    def __init__(self, api_token: str, endpoint: str):
        self.api_token = api_token
        self.endpoint = endpoint

    async def generate_response(self, prompt: str, system_instruction: str) -> str:
        if not self.api_token or self.api_token in ("", "dummy"):
            raise ValueError(f"Missing HF_TOKEN (got: {self.api_token})")
        
        headers = {"Authorization": f"Bearer {self.api_token}"}
        # HuggingFace Inference API format (Mistral/Llama style prompt)
        payload = {
            "inputs": f"<s>[INST] {system_instruction}\n\n{prompt} [/INST]",
            "parameters": {"max_new_tokens": 512, "return_full_text": False}
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            # Usually returns a list of dicts
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', '')
            elif isinstance(data, dict) and 'generated_text' in data:
                return data['generated_text']
            else:
                raise Exception(f"Unexpected response format from HuggingFace: {data}")

class LLMRouter:
    def __init__(self):
        self.config = load_config()
        self.providers = {}
        self.breakers = {}
        self._init_providers()
        self._load_runtime_preferences()

    def _init_providers(self):
        llm_config = self.config['llm']
        
        def add_provider(name, instance):
            self.providers[name] = instance
            self.breakers[name] = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

        # Initialize providers based on config
        if 'grok' in llm_config['providers']:
            add_provider('grok', GrokProvider(
                api_key=os.getenv(llm_config['providers']['grok']['api_key_env'], "dummy"),
                model=llm_config['providers']['grok']['model']
            ))
        
        if 'gemini' in llm_config['providers']:
            add_provider('gemini', GeminiProvider(
                api_key=os.getenv(llm_config['providers']['gemini']['api_key_env'], "dummy"),
                model=llm_config['providers']['gemini']['model']
            ))

        if 'openai' in llm_config['providers']:
            add_provider('openai', OpenAIProvider(
                api_key=os.getenv(llm_config['providers']['openai']['api_key_env'], "dummy"),
                model=llm_config['providers']['openai']['model']
            ))

        if 'groq' in llm_config['providers']:
            add_provider('groq', GroqProvider(
                api_key=os.getenv(llm_config['providers']['groq']['api_key_env'], "dummy"),
                model=llm_config['providers']['groq']['model']
            ))
            
        if 'huggingface' in llm_config['providers']:
            add_provider('huggingface', HuggingFaceProvider(
                api_token=os.getenv(llm_config['providers']['huggingface']['token_env'], "dummy"),
                endpoint=os.getenv(llm_config['providers']['huggingface']['endpoint_env'], "https://router.huggingface.co/models/google/flan-t5-base")
            ))

        if 'local' in llm_config['providers']:
            add_provider('local', LocalLLMProvider(
                base_url=llm_config['providers']['local']['base_url'],
                model=llm_config['providers']['local']['model']
            ))

    def _load_runtime_preferences(self):
        fallback_default = self.config['llm'].get('fallback_order', list(self.providers.keys()))
        primary_default = fallback_default[0] if fallback_default else next(iter(self.providers), None)

        overrides = settings_service.get_many({
            'llm_primary_provider': primary_default,
            'llm_fallback_order': fallback_default,
            'llm_auto_fallback': True
        })

        available_providers = list(self.providers.keys())
        primary = overrides.get('llm_primary_provider')
        if primary not in available_providers:
            primary = primary_default

        fallback_order = overrides.get('llm_fallback_order') or []
        if not isinstance(fallback_order, list):
            fallback_order = fallback_default
        fallback_order = [p for p in fallback_order if p in available_providers and p != primary]

        auto_fallback = overrides.get('llm_auto_fallback')
        auto_fallback_enabled = bool(auto_fallback) if auto_fallback is not None else True

        self.primary_provider = primary
        self.fallback_order = fallback_order
        self.auto_fallback_enabled = auto_fallback_enabled

        routing = []
        if self.primary_provider:
            routing.append(self.primary_provider)
        if self.auto_fallback_enabled:
            routing.extend([p for p in self.fallback_order if p not in routing])
        self.routing_plan = routing if routing else available_providers

    async def generate_answer(self, prompt: str, system_instruction: str) -> Dict[str, Any]:
        # Always refresh routing preferences to pick up latest admin changes
        self._load_runtime_preferences()

        for attempt_index, provider_name in enumerate(self.routing_plan):
            if provider_name not in self.providers:
                continue
            
            breaker = self.breakers[provider_name]
            if not breaker.allow_request():
                print(f"Skipping {provider_name} (Circuit Breaker OPEN)")
                continue
                
            provider = self.providers[provider_name]
            attempt_start = time.time()
            try:
                print(f"Attempting generation with {provider_name}...")
                response_text = await provider.generate_response(prompt, system_instruction)
                breaker.record_success()
                provider_metrics.record_event(
                    provider=provider_name,
                    success=True,
                    latency_ms=(time.time() - attempt_start) * 1000,
                    fallback_depth=attempt_index,
                )
                return {
                    "provider": provider_name,
                    "answer": response_text,
                    "success": True
                }
            except Exception as e:
                print(f"Provider {provider_name} failed: {e}")
                breaker.record_failure()
                provider_metrics.record_event(
                    provider=provider_name,
                    success=False,
                    latency_ms=(time.time() - attempt_start) * 1000,
                    error_message=str(e),
                    fallback_depth=attempt_index,
                )
                continue
        
        return {
            "provider": "none",
            "answer": None,
            "success": False
        }
