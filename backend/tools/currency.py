import requests

def convert(amount: float, src: str, dst: str):
    src, dst = src.upper(), dst.upper()

    #using exchangerate-api.com v4(free, no API key needed)
    try:
        r = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{src}",
            timeout=10,
        ).json()

        if "rates" in r and dst in r["rates"]:
            rate = r["rates"][dst]
            result = amount * rate
            out = {
                "amount": amount,
                "from": src,
                "to": dst,
                "result": round(result, 2),
                "date": r.get("date"),
            }
        else:
            out = {
                "amount": amount,
                "from": src,
                "to": dst,
                "result": None,
                "date": None,
                "error": f"Unable to convert {src} to {dst}"
            }
    except Exception as e:
        out = {
            "amount": amount,
            "from": src,
            "to": dst,
            "result": None,
            "date": None,
            "error": str(e)
        }

    return out
