import requests
from .utils import normalize_city
from cache import cache_get, cache_set, key_for

def get_weather(city: str):
    city = normalize_city(city)
    k = key_for("weather", {"city": city})
    if cached := cache_get(k):
        import json

        return json.loads(cached)

    # 1) geocode (Open-Meteo free geocoding)
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en"},
        timeout=10,
    ).json()
    if not geo.get("results"):
        return {"city": city, "error": "City not found"}
    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    # 2) current weather (Open-Meteo)
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=10,
    ).json()
    out = {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": w.get("current_weather", {}).get("temperature"),
        "windspeed_kmh": w.get("current_weather", {}).get("windspeed"),
        "conditions_code": w.get("current_weather", {}).get("weathercode"),
    }
    cache_set(k, out, ttl=300)
    return out
