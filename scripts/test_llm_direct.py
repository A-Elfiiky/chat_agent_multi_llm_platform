"""
Quick diagnostic script to test LLM providers with actual env loading
"""
import sys
import os
import asyncio
from pathlib import Path

# Load environment the same way run_local.py does
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [BASE_DIR / ".env", BASE_DIR / ".env.local", BASE_DIR / ".env.example"]

for env_path in ENV_CANDIDATES:
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                clean_value = value.split(" #", 1)[0].strip().strip('"').strip("'")
                os.environ[key.strip()] = clean_value
        print(f"[OK] Loaded environment from {env_path.name}")
        break

# Now check what we have
print(f"\n=== API Keys Loaded ===")
print(f"GROQ_API_KEY: {os.environ.get('GROQ_API_KEY', 'MISSING')[:20]}...")
print(f"GEMINI_KEY: {os.environ.get('GEMINI_KEY', 'MISSING')[:20]}...")
print(f"GROK_KEY: {os.environ.get('GROK_KEY', 'MISSING')[:20]}...")

# Import and test the router
sys.path.append(str(BASE_DIR / "services" / "chat-orchestrator"))
from llm_provider import LLMRouter

async def test():
    print(f"\n=== Testing LLM Router ===")
    router = LLMRouter()
    print(f"Providers initialized: {list(router.providers.keys())}")
    print(f"Routing plan: {router.routing_plan}")
    
    # Test with a simple prompt
    result = await router.generate_answer(
        "Hello, reply with just 'Working!'",
        "You are a test assistant."
    )
    
    print(f"\n=== Test Result ===")
    print(f"Success: {result['success']}")
    print(f"Provider: {result['provider']}")
    if result['success']:
        print(f"Answer: {result['answer'][:100]}...")
    else:
        print("[FAIL] All providers failed!")
        print("Check the error messages above for details.")

if __name__ == "__main__":
    asyncio.run(test())
