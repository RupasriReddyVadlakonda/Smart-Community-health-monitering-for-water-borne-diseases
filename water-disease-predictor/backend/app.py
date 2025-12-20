import os
import json
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
from twilio.rest import Client
from dotenv import load_dotenv

# ------------------- Flask Setup -------------------
app = Flask(__name__)
CORS(app)

# ------------------- Paths -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "water_data.csv")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
MODEL_FILE = os.path.join(BASE_DIR, "model.pkl")
MODEL_META_FILE = os.path.join(BASE_DIR, "model_meta.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ------------------- Load Environment Variables -------------------
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
MY_MOBILE_NUMBER = os.getenv("MY_MOBILE_NUMBER")

# ------------------- User Management -------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ------------------- ML Model -------------------
def train_model():
    if not os.path.exists(CSV_FILE):
        return None
    df = pd.read_csv(CSV_FILE)
    X = df[["temperature","rainfall","turbidity","contamination"]].values
    y = df["disease_risk"].values
    model = LinearRegression()
    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)
    meta = {"trained_at": datetime.now().isoformat(), "samples": len(df)}
    with open(MODEL_META_FILE, "w") as f:
        json.dump(meta, f)
    print("Model trained successfully.")
    return model

def load_model():
    if os.path.exists(MODEL_FILE):
        return joblib.load(MODEL_FILE)
    return train_model()

# ------------------- Twilio SMS -------------------
def send_sms_alert(risk_score):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f"⚠️ HIGH RISK ALERT! Water disease risk score: {risk_score:.2f}",
            from_=TWILIO_PHONE_NUMBER,
            to=MY_MOBILE_NUMBER
        )
        print(f"SMS sent successfully. SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

# ------------------- API Routes -------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "ok", "service": "Water Disease Predictor"}), 200

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    if not username or not password:
        return jsonify({"error":"Username & password required"}),400
    users = load_users()
    if username in users:
        return jsonify({"error":"User already exists"}),400
    users[username] = {"password_hash": hash_password(password), "created_at": datetime.now().isoformat()}
    save_users(users)
    return jsonify({"message":"Signup successful"}),201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    users = load_users()
    if username not in users or hash_password(password) != users[username]["password_hash"]:
        return jsonify({"error":"Invalid credentials"}),401
    return jsonify({"message":"Login successful", "username":username}),200

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    try:
        temp = float(data.get("temperature",25))
        rain = float(data.get("rainfall",50))
        turb = float(data.get("turbidity",5))
        cont = float(data.get("contamination",100))
    except:
        return jsonify({"error":"Invalid input"}),400

    model = load_model()
    X = np.array([[temp, rain, turb, cont]])
    prediction = float(model.predict(X)[0])
    prediction = max(0.0, min(1.0, prediction))

    alert_status = "NORMAL"
    risk_level = "LOW"
    if prediction > 0.7:
        risk_level = "HIGH"
        alert_status = "HIGH RISK"
        send_sms_alert(prediction)
    elif prediction > 0.4:
        risk_level = "MODERATE"

    return jsonify({
        "prediction": round(prediction,3),
        "risk_level": risk_level,
        "alert": alert_status,
        "inputs":{"temperature":temp,"rainfall":rain,"turbidity":turb,"contamination":cont}
    }),200

@app.route("/train", methods=["GET"])
def train_route():
    model = train_model()
    if not model:
        return jsonify({"error":"Training failed"}),500
    meta = {}
    if os.path.exists(MODEL_META_FILE):
        with open(MODEL_META_FILE,"r") as f:
            meta = json.load(f)
    return jsonify({"message":"Model trained successfully","meta":meta}),200

# ------------------- Error Handling -------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error":"Endpoint not found"}),404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error":"Internal server error"}),500

# ------------------- Run Server -------------------
if __name__ == "__main__":
    ensure_model_exists = load_model()
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
