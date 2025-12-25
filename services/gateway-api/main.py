from fastapi import FastAPI, HTTPException, Request, Security, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import sys
import json
import asyncio
import time
from typing import Dict, Set
from datetime import datetime

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config
from services.shared.rate_limiter import get_rate_limiter, get_ip_throttler

# Import admin routes from same directory
sys.path.insert(0, os.path.dirname(__file__))
from admin_routes import router as admin_router

app = FastAPI(title="Gateway API")

# Include Admin Router
app.include_router(admin_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
API_KEYS = set(config.get('security', {}).get('api_keys', []))
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize rate limiter
rate_limiter = get_rate_limiter()
ip_throttler = get_ip_throttler()

async def get_api_key(request: Request, api_key_header: str = Security(api_key_header)):
    """Validate API key and check rate limits"""
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check IP throttling first
    ip_allowed, ip_reason = ip_throttler.check_ip(client_ip)
    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ip_reason,
            headers={"Retry-After": "60"}
        )
    
    # Validate API key
    if not API_KEYS:
        # If no keys configured, use default (Dev mode)
        api_key_header = api_key_header or "dev-mode-key"
    else:
        if not api_key_header or api_key_header not in API_KEYS:
            # Log failed auth attempt
            if api_key_header:
                rate_limiter._log_abuse(api_key_header, client_ip, "invalid_api_key", "high")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key"
            )
    
    # Check rate limits
    allowed, reason, retry_after = rate_limiter.check_rate_limit(
        api_key=api_key_header,
        ip_address=client_ip,
        endpoint=str(request.url.path)
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
            headers={"Retry-After": str(retry_after)} if retry_after else {}
        )
    
    return api_key_header

# Service URLs (configurable via env or config in real app)
CHAT_SERVICE_URL = "http://localhost:8002"

async def _forward_chat_request(request: Request, api_key: str):
    start_time = time.time()
    status_code = 200
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CHAT_SERVICE_URL}/chat",
                json=body,
                timeout=30.0
            )
            result = response.json()
            
            # Record successful request
            response_time_ms = int((time.time() - start_time) * 1000)
            rate_limiter.record_request(
                api_key=api_key,
                ip_address=client_ip,
                endpoint="/api/v1/chat",
                status_code=status_code,
                response_time_ms=response_time_ms
            )
            
            return result
            
    except httpx.RequestError as exc:
        status_code = 503
        response_time_ms = int((time.time() - start_time) * 1000)
        rate_limiter.record_request(api_key, client_ip, "/api/v1/chat", status_code, response_time_ms)
        raise HTTPException(status_code=503, detail=f"Chat service unavailable: {exc}")
    except Exception as e:
        status_code = 500
        response_time_ms = int((time.time() - start_time) * 1000)
        rate_limiter.record_request(api_key, client_ip, "/api/v1/chat", status_code, response_time_ms)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat")
async def proxy_chat(request: Request, api_key: str = Depends(get_api_key)):
    return await _forward_chat_request(request, api_key)


@app.post("/chat")
async def legacy_chat_endpoint(request: Request, api_key: str = Depends(get_api_key)):
    """Backward-compatible endpoint used by the Control Center test panel."""
    return await _forward_chat_request(request, api_key)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gateway"}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "chat": set(),
            "admin": set()
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        print(f"✅ WebSocket connected to {channel} channel. Total: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            print(f"❌ WebSocket disconnected from {channel} channel. Remaining: {len(self.active_connections[channel])}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict, channel: str):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        dead_connections = set()
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.active_connections[channel].discard(connection)

manager = ConnectionManager()

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for chat widget - real-time typing indicators and updates"""
    await manager.connect(websocket, "chat")
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "typing":
                # Broadcast typing indicator to admin dashboards
                await manager.broadcast({
                    "type": "user_typing",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, "admin")
            
            elif message_data.get("type") == "message":
                # Process message and get response
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{CHAT_SERVICE_URL}/chat",
                            json={"message": message_data.get("content", "")},
                            timeout=30.0
                        )
                        result = response.json()
                        
                        # Send response back to this client
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "response",
                                "data": result,
                                "timestamp": datetime.utcnow().isoformat()
                            }),
                            websocket
                        )
                        
                        # Broadcast to admin dashboard
                        await manager.broadcast({
                            "type": "new_message",
                            "client_id": client_id,
                            "message": message_data.get("content", ""),
                            "response": result.get("answer", ""),
                            "confidence": result.get("confidence", 0),
                            "timestamp": datetime.utcnow().isoformat()
                        }, "admin")
                        
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": str(e)}),
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "chat")

@app.websocket("/ws/admin/{admin_id}")
async def websocket_admin_endpoint(websocket: WebSocket, admin_id: str):
    """WebSocket endpoint for admin console - real-time metrics and alerts"""
    await manager.connect(websocket, "admin")
    
    # Send initial stats
    async def send_periodic_stats():
        while True:
            try:
                # Get current stats from database
                stats = {
                    "type": "stats_update",
                    "data": {
                        "active_chats": len(manager.active_connections["chat"]),
                        "timestamp": datetime.utcnow().isoformat(),
                        "uptime_seconds": 0  # TODO: Track actual uptime
                    }
                }
                await manager.send_personal_message(json.dumps(stats), websocket)
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception:
                break
    
    # Start periodic stats task
    stats_task = asyncio.create_task(send_periodic_stats())
    
    try:
        while True:
            # Listen for admin commands
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "get_stats":
                # Send immediate stats update
                await manager.send_personal_message(
                    json.dumps({
                        "type": "stats_response",
                        "data": {"active_chats": len(manager.active_connections["chat"])}
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        stats_task.cancel()
        manager.disconnect(websocket, "admin")
