import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- Páginas ----------
@app.route("/")
def home():
    # Render usa esta ruta para ver si está vivo
    return "OK"

@app.route("/index")
def index():
    # Si ya tienes templates/index.html, lo renderiza
    try:
        return render_template("index.html")
    except Exception:
        # Si no tienes el template, al menos no revienta
        return "Index OK (sin template)."

@app.route("/healthz")
def healthz():
    return "healthy"

# ---------- API: divisas (versión que NO exige DB ni API key) ----------
@app.route("/api/history")
def api_history():
    # Devuelve vacío por ahora; cuando conectes DB, aquí lees el historial real
    pair = request.args.get("pair", "EUR/USD")
    return jsonify({"pair": pair, "items": []})

@app.route("/api/rate")
def api_rate():
    """Si no define ALPHA_VANTAGE_API_KEY, devuelve un valor de prueba
    para que la gráfica no se rompa."""
    pair = request.args.get("pair", "EUR/USD")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    if not api_key:
        # Valor dummy para probar sin API key
        return jsonify({
            "pair": pair,
            "rate": 1.2345,
            "ts_utc": datetime.now(timezone.utc).isoformat()
        })

    # Si pones tu API key, puedes activar el proveedor real aquí:
    base, quote = pair.split("/")
    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE&from_currency={base}&to_currency={quote}&apikey={api_key}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        raw = data.get("Realtime Currency Exchange Rate", {})
        rate = float(raw.get("5. Exchange Rate", "0"))
        return jsonify({
            "pair": pair,
            "rate": rate,
            "ts_utc": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        # Si falla el proveedor, al menos no se rompe el front
        return jsonify({"error": "provider_error", "message": str(e)}), 502

# ---------- API: noticias (server-side para evitar CORS) ----------
NEWS_API_KEY = os.getenv("NEWSAPI_KEY", "")  # ← en Render: Settings → Environment

@app.route("/api/news")
def api_news():
    """Pide noticias en el servidor y las devuelve al front (evita CORS del plan gratis)."""
    if not NEWS_API_KEY:
        return jsonify({"status": "error", "message": "Falta NEWSAPI_KEY en el servidor."}), 501
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "language": "es",
            "pageSize": 20,
            "q": "noticias",  # puedes cambiar palabra clave (economia, finanzas, etc.)
            "apiKey": NEWS_API_KEY,
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return jsonify({"status": "ok", "articles": data.get("articles", [])})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


# ---------- Arranque local ----------
if __name__ == "__main__":
    # Esto no se usa en Render (Render corre con gunicorn), pero sirve en local.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

        # No rompemos: devolvemos 501 con mensaje claro
        return jsonify({"error": "no_api_key", "message": "Falta ALPHA_VANTAGE_API_KEY en Render; la app igual arranca."}), 501
    # si luego la pones, aquí puedes llamar al provider real
    # (por ahora respondo fijo para probar el front)
    return jsonify({"pair": pair, "rate": 1.2345, "ts_utc": datetime.now(timezone.utc).isoformat()})
