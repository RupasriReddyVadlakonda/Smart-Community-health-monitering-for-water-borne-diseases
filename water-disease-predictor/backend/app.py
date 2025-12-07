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
import traceback

app = Flask(__name__)
CORS(app)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
USERS_FILE = os.path.join(BASE_DIR, "users.json")
CSV_FILE = os.path.join(PROJECT_ROOT, "data", "water_data.csv")
MODEL_FILE = os.path.join(BASE_DIR, "model.pkl")
MODEL_META_FILE = os.path.join(BASE_DIR, "model_meta.json")

# Ensure directories exist
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

def load_users():
    """Load users from JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Save users to JSON file."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def hash_password(pw):
    """Hash password using SHA256."""
    return hashlib.sha256(pw.encode()).hexdigest()

def create_dummy_model():
    """Create a simple model using synthetic data."""
    print("Creating dummy model with synthetic data...")
    X = np.array([
        [20, 50, 5, 100],
        [25, 100, 8, 200],
        [15, 30, 3, 50],
        [30, 150, 10, 300],
        [22, 60, 6, 120],
        [28, 120, 9, 250],
        [18, 40, 4, 80],
        [26, 110, 7, 180],
        [24, 80, 5.5, 140],
        [32, 160, 11, 320]
    ], dtype=float)
    
    y = np.array([0.2, 0.6, 0.1, 0.9, 0.3, 0.8, 0.15, 0.65, 0.4, 0.95], dtype=float)
    
    try:
        model = LinearRegression()
        model.fit(X, y)
        joblib.dump(model, MODEL_FILE)
        
        with open(MODEL_META_FILE, "w", encoding="utf-8") as f:
            json.dump({"trained_at": datetime.now().isoformat(), "samples": 10, "source": "synthetic"}, f)
        
        print(f"Dummy model saved to {MODEL_FILE}")
        return model
    except Exception as e:
        print(f"Error creating dummy model: {e}")
        return None

def train_model_from_csv():
    """Train model from CSV file."""
    if not os.path.exists(CSV_FILE):
        print(f"CSV file not found at {CSV_FILE}")
        return None
    
    try:
        df = pd.read_csv(CSV_FILE)
        required_cols = ["temperature", "rainfall", "turbidity", "contamination", "disease_risk"]
        
        # Check if all required columns exist
        if not all(col in df.columns for col in required_cols):
            print(f"CSV is missing required columns. Found: {df.columns.tolist()}")
            return None
        
        X = df[["temperature", "rainfall", "turbidity", "contamination"]].values
        y = df["disease_risk"].values
        
        model = LinearRegression()
        model.fit(X, y)
        joblib.dump(model, MODEL_FILE)
        
        with open(MODEL_META_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "trained_at": datetime.now().isoformat(),
                "samples": len(df),
                "source": "csv"
            }, f)
        
        print(f"Model trained on {len(df)} samples from CSV")
        return model
    except Exception as e:
        print(f"Error training from CSV: {e}")
        traceback.print_exc()
        return None

def load_model():
    """Load trained model or create default."""
    if os.path.exists(MODEL_FILE):
        try:
            model = joblib.load(MODEL_FILE)
            print("Model loaded from disk")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return None

def ensure_model_exists():
    """Ensure a model exists, train if needed."""
    model = load_model()
    if model is not None:
        return model
    
    # Try to train from CSV first
    model = train_model_from_csv()
    if model is not None:
        return model
    
    # Fallback to dummy model
    model = create_dummy_model()
    return model

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "ok",
        "service": "Water Disease Predictor",
        "version": "1.0.0"
    }), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route("/signup", methods=["POST"])
def signup():
    """Create a new user account."""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        users = load_users()
        
        if username in users:
            return jsonify({"error": "User already exists"}), 400
        
        users[username] = {
            "password_hash": hash_password(password),
            "created_at": datetime.now().isoformat()
        }
        save_users(users)
        
        return jsonify({"message": "Signup successful"}), 201
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"error": "Signup failed"}), 500

@app.route("/login", methods=["POST"])
def login():
    """Login with username and password."""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        users = load_users()
        
        if username not in users:
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_hash = users[username]["password_hash"]
        
        if hash_password(password) != stored_hash:
            return jsonify({"error": "Invalid credentials"}), 401
        
        return jsonify({"message": "Login successful", "username": username}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@app.route("/predict", methods=["POST"])
def predict():
    """Make a prediction based on water quality parameters."""
    try:
        data = request.get_json()
        
        # Parse inputs
        try:
            temp = float(data.get("temperature", 25))
            rain = float(data.get("rainfall", 50))
            turb = float(data.get("turbidity", 5))
            cont = float(data.get("contamination", 100))
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid input types: {str(e)}"}), 400
        
        # Load model
        model = load_model()
        if model is None:
            return jsonify({"error": "Model not available. Please retrain."}), 500
        
        # Make prediction
        X = np.array([[temp, rain, turb, cont]], dtype=float)
        prediction = float(model.predict(X)[0])
        
        # Clamp prediction to 0-1
        prediction = max(0.0, min(1.0, prediction))
        
        # Determine risk level
        if prediction > 0.7:
            risk_level = "HIGH"
        elif prediction > 0.4:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
        
        return jsonify({
            "prediction": round(prediction, 3),
            "risk_level": risk_level,
            "inputs": {
                "temperature": temp,
                "rainfall": rain,
                "turbidity": turb,
                "contamination": cont
            }
        }), 200
    except Exception as e:
        print(f"Prediction error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route("/train", methods=["GET"])
def train():
    """Retrain the model."""
    try:
        # Try CSV first
        model = train_model_from_csv()
        
        # Fallback to dummy if CSV fails
        if model is None:
            model = create_dummy_model()
        
        if model is None:
            return jsonify({"error": "Failed to train model"}), 500
        
        meta = {}
        if os.path.exists(MODEL_META_FILE):
            with open(MODEL_META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
        
        return jsonify({"message": "Model trained successfully", "meta": meta}), 200
    except Exception as e:
        print(f"Training error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Training failed: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("Water Disease Predictor - Flask Backend")
    print("=" * 50)
    print(f"Base directory: {BASE_DIR}")
    print(f"CSV file: {CSV_FILE}")
    print(f"Model file: {MODEL_FILE}")
    print(f"Users file: {USERS_FILE}")
    print("=" * 50)
    
    # Ensure model exists on startup
    print("Initializing model...")
    ensure_model_exists()
    print("Model ready!")
    print("=" * 50)
    
    print("\n✅ Starting Flask server on http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server\n")
    
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)