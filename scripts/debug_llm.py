import sys
import os
import asyncio
import httpx

# Fix import path - services is a package at root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# We need to import from services.chat-orchestrator which has a hyphen. 
# Python doesn't like hyphens in imports unless we use importlib or rename the folder.
# However, the folder is 'services/chat-orchestrator'.
# Let's check how other files import it. They usually append 'services/chat-orchestrator' to path.

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/chat-orchestrator')))
from llm_provider import LLMRouter

async def test_providers():
    print("--- Testing LLM Providers ---")
    router = LLMRouter()
    print(f"Primary Provider: {router.primary_provider}")
    print(f"Fallback Order: {router.fallback_order}")
    print(f"Routing Plan: {router.routing_plan}")
    
    prompt = "Hello, are you working?"
    system = "You are a test bot."
    
    print(f"\nSending prompt: '{prompt}'")
    result = await router.generate_answer(prompt, system)
    
    print("\n--- Result ---")
    print(f"Success: {result['success']}")
    print(f"Provider: {result['provider']}")
    print(f"Answer: {result['answer']}")
    
    if not result['success']:
        print("\nFAILURE DIAGNOSIS:")
        print("1. Check .env file for keys (GROQ_API_KEY, GEMINI_KEY).")
        print("2. Check internet connection.")
        print("3. Check if keys are valid.")

if __name__ == "__main__":
    asyncio.run(test_providers())
