from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from ingestor import IngestionEngine

app = FastAPI(title="Ingestion & Indexer Service")
engine = IngestionEngine()

class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 3

class IngestRequest(BaseModel):
    file_path: str

@app.post("/ingest")
async def ingest_faqs(request: IngestRequest):
    try:
        engine.ingest(request.file_path)
        return {"status": "success", "message": "Ingestion complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(request: SearchRequest):
    try:
        results = engine.search(request.query, request.k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
