import requests
import json
import time
import sys

GATEWAY_URL = "http://localhost:8000"
INGESTION_URL = "http://localhost:8001"

def test_ingestion():
    print("\n--- Testing Ingestion ---")
    # In a real scenario, we'd upload a file. 
    # For this prototype, the ingestor.py main block ingests the sample file.
    # But we can trigger it via API if we want to re-ingest.
    # Let's assume the service ingests on startup or we trigger it here.
    
    # We'll use the absolute path inside the container or relative path if running locally
    # For this script, we'll just hit the search endpoint to see if data exists.
    pass

def test_chat(question):
    print(f"\n--- Testing Chat: '{question}' ---")
    url = f"{GATEWAY_URL}/api/v1/chat"
    payload = {"message": question}
    
    try:
        start = time.time()
        response = requests.post(url, json=payload)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {response.status_code}")
            print(f"Provider: {data.get('provider')}")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Answer: {data.get('answer_text')}")
            print("Citations:")
            for cit in data.get('citations', []):
                print(f" - [{cit['score']:.2f}] {cit['title']} (ID: {cit['doc_id']})")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Waiting for services to be ready...")
    # In a real script, we'd poll /health endpoints
    
    # 1. Trigger Ingestion (Optional if done at startup)
    # requests.post(f"{INGESTION_URL}/ingest", json={"file_path": "..."})
    
    # 2. Test Questions
    questions = [
        "How do I reset my password?",
        "What is the shipping cost for a $30 order?",
        "Can I return a used item?",
        "Tell me a joke about computers." # Should trigger fallback or low confidence/irrelevant
    ]
    
    for q in questions:
        test_chat(q)
