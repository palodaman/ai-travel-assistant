import requests
from cache import cache_get, cache_set, key_for


def convert(amount: float, src: str, dst: str):
    src, dst = src.upper(), dst.upper()
    k = key_for("fx", {"amount": amount, "src": src, "dst": dst})
    if cached := cache_get(k):
        import json

        return json.loads(cached)

    r = requests.get(
        "https://api.exchangerate.host/convert",
        params={"from": src, "to": dst, "amount": amount},
        timeout=10,
    ).json()
    out = {
        "amount": amount,
        "from": src,
        "to": dst,
        "result": r.get("result"),
        "date": r.get("date"),
    }
    cache_set(k, out, ttl=300)
    return out
