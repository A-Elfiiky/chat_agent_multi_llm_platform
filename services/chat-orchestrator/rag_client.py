import httpx
import os
import sys
from typing import List, Dict, Any

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config

class RAGClient:
    def __init__(self):
        self.config = load_config()
        # In a real docker setup, this would be the service name, e.g., http://ingestion-indexer:8000
        # For local dev, we'll assume it's running on a specific port or we import the logic directly if monolithic.
        # Let's assume microservice architecture with a configurable URL.
        self.base_url = "http://localhost:8001" # Default port for ingestion-indexer

    async def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={"query": query, "k": k},
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except Exception as e:
                print(f"Error calling RAG service: {e}")
                # Fallback or re-raise depending on policy. 
                # For now, return empty list to allow LLM to try without context or fail gracefully.
                return []
