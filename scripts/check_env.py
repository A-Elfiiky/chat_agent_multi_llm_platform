"""
Quick test to check if chat-orchestrator can see env vars
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("=== Environment Check ===")
print(f"GROQ_API_KEY: {os.environ.get('GROQ_API_KEY', 'NOT FOUND')[:30]}...")
print(f"GEMINI_KEY: {os.environ.get('GEMINI_KEY', 'NOT FOUND')[:30]}...")
print(f"GROK_KEY: {os.environ.get('GROK_KEY', 'NOT FOUND')[:30]}...")

# Try loading the router
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/chat-orchestrator')))
from llm_provider import LLMRouter

router = LLMRouter()
print(f"\n=== Router Config ===")
print(f"Providers available: {list(router.providers.keys())}")
print(f"Primary: {router.primary_provider}")
print(f"Fallback: {router.fallback_order}")

# Check what keys the providers actually got
for name, provider in router.providers.items():
    if hasattr(provider, 'api_key'):
        key_preview = provider.api_key[:10] if provider.api_key and provider.api_key != "dummy" else provider.api_key
        print(f"{name}: api_key={key_preview}...")
