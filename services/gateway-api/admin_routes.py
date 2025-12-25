from fastapi import APIRouter, HTTPException, Depends, Header, Response
from fastapi import Body
from pydantic import BaseModel, Field, validator
from typing import Any
from datetime import datetime
import sqlite3
import os
from typing import List, Dict, Any, Optional
import sys
import time

# Add shared modules to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.conversation_memory import ConversationMemory
from services.shared.cache import ResponseCache
from services.shared.rate_limiter import get_rate_limiter
from services.shared.knowledge_gap_analyzer import KnowledgeGapAnalyzer
from services.shared.translation_service import get_translation_service
from services.shared.analytics_service import get_analytics_service
from services.shared.settings_service import get_settings_service
from services.shared.provider_metrics import get_provider_metrics
from services.shared.config_utils import load_config
from services.shared.integration_service import get_integration_service
from services.shared.faq_repository import FAQRepository
from services.shared.llm_test_service import (
    get_llm_test_runner,
    get_llm_test_service,
)
from services.shared.telephony_test_service import (
    get_telephony_test_runner,
    get_telephony_test_service,
)

config = load_config()
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or config.get('security', {}).get('admin_token')
settings_service = get_settings_service()
provider_metrics = get_provider_metrics()

async def require_admin_token(x_admin_token: str = Header(None)):
    if not ADMIN_TOKEN:
        return True  # Dev mode fallback
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return True

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_token)])

DB_PATH = "data/copilot.db"

# Initialize managers
conversation_memory = ConversationMemory(DB_PATH)
response_cache = ResponseCache(DB_PATH)
rate_limiter = get_rate_limiter()
gap_analyzer = KnowledgeGapAnalyzer()
translation_service = get_translation_service()
analytics_service = get_analytics_service()
llm_config = config.get('llm', {})
integration_service = get_integration_service()
faq_repo = FAQRepository(DB_PATH)
llm_test_service = get_llm_test_service(DB_PATH)
llm_test_runner = get_llm_test_runner()
telephony_test_service = get_telephony_test_service(DB_PATH)
telephony_test_runner = get_telephony_test_runner(telephony_test_service)


