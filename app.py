
import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from sqlalchemy import create_engine, text

app = Flask(__name__)

# ---- Database (Postgres via SQLAlchemy Core) ----
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required (e.g. from Render Postgres).")

# Render requires SSL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"sslmode": "require"} if "localhost" not in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                pair TEXT NOT NULL,
                rate DOUBLE PRECISION NOT NULL,
                ts_utc TIMESTAMPTZ NOT NULL
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pair_ts ON exchange_rates(pair, ts_utc);"))

def save_rate(pair: str, rate: float, ts_utc):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO exchange_rates(pair, rate, ts_utc) VALUES (:p, :r, :t)"),
                     {"p": pair, "r": rate, "t": ts_utc})

def load_history(pair: str, limit: int = 1000, start: str | None = None, end: str | None = None):
    q = "SELECT rate, ts_utc FROM exchange_rates WHERE pair = :p"
    params = {"p": pair}
    if start:
        q += " AND ts_utc >= :s"
        params["s"] = start
    if end:
        q += " AND ts_utc <= :e"
        params["e"] = end
    q += " ORDER BY ts_utc ASC LIMIT :lim"
    params["lim"] = limit
    with engine.begin() as conn:
        rows = conn.execute(text(q), params).all()
    return [{"rate": r[0], "ts_utc": r[1].isoformat()} for r in rows]

# ---- Views ----
@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == 'admin' and password == '1234':
        return redirect(url_for('index'))
    else:
        return 'Login failed. Try again.'

@app.route('/index')
def index():
    return render_template('index.html')

# ---- API ----
ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

def fetch_rate_from_provider(pair: str):
    base, quote = pair.split('/')
    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE&from_currency={base}&to_currency={quote}&apikey={ALPHA_API_KEY}"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data and isinstance(data, dict) and data.get("Note"):
        return {"error": "rate_limit", "message": data.get("Note")}
    if "Realtime Currency Exchange Rate" not in data:
        return {"error": "bad_response", "message": "Provider did not return a quote."}
    raw = data["Realtime Currency Exchange Rate"]
    try:
        rate = float(raw["5. Exchange Rate"])
    except Exception:
        return {"error": "bad_response", "message": "Malformed quote from provider."}
    return {"rate": rate}

@app.route("/api/rate")
def api_rate():
    pair = request.args.get("pair", "EUR/USD")
    resp = fetch_rate_from_provider(pair)
    if "error" in resp:
        return jsonify(resp), 429 if resp["error"] == "rate_limit" else 502
    ts = datetime.now(timezone.utc)
    try:
        save_rate(pair, resp["rate"], ts)
    except Exception as e:
        pass
    return jsonify({"pair": pair, "rate": resp["rate"], "ts_utc": ts.isoformat()})

@app.route("/api/history")
def api_history():
    pair = request.args.get("pair", "EUR/USD")
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        limit = int(request.args.get("limit", "1000"))
    except ValueError:
        limit = 1000
    items = load_history(pair, limit=limit, start=start, end=end)
    return jsonify({"pair": pair, "items": items, "start": start, "end": end})

@app.route("/api/delete_history", methods=["POST"])
def api_delete_history():
    js = request.get_json(silent=True) or {}
    pair = js.get("pair", "EUR/USD")
    start = js.get("start")
    end = js.get("end")
    q = "DELETE FROM exchange_rates WHERE pair = :p"
    params = {"p": pair}
    if start:
        q += " AND ts_utc >= :s"
        params["s"] = start
    if end:
        q += " AND ts_utc <= :e"
        params["e"] = end
    with engine.begin() as conn:
        res = conn.execute(text(q), params)
        deleted = res.rowcount or 0
    return jsonify({"pair": pair, "deleted": deleted})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
