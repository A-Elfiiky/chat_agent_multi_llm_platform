import sys
import os
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
import time
from threading import Lock
from twilio.twiml.voice_response import VoiceResponse, Gather

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from voice_services import VoiceServiceFactory

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config

app = FastAPI(title="Voice Orchestrator")
config = load_config()

asr_service = VoiceServiceFactory.get_asr(config['voice']['asr']['provider'])
tts_service = VoiceServiceFactory.get_tts(config['voice']['tts']['provider'])


class VoiceMetrics:
    """In-memory counters that feed the Control Center voice dashboard."""

    def __init__(self):
        self._lock = Lock()
        self._metrics = {
            "total_calls": 0,
            "active_calls": 0,
            "avg_duration": 0,
            "success_rate": 1.0,
        }
        self._call_started_at = {}

    def start_call(self, call_sid: str):
        with self._lock:
            self._metrics["total_calls"] += 1
            self._metrics["active_calls"] += 1
            self._call_started_at[call_sid] = time.time()

    def end_call(self, call_sid: str, successful: bool = True):
        with self._lock:
            if call_sid in self._call_started_at:
                duration = time.time() - self._call_started_at.pop(call_sid)
                prev_avg = self._metrics["avg_duration"]
                total = max(self._metrics["total_calls"], 1)
                self._metrics["avg_duration"] = ((prev_avg * (total - 1)) + duration) / total
            self._metrics["active_calls"] = max(self._metrics["active_calls"] - 1, 0)
            if not successful:
                # simple rolling success metric
                self._metrics["success_rate"] = max(self._metrics["success_rate"] - 0.05, 0.0)

    def snapshot(self):
        with self._lock:
            return dict(self._metrics)


voice_metrics = VoiceMetrics()

# Load IVR Flow
with open(os.path.join(os.path.dirname(__file__), 'ivr_flow.json'), 'r') as f:
    IVR_FLOW = {node['id']: node for node in json.load(f)}

@app.post("/voice/webhook")
async def voice_webhook(request: Request):
    """
    Webhook for Twilio.
    Receives form data from Twilio (CallSid, SpeechResult, Digits, etc.)
    Returns TwiML XML.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    speech_result = form_data.get("SpeechResult")
    digits = form_data.get("Digits")
    
    print(f"Call {call_sid}: Speech='{speech_result}', Digits='{digits}'")
    
    resp = VoiceResponse()
    
    # Simple State Machine Logic
    # In a real app, we'd fetch the current state from a DB using CallSid
    # Here we infer state from input
    
    call_sid = call_sid or "unknown"

    if call_sid not in voice_metrics._call_started_at:
        voice_metrics.start_call(call_sid)

    if speech_result:
        # We are in the AI Assistant flow
        print(f"Processing AI Query: {speech_result}")
        # Call Chat Orchestrator (Mock for now)
        ai_answer = f"I found this info for '{speech_result}': Returns are free within 30 days."
        
        resp.say(ai_answer)
        resp.say("Is there anything else I can help with?")
        gather = Gather(input='speech', action='/voice/webhook', timeout=3)
        resp.append(gather)
        
    elif digits:
        # Menu Selection
        if digits == '1':
            node = IVR_FLOW['flow_order_status']
            resp.say(node['prompt'])
            resp.hangup()
            voice_metrics.end_call(call_sid)
        elif digits == '2':
            node = IVR_FLOW['flow_returns']
            resp.say(node['prompt'])
            resp.hangup()
            voice_metrics.end_call(call_sid)
        elif digits == '3':
            node = IVR_FLOW['flow_ai_assistant']
            gather = Gather(input='speech', action='/voice/webhook', timeout=5)
            gather.say(node['prompt'])
            resp.append(gather)
        else:
            resp.say("Invalid option.")
            resp.redirect('/voice/webhook') # Loop back to start
            
    else:
        # Initial Call - Start Main Menu
        node = IVR_FLOW['flow_main_menu']
        gather = Gather(num_digits=1, action='/voice/webhook')
        gather.say(node['prompt'])
        resp.append(gather)
        resp.redirect('/voice/webhook') # Loop if no input

    return Response(content=str(resp), media_type="application/xml")

@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/stats")
async def stats():
    return voice_metrics.snapshot()