class FAQBaseModel(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    answer: str = Field(..., min_length=5)
    category: str = Field(..., min_length=2, max_length=120)
    tags: List[str] = Field(default_factory=list)
    status: str = Field(default="active")

    @validator('question', 'answer', 'category')
    def strip_and_validate(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned

    @validator('status')
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"active", "draft", "archived"}:
            raise ValueError("status must be one of: active, draft, archived")
        return normalized

    @validator('tags', each_item=True)
    def validate_tags(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("tags cannot contain empty values")
        return cleaned


class FAQCreateRequest(FAQBaseModel):
    pass


class FAQUpdateRequest(FAQBaseModel):
    last_updated: datetime = Field(..., description="Timestamp of the last known update for optimistic locking")


class FAQResponse(FAQBaseModel):
    id: str
    created_at: datetime
    last_updated: datetime


class FAQListResponse(BaseModel):
    items: List[FAQResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class LLMRunTestRequest(BaseModel):
    providers: Optional[List[str]] = None
    prompt: Optional[str] = None


class TelephonyRunTestRequest(BaseModel):
    tests: Optional[List[str]] = None
    mode: str = Field(default="dry", pattern=r"^(dry|live)$")


def _faq_record_to_response(record: Dict[str, Any]) -> FAQResponse:
    return FAQResponse(
        id=record['id'],
        question=record['question'],
        answer=record['answer'],
        category=record.get('category') or "General",
        tags=record.get('tags') or [],
        status=record.get('status') or 'active',
        created_at=datetime.fromisoformat(record['created_at']) if record.get('created_at') else datetime.utcnow(),
        last_updated=datetime.fromisoformat(record['updated_at']) if record.get('updated_at') else datetime.utcnow(),
    )


def _get_available_providers() -> List[str]:
    return list(llm_config.get('providers', {}).keys())


def _resolve_provider_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    trimmed = name.strip()
    if not trimmed:
        return None
    lower_name = trimmed.lower()
    if lower_name in {"all", "*"}:
        return None
    candidates = _get_available_providers() + llm_test_runner.get_active_providers()
    for candidate in candidates:
        if candidate and candidate.lower() == lower_name:
            return candidate
    return lower_name

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_logs(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM rag_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

@router.get("/stats")
async def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        stats = {}
        
        # Total Interactions
        cursor.execute("SELECT COUNT(*) FROM rag_logs")
        stats['total_interactions'] = cursor.fetchone()[0]
        
        # Avg Latency
        cursor.execute("SELECT AVG(latency_ms) FROM rag_logs")
        stats['avg_latency_ms'] = cursor.fetchone()[0] or 0
        
        # Provider Usage
        cursor.execute("SELECT llm_provider, COUNT(*) FROM rag_logs GROUP BY llm_provider")
        stats['provider_usage'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Sentiment stats (if available)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN json_extract(metadata, '$.sentiment') = 'positive' THEN 1 END) as positive,
                    COUNT(CASE WHEN json_extract(metadata, '$.sentiment') = 'negative' THEN 1 END) as negative,
                    COUNT(CASE WHEN json_extract(metadata, '$.sentiment') = 'neutral' THEN 1 END) as neutral,
                    COUNT(CASE WHEN json_extract(metadata, '$.needs_escalation') = 1 THEN 1 END) as escalations
                FROM conversation_messages
                WHERE role = 'user'
            """)
            sentiment_row = cursor.fetchone()
            if sentiment_row:
                stats['sentiment_stats'] = {
                    'positive': sentiment_row[0],
                    'negative': sentiment_row[1],
                    'neutral': sentiment_row[2],
                    'escalations_needed': sentiment_row[3]
                }
        except Exception:
            pass  # Table might not exist yet
        
        # Cache stats
        stats['cache_stats'] = response_cache.get_stats()
        
        # Active sessions
        active_sessions = conversation_memory.get_active_sessions(hours=24)
        stats['active_sessions_24h'] = len(active_sessions)
        
        return stats
    finally:
        conn.close()

@router.get("/conversations")
async def get_active_conversations(hours: int = 24):
    """Get active conversation sessions"""
    sessions = conversation_memory.get_active_sessions(hours=hours)
    
    # Get details for each session
    detailed_sessions = []
    for session in sessions:
        history = conversation_memory.get_conversation_history(
            session['session_id'],
            limit=5
        )
        entities = conversation_memory.get_session_entities(session['session_id'])
        
        detailed_sessions.append({
            **session,
            'message_count': len(history),
            'last_message': history[-1]['content'] if history else None,
            'entities': entities
        })
    
    return detailed_sessions

@router.get("/conversation/{session_id}")
async def get_conversation_details_route(session_id: str):
    return await get_conversation_details(session_id)


@router.get("/analytics/fallbacks")
async def get_fallback_stats(days: int = 7, limit: int = 20):
    summary = provider_metrics.get_summary(days=days)
    distribution = provider_metrics.get_fallback_distribution(days=days)
    failures = provider_metrics.get_recent_failures(limit=limit)
    return {
        "summary": summary,
        "distribution": distribution,
        "recent_failures": failures
    }


async def get_conversation_details(session_id: str):
    """Get full conversation history for a session"""
    history = conversation_memory.get_conversation_history(session_id, limit=100)
    entities = conversation_memory.get_session_entities(session_id)
    
    return {
        'session_id': session_id,
        'history': history,
        'entities': entities
    }


# FAQ Management -------------------------------------------------------------

@router.get("/faqs", response_model=FAQListResponse)
async def list_faqs(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
):
    records, total = faq_repo.list(
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        status=status,
    )
    items = [_faq_record_to_response(record) for record in records]
    has_next = page * page_size < total
    return FAQListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )


@router.post("/faqs", response_model=FAQResponse, status_code=201)
async def create_faq(payload: FAQCreateRequest):
    record = faq_repo.create(
        question=payload.question,
        answer=payload.answer,
        category=payload.category,
        tags=payload.tags,
        status=payload.status,
    )
    return _faq_record_to_response(record)


@router.put("/faqs/{faq_id}", response_model=FAQResponse)
async def update_faq(faq_id: str, payload: FAQUpdateRequest):
    existing = faq_repo.get(faq_id)
    if not existing:
        raise HTTPException(status_code=404, detail="FAQ not found")

    stored_updated_at = existing.get('updated_at')
    try:
        stored_dt = datetime.fromisoformat(stored_updated_at) if stored_updated_at else None
    except ValueError:
        stored_dt = None

    incoming_dt = payload.last_updated.replace(tzinfo=None)
    if stored_dt and stored_dt.replace(tzinfo=None) != incoming_dt:
        raise HTTPException(status_code=409, detail="FAQ was updated by another user. Please refresh and try again.")

    record = faq_repo.update(
        faq_id,
        question=payload.question,
        answer=payload.answer,
        category=payload.category,
        tags=payload.tags,
        status=payload.status,
    )
    if not record:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return _faq_record_to_response(record)


@router.delete("/faqs/{faq_id}", status_code=204)
async def delete_faq(faq_id: str):
    deleted = faq_repo.delete(faq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return Response(status_code=204)


# Integrations & Webhooks ---------------------------------------------------

@router.get("/integrations")
async def get_integrations_state():
    return integration_service.get_state()


@router.post("/integrations/{name}/connect")
async def connect_integration_route(name: str, payload: Optional[Dict[str, Any]] = Body(None)):
    try:
        integration = integration_service.connect_integration(
            name=name,
            api_key=(payload or {}).get('api_key'),
            webhook_url=(payload or {}).get('webhook_url'),
            metadata=(payload or {}).get('metadata'),
        )
        return {"status": "connected", "integration": integration}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/integrations/{name}/disconnect")
async def disconnect_integration_route(name: str):
    try:
        integration = integration_service.disconnect_integration(name)
        return {"status": "disconnected", "integration": integration}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/integrations/api-keys")
async def add_api_key_route(payload: Dict[str, Any] = Body(...)):
    service = payload.get('service')
    key_name = payload.get('key_name')
    key_value = payload.get('key_value')
    if not service or not key_name or not key_value:
        raise HTTPException(status_code=400, detail="service, key_name and key_value are required")
    try:
        api_key = integration_service.add_api_key(service, key_name, key_value)
        return {"status": "created", "api_key": api_key}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/integrations/api-keys/{key_id}/rotate")
async def rotate_api_key_route(key_id: int, payload: Dict[str, Any] = Body(...)):
    new_value = payload.get('key_value')
    if not new_value:
        raise HTTPException(status_code=400, detail="key_value is required")
    try:
        api_key = integration_service.rotate_api_key(key_id, new_value)
        return {"status": "rotated", "api_key": api_key}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/integrations/api-keys/{key_id}")
async def revoke_api_key_route(key_id: int):
    integration_service.revoke_api_key(key_id)
    return {"status": "revoked", "key_id": key_id}


@router.post("/integrations/webhooks")
async def add_webhook_route(payload: Dict[str, Any] = Body(...)):
    name = payload.get('name')
    url = payload.get('url')
    events = payload.get('events')
    if not name or not url:
        raise HTTPException(status_code=400, detail="name and url are required")
    webhook = integration_service.add_webhook(name, url, events)
    return {"status": "created", "webhook": webhook}


@router.delete("/integrations/webhooks/{webhook_id}")
async def delete_webhook_route(webhook_id: int):
    integration_service.delete_webhook(webhook_id)
    return {"status": "deleted", "webhook_id": webhook_id}

@router.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    return response_cache.get_stats()

@router.get("/cache/popular")
async def get_popular_queries(limit: int = 20):
    """Get most popular cached queries"""
    return response_cache.get_popular_queries(limit=limit)

@router.post("/cache/clear")
async def clear_cache():
    """Clear the entire response cache"""
    response_cache.clear_all()
    return {"status": "success", "message": "Cache cleared"}

@router.post("/cache/cleanup")
async def cleanup_cache():
    """Remove expired cache entries"""
    deleted = response_cache.cleanup_expired()
    return {"status": "success", "deleted_entries": deleted}


@router.get("/settings/llm")
async def get_llm_settings():
    fallback_order_default = llm_config.get('fallback_order', [])
    fallback_order = settings_service.get('llm_fallback_order', fallback_order_default)
    if not isinstance(fallback_order, list) or not fallback_order:
        fallback_order = fallback_order_default

    primary_default = fallback_order_default[0] if fallback_order_default else None
    primary_provider = settings_service.get('llm_primary_provider', primary_default)
    auto_fallback = settings_service.get('llm_auto_fallback', True)

    return {
        "primary_provider": primary_provider,
        "fallback_order": fallback_order,
        "auto_fallback": bool(auto_fallback),
        "available_providers": _get_available_providers()
    }


@router.post("/settings/llm")
async def update_llm_settings(payload: Dict[str, Any]):
    available = _get_available_providers()
    fallback_order_default = llm_config.get('fallback_order', available)

    primary = payload.get('primary_provider')
    fallback_order = payload.get('fallback_order')
    auto_fallback = payload.get('auto_fallback')

    if primary and primary not in available:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{primary}'")

    if fallback_order:
        if not isinstance(fallback_order, list):
            raise HTTPException(status_code=400, detail="fallback_order must be a list")
        invalid = [p for p in fallback_order if p not in available]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown providers in fallback_order: {', '.join(invalid)}")
        settings_service.set('llm_fallback_order', fallback_order)
    elif fallback_order is None:
        # keep existing else default to config
        pass

    if primary:
        settings_service.set('llm_primary_provider', primary)
    elif primary is None and not settings_service.get('llm_primary_provider') and fallback_order_default:
        settings_service.set('llm_primary_provider', fallback_order_default[0])

    if auto_fallback is not None:
        settings_service.set('llm_auto_fallback', bool(auto_fallback))

    return {"status": "success"}


@router.get("/llm/tests/summary")
async def get_llm_test_summary():
    latest = llm_test_service.get_latest_results()
    timestamps = [item.get('created_at') for item in latest if item.get('created_at')]
    last_run = max(timestamps) if timestamps else None
    return {
        "providers": latest,
        "config_providers": llm_test_runner.get_configured_providers(),
        "active_providers": llm_test_runner.get_active_providers(),
        "last_run_at": last_run,
    }


@router.get("/llm/tests/history")
async def get_llm_test_history(provider: Optional[str] = None, limit: int = 25):
    normalized = _resolve_provider_name(provider)
    safe_limit = max(1, min(limit, 200))
    history = llm_test_service.get_history(provider=normalized, limit=safe_limit)
    return {
        "results": history,
        "provider": normalized,
        "limit": safe_limit,
    }


@router.post("/llm/tests/run")
async def run_llm_tests(payload: Optional[LLMRunTestRequest] = Body(None)):
    request = payload or LLMRunTestRequest()
    providers = None
    if request.providers:
        normalized = []
        for name in request.providers:
            resolved = _resolve_provider_name(name)
            if resolved:
                normalized.append(resolved)
        providers = normalized or None

    results = await llm_test_runner.run_tests(
        providers=providers,
        prompt=request.prompt,
    )

    return {
        "results": results,
        "requested_providers": providers or llm_test_runner.get_configured_providers() or llm_test_runner.get_active_providers(),
    }


@router.get("/telephony/tests/summary")
async def get_telephony_test_summary():
    latest = telephony_test_service.get_latest_results()
    timestamps = [item.get("created_at") for item in latest if item.get("created_at")]
    last_run = max(timestamps) if timestamps else None
    return {
        "tests": latest,
        "available_tests": telephony_test_runner.get_available_tests(),
        "voice_context": telephony_test_runner.voice_context(),
        "env_snapshot": telephony_test_runner.environment_snapshot(),
        "default_mode": telephony_test_runner.default_mode,
        "last_run_at": last_run,
    }


@router.get("/telephony/tests/history")
async def get_telephony_test_history(test_type: Optional[str] = None, limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    history = telephony_test_service.get_history(test_type=test_type, limit=safe_limit)
    return {
        "results": history,
        "test_type": test_type,
        "limit": safe_limit,
    }


@router.post("/telephony/tests/run")
async def run_telephony_tests(payload: Optional[TelephonyRunTestRequest] = Body(None)):
    request = payload or TelephonyRunTestRequest()
    tests = request.tests or None
    results = await telephony_test_runner.run_tests(tests=tests, mode=request.mode)
    return {
        "results": results,
        "requested_tests": tests or telephony_test_runner.get_available_tests(),
        "mode": request.mode,
    }


@router.get("/settings/rag")
async def get_rag_settings():
    default_threshold = config.get('rag', {}).get('confidence_threshold', 0.35)
    confidence_threshold = settings_service.get('confidence_threshold', default_threshold)
    return {
        "confidence_threshold": float(confidence_threshold),
        "default_confidence_threshold": default_threshold
    }


@router.post("/settings/rag")
async def update_rag_settings(payload: Dict[str, Any]):
    threshold = payload.get('confidence_threshold')
    if threshold is None:
        raise HTTPException(status_code=400, detail="confidence_threshold is required")
    try:
        threshold_value = float(threshold)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="confidence_threshold must be a number")

    if threshold_value < 0 or threshold_value > 2:
        raise HTTPException(status_code=400, detail="confidence_threshold must be between 0 and 2")

    settings_service.set('confidence_threshold', threshold_value)
    return {"status": "success", "confidence_threshold": threshold_value}

@router.get("/sentiment/alerts")
async def get_sentiment_alerts(hours: int = 24):
    """Get conversations that need escalation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get messages with escalation flags
        cursor.execute("""
            SELECT 
                cm.session_id,
                cm.content,
                cm.timestamp,
                cm.metadata,
                cs.client_id
            FROM conversation_messages cm
            JOIN conversation_sessions cs ON cm.session_id = cs.session_id
            WHERE cm.role = 'user'
                AND json_extract(cm.metadata, '$.needs_escalation') = 1
                AND datetime(cm.timestamp) > datetime('now', '-' || ? || ' hours')
            ORDER BY cm.timestamp DESC
        """, (hours,))
        
        alerts = []
        for row in cursor.fetchall():
            import json
            metadata = json.loads(row[3]) if row[3] else {}
            alerts.append({
                'session_id': row[0],
                'message': row[1],
                'timestamp': row[2],
                'client_id': row[4],
                'sentiment': metadata.get('sentiment'),
                'flags': metadata.get('flags', [])
            })
        
        return alerts
    finally:
        conn.close()

@router.post("/memory/cleanup")
async def cleanup_old_conversations(days: int = 30):
    """Clean up old conversation data"""
    deleted = conversation_memory.cleanup_old_sessions(days=days)
    return {"status": "success", "deleted_sessions": deleted}

# Rate Limiting Endpoints

@router.get("/rate-limits/usage/{api_key}")
async def get_api_key_usage(api_key: str, hours: int = 24):
    """Get usage statistics for an API key"""
    stats = rate_limiter.get_usage_stats(api_key, hours=hours)
    return stats

@router.get("/rate-limits/abuse-incidents")
async def get_abuse_incidents(hours: int = 24):
    """Get recent abuse incidents"""
    incidents = rate_limiter.get_abuse_incidents(hours=hours)
    return incidents

@router.get("/rate-limits/blocked")
async def get_blocked_entities():
    """Get currently blocked API keys and IPs"""
    blocked = rate_limiter.get_blocked_entities()
    return blocked

@router.post("/rate-limits/block")
async def block_entity(
    entity_type: str,  # "api_key" or "ip"
    entity_value: str,
    reason: str,
    duration_seconds: int = 3600
):
    """Manually block an API key or IP address"""
    if entity_type not in ["api_key", "ip"]:
        raise HTTPException(status_code=400, detail="entity_type must be 'api_key' or 'ip'")
    
    rate_limiter.block_entity(entity_type, entity_value, reason, duration_seconds)
    return {"status": "success", "message": f"Blocked {entity_type}: {entity_value}"}

@router.post("/rate-limits/unblock")
async def unblock_entity(entity_type: str, entity_value: str):
    """Manually unblock an API key or IP address"""
    if entity_type not in ["api_key", "ip"]:
        raise HTTPException(status_code=400, detail="entity_type must be 'api_key' or 'ip'")
    
    rate_limiter.unblock_entity(entity_type, entity_value)
    return {"status": "success", "message": f"Unblocked {entity_type}: {entity_value}"}

@router.post("/rate-limits/cleanup")
async def cleanup_rate_limit_records(days: int = 30):
    """Clean up old rate limiting records"""
    deleted = rate_limiter.cleanup_old_records(days=days)
    return {"status": "success", "deleted_records": deleted}

@router.get("/rate-limits/stats")
async def get_rate_limit_stats():
    """Get overall rate limiting statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total requests today
        cursor.execute("""
            SELECT COUNT(*) FROM api_key_usage
            WHERE date(timestamp) = date('now')
        """)
        requests_today = cursor.fetchone()[0]
        
        # Unique API keys
        cursor.execute("""
            SELECT COUNT(DISTINCT api_key) FROM api_key_usage
            WHERE date(timestamp) = date('now')
        """)
        unique_keys = cursor.fetchone()[0]
        
        # Total abuse incidents
        cursor.execute("""
            SELECT COUNT(*) FROM abuse_incidents
            WHERE date(timestamp) = date('now')
        """)
        abuse_count = cursor.fetchone()[0]
        
        # Currently blocked entities
        cursor.execute("""
            SELECT COUNT(*) FROM blocked_entities
            WHERE blocked_until > datetime('now')
        """)
        blocked_count = cursor.fetchone()[0]
        
        # Top API keys by usage
        cursor.execute("""
            SELECT api_key, COUNT(*) as request_count
            FROM api_key_usage
            WHERE date(timestamp) = date('now')
            GROUP BY api_key
            ORDER BY request_count DESC
            LIMIT 10
        """)
        top_keys = [{"api_key": row[0], "requests": row[1]} for row in cursor.fetchall()]
        
        return {
            "requests_today": requests_today,
            "unique_api_keys": unique_keys,
            "abuse_incidents_today": abuse_count,
            "currently_blocked": blocked_count,
            "top_api_keys": top_keys
        }
    finally:
        conn.close()

# ==================== Knowledge Gap Management ====================

@router.get("/knowledge-gaps")
async def get_knowledge_gaps(
    min_frequency: int = 3,
    days: int = 7
):
    """Get recurring questions that the system struggles to answer well."""
    gaps = gap_analyzer.get_knowledge_gaps(
        min_frequency=min_frequency,
        days=days
    )
    return {
        "knowledge_gaps": gaps,
        "total": len(gaps)
    }

@router.get("/faq-suggestions")
async def get_faq_suggestions(
    status: Optional[str] = None,
    limit: int = 50
):
    """Get FAQ improvement suggestions."""
    conn = gap_analyzer._get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM faq_suggestions"
    params = []
    
    if status:
        query += " WHERE status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    suggestions = []
    
    for row in cursor.fetchall():
        suggestions.append({
            "id": row[0],
            "question": row[1],
            "frequency": row[2],
            "avg_confidence": row[3],
            "sample_answer": row[4],
            "status": row[5],
            "created_at": row[6],
            "reviewed_at": row[7],
            "notes": row[8]
        })
    
    conn.close()
    return {
        "suggestions": suggestions,
        "total": len(suggestions)
    }

@router.post("/faq-suggestions/{suggestion_id}/approve")
async def approve_faq_suggestion(
    suggestion_id: int,
    notes: Optional[str] = None
):
    """Approve a FAQ suggestion."""
    conn = gap_analyzer._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE faq_suggestions
        SET status = 'approved',
            reviewed_at = ?,
            notes = ?
        WHERE id = ?
    """, (time.time(), notes, suggestion_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "FAQ suggestion approved"}

@router.post("/faq-suggestions/{suggestion_id}/reject")
async def reject_faq_suggestion(
    suggestion_id: int,
    notes: Optional[str] = None
):
    """Reject a FAQ suggestion."""
    conn = gap_analyzer._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE faq_suggestions
        SET status = 'rejected',
            reviewed_at = ?,
            notes = ?
        WHERE id = ?
    """, (time.time(), notes, suggestion_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "FAQ suggestion rejected"}

@router.get("/knowledge-improvement-report")
async def get_improvement_report(days: int = 30):
    """Get comprehensive knowledge base improvement report."""
    report = gap_analyzer.get_improvement_report(days=days)
    return report

# ==================== Translation & Multi-language ====================

@router.get("/translation/stats")
async def get_translation_stats():
    """Get translation usage statistics."""
    cache_stats = translation_service.get_cache_stats()
    return cache_stats

@router.get("/translation/languages")
async def get_language_usage(days: int = 30):
    """Get language usage statistics."""
    language_stats = translation_service.get_language_stats(days=days)
    return {
        "languages": language_stats,
        "total_languages": len(language_stats),
        "period_days": days
    }

@router.get("/translation/supported-languages")
async def get_supported_languages():
    """Get list of supported languages."""
    return {
        "supported_languages": translation_service.SUPPORTED_LANGUAGES,
        "total": len(translation_service.SUPPORTED_LANGUAGES)
    }

@router.post("/translation/cleanup-cache")
async def cleanup_translation_cache(days: int = 90):
    """Clean up old translation cache entries."""
    deleted = translation_service.cleanup_old_cache(days=days)
    return {
        "status": "success",
        "deleted_entries": deleted,
        "message": f"Cleaned up translation cache older than {days} days"
    }

@router.post("/translation/translate")
async def manual_translate(
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None
):
    """Manually translate text (for testing purposes)."""
    result = translation_service.translate(
        text=text,
        target_lang=target_lang,
        source_lang=source_lang
    )
    return result

# ==================== Analytics Dashboard ====================

@router.get("/analytics/dashboard")
async def get_analytics_dashboard(days: int = 7):
    """Get comprehensive dashboard overview with all key metrics."""
    overview = analytics_service.get_dashboard_overview(days=days)
    return overview

@router.get("/analytics/popular-questions")
async def get_popular_questions(limit: int = 20, days: int = 30):
    """Get most frequently asked questions."""
    questions = analytics_service.get_popular_questions(limit=limit, days=days)
    return {
        "questions": questions,
        "total": len(questions),
        "period_days": days
    }

@router.get("/analytics/traffic/hourly")
async def get_hourly_traffic(days: int = 7):
    """Get hourly traffic patterns."""
    traffic = analytics_service.get_hourly_traffic(days=days)
    return {
        "hourly_traffic": traffic,
        "period_days": days
    }

@router.get("/analytics/metrics/daily")
async def get_daily_metrics(days: int = 30):
    """Get daily metrics over time."""
    metrics = analytics_service.get_daily_metrics(days=days)
    return {
        "daily_metrics": metrics,
        "period_days": days
    }

@router.get("/analytics/engagement")
async def get_user_engagement(days: int = 30):
    """Get user engagement metrics."""
    engagement = analytics_service.get_user_engagement(days=days)
    return engagement

@router.get("/analytics/performance")
async def get_performance_stats(days: int = 7):
    """Get system performance statistics."""
    performance = analytics_service.get_performance_stats(days=days)
    return performance


@router.get("/analytics/fallbacks")
async def get_fallback_stats(days: int = 7, limit: int = 20):
    """Get LLM provider fallback performance."""
    summary = provider_metrics.get_summary(days=days)
    distribution = provider_metrics.get_fallback_distribution(days=days)
    failures = provider_metrics.get_recent_failures(limit=limit)
    return {
        "summary": summary,
        "distribution": distribution,
        "recent_failures": failures
    }

@router.get("/analytics/costs")
async def get_cost_analysis(days: int = 30):
    """Get cost analysis and estimates."""
    costs = analytics_service.get_cost_analysis(days=days)
    return costs

@router.get("/analytics/export")
async def export_analytics(days: int = 30):
    """Export comprehensive analytics report."""
    dashboard = analytics_service.get_dashboard_overview(days=days)
    popular_questions = analytics_service.get_popular_questions(limit=50, days=days)
    daily_metrics = analytics_service.get_daily_metrics(days=days)
    engagement = analytics_service.get_user_engagement(days=days)
    performance = analytics_service.get_performance_stats(days=days)
    costs = analytics_service.get_cost_analysis(days=days)
    
    return {
        "generated_at": time.time(),
        "period_days": days,
        "dashboard_overview": dashboard,
        "popular_questions": popular_questions,
        "daily_metrics": daily_metrics,
        "user_engagement": engagement,
        "performance_stats": performance,
        "cost_analysis": costs
    }
