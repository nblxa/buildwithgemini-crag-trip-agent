"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Why A2A: agents-cli 1.1.0 (GA) deploys ADK agents to Agent Runtime as A2A agents
and no longer registers the reasoning-engine operation schema the old
`agent_engines.get(...).stream_query()` path relied on (operation_schemas() comes
back empty). The container serves the A2A protocol over the Agent Engine HTTP
passthrough, so this proxy fetches the agent's card and sends messages with the
a2a-sdk client (the same path `agents-cli run --mode a2a` uses). This works for
both A2A and plain ADK 1.1.0 deployments (the container serves A2A either way).

Run:
  pip install -r requirements.txt
  export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
  export AGENT_DIRECTORY="app"   # your agent's app directory (agents-cli-manifest.yaml)
  python main.py                 # -> http://localhost:8080
"""

import os
import uuid
import httpx
import google.auth
import google.auth.transport.requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/697814514458/locations/us-east1/reasoningEngines/1870064769684209664"
)
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP passthrough.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}


def _extract_parts(parts: list) -> list[dict]:
    """Turn A2A response parts into structured parts for the chat UI."""
    out: list[dict] = []
    for p in parts:
        if isinstance(p, dict):
            if p.get("kind") == "text" and p.get("text"):
                out.append({"kind": "text", "text": p["text"]})
            elif "data" in p:
                data_obj = p["data"]
                if isinstance(data_obj, dict):
                    meta = data_obj.get("metadata") or p.get("metadata") or {}
                    mime = meta.get("mimeType") if isinstance(meta, dict) else None
                    inner_data = data_obj.get("data", data_obj)
                    if mime == _A2UI_MIME or "beginRendering" in inner_data or "surfaceUpdate" in inner_data or "dataModelUpdate" in inner_data:
                        out.append({"kind": "a2ui", "data": inner_data})
                    elif "text" in data_obj:
                        out.append({"kind": "text", "text": data_obj["text"]})
            elif p.get("kind") == "file" and "file" in p:
                uri = p["file"].get("uri")
                if uri:
                    out.append({"kind": "text", "text": uri})
        else:
            text = getattr(p, "text", None)
            if text:
                out.append({"kind": "text", "text": text})
            data = getattr(p, "data", None)
            if data is not None:
                out.append({"kind": "a2ui", "data": data})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    msg_payload = {
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": [{"text": message}],
    }
    if _contexts.get(user_id):
        msg_payload["contextId"] = _contexts[user_id]

    rpc_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": msg_payload
        }
    }

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        resp = await client.post(A2A_BASE, json=rpc_body)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return JSONResponse({
                "parts": [{"kind": "text", "text": f"Agent Error: {data['error'].get('message', data['error'])}"}]
            })

        result = data.get("result", {})
        if "contextId" in result:
            _contexts[user_id] = result["contextId"]

        for artifact in result.get("artifacts") or []:
            parts.extend(_extract_parts(artifact.get("parts") or []))

        if not parts:
            for item in result.get("history") or []:
                if item.get("role") == "agent":
                    parts.extend(_extract_parts(item.get("parts") or []))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

