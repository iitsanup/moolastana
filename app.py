from flask import Flask, render_template, request, jsonify
import requests
from functools import lru_cache
import time

app = Flask(__name__)

# ===================== SUPABASE CONFIG =====================
SUPABASE_URL = "https://bqkvwpfqdkhuotutpebv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxa3Z3cGZxZGtodW90dXRwZWJ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE0MDYyNTMsImV4cCI6MjA5Njk4MjI1M30.RvuJbBAGuS1z8kFfdbZUBbcFzo2w7oPp8Rx6TUV6vpA"

# ✅ Reuse single session for all requests (saves memory)
SESSION = requests.Session()
SESSION.headers.update({
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
})

# ✅ Simple in-memory cache to reduce repeated Supabase calls
_cache = {}
_cache_ttl = 60  # seconds

def cache_get(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < _cache_ttl:
            return val
    return None

def cache_set(key, val):
    _cache[key] = (val, time.time())

def cache_clear(key):
    _cache.pop(key, None)

def supabase_get(table, params=""):
    cache_key = f"{table}?{params}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    res = SESSION.get(url)
    data = res.json()
    cache_set(cache_key, data)
    return data

def supabase_post(table, data):
    cache_clear(table)
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = SESSION.post(url, json=data, headers={"Prefer": "return=representation"})
    return res.json()

def supabase_patch(table, match_col, match_val, data):
    cache_clear(table)
    url = f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}"
    res = SESSION.patch(url, json=data, headers={"Prefer": "return=representation"})
    return res.json()

def supabase_delete(table, match_col, match_val):
    cache_clear(table)
    url = f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}"
    res = SESSION.delete(url)
    return res.status_code

# ===================== MAIN PAGE =====================
@app.route("/")
def home():
    return render_template("index.html")

# ===================== FAMILY APIs =====================
@app.route("/get_families")
def get_families():
    return jsonify(supabase_get("families", "order=family_number.asc,id.asc"))

@app.route("/save_family", methods=["POST"])
def save_family():
    body = request.get_json()
    family_number = body.get("family_number")
    family_name = body.get("family_name")
    members = body.get("members", [])
    supabase_delete("families", "family_number", family_number)
    rows = [{"family_number": family_number, "family_name": family_name, "member_name": m.strip()}
            for m in members if m and m.strip()]
    if rows:
        supabase_post("families", rows)
    return jsonify({"status": "success"})

@app.route("/add_family", methods=["POST"])
def add_family():
    return jsonify({"status": "success", "data": supabase_post("families", request.get_json())})

# ===================== TRUSTEE APIs =====================
@app.route("/get_trustees")
def get_trustees():
    return jsonify(supabase_get("trustees", "order=member_number.asc"))

@app.route("/save_trustee", methods=["POST"])
def save_trustee():
    body = request.get_json()
    member_number = body.get("member_number")
    existing = supabase_get("trustees", f"member_number=eq.{member_number}")
    if existing:
        supabase_patch("trustees", "member_number", member_number, body)
    else:
        supabase_post("trustees", body)
    return jsonify({"status": "success"})

# ===================== CONTACT APIs =====================
@app.route("/get_contact")
def get_contact():
    return jsonify(supabase_get("contact_info", "order=id.asc"))

@app.route("/save_contact", methods=["POST"])
def save_contact():
    body = request.get_json()
    key = body.get("key")
    existing = supabase_get("contact_info", f"key=eq.{key}")
    if existing:
        supabase_patch("contact_info", "key", key, body)
    else:
        supabase_post("contact_info", body)
    return jsonify({"status": "success"})

# ===================== MEMBER DATABASE APIs =====================
@app.route("/get_member_db")
def get_member_db():
    return jsonify(supabase_get("member_database", "order=id.asc"))

@app.route("/save_member_db", methods=["POST"])
def save_member_db():
    return jsonify({"status": "success", "data": supabase_post("member_database", request.get_json())})

@app.route("/delete_member_db/<int:member_id>", methods=["DELETE"])
def delete_member_db(member_id):
    supabase_delete("member_database", "id", member_id)
    return jsonify({"status": "success"})

@app.route("/update_member_db/<int:member_id>", methods=["PATCH"])
def update_member_db(member_id):
    supabase_patch("member_database", "id", member_id, request.get_json())
    return jsonify({"status": "success"})

# ===================== PAYMENT APIs =====================
@app.route("/get_payments")
def get_payments():
    return jsonify(supabase_get("payments", "order=family_number.asc"))

@app.route("/save_payment", methods=["POST"])
def save_payment():
    body = request.get_json()
    member_name = body.get("member_name")
    year = body.get("year")
    existing = supabase_get("payments", f"member_name=eq.{member_name}&year=eq.{year}")
    if existing:
        supabase_patch("payments", "member_name", member_name, body)
    else:
        supabase_post("payments", body)
    return jsonify({"status": "success"})

@app.route("/get_payment_status")
def get_payment_status():
    member = request.args.get("member_name")
    year = request.args.get("year")
    return jsonify(supabase_get("payments", f"member_name=eq.{member}&year=eq.{year}"))

# ===================== SEVA BOOKING APIs =====================
@app.route("/book_seva", methods=["POST"])
def book_seva():
    return jsonify({"status": "success", "data": supabase_post("seva_bookings", request.get_json())})

@app.route("/get_seva_bookings")
def get_seva_bookings():
    return jsonify(supabase_get("seva_bookings", "order=booked_at.desc"))

# ===================== EVENTS APIs =====================
@app.route("/get_events")
def get_events():
    return jsonify(supabase_get("events", "order=id.desc"))

@app.route("/save_event", methods=["POST"])
def save_event():
    return jsonify({"status": "success", "data": supabase_post("events", request.get_json())})

@app.route("/delete_event/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    supabase_delete("events", "id", event_id)
    return jsonify({"status": "success"})

# ===================== CALENDAR EVENTS APIs =====================
@app.route("/get_calendar_events")
def get_calendar_events():
    year = request.args.get("year", "2026")
    return jsonify(supabase_get("calendar_events", f"year=eq.{year}&order=event_date.asc"))

@app.route("/save_calendar_event", methods=["POST"])
def save_calendar_event():
    return jsonify({"status": "success", "data": supabase_post("calendar_events", request.get_json())})

@app.route("/delete_calendar_event/<int:event_id>", methods=["DELETE"])
def delete_calendar_event(event_id):
    supabase_delete("calendar_events", "id", event_id)
    return jsonify({"status": "success"})

@app.route("/get_next_event")
def get_next_event():
    from datetime import date
    today = date.today().isoformat()
    return jsonify(supabase_get("calendar_events", f"event_date=gte.{today}&order=event_date.asc&limit=3"))

# ===================== RUN =====================
# ===================== RUN =====================
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
