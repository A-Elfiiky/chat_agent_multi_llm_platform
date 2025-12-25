import os

# Disable SSL verification for HuggingFace downloads (local dev only)
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

import json
import faiss
import numpy as np
import pickle
import sys
import glob

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Patch requests to disable SSL verification
import requests
from requests import Session
original_request = Session.request
def patched_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return original_request(self, *args, **kwargs)
Session.request = patched_request

from sentence_transformers import SentenceTransformer
from typing import List, Dict

# Document Parsers
from pypdf import PdfReader
from docx import Document

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config

class IngestionEngine:
    def __init__(self):
        self.config = load_config()
        self.model_name = "all-MiniLM-L6-v2" # Lightweight model for prototype
        self.model = SentenceTransformer(self.model_name)
        self.vector_store_path = self.config['database']['vector_store_path']
        self.index_file = os.path.join(self.vector_store_path, "index.faiss")
        self.metadata_file = os.path.join(self.vector_store_path, "metadata.pkl")
        
        # Ensure directory exists
        os.makedirs(self.vector_store_path, exist_ok=True)
        self._ensure_default_index()

    def _has_existing_index(self) -> bool:
        return os.path.exists(self.index_file) and os.path.exists(self.metadata_file)

    def _ensure_default_index(self):
        """Automatically seed the vector store with sample data if empty."""
        if self._has_existing_index():
            return
        sample_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/faqs/sample_faq.json'))
        if not os.path.exists(sample_file):
            print("⚠️  Sample FAQ file not found; vector store will remain empty until ingestion runs.")
            return
        try:
            print("🔄 Vector store missing — ingesting sample FAQs for default coverage...")
            self.ingest(sample_file)
        except Exception as exc:
            print(f"⚠️  Failed to ingest sample FAQs: {exc}")

    def load_file(self, file_path: str) -> List[Dict]:
        ext = os.path.splitext(file_path)[1].lower()
        faqs = []
        
        try:
            if ext == '.json':
                with open(file_path, 'r') as f:
                    faqs = json.load(f)
            elif ext == '.pdf':
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                # Simple chunking by paragraphs for PDF
                # In a real app, use a smarter splitter (e.g., LangChain RecursiveCharacterTextSplitter)
                paragraphs = [p for p in text.split('\n\n') if len(p.strip()) > 50]
                for i, p in enumerate(paragraphs):
                    faqs.append({
                        "id": f"{os.path.basename(file_path)}-{i}",
                        "title": f"Excerpt from {os.path.basename(file_path)}",
                        "section": "Document",
                        "content": p.strip(),
                        "tags": ["pdf"]
                    })
            elif ext == '.docx':
                doc = Document(file_path)
                for i, para in enumerate(doc.paragraphs):
                    if len(para.text.strip()) > 50:
                        faqs.append({
                            "id": f"{os.path.basename(file_path)}-{i}",
                            "title": f"Excerpt from {os.path.basename(file_path)}",
                            "section": "Document",
                            "content": para.text.strip(),
                            "tags": ["docx"]
                        })
            else:
                print(f"Unsupported file type: {ext}")
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return faqs

    def create_chunks(self, faqs: List[Dict]) -> List[Dict]:
        chunks = []
        for faq in faqs:
            # Simple chunking: Title + Content
            text = f"{faq['title']}\n{faq['content']}"
            chunks.append({
                "id": faq['id'],
                "text": text,
                "metadata": faq
            })
        return chunks

    def ingest(self, file_path: str):
        print(f"Loading data from {file_path}...")
        items = self.load_file(file_path)
        if not items:
            print("No items found to ingest.")
            return

        chunks = self.create_chunks(items)
        
        texts = [chunk['text'] for chunk in chunks]
        print(f"Embedding {len(texts)} chunks...")
        embeddings = self.model.encode(texts)
        
        # Load existing index if available to append (simplified: just overwriting or creating new for now)
        # For production, we should load existing, add new, and save back.
        # Here we will just create a new one for the demo simplicity or append if we implemented it.
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype('float32'))
        
        # Save index and metadata
        print(f"Saving index to {self.index_file}...")
        faiss.write_index(index, self.index_file)
        
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(chunks, f)
            
        print("Ingestion complete.")

    def search(self, query: str, k: int = 3):
        if not os.path.exists(self.index_file) or not os.path.exists(self.metadata_file):
            return []
            
        index = faiss.read_index(self.index_file)
        with open(self.metadata_file, 'rb') as f:
            chunks = pickle.load(f)
            
        query_vector = self.model.encode([query])
        distances, indices = index.search(np.array(query_vector).astype('float32'), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                results.append({
                    "chunk": chunks[idx],
                    "score": float(distances[0][i]) # L2 distance (lower is better)
                })
        return results

if __name__ == "__main__":
    engine = IngestionEngine()
    # For prototype, just ingest the sample file
    sample_faq_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/faqs/sample_faq.json'))
    engine.ingest(sample_faq_path)
