from flask import jsonify, request
from datetime import datetime, timezone
import os

@app.route("/api/history")
def api_history():
    pair = request.args.get("pair", "EUR/USD")
    # De momento vacío (hasta conectar DB) para que el front no falle:
    return jsonify({"pair": pair, "items": []})

@app.route("/api/rate")
def api_rate():
    pair = request.args.get("pair", "EUR/USD")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        # Respuesta de prueba para que la app funcione aunque no haya key:
        return jsonify({"pair": pair, "rate": 1.2345,
                        "ts_utc": datetime.now(timezone.utc).isoformat()})
    # (Cuando pongas tu key: aquí llamas al proveedor real y guardas en DB)

