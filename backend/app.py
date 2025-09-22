import os 
import structlog
from flask import Flask, request, jsonify
from security import harden
from schemas import WeatherInput, ConvertInput
from tools.weather import get_weather
from tools.currency import convert
from gemini_agent import run_agent

log = structlog.get_logger()
app = harden(Flask(__name__))


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


# Chat endpoint for the frontend
@app.post("/chat")
def chat():
    body = request.get_json(force=True) or {}
    msg = body.get("message", "")
    history = body.get("history", [])
    if not msg:
        return {"error": "message is required"}, 400
    text, traces = run_agent(msg, history)
    log.info("chat_completion", message=msg, traces=traces)
    return jsonify({"text": text, "traces": traces})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
