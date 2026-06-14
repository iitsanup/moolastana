from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# ===================== SUPABASE CONFIG =====================
SUPABASE_URL = "https://bqkvwpfqdkhuotutpebv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxa3Z3cGZxZGtodW90dXRwZWJ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE0MDYyNTMsImV4cCI6MjA5Njk4MjI1M30.RvuJbBAGuS1z8kFfdbZUBbcFzo2w7oPp8Rx6TUV6vpA"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def supabase_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    res = requests.get(url, headers=HEADERS)
    return res.json()

def supabase_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, json=data, headers={**HEADERS, "Prefer": "return=representation"})
    return res.json()

def supabase_patch(table, match_col, match_val, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}"
    res = requests.patch(url, json=data, headers={**HEADERS, "Prefer": "return=representation"})
    return res.json()

def supabase_delete(table, match_col, match_val):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}"
    res = requests.delete(url, headers=HEADERS)
    return res.status_code

# ===================== MAIN PAGE =====================
@app.route("/")
def home():
    return render_template("index.html")

# ===================== FAMILY APIs =====================

@app.route("/get_families")
def get_families():
    data = supabase_get("families", "order=family_number.asc,id.asc")
    return jsonify(data)

@app.route("/save_family", methods=["POST"])
def save_family():
    body = request.get_json()
    family_number = body.get("family_number")
    family_name = body.get("family_name")
    members = body.get("members", [])

    # Delete existing members for this family
    supabase_delete("families", "family_number", family_number)

    # Insert new members
    rows = []
    for member in members:
        if member and member.strip():
            rows.append({
                "family_number": family_number,
                "family_name": family_name,
                "member_name": member.strip()
            })

    if rows:
        supabase_post("families", rows)

    return jsonify({"status": "success"})

@app.route("/add_family", methods=["POST"])
def add_family():
    body = request.get_json()
    result = supabase_post("families", body)
    return jsonify({"status": "success", "data": result})

# ===================== TRUSTEE APIs =====================

@app.route("/get_trustees")
def get_trustees():
    data = supabase_get("trustees", "order=member_number.asc")
    return jsonify(data)

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
    data = supabase_get("contact_info", "order=id.asc")
    return jsonify(data)

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
    data = supabase_get("member_database", "order=id.asc")
    return jsonify(data)

@app.route("/save_member_db", methods=["POST"])
def save_member_db():
    body = request.get_json()
    result = supabase_post("member_database", body)
    return jsonify({"status": "success", "data": result})

@app.route("/delete_member_db/<int:member_id>", methods=["DELETE"])
def delete_member_db(member_id):
    supabase_delete("member_database", "id", member_id)
    return jsonify({"status": "success"})

# ===================== PAYMENT APIs =====================

@app.route("/get_payments")
def get_payments():
    data = supabase_get("payments", "order=family_number.asc")
    return jsonify(data)

@app.route("/save_payment", methods=["POST"])
def save_payment():
    body = request.get_json()
    member_name = body.get("member_name")
    year = body.get("year")

    # Check if exists
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
    data = supabase_get("payments", f"member_name=eq.{member}&year=eq.{year}")
    return jsonify(data)

# ===================== SEVA BOOKING APIs =====================

@app.route("/book_seva", methods=["POST"])
def book_seva():
    body = request.get_json()
    result = supabase_post("seva_bookings", body)
    return jsonify({"status": "success", "data": result})

@app.route("/get_seva_bookings")
def get_seva_bookings():
    data = supabase_get("seva_bookings", "order=booked_at.desc")
    return jsonify(data)

# ===================== EVENTS APIs =====================

@app.route("/get_events")
def get_events():
    data = supabase_get("events", "order=id.desc")
    return jsonify(data)

@app.route("/save_event", methods=["POST"])
def save_event():
    body = request.get_json()
    result = supabase_post("events", body)
    return jsonify({"status": "success", "data": result})

@app.route("/delete_event/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    supabase_delete("events", "id", event_id)
    return jsonify({"status": "success"})

# ===================== RUN =====================
if __name__ == '__main__':
    app.run(debug=False)
