# backend/app.py (minimal)
from flask import Flask

app = Flask(__name__)

@app.get("/healthz")
def health():
    return {"ok": True}

if __name__ == "__main__":
    app.run(port=8000, debug=True)
