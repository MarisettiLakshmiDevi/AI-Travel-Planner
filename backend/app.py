# app.py
import os
import json
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

# Optional libraries we use:
# google-genai (Gemini/Vertex AI) and googlemaps (Places, Geocode)
try:
    from google import genai
    from google.genai.types import HttpOptions
except Exception:
    genai = None

try:
    import googlemaps
except Exception:
    googlemaps = None

app = Flask(_name_)
CORS(app)  # allow your frontend to call this service

# init clients (read keys from env vars)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")        # Gemini / Google AI Studio / Dev API key
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")      # Google Maps Platform key

# init GenAI client (Gemini / Google Gen AI SDK)
genai_client = None
if genai:
    try:
        # The SDK will pick the API key from GOOGLE_API_KEY environment variable by default.
        genai_client = genai.Client(http_options=HttpOptions(api_version="v1"))
    except Exception as e:
        print("Warning: genai client init failed:", e)

# init Google Maps client
gmaps = None
if googlemaps and GOOGLE_MAPS_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
    except Exception as e:
        print("Warning: googlemaps init failed:", e)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/generate", methods=["POST"])
def generate_itinerary():
    data = request.get_json() or {}
    origin = data.get("origin", "Eluru")
    destination = data.get("destination", "Goa")
    try:
        days = int(data.get("days", 3))
    except Exception:
        days = 3
    try:
        budget = int(data.get("budget", 5000))
    except Exception:
        budget = 5000
    interests = data.get("interests", [])

    # 1) Try to fetch a few attractions from Google Maps (Places)
    attractions_summary = []
    if gmaps:
        try:
            geocode = gmaps.geocode(destination)
            if geocode:
                loc = geocode[0]["geometry"]["location"]
                latlng = (loc["lat"], loc["lng"])
                for interest in interests[:4]:  # limit to first 4 interests
                    places = gmaps.places_nearby(location=latlng,
                                                 radius=7000,
                                                 keyword=interest,
                                                 type="tourist_attraction")
                    results = places.get("results", [])[:5]
                    found = [{"name": r.get("name"), "vicinity": r.get("vicinity", "")} for r in results]
                    attractions_summary.append({"interest": interest, "places": found})
        except Exception as e:
            print("Google Maps error:", e)

    # 2) Build a prompt and call Gemini / Gen AI to produce structured JSON itinerary
    ai_prompt = f"""
You are a JSON-output assistant that builds short, budget-friendly travel itineraries for students.
Input:
- origin: {origin}
- destination: {destination}
- days: {days}
- budget_inr: {budget}
- interests: {interests}
- attractions (list of places from Maps): {attractions_summary}

Produce only valid JSON (no extra commentary) with keys:
- summary: short single-line summary
- transport: list of objects {{mode, approx_cost_inr or null}}
- daily_plan: list of length {days} with objects {{day, morning, afternoon, evening, cost_inr}}
- total_cost: integer
- notes: short notes for traveler

Return the JSON only.
"""
    ai_text = None
    ai_json = None
    if genai_client:
        try:
            resp = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=ai_prompt
            )
            ai_text = getattr(resp, "text", None) or str(resp)
            # try to parse JSON
            try:
                ai_json = json.loads(ai_text)
            except Exception:
                # sometimes model returns text with backticks or explanation; try to extract JSON substring
                import re
                m = re.search(r"\{.*\}", ai_text, re.S)
                if m:
                    try:
                        ai_json = json.loads(m.group(0))
                    except Exception:
                        ai_json = None
        except Exception as e:
            print("GenAI call failed:", e)

    # 3) If AI returned valid JSON, return that. Otherwise, fall back to a simple mock itinerary.
    if ai_json:
        return jsonify(ai_json)

    # Fallback mock (if API calls failed)
    daily_plan = []
    for i in range(days):
        cost = random.randint(400, 900)
        daily_plan.append({
            "day": i + 1,
            "morning": "Local sightseeing",
            "afternoon": "Street food and local market",
            "evening": "Relax / nightlife (optional)",
            "cost": cost
        })
    transport = [
        {"mode": "Train", "cost": 500},
        {"mode": "Bus", "cost": 300},
        {"mode": "Flight", "cost": None}
    ]
    total_cost = sum(d["cost"] for d in daily_plan) + min(t["cost"] for t in transport if t["cost"])
    result = {
        "summary": f"{days}-day trip {origin} → {destination}",
        "transport": transport,
        "daily_plan": daily_plan,
        "total_cost": total_cost,
        "notes": "Could not reach external APIs; returned fallback plan. Deploy and set keys to enable live itinerary."
    }
    return jsonify(result)


if _name_ == "_main_":
    # local dev: set PORT=8080 (Cloud Run uses 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
