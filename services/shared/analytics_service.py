"""
Analytics Service
Provides comprehensive analytics and metrics for the AI customer service platform.

Features:
- Real-time usage statistics
- Performance metrics
- Popular questions tracking
- User engagement analytics
- Cost analysis
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


class AnalyticsService:
    """
    Centralized analytics service for monitoring platform performance and usage.
    """
    
    def __init__(self, db_path: str = "data/copilot.db"):
        """Initialize analytics service."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize analytics tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Analytics events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                session_id TEXT,
                user_id TEXT,
                timestamp REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type
            ON analytics_events(event_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp
            ON analytics_events(timestamp)
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT,
                timestamp REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_name
            ON performance_metrics(metric_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp
            ON performance_metrics(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_dashboard_overview(self, days: int = 7) -> Dict:
        """
        Get comprehensive dashboard overview.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dashboard metrics
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total interactions
        cursor.execute("""
            SELECT COUNT(*) FROM interaction_logs
            WHERE timestamp >= ?
        """, (cutoff,))
        total_interactions = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time_ms) FROM interaction_logs
            WHERE timestamp >= ? AND response_time_ms IS NOT NULL
        """, (cutoff,))
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Sentiment distribution
        cursor.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM interaction_logs
            WHERE timestamp >= ? AND sentiment IS NOT NULL
            GROUP BY sentiment
        """, (cutoff,))
        sentiment_dist = dict(cursor.fetchall())
        
        # Escalation rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN escalation_needed = 1 THEN 1 END) as escalations,
                COUNT(*) as total
            FROM interaction_logs
            WHERE timestamp >= ?
        """, (cutoff,))
        esc_row = cursor.fetchone()
        escalation_rate = (esc_row[0] / max(esc_row[1], 1)) * 100 if esc_row else 0
        
        # Cache hit rate
        cursor.execute("""
            SELECT hit_count, query FROM cache
            WHERE created_at >= ?
        """, (cutoff,))
        cache_data = cursor.fetchall()
        cache_hits = sum(row[0] for row in cache_data)
        cache_entries = len(cache_data)
        cache_hit_rate = (cache_hits / max(cache_entries, 1)) if cache_entries > 0 else 0
        
        # Active sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM interaction_logs
            WHERE timestamp >= ?
        """, (cutoff,))
        active_sessions = cursor.fetchone()[0]
        
        # Provider distribution
        cursor.execute("""
            SELECT provider, COUNT(*) as count
            FROM interaction_logs
            WHERE timestamp >= ? AND provider IS NOT NULL
            GROUP BY provider
        """, (cutoff,))
        provider_dist = dict(cursor.fetchall())
        
        # Confidence score average
        cursor.execute("""
            SELECT AVG(confidence) FROM interaction_logs
            WHERE timestamp >= ? AND confidence IS NOT NULL
        """, (cutoff,))
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "period_days": days,
            "total_interactions": total_interactions,
            "active_sessions": active_sessions,
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_confidence": round(avg_confidence, 3),
            "escalation_rate": round(escalation_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "sentiment_distribution": sentiment_dist,
            "provider_distribution": provider_dist
        }
    
    def get_popular_questions(self, limit: int = 20, days: int = 30) -> List[Dict]:
        """
        Get most frequently asked questions.
        
        Args:
            limit: Maximum number of questions to return
            days: Number of days to analyze
            
        Returns:
            List of popular questions with counts
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_message,
                COUNT(*) as ask_count,
                AVG(confidence) as avg_confidence,
                AVG(response_time_ms) as avg_response_time
            FROM interaction_logs
            WHERE timestamp >= ? AND user_message IS NOT NULL
            GROUP BY LOWER(user_message)
            ORDER BY ask_count DESC
            LIMIT ?
        """, (cutoff, limit))
        
        questions = []
        for row in cursor.fetchall():
            questions.append({
                "question": row[0],
                "count": row[1],
                "avg_confidence": round(row[2], 3) if row[2] else 0,
                "avg_response_time_ms": round(row[3], 2) if row[3] else 0
            })
        
        conn.close()
        return questions
    
    def get_hourly_traffic(self, days: int = 7) -> List[Dict]:
        """
        Get hourly traffic patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Hourly traffic data
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%H', datetime(timestamp, 'unixepoch')) as hour,
                COUNT(*) as count
            FROM interaction_logs
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
        """, (cutoff,))
        
        hourly_data = []
        for row in cursor.fetchall():
            hourly_data.append({
                "hour": int(row[0]),
                "count": row[1]
            })
        
        conn.close()
        return hourly_data
    
    def get_daily_metrics(self, days: int = 30) -> List[Dict]:
        """
        Get daily metrics over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Daily metrics
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                date(datetime(timestamp, 'unixepoch')) as day,
                COUNT(*) as interactions,
                AVG(response_time_ms) as avg_response_time,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN escalation_needed = 1 THEN 1 END) as escalations,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM interaction_logs
            WHERE timestamp >= ?
            GROUP BY day
            ORDER BY day
        """, (cutoff,))
        
        daily_metrics = []
        for row in cursor.fetchall():
            daily_metrics.append({
                "date": row[0],
                "interactions": row[1],
                "avg_response_time_ms": round(row[2], 2) if row[2] else 0,
                "avg_confidence": round(row[3], 3) if row[3] else 0,
                "escalations": row[4],
                "unique_sessions": row[5]
            })
        
        conn.close()
        return daily_metrics
    
    def get_user_engagement(self, days: int = 30) -> Dict:
        """
        Get user engagement metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Engagement metrics
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Average messages per session
        cursor.execute("""
            SELECT 
                session_id,
                COUNT(*) as message_count
            FROM interaction_logs
            WHERE timestamp >= ?
            GROUP BY session_id
        """, (cutoff,))
        
        session_counts = [row[1] for row in cursor.fetchall()]
        avg_messages_per_session = sum(session_counts) / max(len(session_counts), 1)
        
        # Session duration distribution
        cursor.execute("""
            SELECT 
                session_id,
                MAX(timestamp) - MIN(timestamp) as duration
            FROM interaction_logs
            WHERE timestamp >= ?
            GROUP BY session_id
        """, (cutoff,))
        
        durations = [row[1] for row in cursor.fetchall()]
        avg_session_duration = sum(durations) / max(len(durations), 1)
        
        # Return rate (sessions with multiple days)
        cursor.execute("""
            SELECT 
                session_id,
                COUNT(DISTINCT date(datetime(timestamp, 'unixepoch'))) as days_active
            FROM interaction_logs
            WHERE timestamp >= ?
            GROUP BY session_id
        """, (cutoff,))
        
        multi_day_sessions = sum(1 for row in cursor.fetchall() if row[1] > 1)
        total_sessions = len(session_counts)
        return_rate = (multi_day_sessions / max(total_sessions, 1)) * 100
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "avg_messages_per_session": round(avg_messages_per_session, 2),
            "avg_session_duration_seconds": round(avg_session_duration, 2),
            "return_rate_percent": round(return_rate, 2),
            "multi_day_sessions": multi_day_sessions
        }
    
    def get_performance_stats(self, days: int = 7) -> Dict:
        """
        Get system performance statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance statistics
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Response time percentiles
        cursor.execute("""
            SELECT response_time_ms
            FROM interaction_logs
            WHERE timestamp >= ? AND response_time_ms IS NOT NULL
            ORDER BY response_time_ms
        """, (cutoff,))
        
        response_times = [row[0] for row in cursor.fetchall()]
        
        percentiles = {}
        if response_times:
            percentiles = {
                "p50": response_times[int(len(response_times) * 0.5)],
                "p75": response_times[int(len(response_times) * 0.75)],
                "p90": response_times[int(len(response_times) * 0.9)],
                "p95": response_times[int(len(response_times) * 0.95)],
                "p99": response_times[int(len(response_times) * 0.99)] if len(response_times) > 100 else response_times[-1]
            }
        
        # Error rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN confidence < 0.5 THEN 1 END) as low_confidence,
                COUNT(*) as total
            FROM interaction_logs
            WHERE timestamp >= ?
        """, (cutoff,))
        
        row = cursor.fetchone()
        error_rate = (row[0] / max(row[1], 1)) * 100 if row else 0
        
        conn.close()
        
        return {
            "response_time_percentiles": percentiles,
            "error_rate_percent": round(error_rate, 2),
            "total_requests": len(response_times)
        }
    
    def get_cost_analysis(self, days: int = 30) -> Dict:
        """
        Estimate costs based on LLM provider usage.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Cost analysis
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Provider usage
        cursor.execute("""
            SELECT provider, COUNT(*) as count
            FROM interaction_logs
            WHERE timestamp >= ? AND provider IS NOT NULL
            GROUP BY provider
        """, (cutoff,))
        
        provider_usage = dict(cursor.fetchall())
        
        # Estimated costs (rough estimates)
        cost_per_request = {
            "openai": 0.002,  # ~$0.002 per request
            "anthropic": 0.0015,
            "google": 0.001,
            "local": 0.0
        }
        
        estimated_cost = sum(
            provider_usage.get(provider, 0) * cost
            for provider, cost in cost_per_request.items()
        )
        
        # Cache savings
        cursor.execute("""
            SELECT SUM(hit_count) FROM cache
            WHERE created_at >= ?
        """, (cutoff,))
        
        cache_hits = cursor.fetchone()[0] or 0
        cache_savings = cache_hits * 0.0015  # Average cost saved per cache hit
        
        conn.close()
        
        return {
            "estimated_cost_usd": round(estimated_cost, 2),
            "cache_savings_usd": round(cache_savings, 2),
            "total_requests": sum(provider_usage.values()),
            "provider_breakdown": provider_usage,
            "cost_per_provider": {
                provider: round(count * cost_per_request.get(provider, 0), 2)
                for provider, count in provider_usage.items()
            }
        }


# Singleton instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """Get or create singleton analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
