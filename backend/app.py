# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import os

app = Flask(__name__)
# For now allow all origins; later restrict to your frontend domain
CORS(app)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/generate", methods=["POST"])
def generate_itinerary():
    data = request.get_json() or {}
    origin = data.get("origin", "Eluru")
    destination = data.get("destination", "Goa")
    days = int(data.get("days", 2))
    interests = data.get("interests", [])
    # (Your existing itinerary generation logic here)
    # Example mock response:
    daily_plan = []
    for i in range(days):
        daily_plan.append({
            "day": i+1,
            "morning": "Sightseeing",
            "afternoon": "Local food",
            "evening": "Beach/market",
            "cost": random.randint(400,800)
        })
    transport = [
        {"mode":"Train","cost":500},
        {"mode":"Bus","cost":300},
        {"mode":"Flight","cost":None}
    ]
    total_cost = sum(d["cost"] for d in daily_plan) + min(t["cost"] for t in transport if t["cost"])
    return jsonify({
        "summary": f"{days}-day trip {origin} → {destination}",
        "transport": transport,
        "daily_plan": daily_plan,
        "total_cost": total_cost,
        "notes": "Budget friendly"
    })

# Local dev only: keep this block
if __name__ == "__main__":
    # debug=True only for local development
    app.run(debug=True, host="0.0.0.0", port=5000)
