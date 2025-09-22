import structlog
from flask import Flask, request, jsonify
from security import harden
from schemas import WeatherInput, ConvertInput
from tools.weather import get_weather
from tools.currency import convert

log = structlog.get_logger()
app = harden(Flask(__name__))


@app.get("/healthz")
def health():
    return {"ok": True}


# Plain tool endpoints (callable directly)
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


if __name__ == "__main__":
    app.run(port=8000, debug=True)
