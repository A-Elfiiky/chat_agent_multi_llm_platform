"""
Pre-download models with SSL verification disabled
Run this before starting services if you encounter SSL errors
"""
import os
import ssl

# Disable SSL verification
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

print("Downloading sentence-transformers model...")
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model downloaded successfully to cache!")
print(f"Model location: {model._model_card_vars['model_id']}")
