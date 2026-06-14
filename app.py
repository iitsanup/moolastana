from flask import Flask, render_template, request, jsonify
import json, os

app = Flask(__name__)

DATA_FILE = "data.json"

# Load data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"families": []}

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def home():
    return render_template("index.html")


# ✅ API: ADD FAMILY
@app.route("/add_family", methods=["POST"])
def add_family():

    data = load_data()

    new_family = request.get_json()

    data["families"].append(new_family)

    save_data(data)

    return jsonify({"status": "success"})


# ✅ API: GET FAMILY LIST
@app.route("/get_families")
def get_families():

    data = load_data()

    return jsonify(data["families"])

if __name__ == '__main__':
    app.run(debug=False)