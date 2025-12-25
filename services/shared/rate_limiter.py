"""
Rate Limiting & Abuse Prevention System
Protects API from abuse, implements quotas, and detects suspicious patterns
"""
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import hashlib
import os

class RateLimiter:
    """
    Sliding window rate limiter with multiple strategies:
    - Per-API-key quotas
    - Per-IP throttling
    - Suspicious pattern detection
    - Burst protection
    """
    
    def __init__(self, db_path: str = "data/copilot.db"):
        self.db_path = db_path
        
        # In-memory cache for performance
        self.request_history: Dict[str, list] = defaultdict(list)
        self.blocked_keys: Dict[str, float] = {}  # key -> block_until_timestamp
        self.blocked_ips: Dict[str, float] = {}
        
        # Rate limit configurations
        self.limits = {
            'requests_per_minute': 20,
            'requests_per_hour': 500,
            'requests_per_day': 5000,
            'burst_limit': 10,  # Max requests in 1 second
            'burst_window': 1,  # seconds
        }
        
        # Abuse detection thresholds
        self.abuse_thresholds = {
            'failed_auth_limit': 5,  # Failed auth attempts before block
            'rapid_fire_threshold': 50,  # Requests in 10 seconds
            'identical_requests_limit': 20,  # Same query repeated
            'block_duration': 3600,  # 1 hour block
        }
        
        self._init_db()
    
    def _init_db(self):
        """Initialize rate limiting tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # API key usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_key_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT,
                    ip_address TEXT,
                    endpoint TEXT,
                    timestamp TEXT,
                    status_code INTEGER,
                    response_time_ms INTEGER
                )
            """)
            
            # Blocked entities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    entity_value TEXT,
                    reason TEXT,
                    blocked_at TEXT,
                    blocked_until TEXT,
                    auto_unblock INTEGER DEFAULT 1
                )
            """)
            
            # Abuse incidents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS abuse_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    entity_value TEXT,
                    incident_type TEXT,
                    details TEXT,
                    timestamp TEXT,
                    severity TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_key_timestamp 
                ON api_key_usage(api_key, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ip_timestamp 
                ON api_key_usage(ip_address, timestamp)
            """)
            
            conn.commit()
    
    def check_rate_limit(
        self, 
        api_key: str, 
        ip_address: str,
        endpoint: str = "/api/v1/chat"
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request should be allowed
        
        Returns:
            (allowed: bool, reason: str, retry_after: int)
        """
        now = time.time()
        
        # Check if blocked
        if api_key in self.blocked_keys:
            if now < self.blocked_keys[api_key]:
                retry_after = int(self.blocked_keys[api_key] - now)
                return False, "API key blocked due to abuse", retry_after
            else:
                del self.blocked_keys[api_key]
        
        if ip_address in self.blocked_ips:
            if now < self.blocked_ips[ip_address]:
                retry_after = int(self.blocked_ips[ip_address] - now)
                return False, "IP address blocked due to abuse", retry_after
            else:
                del self.blocked_ips[ip_address]
        
        # Clean old requests from history
        self._cleanup_history(api_key, now)
        
        # Get request history
        requests = self.request_history[api_key]
        
        # Check burst limit (requests in last second)
        recent = [r for r in requests if now - r < self.limits['burst_window']]
        if len(recent) >= self.limits['burst_limit']:
            self._log_abuse(api_key, ip_address, "burst_limit_exceeded")
            return False, "Too many requests in short time (burst protection)", 1
        
        # Check per-minute limit
        last_minute = [r for r in requests if now - r < 60]
        if len(last_minute) >= self.limits['requests_per_minute']:
            return False, "Rate limit: Max 20 requests per minute", 60
        
        # Check per-hour limit
        last_hour = [r for r in requests if now - r < 3600]
        if len(last_hour) >= self.limits['requests_per_hour']:
            return False, "Rate limit: Max 500 requests per hour", 3600
        
        # Check per-day limit
        last_day = [r for r in requests if now - r < 86400]
        if len(last_day) >= self.limits['requests_per_day']:
            return False, "Rate limit: Max 5000 requests per day", 86400
        
        # Passed all checks
        return True, None, None
    
    def record_request(
        self,
        api_key: str,
        ip_address: str,
        endpoint: str,
        status_code: int,
        response_time_ms: int
    ):
        """Record a request for rate limiting and analytics"""
        now = time.time()
        
        # Add to in-memory history
        self.request_history[api_key].append(now)
        
        # Persist to database (async in production)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_key_usage 
                    (api_key, ip_address, endpoint, timestamp, status_code, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    api_key,
                    ip_address,
                    endpoint,
                    datetime.utcnow().isoformat(),
                    status_code,
                    response_time_ms
                ))
                conn.commit()
        except Exception as e:
            print(f"Error recording request: {e}")
    
    def _cleanup_history(self, api_key: str, now: float):
        """Remove requests older than 24 hours from memory"""
        cutoff = now - 86400
        self.request_history[api_key] = [
            r for r in self.request_history[api_key] if r > cutoff
        ]
    
    def _log_abuse(
        self,
        entity_value: str,
        ip_address: str,
        incident_type: str,
        severity: str = "medium"
    ):
        """Log abuse incident"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO abuse_incidents
                    (entity_type, entity_value, incident_type, details, timestamp, severity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "api_key",
                    entity_value,
                    incident_type,
                    f"IP: {ip_address}",
                    datetime.utcnow().isoformat(),
                    severity
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging abuse: {e}")
    
    def block_entity(
        self,
        entity_type: str,
        entity_value: str,
        reason: str,
        duration_seconds: int = None
    ):
        """Block an API key or IP address"""
        if duration_seconds is None:
            duration_seconds = self.abuse_thresholds['block_duration']
        
        block_until = time.time() + duration_seconds
        
        # Add to in-memory cache
        if entity_type == "api_key":
            self.blocked_keys[entity_value] = block_until
        elif entity_type == "ip":
            self.blocked_ips[entity_value] = block_until
        
        # Persist to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO blocked_entities
                    (entity_type, entity_value, reason, blocked_at, blocked_until)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entity_type,
                    entity_value,
                    reason,
                    datetime.utcnow().isoformat(),
                    datetime.fromtimestamp(block_until).isoformat()
                ))
                conn.commit()
                
                print(f"🚫 Blocked {entity_type}: {entity_value} for {duration_seconds}s - Reason: {reason}")
        except Exception as e:
            print(f"Error blocking entity: {e}")
    
    def unblock_entity(self, entity_type: str, entity_value: str):
        """Manually unblock an entity"""
        if entity_type == "api_key" and entity_value in self.blocked_keys:
            del self.blocked_keys[entity_value]
        elif entity_type == "ip" and entity_value in self.blocked_ips:
            del self.blocked_ips[entity_value]
        
        print(f"✅ Unblocked {entity_type}: {entity_value}")
    
    def get_usage_stats(self, api_key: str, hours: int = 24) -> Dict:
        """Get usage statistics for an API key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            # Total requests
            cursor.execute("""
                SELECT COUNT(*) FROM api_key_usage
                WHERE api_key = ? AND timestamp > ?
            """, (api_key, cutoff))
            total_requests = cursor.fetchone()[0]
            
            # Successful requests
            cursor.execute("""
                SELECT COUNT(*) FROM api_key_usage
                WHERE api_key = ? AND timestamp > ? AND status_code = 200
            """, (api_key, cutoff))
            successful = cursor.fetchone()[0]
            
            # Average response time
            cursor.execute("""
                SELECT AVG(response_time_ms) FROM api_key_usage
                WHERE api_key = ? AND timestamp > ?
            """, (api_key, cutoff))
            avg_response_time = cursor.fetchone()[0] or 0
            
            # Requests per hour breakdown
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*)
                FROM api_key_usage
                WHERE api_key = ? AND timestamp > ?
                GROUP BY hour
                ORDER BY hour
            """, (api_key, cutoff))
            hourly_breakdown = dict(cursor.fetchall())
            
            return {
                'api_key': api_key,
                'period_hours': hours,
                'total_requests': total_requests,
                'successful_requests': successful,
                'failed_requests': total_requests - successful,
                'avg_response_time_ms': round(avg_response_time, 2),
                'hourly_breakdown': hourly_breakdown
            }
    
    def get_abuse_incidents(self, hours: int = 24) -> list:
        """Get recent abuse incidents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            cursor.execute("""
                SELECT entity_type, entity_value, incident_type, details, timestamp, severity
                FROM abuse_incidents
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff,))
            
            incidents = []
            for row in cursor.fetchall():
                incidents.append({
                    'entity_type': row[0],
                    'entity_value': row[1],
                    'incident_type': row[2],
                    'details': row[3],
                    'timestamp': row[4],
                    'severity': row[5]
                })
            
            return incidents
    
    def get_blocked_entities(self) -> list:
        """Get currently blocked entities"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                SELECT entity_type, entity_value, reason, blocked_at, blocked_until
                FROM blocked_entities
                WHERE blocked_until > ? AND auto_unblock = 1
                ORDER BY blocked_at DESC
            """, (now,))
            
            blocked = []
            for row in cursor.fetchall():
                blocked.append({
                    'entity_type': row[0],
                    'entity_value': row[1],
                    'reason': row[2],
                    'blocked_at': row[3],
                    'blocked_until': row[4]
                })
            
            return blocked
    
    def cleanup_old_records(self, days: int = 30):
        """Clean up old usage records"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                DELETE FROM api_key_usage WHERE timestamp < ?
            """, (cutoff,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted


class IPThrottler:
    """
    IP-based throttling for additional protection
    Works alongside API key rate limiting
    """
    
    def __init__(self):
        self.ip_requests: Dict[str, list] = defaultdict(list)
        self.ip_limit_per_minute = 30
    
    def check_ip(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Check if IP should be throttled"""
        now = time.time()
        
        # Clean old requests
        cutoff = now - 60
        self.ip_requests[ip_address] = [
            r for r in self.ip_requests[ip_address] if r > cutoff
        ]
        
        # Check limit
        if len(self.ip_requests[ip_address]) >= self.ip_limit_per_minute:
            return False, "IP rate limit exceeded: 30 requests per minute"
        
        # Record this request
        self.ip_requests[ip_address].append(now)
        
        return True, None


# Singleton instances
_rate_limiter = None
_ip_throttler = None

def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def get_ip_throttler() -> IPThrottler:
    """Get or create IP throttler instance"""
    global _ip_throttler
    if _ip_throttler is None:
        _ip_throttler = IPThrottler()
    return _ip_throttler
