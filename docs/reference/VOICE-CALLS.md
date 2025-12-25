# ☎️ Voice / Calling Setup Guide

This guide explains how to wire up the Voice Orchestrator (`services/voice-orchestrator`) so you can answer inbound Twilio calls with the IVR + AI assistant that ships with the Copilot platform.

## 1. Prerequisites

1. **Twilio account + phone number** with voice capability.
2. **Public HTTPS URL** that Twilio can reach (e.g., `ngrok http 8004`).
3. **Configured environment variables** in `.env` (or `.env.local`):
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
   - `BASE_URL` → must match your public tunnel domain (e.g., the ngrok URL)
   - `GROQ_API_KEY` / `GEMINI_KEY` / `OPENAI_API_KEY` (for AI fallback inside the IVR)
4. Run `./start.ps1` (or `launch.ps1`) so the **Voice Orchestrator** is listening on `http://localhost:8004`.

## 2. Start the services + tunnel

```powershell
# Start the platform (spawns ingestion, chat, gateway, voice, email worker)
.\launch.ps1

# In a second terminal expose the voice service
ngrok http 8004
```

Copy the public HTTPS URL reported by ngrok (e.g., `https://purple-lion.ngrok-free.app`).

## 3. Configure the Twilio webhook

1. In the Twilio Console, open **Phone Numbers → Manage → Active numbers → <your number>**.
2. Under **Voice & Fax** set:
   - **Config**: `Webhook`
   - **URL**: `https://<your-ngrok-domain>/voice/webhook`
   - **Method**: `HTTP POST`
3. Save the changes. Twilio will now POST every voice event to the FastAPI endpoint in `voice-orchestrator/main.py`.

> ⚠️ Twilio only accepts HTTPS. If you deploy outside ngrok, make sure the `BASE_URL` env var references a real TLS endpoint that proxies to port `8004`.

## 4. How the IVR works

- Incoming calls hit `/voice/webhook`, which builds TwiML using [`twilio.twiml.voice_response`](https://www.twilio.com/docs/voice/twiml).
- The menu + prompts live in `services/voice-orchestrator/ivr_flow.json`:
  - `1` → order status prompt (static)
  - `2` → returns prompt (static)
  - `3` → AI assistant path (speech input)
- When the caller speaks (option `3`), the service currently calls the Chat Orchestrator via a stub (`ai_answer = ...`). You can replace that with a real HTTP call to `http://localhost:8000/chat` if you want live answers.
- Metrics are tracked in-memory (`VoiceMetrics`) and surfaced via `GET /stats` for the Control Center.

## 5. Testing locally (without Twilio)

You can emulate Twilio by posting `application/x-www-form-urlencoded` payloads:

```powershell
curl -X POST http://localhost:8004/voice/webhook ^
     -H "Content-Type: application/x-www-form-urlencoded" ^
     -d "CallSid=TEST123&Digits=1"
```

- Sending `Digits=1` or `Digits=2` walks the IVR menu.
- Sending `SpeechResult=How do I track my order?` imitates the AI assistant branch.

## 6. Outbound / Click-to-Call

Outbound calls are not automated yet, but you can use the Twilio REST API with the same webhook:

```powershell
curl -X POST https://api.twilio.com/2010-04-01/Accounts/$env:TWILIO_ACCOUNT_SID/Calls.json ^
     -u "$env:TWILIO_ACCOUNT_SID:$env:TWILIO_AUTH_TOKEN" ^
     -d "To=<destination-number>" ^
     -d "From=$env:TWILIO_PHONE_NUMBER" ^
     -d "Url=https://<your-ngrok-domain>/voice/webhook"
```

Twilio will dial the customer and immediately hand the call off to your IVR.

## 7. Telephony Tester & Health Checks (NEW)

Use the Control Center sidebar (**Telephony Tests**) to verify every voice prerequisite before dialing real customers:

1. Open the Control Center and authenticate with your admin token.
2. Click **Telephony Tests** to load the summary card, which surfaces Twilio credentials, webhook reachability, ngrok/Base URL, and Voice Orchestrator uptime in one place.
3. Choose **Dry Run** to ping the webhook + Twilio REST API without placing a live call. This validates credentials, environment variables, and voice stats safely.
4. Switch to **Live Mode** only after dry runs pass. The tester will request confirmation before dialing the configured Twilio number.
5. Review the **History** table (backed by `telephony_test_logs`) to confirm when the last health check ran, latency, call SID, and any error details.

### API access
Prefer the Control Center UI, but you can trigger the same diagnostics over HTTP (remember the `X-Admin-Token` header if configured):

```powershell
curl -X POST http://localhost:8000/admin/telephony/tests/run ^
       -H "Content-Type: application/json" ^
       -H "X-Admin-Token: <ADMIN_TOKEN>" ^
       -d '{
                "tests": ["credentials", "webhook", "outbound"],
                "mode": "dry"
             }'
```

- `mode` accepts `dry` (no live call) or `live` (places an outbound call).
- Use `GET /admin/telephony/tests/summary` to fetch the same panel data the Control Center renders, and `GET /admin/telephony/tests/history?limit=25` for recent runs.

## 8. Troubleshooting checklist

| Symptom | What to check |
| --- | --- |
| Twilio 502/11200 errors | Ensure ngrok tunnel is alive and `BASE_URL` matches the public URL. |
| IVR loops forever | Verify your webhook is `POST` and the action URLs (`/voice/webhook`) are reachable. |
| "AI" branch always static | Replace the placeholder `ai_answer = ...` with a real call to Gateway `/chat` once Groq/Gemini keys are configured. |
| Control Center voice stats stay zero | Confirm the voice service is running (port 8004) and Twilio is hitting it; stats increment only for live calls or Telephony Tester probes. |
| Telephony Tests fail in dry mode | Check that `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `BASE_URL` are loaded in the gateway/voice services; dry runs read env vars only. |
| Telephony Tests fail in live mode | Ensure your Twilio number is verified for the destination, and that ngrok/Base URL is publicly reachable. |

Once Twilio + ngrok are wired up, you can call the Twilio number from any phone and walk through the same flow the Control Center dashboard visualizes.
