import requests
from .utils import normalize_city
from cache import cache_get, cache_set, key_for

def get_weather(city: str, state: str = None, country: str = None):
    city = normalize_city(city)

    # Build search query - try different combinations
    search_queries = []

    # Primary query with all provided info
    if state and country:
        search_queries.append(f"{city}, {state}, {country}")
    elif state:
        search_queries.append(f"{city}, {state}")
    elif country:
        search_queries.append(f"{city}, {country}")

    # Always add just the city as fallback
    search_queries.append(city)

    # Use full search query for cache key
    cache_params = {"city": city}
    if state:
        cache_params["state"] = state
    if country:
        cache_params["country"] = country

    k = key_for("weather", cache_params)
    if cached := cache_get(k):
        import json

        return json.loads(cached)

    # Try each search query until we find results
    geo = None

    for query in search_queries:
        # 1) geocode (Open-Meteo free geocoding)
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 5, "language": "en"},  # Get more results to filter
            timeout=10,
        ).json()

        if response.get("results"):
            # If we have state/country requirements, try to filter
            if country or state:
                for result in response["results"]:
                    # Check country match
                    if country and result.get("country"):
                        if country.lower() not in result["country"].lower():
                            continue
                    # Check state/admin1 match
                    if state and result.get("admin1"):
                        if state.lower() not in result["admin1"].lower():
                            continue
                    # Found a match
                    geo = {"results": [result]}
                    break

            # If no filtered match or no requirements, use first result
            if not geo:
                geo = {"results": [response["results"][0]]}
                break

    if not geo or not geo.get("results"):
        return {"city": f"{city}, {state or ''}, {country or ''}".strip(", "), "error": "City not found"}

    # Get the first result and extract location details
    result = geo["results"][0]
    lat = result["latitude"]
    lon = result["longitude"]

    # Build location display name
    location_name = result.get("name", city)
    if result.get("admin1"):  # State/region
        location_name += f", {result['admin1']}"
    if result.get("country"):
        location_name += f", {result['country']}"

    # 2) current weather (Open-Meteo)
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=10,
    ).json()
    out = {
        "city": location_name,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": w.get("current_weather", {}).get("temperature"),
        "windspeed_kmh": w.get("current_weather", {}).get("windspeed"),
        "conditions_code": w.get("current_weather", {}).get("weathercode"),
    }
    cache_set(k, out, ttl=300)
    return out
