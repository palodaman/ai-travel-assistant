import os

# Suppress gRPC warnings before importing any Google libraries
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

import json
import structlog
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from security import harden
from schemas import WeatherInput, ConvertInput
from tools.weather import get_weather
from tools.currency import convert
from gemini_agent import run_agent, run_agent_stream

log = structlog.get_logger()
app = Flask(__name__)

# Apply CORS first, then other security hardening
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
app = harden(app)


@app.get("/healthz")
def health():
    return {"ok": True}


# Plain tool endpoints (callable directly or by Gemini)
@app.post("/tools/weather")
def weather_ep():
    data = request.get_json(force=True, silent=True) or {}
    try:
        inp = WeatherInput(**data)
    except Exception as e:
        return {"error": str(e)}, 400
    out = get_weather(inp.city)
    return jsonify(out)


@app.post("/tools/convert")
def convert_ep():
    data = request.get_json(force=True, silent=True) or {}
    try:
        inp = ConvertInput(**data)
    except Exception as e:
        return {"error": str(e)}, 400
    out = convert(inp.amount, inp.from_, inp.to)
    return jsonify(out)


# Chat endpoint with streaming
@app.post("/chat")
def chat():
    body = request.get_json(force=True) or {}
    msg = body.get("message", "")
    history = body.get("history", [])
    if not msg:
        return {"error": "message is required"}, 400

    def generate():
        try:
            for chunk in run_agent_stream(msg, history):
                # Format as Server-Sent Event
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            log.error("stream_error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
