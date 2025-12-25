"""
Caching Layer for LLM Responses
Reduces API costs by caching frequently asked questions
"""
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

class ResponseCache:
    """
    Cache for LLM responses to reduce API calls and costs.
    Uses SQLite for persistence and simple string similarity for matching.
    In production, consider Redis for distributed caching.
    """
    
    def __init__(self, db_path: str = "data/copilot.db", ttl_hours: int = 24):
        self.db_path = db_path
        self.ttl_hours = ttl_hours
        self._init_db()
    
    def _init_db(self):
        """Initialize cache tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE,
                    original_query TEXT,
                    response_data TEXT,
                    created_at TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 1,
                    metadata TEXT
                )
            """)
            
            # Create index on query_hash for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_hash 
                ON response_cache(query_hash)
            """)
            
            # Create index on created_at for cleanup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON response_cache(created_at)
            """)
            
            conn.commit()
    
    def _hash_query(self, query: str, context_hash: str = "") -> str:
        """Create hash of normalized query for cache key"""
        # Normalize query (lowercase, strip whitespace)
        normalized = query.lower().strip()
        
        # Include context in hash if provided
        combined = f"{normalized}:{context_hash}"
        
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, query: str, context_hash: str = "") -> Optional[Dict[str, Any]]:
        """
        Get cached response for query
        
        Returns:
            Cached response data or None if not found/expired
        """
        query_hash = self._hash_query(query, context_hash)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get cached entry
            cursor.execute("""
                SELECT response_data, created_at, access_count
                FROM response_cache
                WHERE query_hash = ?
            """, (query_hash,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            response_data, created_at, access_count = row
            
            # Check if expired
            created_time = datetime.fromisoformat(created_at)
            if datetime.utcnow() - created_time > timedelta(hours=self.ttl_hours):
                # Delete expired entry
                cursor.execute(
                    "DELETE FROM response_cache WHERE query_hash = ?",
                    (query_hash,)
                )
                conn.commit()
                return None
            
            # Update access stats
            cursor.execute("""
                UPDATE response_cache
                SET last_accessed = ?, access_count = ?
                WHERE query_hash = ?
            """, (datetime.utcnow().isoformat(), access_count + 1, query_hash))
            
            conn.commit()
            
            # Parse and return cached data
            cached = json.loads(response_data)
            cached['cache_hit'] = True
            cached['access_count'] = access_count + 1
            
            return cached
    
    def set(
        self, 
        query: str, 
        response_data: Dict[str, Any],
        context_hash: str = "",
        metadata: Dict = None
    ):
        """Cache a response"""
        query_hash = self._hash_query(query, context_hash)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO response_cache
                (query_hash, original_query, response_data, created_at, last_accessed, access_count, metadata)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                query_hash,
                query,
                json.dumps(response_data),
                now,
                now,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
    
    def invalidate(self, query: str, context_hash: str = ""):
        """Invalidate (delete) a cached entry"""
        query_hash = self._hash_query(query, context_hash)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM response_cache WHERE query_hash = ?",
                (query_hash,)
            )
            conn.commit()
    
    def clear_all(self):
        """Clear entire cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM response_cache")
            conn.commit()
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(hours=self.ttl_hours)).isoformat()
            
            cursor.execute(
                "DELETE FROM response_cache WHERE created_at < ?",
                (cutoff,)
            )
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM response_cache")
            total_entries = cursor.fetchone()[0]
            
            # Total access count
            cursor.execute("SELECT SUM(access_count) FROM response_cache")
            total_accesses = cursor.fetchone()[0] or 0
            
            # Most accessed queries
            cursor.execute("""
                SELECT original_query, access_count
                FROM response_cache
                ORDER BY access_count DESC
                LIMIT 10
            """)
            top_queries = [
                {"query": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]
            
            # Cache age stats
            cursor.execute("""
                SELECT 
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM response_cache
            """)
            age_stats = cursor.fetchone()
            
            return {
                "total_entries": total_entries,
                "total_accesses": total_accesses,
                "hit_rate": (total_accesses - total_entries) / max(total_accesses, 1),
                "top_queries": top_queries,
                "oldest_entry": age_stats[0] if age_stats[0] else None,
                "newest_entry": age_stats[1] if age_stats[1] else None
            }
    
    def get_popular_queries(self, limit: int = 20) -> list:
        """Get most frequently accessed queries"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT original_query, access_count, last_accessed
                FROM response_cache
                ORDER BY access_count DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    "query": row[0],
                    "access_count": row[1],
                    "last_accessed": row[2]
                }
                for row in cursor.fetchall()
            ]


class SmartCache(ResponseCache):
    """
    Enhanced cache with semantic similarity matching.
    Can match similar questions even if phrased differently.
    Requires sentence-transformers for embeddings.
    """
    
    def __init__(self, *args, similarity_threshold: float = 0.85, **kwargs):
        super().__init__(*args, **kwargs)
        self.similarity_threshold = similarity_threshold
        self._init_embeddings()
    
    def _init_embeddings(self):
        """Initialize embedding model for semantic matching"""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.semantic_enabled = True
            print("✅ Semantic cache enabled")
        except ImportError:
            print("⚠️  sentence-transformers not available. Using exact match only.")
            self.semantic_enabled = False
    
    def _get_embedding(self, text: str):
        """Get embedding vector for text"""
        if not self.semantic_enabled:
            return None
        return self.embedder.encode([text])[0].tolist()
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def find_similar(self, query: str, limit: int = 5) -> list:
        """Find similar cached queries using semantic search"""
        if not self.semantic_enabled:
            # Fall back to exact match
            cached = self.get(query)
            return [cached] if cached else []
        
        query_embedding = self._get_embedding(query)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT original_query, response_data, metadata
                FROM response_cache
            """)
            
            similar = []
            for row in cursor.fetchall():
                original_query, response_data, metadata_str = row
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                # Get stored embedding or compute it
                if 'embedding' in metadata:
                    cached_embedding = metadata['embedding']
                else:
                    cached_embedding = self._get_embedding(original_query)
                
                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                if similarity >= self.similarity_threshold:
                    similar.append({
                        'query': original_query,
                        'similarity': similarity,
                        'response': json.loads(response_data)
                    })
            
            # Sort by similarity and return top matches
            similar.sort(key=lambda x: x['similarity'], reverse=True)
            return similar[:limit]
