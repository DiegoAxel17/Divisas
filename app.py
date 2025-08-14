import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

@app.route("/index")
def index():
    # si no tienes plantilla aún, devuelve algo simple
    try:
        return render_template("index.html")
    except Exception:
        return "Index OK (sin template)."

@app.route("/healthz")
def healthz():
    return "healthy"

# --- endpoints de tu app (versión que NO rompe si falta API key/DB) ---
@app.route("/api/history")
def history():
    # Devuelve vacío para que el front no truene; luego enchufamos DB
    pair = request.args.get("pair", "EUR/USD")
    return jsonify({"pair": pair, "items": []})

@app.route("/api/rate")
def rate():
    pair = request.args.get("pair", "EUR/USD")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        # No rompemos: devolvemos 501 con mensaje claro
        return jsonify({"error": "no_api_key", "message": "Falta ALPHA_VANTAGE_API_KEY en Render; la app igual arranca."}), 501
    # si luego la pones, aquí puedes llamar al provider real
    # (por ahora respondo fijo para probar el front)
    return jsonify({"pair": pair, "rate": 1.2345, "ts_utc": datetime.now(timezone.utc).isoformat()})
