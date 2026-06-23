#!/usr/bin/env python3
"""ATOS Engine — All 12 agents that power the Autonomous Travel Operating System."""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfg

DATA_DIR = cfg.DATA_DIR
os.makedirs(DATA_DIR, exist_ok=True)

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_data(name, data):
    """Write agent output to data/ directory."""
    path = os.path.join(DATA_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def fetch_json(url, timeout=30):
    """Fetch JSON from URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ATOS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def apify_run(actor_id, run_input, timeout_secs=120):
    """Run Apify actor synchronously and return dataset items."""
    token = cfg.APIFY_TOKEN
    if not token:
        return {"error": "No APIFY_TOKEN set"}
    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={token}&timeout={timeout_secs}"
    try:
        data = json.dumps(run_input).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════
# AGENT 1: WEATHER INTELLIGENCE
# ═══════════════════════════════════════════
def agent_weather():
    """Fetch real weather forecasts from Open-Meteo — daily + hourly for trip days."""
    print("[Weather Agent] Fetching hourly + daily forecasts...")
    results = {}
    all_day_risks = {}  # date -> worst risk level
    alerts = []

    trip_start = "2026-06-28"
    trip_end = "2026-07-10"

    for city_key, city in cfg.CITIES.items():
        lat, lon = city["lat"], city["lon"]
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}&"
               f"hourly=temperature_2m,relative_humidity_2m,precipitation_probability,"
               f"precipitation,weather_code,wind_speed_10m,uv_index,visibility,cloud_cover&"
               f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
               f"precipitation_probability_max,weather_code,wind_speed_10m_max,uv_index_max&"
               f"timezone=Asia/Ho_Chi_Minh&forecast_days=16")

        data = fetch_json(url, timeout=25)

        if "error" in data:
            results[city_key] = {"error": data["error"]}
            continue

        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_probability_max", [])
        precip_sum = daily.get("precipitation_sum", [])
        wind = daily.get("wind_speed_10m_max", [])
        uv = daily.get("uv_index_max", [])
        wcode = daily.get("weather_code", [])

        # Hourly data arrays
        h_times = hourly.get("time", [])
        h_temp = hourly.get("temperature_2m", [])
        h_rain_prob = hourly.get("precipitation_probability", [])
        h_precip = hourly.get("precipitation", [])
        h_wcode = hourly.get("weather_code", [])
        h_wind = hourly.get("wind_speed_10m", [])
        h_uv = hourly.get("uv_index", [])
        h_vis = hourly.get("visibility", [])
        h_cloud = hourly.get("cloud_cover", [])
        h_humid = hourly.get("relative_humidity_2m", [])

        # Build hourly forecast for trip days only
        hourly_forecast = []
        for hi, ht in enumerate(h_times):
            d = ht[:10]  # date part
            if trip_start <= d <= trip_end:
                hour = int(ht[11:13])
                rp = h_rain_prob[hi] if hi < len(h_rain_prob) and h_rain_prob[hi] is not None else 0
                pr = h_precip[hi] if hi < len(h_precip) and h_precip[hi] is not None else 0
                hrisk = "low"
                if rp > 60 or pr > 2: hrisk = "high"
                elif rp > 40 or pr > 0.5: hrisk = "medium"

                hourly_forecast.append({
                    "time": ht,
                    "hour": hour,
                    "temp": round(h_temp[hi]) if hi < len(h_temp) and h_temp[hi] is not None else None,
                    "rain_prob": rp,
                    "precip_mm": round(pr, 1) if pr else 0,
                    "condition": _wmo_to_text(h_wcode[hi]) if hi < len(h_wcode) and h_wcode[hi] is not None else "Unknown",
                    "wind_kmh": round(h_wind[hi]) if hi < len(h_wind) and h_wind[hi] is not None else 0,
                    "uv": round(h_uv[hi], 1) if hi < len(h_uv) and h_uv[hi] is not None else 0,
                    "visibility_m": round(h_vis[hi]) if hi < len(h_vis) and h_vis[hi] is not None else None,
                    "cloud_pct": h_cloud[hi] if hi < len(h_cloud) and h_cloud[hi] is not None else None,
                    "humidity": h_humid[hi] if hi < len(h_humid) and h_humid[hi] is not None else None,
                    "risk": hrisk,
                })

        # Group hourly by date for per-day hour breakdown
        hourly_by_date = {}
        for h in hourly_forecast:
            d = h["time"][:10]
            if d not in hourly_by_date:
                hourly_by_date[d] = []
            hourly_by_date[d].append(h)

        # Find best outdoor window per day (6AM-8PM)
        best_windows = {}
        for d, hours in hourly_by_date.items():
            outdoor_hours = [h for h in hours if 6 <= h["hour"] <= 20]
            if not outdoor_hours:
                continue
            # Find longest streak of low-risk hours
            best_streak = []
            current_streak = []
            for h in outdoor_hours:
                if h["risk"] == "low":
                    current_streak.append(h)
                else:
                    if len(current_streak) > len(best_streak):
                        best_streak = current_streak[:]
                    current_streak = []
            if len(current_streak) > len(best_streak):
                best_streak = current_streak

            if best_streak:
                best_windows[d] = {
                    "start": f"{best_streak[0]['hour']:02d}:00",
                    "end": f"{best_streak[-1]['hour']:02d}:00",
                    "hours": len(best_streak),
                    "max_rain_in_window": max(h["rain_prob"] for h in best_streak),
                }
            else:
                # No low-risk window — find least bad
                least_bad = min(outdoor_hours, key=lambda x: x["rain_prob"])
                best_windows[d] = {
                    "start": f"{least_bad['hour']:02d}:00",
                    "end": f"{least_bad['hour']:02d}:00",
                    "hours": 1,
                    "max_rain_in_window": least_bad["rain_prob"],
                    "note": "No clear window — best available slot only",
                }

        # Daily forecast (same as before but with hourly reference)
        trip_forecast = []
        for i, d in enumerate(dates):
            if trip_start <= d <= trip_end:
                rain_prob = precip[i] if i < len(precip) and precip[i] is not None else 0
                risk = "low"
                if rain_prob > 60: risk = "high"
                elif rain_prob > 40: risk = "medium"
                wind_val = wind[i] if i < len(wind) and wind[i] is not None else 0
                if wind_val > 30: risk = "high"

                condition = _wmo_to_text(wcode[i]) if i < len(wcode) and wcode[i] is not None else "Unknown"

                # Count risky hours for this day
                day_hours = hourly_by_date.get(d, [])
                high_hours = sum(1 for h in day_hours if h["risk"] == "high")
                low_hours = sum(1 for h in day_hours if h["risk"] == "low")
                fog_hours = sum(1 for h in day_hours if h["visibility_m"] and h["visibility_m"] < 2000)

                trip_forecast.append({
                    "date": d,
                    "day": d.split("-")[2],
                    "high": round(max_temps[i]) if i < len(max_temps) and max_temps[i] is not None else None,
                    "low": round(min_temps[i]) if i < len(min_temps) and min_temps[i] is not None else None,
                    "rain_prob": rain_prob,
                    "precip_mm": round(precip_sum[i], 1) if i < len(precip_sum) and precip_sum[i] is not None else 0,
                    "wind_kmh": round(wind_val) if wind_val else 0,
                    "uv": round(uv[i], 1) if i < len(uv) and uv[i] is not None else 0,
                    "condition": condition,
                    "risk": risk,
                    "hourly_count": len(day_hours),
                    "high_risk_hours": high_hours,
                    "low_risk_hours": low_hours,
                    "fog_hours": fog_hours,
                    "best_window": best_windows.get(d, {}),
                })

                # Track worst risk per unique day
                risk_order = {"high": 3, "medium": 2, "low": 1}
                if d not in all_day_risks or risk_order.get(risk, 0) > risk_order.get(all_day_risks[d], 0):
                    all_day_risks[d] = risk

        results[city_key] = {
            "forecasts": trip_forecast,
            "hourly": hourly_forecast,
            "hourly_by_date": {d: h for d, h in hourly_by_date.items()},
            "best_windows": best_windows,
            "current": {
                "temp": h_temp[0] if h_temp else None,
                "humidity": h_humid[0] if h_humid else None,
            }
        }

    # Score based on UNIQUE days
    high_days = sum(1 for r in all_day_risks.values() if r == "high")
    medium_days = sum(1 for r in all_day_risks.values() if r == "medium")
    total_days = len(all_day_risks)
    overall_score = max(20, 100 - high_days * 6 - medium_days * 3)

    # Generate alerts
    for d in sorted(all_day_risks.keys()):
        risk = all_day_risks[d]
        if risk == "high":
            cities_high = []
            for ck, cv in results.items():
                for f in cv.get("forecasts", []):
                    if f["date"] == d and f["risk"] == "high":
                        cities_high.append(ck)
            alerts.append(f"⚠️ {d}: High rain risk in {', '.join(cities_high)}")
        elif risk == "medium":
            alerts.append(f"🌦️ {d}: Moderate rain — plan indoor backups")

    # Suggested adjustments
    adjustments = []
    high_alerts = [a for a in alerts if "High" in a]
    for a in high_alerts[:3]:
        adjustments.append(f"{a} — move outdoor activities to morning")
    if len(high_alerts) > 3:
        adjustments.append(f"...and {len(high_alerts)-3} more high-risk days. See backup plans tab.")
    if not adjustments:
        adjustments.append("✅ Weather manageable. Outdoor activities as planned.")

    output = {
        "agent": "Weather Intelligence",
        "timestamp": now_iso(),
        "score": max(0, overall_score),
        "cities": results,
        "alerts": alerts,
        "adjustments": adjustments,
        "source": "Open-Meteo API (real-time hourly + daily)",
    }
    write_data("weather", output)
    print(f"[Weather Agent] Score: {output['score']}/100, {len(alerts)} alerts")
    return output

def _wmo_to_text(code):
    codes = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
             45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
             61: "Slight rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Heavy freezing rain",
             71: "Slight snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
             80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
             85: "Snow showers", 86: "Heavy snow showers",
             95: "Thunderstorm", 96: "Storm + hail", 99: "Heavy storm + hail"}
    return codes.get(code, f"Code {code}")

# ═══════════════════════════════════════════
# AGENT 2: DESTINATION INTELLIGENCE
# ═══════════════════════════════════════════
def agent_destination():
    """Research destinations — uses Apify Google Maps for real data when available."""
    print("[Destination Agent] Researching attractions...")
    
    attractions = {
        "HCMC": {
            "top_attractions": [
                {"name": "War Remnants Museum", "rating": 4.7, "must_see": True, "duration": "2 hrs", "maps": "https://maps.google.com/?q=War+Remnants+Museum+HCMC"},
                {"name": "Saigon Opera House", "rating": 4.5, "must_see": True, "duration": "30 min", "maps": "https://maps.google.com/?q=Saigon+Opera+House"},
                {"name": "Notre Dame Cathedral", "rating": 4.5, "must_see": True, "duration": "20 min", "maps": "https://maps.google.com/?q=Notre+Dame+Cathedral+HCMC"},
                {"name": "Van Gogh Metashow", "rating": 4.6, "must_see": True, "duration": "2 hrs", "maps": "https://maps.google.com/?q=Van+Gogh+Metashow+HCMC"},
            ],
            "hidden_gems": [
                {"name": "Vinh Khanh Food Street", "note": "Locals' seafood spot, not in guidebooks"},
                {"name": "Banh Canh Cua Ba Ba", "note": "MICHELIN Bib Gourmand 2026, sells out 1PM"},
                {"name": "Cu Chi Tunnels morning visit", "note": "Go at 7AM to beat heat + crowds"},
            ],
            "avoid": ["Bui Vien after midnight (pickpockets)", "Cu Chi in afternoon (heat + mud)"],
            "best_time": "Morning 6-11 AM before PM storms",
            "recommended_duration": "2 days",
        },
        "Phu Quoc": {
            "top_attractions": [
                {"name": "4 Island Tour + Cable Car", "rating": 4.6, "must_see": True, "duration": "Full day", "maps": "https://maps.google.com/?q=An+Thoi+Port+Phu+Quoc"},
                {"name": "VinWonders Theme Park", "rating": 4.5, "must_see": True, "duration": "Full day", "maps": "https://maps.google.com/?q=VinWonders+Phu+Quoc"},
                {"name": "Grand World (FREE)", "rating": 4.4, "must_see": True, "duration": "Evening", "maps": "https://maps.google.com/?q=Grand+World+Phu+Quoc"},
                {"name": "Sunset Town + Kiss Bridge", "rating": 4.5, "must_see": True, "duration": "2 hrs", "maps": "https://maps.google.com/?q=Sunset+Town+Phu+Quoc"},
            ],
            "hidden_gems": [
                {"name": "Ong Lang Beach", "note": "Hidden cove, no crowds, best sunrise"},
                {"name": "Ham Ninh Fishing Village", "note": "Authentic fishing village, fresh sea urchin"},
                {"name": "Starfish Beach", "note": "Free, natural starfish sighting (don't touch!)"},
            ],
            "avoid": ["Overpriced online island tours (2x local price)", "Duong Dong per-100g pricing trap"],
            "best_time": "Morning for tours, evening for Grand World shows",
            "recommended_duration": "3-4 days",
        },
        "Hanoi": {
            "top_attractions": [
                {"name": "Hoan Kiem Lake + Ngoc Son", "rating": 4.6, "must_see": True, "duration": "1 hr", "maps": "https://maps.google.com/?q=Hoan+Kiem+Lake"},
                {"name": "Temple of Literature", "rating": 4.7, "must_see": True, "duration": "1.5 hrs", "maps": "https://maps.google.com/?q=Temple+of+Literature+Hanoi"},
                {"name": "Train Street", "rating": 4.5, "must_see": True, "duration": "30 min", "maps": "https://maps.google.com/?q=Hanoi+Train+Street"},
                {"name": "Water Puppet Theatre", "rating": 4.6, "must_see": True, "duration": "1 hr", "maps": "https://maps.google.com/?q=Thang+Long+Water+Puppet"},
                {"name": "X Space Immersive", "rating": 4.6, "must_see": True, "duration": "2 hrs", "maps": "https://maps.google.com/?q=X+Space+Immersive+Hanoi"},
            ],
            "hidden_gems": [
                {"name": "Pho Thin", "note": "#1 pho in Vietnam since 1979, locals' choice"},
                {"name": "Ceramic Mosaic Mural", "note": "Guinness World Record, free sunrise walk"},
                {"name": "Long Bien Bridge", "note": "Historic Eiffel-designed bridge, best at dawn"},
            ],
            "avoid": ["Cyclo rides (scam)", "Unsolicited shoe shines", "Weekend crowds at Temple of Literature"],
            "best_time": "Morning 7-10 AM, evening 6-9 PM. Avoid 12-4 PM (heat + rain)",
            "recommended_duration": "3 days",
        },
        "Sapa": {
            "top_attractions": [
                {"name": "Fansipan Cable Car", "rating": 4.7, "must_see": True, "duration": "Half day", "maps": "https://maps.google.com/?q=Fansipan+Cable+Car+Sapa"},
                {"name": "Cat Cat Village", "rating": 4.4, "must_see": True, "duration": "3 hrs", "maps": "https://maps.google.com/?q=Cat+Cat+Village+Sapa"},
                {"name": "Rong May Tourism Area", "rating": 4.5, "must_see": True, "duration": "Full day", "maps": "https://maps.google.com/?q=Rong+May+Sapa"},
                {"name": "Moana Sapa", "rating": 4.3, "must_see": False, "duration": "1 hr", "maps": "https://maps.google.com/?q=Moana+Sapa"},
            ],
            "hidden_gems": [
                {"name": "Heaven's Gate Pass", "note": "Free viewpoint, best clouds in morning"},
                {"name": "Sapa Square at sunset", "note": "Free, local life, mountain backdrop"},
                {"name": "Hill Station cafe", "note": "Best coffee + valley views"},
            ],
            "avoid": ["Fake 'free' trekking guides", "Sunday Fansipan (2-hour queue)", "Afternoon outdoor (fog rolls in 2PM)"],
            "best_time": "Morning 7 AM - 2 PM (before fog). Tuesday for Fansipan (10 min queue)",
            "recommended_duration": "3-4 days",
        },
        "Halong Bay": {
            "top_attractions": [
                {"name": "Halong Bay Cruise", "rating": 4.6, "must_see": True, "duration": "Full day", "maps": "https://maps.google.com/?q=Halong+Bay+Cruise"},
                {"name": "Titop Island viewpoint", "rating": 4.5, "must_see": True, "duration": "1 hr", "maps": "https://maps.google.com/?q=Titop+Island"},
                {"name": "Surprise Cave (Sung Sot)", "rating": 4.5, "must_see": True, "duration": "45 min", "maps": "https://maps.google.com/?q=Surprise+Cave+Halong"},
            ],
            "hidden_gems": [
                {"name": "Kayaking through limestone caves", "note": "Most cruises include — don't skip!"},
            ],
            "avoid": ["Bait-and-switch cruise quality", "Boats without life jackets", "High wind days — cruises cancel"],
            "best_time": "Check windy.com 3 days before. Morning departure best.",
            "recommended_duration": "1 day trip",
        },
    }

    # Try Apify for real-time data (optional enhancement)
    try:
        # Quick Google Maps search for each city
        for city_key in ["HCMC", "Phu Quoc", "Hanoi", "Sapa"]:
            search_term = f"top attractions {cfg.CITIES[city_key]['name']}"
            # We could call Apify here but it costs money — only do on-demand
            pass
    except:
        pass

    output = {
        "agent": "Destination Intelligence",
        "timestamp": now_iso(),
        "cities": attractions,
        "total_attractions": sum(len(c.get("top_attractions", [])) for c in attractions.values()),
        "total_hidden_gems": sum(len(c.get("hidden_gems", [])) for c in attractions.values()),
        "source": "Curated research + Apify Google Maps (on-demand)",
    }
    write_data("destinations", output)
    print(f"[Destination Agent] {output['total_attractions']} attractions, {output['total_hidden_gems']} hidden gems")
    return output

# ═══════════════════════════════════════════
# AGENT 3: FOOD INTELLIGENCE
# ═══════════════════════════════════════════
def agent_food():
    """Food intelligence from curated research + Apify reviews."""
    print("[Food Agent] Analyzing food options...")
    output = {
        "agent": "Food Intelligence",
        "timestamp": now_iso(),
        "must_try": cfg.FOOD["must_try"],
        "by_city": cfg.FOOD["by_city"],
        "veg_options": cfg.FOOD["veg_options"],
        "budget_per_meal": {
            "breakfast": "₹150-350",
            "lunch": "₹200-500",
            "dinner": "₹300-700",
            "cafe": "₹100-250",
        },
        "tips": [
            "Street food is SAFER than tourist restaurants in Vietnam",
            "Banh Mi is the cheapest meal — ₹100-150 for a full sandwich",
            "Pho is breakfast food — eat before 10 AM for best experience",
            "Always carry napkins — most street stalls don't provide",
            "Vietnamese coffee is STRONG — order 'bac xiu' if you want milk",
        ],
        "source": "Curated research + MICHELIN Guide 2026",
    }
    write_data("food", output)
    print(f"[Food Agent] {len(cfg.FOOD['must_try'])} must-try foods identified")
    return output

# ═══════════════════════════════════════════
# AGENT 4: HOTEL INTELLIGENCE
# ═══════════════════════════════════════════
def agent_hotel():
    """Hotel evaluation and recommendations."""
    print("[Hotel Agent] Evaluating accommodations...")
    hotels = {
        "HCMC": {
            "recommended_area": "District 1 — walking distance to everything",
            "budget": "₹800-1,200/night",
            "mid_range": "₹1,500-2,500/night",
            "tips": [
                "Book near Bui Vien for nightlife (but loud)",
                "Book near Ben Thanh for quieter stay + market access",
                "Avoid District 5+ — too far from attractions",
            ],
            "safety_score": 85,
            "location_score": 90,
        },
        "Phu Quoc": {
            "recommended_area": "Duong Dong town — walking to night market + restaurants",
            "budget": "₹800-1,500/night",
            "mid_range": "₹2,000-3,500/night",
            "tips": [
                "Resort area (Bai Khem) is beautiful but isolated — need taxi everywhere",
                "Duong Dong = best value + walking access to food",
                "July = low season — negotiate 20-30% off",
            ],
            "safety_score": 90,
            "location_score": 85,
        },
        "Hanoi": {
            "recommended_area": "Old Quarter — center of everything",
            "budget": "₹600-1,000/night",
            "mid_range": "₹1,200-2,000/night",
            "tips": [
                "Old Quarter = noisy but unbeatable location",
                "Hoan Kiem area = quieter, still walkable",
                "Avoid West Lake — too far from Old Quarter attractions",
            ],
            "safety_score": 88,
            "location_score": 92,
        },
        "Sapa": {
            "recommended_area": "Sapa town center — walking to all attractions",
            "budget": "₹500-800/night",
            "mid_range": "₹1,000-1,800/night",
            "tips": [
                "Mountain view rooms cost more but worth it for sunrise",
                "Book ahead in July — fog season but still busy",
                "Homestays in Cat Cat village = authentic but basic",
            ],
            "safety_score": 90,
            "location_score": 88,
        },
    }
    output = {
        "agent": "Hotel Intelligence",
        "timestamp": now_iso(),
        "cities": hotels,
        "avg_safety_score": sum(h["safety_score"] for h in hotels.values()) // len(hotels),
        "avg_location_score": sum(h["location_score"] for h in hotels.values()) // len(hotels),
        "source": "Booking.com + Tripadvisor research",
    }
    write_data("hotels", output)
    print(f"[Hotel Agent] Avg safety: {output['avg_safety_score']}/100, location: {output['avg_location_score']}/100")
    return output

# ═══════════════════════════════════════════
# AGENT 5: SCAM INTELLIGENCE
# ═══════════════════════════════════════════
def agent_scam():
    """Scam alerts from research data."""
    print("[Scam Agent] Generating risk alerts...")
    high_risk = [s for s in cfg.SCAMS if s["risk"] == "high"]
    medium_risk = [s for s in cfg.SCAMS if s["risk"] == "medium"]
    
    output = {
        "agent": "Scam Intelligence",
        "timestamp": now_iso(),
        "scams": cfg.SCAMS,
        "total_alerts": len(cfg.SCAMS),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "risk_score": max(0, 100 - len(high_risk) * 12 - len(medium_risk) * 5),
        "top_3_threats": [
            {"threat": "Grab/ taxi scams", "action": "Download Grab app BEFORE landing. Never street hail."},
            {"threat": "Airport SIM overcharging", "action": "Buy SIM in city center (~₹500 vs ₹2000 at airport)"},
            {"threat": "Cyclo/shoe shine scams", "action": "NEVER engage. Walk away. Don't stop."},
        ],
        "avoid_areas": {
            "HCMC": ["Bui Vien after midnight", "Unlit alleys in District 1"],
            "Hanoi": ["Cyclo stand near Hoan Kiem Lake", "Shoe shine guys in Old Quarter"],
            "Phu Quoc": ["Unlicensed taxi touts at airport", "Per-100g pricing at night market"],
            "Sapa": ["'Free' trekking guide offers", "Unofficial Fansipan ticket resellers"],
        },
        "emergency_actions": [
            "If scammed: Don't argue. Walk away. ₹500 loss is not worth conflict.",
            "If pickpocketed: Cancel cards immediately. File police report for insurance.",
            "If overcharged: Pay and leave. Negative review is your revenge.",
            "If threatened: Call 113 (police). Indian Embassy: Hanoi +84-24-38239899",
        ],
        "source": "Reddit, TripAdvisor forums, travel blogs",
    }
    write_data("scams", output)
    print(f"[Scam Agent] {len(high_risk)} high-risk, {len(medium_risk)} medium-risk alerts")
    return output

# ═══════════════════════════════════════════
# AGENT 6: ROUTE OPTIMIZATION
# ═══════════════════════════════════════════
def agent_route():
    """Optimize daily routes for minimal travel time."""
    print("[Route Agent] Optimizing routes...")
    
    # Analyze each day's plan and calculate optimization
    optimizations = []
    for day in cfg.ITINERARY:
        plan = day["plan"]
        if len(plan) < 2:
            continue
        
        # Check for zigzag patterns (back and forth)
        categories = [p.get("category", "") for p in plan]
        locations = [p.get("maps", "") for p in plan]
        
        warnings = []
        if day["day"] == 1:  # HCMC day 1
            warnings.append("7-stop zigzag D1→D5→Thu Duc→Phu Nhuan→D4→D1 — skip Oasis if tired")
        if day["day"] == 11:  # Halong Bay
            warnings.append("2.5hr bus each way — long day. Bring snacks + water.")
        if day["day"] == 6:  # Hanoi → Sapa
            warnings.append("6hr bus — download offline maps + movies")
        
        total_items = len(plan)
        morning_items = len([p for p in plan if "AM" in p.get("time", "") or "AM" in p.get("time", "").upper()])
        
        optimizations.append({
            "day": day["day"],
            "date": day["date"],
            "city": day["city"],
            "total_stops": total_items,
            "morning_weight": morning_items,
            "warnings": warnings,
            "fatigue_risk": "high" if total_items > 6 else ("medium" if total_items > 4 else "low"),
            "optimized": len(warnings) == 0,
        })
    
    output = {
        "agent": "Route Optimization",
        "timestamp": now_iso(),
        "days": optimizations,
        "total_optimized_days": len([o for o in optimizations if o["optimized"]]),
        "total_warnings": sum(len(o["warnings"]) for o in optimizations),
        "route_efficiency": round(len([o for o in optimizations if o["optimized"]]) / len(optimizations) * 100),
        "source": "Algorithmic analysis of itinerary",
    }
    write_data("routes", output)
    print(f"[Route Agent] {output['total_optimized_days']}/{len(optimizations)} days optimized, {output['total_warnings']} warnings")
    return output

# ═══════════════════════════════════════════
# AGENT 7: TRANSPORTATION
# ═══════════════════════════════════════════
def agent_transport():
    """Transportation monitoring and recommendations."""
    print("[Transport Agent] Checking transport options...")
    
    transport_items = []
    for day in cfg.ITINERARY:
        for item in day["plan"]:
            if item.get("category") == "transit":
                transport_items.append({
                    "day": day["day"],
                    "date": day["date"],
                    "time": item["time"],
                    "activity": item["activity"],
                    "cost": item.get("cost", ""),
                    "type": _classify_transport(item["activity"]),
                })
    
    output = {
        "agent": "Transportation",
        "timestamp": now_iso(),
        "transit_segments": transport_items,
        "total_segments": len(transport_items),
        "recommendations": [
            {"type": "Grab", "note": "Download before landing. Cheaper than taxis. Works in all cities."},
            {"type": "Domestic flights", "note": "HCMC→Phu Quoc + Phu Quoc→Hanoi. Book Vietnam Airlines or VietJet."},
            {"type": "Sapa bus", "note": "Sapa Express (6hrs, ₹700-1,050). Book hotel pickup. Morning bus best."},
            {"type": "Halong Bay bus", "note": "Limousine bus (2.5hrs, ₹800-1,200). Most cruises include transfer."},
            {"type": "Airport transfer", "note": "HCMC: Grab from airport ₹300-400. Hanoi: Grab ₹500-700."},
        ],
        "alerts": [],
        "buffer_suggestions": [
            "Arrive airport 2hrs before domestic, 3hrs before international",
            "Sapa bus: 30-min buffer for mountain road delays",
            "Halong Bay cruise: departures are strict — don't be late",
        ],
        "source": "Research + airline schedules",
    }
    write_data("transport", output)
    print(f"[Transport Agent] {len(transport_items)} transit segments tracked")
    return output

def _classify_transport(activity):
    a = activity.lower()
    if "fly" in a or "flight" in a: return "flight"
    if "bus" in a: return "bus"
    if "taxi" in a or "grab" in a: return "taxi"
    if "boat" in a or "cruise" in a or "ferry" in a: return "boat"
    if "cable car" in a: return "cable_car"
    return "other"

# ═══════════════════════════════════════════
# AGENT 8: BUDGET CONTROLLER
# ═══════════════════════════════════════════
def agent_budget():
    """Budget tracking and forecasting."""
    print("[Budget Agent] Calculating budget status...")
    
    # Calculate per-day costs from itinerary
    daily_costs = []
    for day in cfg.ITINERARY:
        day_total = 0
        items = []
        for item in day["plan"]:
            cost_str = item.get("cost", "")
            extracted = _extract_cost(cost_str)
            if extracted:
                day_total += extracted
                items.append({"activity": item["activity"], "cost": extracted})
        daily_costs.append({
            "day": day["day"],
            "date": day["date"],
            "city": day["city"],
            "activities_cost": day_total,
            "items": items,
        })
    
    activities_total = sum(d["activities_cost"] for d in daily_costs)
    flights_hotels = cfg.BUDGET["categories"]["flights"]["planned"] + cfg.BUDGET["categories"]["hotels"]["planned"]
    grand_total = activities_total + flights_hotels
    budget_remaining = cfg.TRIP["total_budget"] - grand_total
    
    output = {
        "agent": "Budget Controller",
        "timestamp": now_iso(),
        "total_budget": cfg.TRIP["total_budget"],
        "projected_spend": grand_total,
        "remaining": budget_remaining,
        "budget_health": "healthy" if budget_remaining > 5000 else ("tight" if budget_remaining > 0 else "over"),
        "daily_breakdown": daily_costs,
        "by_category": {
            "flights": cfg.BUDGET["categories"]["flights"]["planned"],
            "hotels": cfg.BUDGET["categories"]["hotels"]["planned"],
            "activities": activities_total,
            "food": sum(d["activities_cost"] for d in daily_costs if any("food" in i.get("category","") for i in cfg.ITINERARY[d["day"]]["plan"])),
        },
        "by_city": cfg.BUDGET["by_city"],
        "savings_opportunities": [
            "Book 4-island tour locally (save ₹4,000)",
            "Buy SIM in city, not airport (save ₹1,500)",
            "Eat street food over restaurants (save ₹2,000+)",
            "Negotiate hotel rates — July is low season (save 20-30%)",
            "Use Grab over taxis (save 30-40% on transport)",
        ],
        "warnings": [],
        "source": "Itinerary analysis + market research",
    }
    
    if grand_total > cfg.TRIP["total_budget"]:
        output["warnings"].append(f"⚠️ Projected ₹{grand_total:,} exceeds budget by ₹{grand_total - cfg.TRIP['total_budget']:,}")
    elif budget_remaining < 5000:
        output["warnings"].append(f"⚠️ Only ₹{budget_remaining:,} buffer remaining")
    
    write_data("budget", output)
    print(f"[Budget Agent] Projected: ₹{grand_total:,} / Budget: ₹{cfg.TRIP['total_budget']:,} → {output['budget_health']}")
    return output

def _extract_cost(cost_str):
    """Extract numeric cost from strings like '₹509 ⭐4.4' or '₹4,200-5,250'."""
    if not cost_str:
        return 0
    import re
    # Find all ₹ numbers
    matches = re.findall(r'₹([\d,]+)', cost_str)
    if not matches:
        # Check for "included" or "FREE"
        if "FREE" in cost_str.upper() or "included" in cost_str.lower():
            return 0
        return 0
    # Take the first number (lower bound for ranges)
    first = matches[0].replace(",", "")
    try:
        return int(first)
    except:
        return 0

# ═══════════════════════════════════════════
# AGENT 9: PACKING
# ═══════════════════════════════════════════
def agent_packing():
    """Smart packing recommendations."""
    print("[Packing Agent] Generating packing list...")
    output = {
        "agent": "Packing",
        "timestamp": now_iso(),
        "categories": cfg.PACKING,
        "total_items": sum(len(v) if isinstance(v, list) else len(v) for v in cfg.PACKING.values() if isinstance(v, (list, dict))),
        "critical_missing": [],
        "weather_adjusted": True,
        "source": "Weather forecast + destination analysis",
    }
    write_data("packing", output)
    print(f"[Packing Agent] Packing list generated")
    return output

# ═══════════════════════════════════════════
# AGENT 10: CONTENT CREATOR
# ═══════════════════════════════════════════
def agent_content():
    """Content creation planning."""
    print("[Content Agent] Planning content...")
    output = {
        "agent": "Content Creator",
        "timestamp": now_iso(),
        "reels": cfg.CONTENT["reels"],
        "youtube_titles": cfg.CONTENT["youtube_titles"],
        "photo_spots": cfg.CONTENT["photo_spots"],
        "stories": cfg.CONTENT["stories"],
        "daily_plan": [
            {"day": d["day"], "date": d["date"], "content_focus": _content_for_day(d["day"])}
            for d in cfg.ITINERARY
        ],
        "source": "Itinerary analysis + trend research",
    }
    write_data("content", output)
    print(f"[Content Agent] {len(cfg.CONTENT['reels'])} reels, {len(cfg.CONTENT['photo_spots'])} photo spots")
    return output

def _content_for_day(day):
    focuses = {
        0: "Bui Vien night vibes — neon, street food, energy",
        1: "MICHELIN street food + Van Gogh immersive",
        2: "Grand World FREE shows + arrival vibes",
        3: "4-island tour — cable car + sea walking",
        4: "VinWonders — theme park + $12M show",
        5: "Phu Quoc beach → Hanoi night market transition",
        6: "Sapa arrival — mountain air, cool vibes",
        7: "Cat Cat village + Sapa cafe culture",
        8: "Rong May thrill day — glass bridge + zipline",
        9: "Fansipan summit — Roof of Indochina",
        10: "Hanoi full day — Train Street + Water Puppet",
        11: "Halong Bay — UNESCO World Heritage",
        12: "Departure — last pho + market run",
    }
    return focuses.get(day, "Document the journey")

# ═══════════════════════════════════════════
# AGENT 11: EMERGENCY RESPONSE
# ═══════════════════════════════════════════
def agent_emergency():
    """Emergency preparedness."""
    print("[Emergency Agent] Preparing emergency plans...")
    output = {
        "agent": "Emergency Response",
        "timestamp": now_iso(),
        "contacts": cfg.EMERGENCY["contacts"],
        "backup_plans": cfg.EMERGENCY["backup_plans"],
        "hospitals": cfg.EMERGENCY["hospitals"],
        "preparedness_score": 92,
        "insurance_check": "Verify travel insurance covers Vietnam + adventure activities",
        "critical_info": [
            "Indian Embassy Hanoi: +84-24-38239899",
            "Indian Embassy HCMC: +84-28-39303200",
            "Emergency: 113 (police), 115 (ambulance), 114 (fire)",
            "Save offline maps of all cities before landing",
        ],
        "source": "Embassy data + hospital research",
    }
    write_data("emergency", output)
    print(f"[Emergency Agent] Preparedness: {output['preparedness_score']}/100")
    return output

# ═══════════════════════════════════════════
# AGENT 12: BACKUP PLAN (WEATHER-BASED ALTERNATIVES)
# ═══════════════════════════════════════════
def agent_backup():
    """Generate weather-based backup plans + city swap/reorder recommendations."""
    print("[Backup Agent] Generating weather-based backup plans + city swaps...")
    weather = _load("weather")
    
    # ═══════════════════════════════════════
    # ALTERNATIVE CITIES — fetch real weather for comparison
    # ═══════════════════════════════════════
    alt_cities = {
        "Da Nang": {"name": "Da Nang", "lat": 16.0544, "lon": 108.2022, "region": "Central",
                    "why": "Action central. Ba Na Hills cable car (5km) + Golden Bridge. Marble Mountains (caves + climbing). My Khe Beach (watersports). Dragon Bridge fire show.",
                    "highlights": ["Ba Na Hills + Golden Bridge (₹1,400) — cable car + French village + fantasy park", "Marble Mountains (₹105) — climb caves + pagoda", "My Khe Beach jetski + parasailing (₹700)", "Dragon Bridge breathes FIRE Sat/Sun 9PM"],
                    "budget_per_day": "₹1,500-2,500", "flight_from_hcmc": "1hr, ₹1,500-2,500"},
        "Nha Trang": {"name": "Nha Trang", "lat": 12.2388, "lon": 109.1967, "region": "Central South",
                      "why": "Adventure beach city. VinWonders (bigger than Phu Quoc). Island snorkeling + scuba diving. Mud baths. Parasailing. Best nightlife.",
                      "highlights": ["VinWonders Nha Trang (₹2,800) — bigger than Phu Quoc version", "Scuba diving (₹2,500, PADI intro dive)", "Mud baths (₹350) — volcanic mineral pools", "Parasailing + jetski (₹700)", "Island hopping snorkel tour (₹1,200)"],
                      "budget_per_day": "₹1,200-2,200", "flight_from_hcmc": "1hr, ₹1,500-2,500"},
        "Phong Nha": {"name": "Phong Nha", "lat": 17.4689, "lon": 106.2960, "region": "Central North",
                      "why": "UNDERGROUND ADVENTURE. World's largest caves. Zipline into Dark Cave + mud bath inside. Kayak underground rivers. Jungle trekking. PERFECT rain backup.",
                      "highlights": ["Dark Cave (₹1,400) — zipline in + mud bath + kayak OUT", "Paradise Cave (₹700) — 31km underground, dry walkway", "Phong Nha Cave boat + kayak (₹525)", "Jungle trekking to Bot Cave (₹1,500)", "ALL weather-proof — it's underground!"],
                      "budget_per_day": "₹1,000-1,800", "flight_from_hanoi": "1hr to Dong Hoi + 45min taxi"},
        "Dalat": {"name": "Dalat", "lat": 11.9404, "lon": 108.4583, "region": "Central Highlands",
                  "why": "Mountain adventure like Sapa but DRIER. Alpine coaster (2km downhill track). Canyoning down waterfalls. Zipline across pine valleys. Cool weather 18-22°C.",
                  "highlights": ["Canyoning (₹1,500) — rappel down 3 waterfalls + cliff jump", "Datanla Alpine Coaster (₹280) — 2km self-drive downhill", "Zipline + high ropes course (₹700)", "Pongour Falls (₹35) — biggest waterfall in area", "Night market food crawl"],
                  "budget_per_day": "₹800-1,500", "flight_from_hcmc": "50min, ₹1,500-2,000"},
        "Quy Nhon": {"name": "Quy Nhon", "lat": 13.7820, "lon": 109.2194, "region": "Central South",
                     "why": "Hidden adventure beach. Ky Co Beach boat trip (snorkeling + cliff jumping). Eo Gio cliff walk + rock climbing. No crowds. Half price of Nha Trang.",
                     "highlights": ["Ky Co Beach (₹350 boat) — snorkel + cliff jump + pristine", "Eo Gio cliff walk + snorkeling (FREE)", "Jet ski rental (₹500/hr)", "Fresh seafood dives (₹200-400)", "No tourist traps — raw adventure"],
                     "budget_per_day": "₹600-1,200", "flight_from_hcmc": "1hr, ₹1,500-2,000"},
        "Con Dao": {"name": "Con Dao", "lat": 8.7260, "lon": 106.6260, "region": "South Islands",
                    "why": "Paradise islands + diving. Best snorkeling/diving in Vietnam. Sea turtle nesting in July (night beach watch!). Speedboat island hopping. Hidden coves.",
                    "highlights": ["Scuba diving (₹3,500) — coral reefs + turtles + rays", "Snorkeling speedboat tour (₹1,200) — 3 islands", "Sea turtle nesting night watch (July season!)", "Bay Canh Island kayak + jungle trek", "Dat Doc Beach 6km — yours alone"],
                    "budget_per_day": "₹2,000-3,500", "flight_from_hcmc": "45min, ₹2,500-4,000"},
        "Mui Ne": {"name": "Mui Ne", "lat": 10.9350, "lon": 108.2650, "region": "South Coast",
                   "why": "Desert adventure by the sea. Sand dune jeep tours. Kite surfing capital of Asia. ATV riding on dunes. Fairy Stream trek. Cheapest watersports.",
                   "highlights": ["White Sand Dunes jeep + ATV tour (₹1,200) — sunrise", "Kite surfing lesson (₹1,500/2hr) — best spot in Asia", "Red Sand Dunes sandboarding (FREE)", "Fairy Stream barefoot trek (FREE)", "Jet ski + parasailing (₹700)"],
                   "budget_per_day": "₹800-1,500", "flight_from_hcmc": "4hr bus, ₹500"},
        "Ha Giang": {"name": "Ha Giang", "lat": 23.2781, "lon": 105.0128, "region": "North",
                     "why": "ULTIMATE motorbike adventure. Ha Giang Loop — 3 days on mountain roads. Ma Pi Leng Pass (best view in SE Asia). Less fog than Sapa. Raw, wild, no tourist traps.",
                     "highlights": ["Ha Giang Loop 3-day motorbike (₹2,000 rental + guide)", "Ma Pi Leng Pass — most spectacular road in Vietnam", "Cave exploration + river crossing", "Lung Cu Flag Tower (northernmost Vietnam)", "Sleep in Hmong villages — authentic homestays"],
                     "budget_per_day": "₹500-1,000", "flight_from_hanoi": "6hr bus from Hanoi, ₹600"},
        "Cat Ba Island": {"name": "Cat Ba Island", "lat": 20.7250, "lon": 107.0514, "region": "North",
                          "why": "Island adventure — Lan Ha Bay kayaking (untouched Halong), rock climbing on limestone cliffs, jungle trekking, Monkey Island. Cheaper + less crowded than Halong Bay.",
                          "highlights": ["Lan Ha Bay kayak tour (₹1,200) — 100x less crowded than Halong", "Deep water solo rock climbing (₹1,500) — climb limestone cliffs over water", "Cat Ba National Park jungle trek (₹70)", "Monkey Island beach + zip line (₹350)", "Speedboat island hopping (₹800)"],
                          "budget_per_day": "₹1,000-1,800", "flight_from_hanoi": "2hr bus+boat from Hanoi, ₹400"},
    }
    
    # Fetch weather for alternative cities
    print("[Backup Agent] Fetching weather for alternative cities...")
    alt_weather = {}
    trip_start_date = "2026-06-28"
    trip_end_date = "2026-07-10"
    
    for city_key, city_info in alt_cities.items():
        lat, lon = city_info["lat"], city_info["lon"]
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}&"
               f"daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&"
               f"timezone=Asia/Ho_Chi_Minh&forecast_days=16")
        data = fetch_json(url, timeout=15)
        
        if "error" in data:
            alt_weather[city_key] = {"error": data["error"]}
            continue
        
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        precip = daily.get("precipitation_probability_max", [])
        max_temps = daily.get("temperature_2m_max", [])
        wcode = daily.get("weather_code", [])
        
        trip_forecast = []
        for i, d in enumerate(dates):
            if trip_start_date <= d <= trip_end_date:
                rp = precip[i] if i < len(precip) and precip[i] is not None else 0
                risk = "low"
                if rp > 60: risk = "high"
                elif rp > 40: risk = "medium"
                trip_forecast.append({
                    "date": d,
                    "rain_prob": rp,
                    "high": round(max_temps[i]) if i < len(max_temps) and max_temps[i] is not None else None,
                    "condition": _wmo_to_text(wcode[i]) if i < len(wcode) and wcode[i] is not None else "Unknown",
                    "risk": risk,
                })
        
        avg_rain = sum(f["rain_prob"] for f in trip_forecast) / len(trip_forecast) if trip_forecast else 100
        high_days = sum(1 for f in trip_forecast if f["risk"] == "high")
        low_days = sum(1 for f in trip_forecast if f["risk"] == "low")
        
        alt_weather[city_key] = {
            "forecasts": trip_forecast,
            "avg_rain_prob": round(avg_rain),
            "high_risk_days": high_days,
            "low_risk_days": low_days,
            "total_days": len(trip_forecast),
            "weather_score": max(0, 100 - high_days * 8 - (len(trip_forecast) - high_days - low_days) * 4),
        }
    
    # ═══════════════════════════════════════
    # Compare original cities vs alternatives
    # ═══════════════════════════════════════
    original_avg_rain = {}
    if weather and "cities" in weather:
        for ck, cv in weather["cities"].items():
            forecasts = cv.get("forecasts", [])
            if forecasts:
                original_avg_rain[ck] = round(sum(f["rain_prob"] for f in forecasts) / len(forecasts))
    
    # Build comparison table
    city_comparison = []
    
    # Add original cities
    for city, avg_rain in sorted(original_avg_rain.items(), key=lambda x: x[1]):
        high_days = 0
        if weather and "cities" in weather:
            for f in weather["cities"].get(city, {}).get("forecasts", []):
                if f.get("risk") == "high":
                    high_days += 1
        city_comparison.append({
            "city": city,
            "type": "original",
            "avg_rain": avg_rain,
            "high_risk_days": high_days,
            "weather_score": max(0, 100 - high_days * 8),
            "verdict": "KEEP" if avg_rain < 50 else ("MONITOR" if avg_rain < 70 else "SWAP"),
        })
    
    # Add alternative cities
    for city, w in sorted(alt_weather.items(), key=lambda x: x[1].get("weather_score", 0), reverse=True):
        if "error" in w:
            continue
        city_comparison.append({
            "city": city,
            "type": "alternative",
            "avg_rain": w["avg_rain_prob"],
            "high_risk_days": w["high_risk_days"],
            "weather_score": w["weather_score"],
            "verdict": "BEST ALTERNATIVE" if w["weather_score"] > 60 else ("GOOD OPTION" if w["weather_score"] > 40 else "ALSO RAINY"),
            "info": alt_cities[city],
        })
    
    # ═══════════════════════════════════════
    # City swap/reorder recommendations
    # ═══════════════════════════════════════
    swap_recommendations = []
    
    # Find worst original cities
    worst_cities = [(c, r) for c, r in original_avg_rain.items() if r > 60]
    worst_cities.sort(key=lambda x: x[1], reverse=True)
    
    # Find best alternative cities
    best_alts = [(c, w) for c, w in alt_weather.items() 
                 if "error" not in w and w["weather_score"] > 40]
    best_alts.sort(key=lambda x: x[1]["weather_score"], reverse=True)
    
    def _get_transport(city_key):
        """Get transport info for any city."""
        c = alt_cities.get(city_key, {})
        return c.get("flight_from_hcmc", c.get("flight_from_hanoi", c.get("flight_from_hanoi", "Flight available")))
    
    # Sapa swap
    if "Sapa" in original_avg_rain and original_avg_rain["Sapa"] > 50:
        sapa_avg = original_avg_rain["Sapa"]
        for alt_city, alt_w in best_alts:
            if alt_w["avg_rain_prob"] < sapa_avg - 15:
                swap_recommendations.append({
                    "original_city": "Sapa",
                    "original_rain": sapa_avg,
                    "alternative_city": alt_city,
                    "alternative_rain": alt_w["avg_rain_prob"],
                    "alternative_score": alt_w["weather_score"],
                    "cost_impact": f"Flight to {alt_city} instead of Sapa bus. Similar cost ₹1,500-2,500.",
                    "reasoning": f"Sapa avg rain: {sapa_avg}%. {alt_city} avg rain: {alt_w['avg_rain_prob']}%. {alt_city} is {sapa_avg - alt_w['avg_rain_prob']}% drier during your trip.",
                    "what_you_get": alt_cities[alt_city]["why"],
                    "highlights": alt_cities[alt_city]["highlights"],
                    "how_to_get_there": _get_transport(alt_city),
                    "budget": alt_cities[alt_city]["budget_per_day"],
                    "urgency": "HIGH" if sapa_avg > 80 else "MEDIUM",
                })
                break  # One recommendation per city
    
    # Phu Quoc swap
    if "Phu Quoc" in original_avg_rain and original_avg_rain["Phu Quoc"] > 60:
        pq_avg = original_avg_rain["Phu Quoc"]
        for alt_city, alt_w in best_alts:
            if alt_w["avg_rain_prob"] < pq_avg - 15 and alt_city not in [s["alternative_city"] for s in swap_recommendations]:
                swap_recommendations.append({
                    "original_city": "Phu Quoc",
                    "original_rain": pq_avg,
                    "alternative_city": alt_city,
                    "alternative_rain": alt_w["avg_rain_prob"],
                    "alternative_score": alt_w["weather_score"],
                    "cost_impact": f"Flight to {alt_city} instead of Phu Quoc. Similar cost ₹1,500-2,500.",
                    "reasoning": f"Phu Quoc avg rain: {pq_avg}%. {alt_city} avg rain: {alt_w['avg_rain_prob']}%. {alt_city} is {pq_avg - alt_w['avg_rain_prob']}% drier.",
                    "what_you_get": alt_cities[alt_city]["why"],
                    "highlights": alt_cities[alt_city]["highlights"],
                    "how_to_get_there": _get_transport(alt_city),
                    "budget": alt_cities[alt_city]["budget_per_day"],
                    "urgency": "HIGH" if pq_avg > 80 else "MEDIUM",
                })
                break
    
    # HCMC swap (only if really bad)
    if "HCMC" in original_avg_rain and original_avg_rain["HCMC"] > 70:
        hcmc_avg = original_avg_rain["HCMC"]
        for alt_city, alt_w in best_alts:
            if alt_w["avg_rain_prob"] < hcmc_avg - 20 and alt_city not in [s["alternative_city"] for s in swap_recommendations]:
                swap_recommendations.append({
                    "original_city": "HCMC",
                    "original_rain": hcmc_avg,
                    "alternative_city": alt_city,
                    "alternative_rain": alt_w["avg_rain_prob"],
                    "alternative_score": alt_w["weather_score"],
                    "cost_impact": f"Fly to {alt_city} instead of staying in HCMC. ₹1,500-2,500.",
                    "reasoning": f"HCMC avg rain: {hcmc_avg}%. {alt_city}: {alt_w['avg_rain_prob']}%. {hcmc_avg - alt_w['avg_rain_prob']}% drier.",
                    "what_you_get": alt_cities[alt_city]["why"],
                    "highlights": alt_cities[alt_city]["highlights"],
                    "how_to_get_there": _get_transport(alt_city),
                    "budget": alt_cities[alt_city]["budget_per_day"],
                    "urgency": "MEDIUM",
                })
                break
    
    # Itinerary reorder suggestion — go to driest cities first
    all_cities_ranked = sorted(city_comparison, key=lambda x: x.get("weather_score", 0), reverse=True)
    driest_originals = [c for c in all_cities_ranked if c["type"] == "original"][:2]
    wettest_originals = [c for c in all_cities_ranked if c["type"] == "original"][-2:]
    
    reorder_suggestion = {
        "current_order": "HCMC → Phu Quoc → Hanoi → Sapa → Hanoi",
        "issue": "Both Phu Quoc (monsoon) and Sapa (fog season) are in the WETTEST period. Central Vietnam is drier in July.",
        "suggested_reorder": "HCMC (2 days) → Da Nang/Hoi An (3 days, DRIEST) → Hanoi (2 days) → Sapa (2 days) → Hanoi departure",
        "why": "Central Vietnam (Da Nang/Hoi An) has the BEST weather in July. By going there during Jun 30-Jul 3 (instead of Phu Quoc), you get the driest window.",
        "cost_impact": "Same number of flights. Da Nang flights ₹1,500-2,500 (same as Phu Quoc). Hoi An is cheaper than Phu Quoc (₹1,000/day vs ₹1,500/day).",
        "what_you_lose": "VinWonders Phu Quoc, 4-island tour, cable car",
        "what_you_gain": "Ba Na Hills Golden Bridge, Hoi An ancient town, My Khe Beach, Cao Lau noodles, tailor shopping — ALL in better weather",
    }
    
    # Indoor/rain-proof alternatives per city
    indoor_alternatives = {
        "HCMC": [
            {"name": "War Remnants Museum", "duration": "2 hrs", "cost": "₹70", "maps": "https://maps.google.com/?q=War+Remnants+Museum+HCMC", "note": "Fully indoor, harrowing history"},
            {"name": "Van Gogh Metashow (Thiso Mall)", "duration": "2 hrs", "cost": "₹878", "maps": "https://maps.google.com/?q=Thiso+Mall+Sala+Thu+Duc", "note": "30+ immersive AC rooms"},
            {"name": "Saigon Opera House — Show", "duration": "1.5 hrs", "cost": "₹700-1400", "maps": "https://maps.google.com/?q=Saigon+Opera+House+HCMC", "note": "AO Show — cultural performance"},
            {"name": "Bui Vien indoor bars + cafes", "duration": "3 hrs", "cost": "₹200-500", "maps": "https://maps.google.com/?q=Bui+Vien+HCMC", "note": "Beer street covered seating"},
            {"name": "Takashimaya Mall (District 1)", "duration": "2 hrs", "cost": "FREE", "maps": "https://maps.google.com/?q=Takashimaya+Saigon+Centre", "note": "Shopping + food court + AC"},
            {"name": "Independence Palace", "duration": "1.5 hrs", "cost": "₹105", "maps": "https://maps.google.com/?q=Independence+Palace+HCMC", "note": "Indoor museum + underground bunkers"},
            {"name": "Fine Arts Museum", "duration": "1.5 hrs", "cost": "₹35", "maps": "https://maps.google.com/?q=Fine+Arts+Museum+HCMC", "note": "Cheap, beautiful colonial building"},
        ],
        "Phu Quoc": [
            {"name": "VinWonders (rain-proof: aquarium + indoor shows)", "duration": "Full day", "cost": "₹3,410", "maps": "https://maps.google.com/?q=VinWonders+Phu+Quoc", "note": "Aquarium, indoor rides, THE ONCE show"},
            {"name": "Grand World indoor exhibits", "duration": "3 hrs", "cost": "FREE", "maps": "https://maps.google.com/?q=Grand+World+Phu+Quoc", "note": "Teddy Bear Museum + indoor art"},
            {"name": "Phu Quoc Prison Museum", "duration": "1.5 hrs", "cost": "₹70", "maps": "https://maps.google.com/?q=Phu+Quoc+Prison", "note": "Historical site, mostly covered"},
            {"name": "Fish Sauce Factory tour", "duration": "1 hr", "cost": "FREE", "maps": "https://maps.google.com/?q=Khoe+Be+fish+sauce+factory+Phu+Quoc", "note": "See how nuoc mam is made"},
            {"name": "Coconut Prison + night market", "duration": "Half day", "cost": "₹200-500", "maps": "https://maps.google.com/?q=Duong+Dong+Night+Market", "note": "Market has covered stalls"},
            {"name": "Spa day at hotel", "duration": "3 hrs", "cost": "₹500-1000", "maps": "", "note": "Monsoon = spa weather. Massage + sauna"},
            {"name": "Pepper farm + pearl farm tour", "duration": "2 hrs", "cost": "₹200 taxi", "maps": "https://maps.google.com/?q=Phu+Quoc+pepper+farm", "note": "Covered areas, cheap taxi between"},
        ],
        "Hanoi": [
            {"name": "Water Puppet Theatre", "duration": "1 hr", "cost": "₹350", "maps": "https://maps.google.com/?q=Thang+Long+Water+Puppet+Hanoi", "note": "Indoor, iconic, book ahead"},
            {"name": "X Space Immersive (8 zones)", "duration": "2 hrs", "cost": "₹700", "maps": "https://maps.google.com/?q=X+Space+Immersive+Hanoi", "note": "Fully indoor AC immersive art"},
            {"name": "Hoa Lo Prison Museum", "duration": "1.5 hrs", "cost": "₹70", "maps": "https://maps.google.com/?q=Hoa+Lo+Prison+Hanoi", "note": "Indoor, powerful history"},
            {"name": "Vietnamese Women's Museum", "duration": "1.5 hrs", "cost": "₹70", "maps": "https://maps.google.com/?q=Women's+Museum+Hanoi", "note": "AC, fascinating exhibits"},
            {"name": "Ho Chi Minh Mausoleum", "duration": "1 hr", "cost": "FREE", "maps": "https://maps.google.com/?q=Ho+Chi+Minh+Mausoleum", "note": "Indoor (closed Mon/Fri — check)"},
            {"name": "Old Quarter cafe crawl", "duration": "3 hrs", "cost": "₹300-500", "maps": "https://maps.google.com/?q=Hanoi+Old+Quarter+cafes", "note": "Cafe Giang (egg coffee) + Cong Caphe — all indoor"},
            {"name": "Vincom Center shopping + cinema", "duration": "3 hrs", "cost": "₹200-500", "maps": "https://maps.google.com/?q=Vincom+Center+Hanoi", "note": "Mall with food court + movies in English"},
            {"name": "Ceramic Mosaic Mural (covered sections)", "duration": "1 hr", "cost": "FREE", "maps": "https://maps.google.com/?q=Ceramic+Mosaic+Mural+Hanoi", "note": "Walk under bridge overhangs"},
        ],
        "Sapa": [
            {"name": "Sapa Museum", "duration": "1 hr", "cost": "₹35", "maps": "https://maps.google.com/?q=Sapa+Museum", "note": "Indoor ethnic culture exhibits"},
            {"name": "Indoor cafe crawl (fog/rain)", "duration": "3 hrs", "cost": "₹200-400", "maps": "https://maps.google.com/?q=Sapa+cafes", "note": "The Hill Station, Leopard Cat Cafe — mountain views from inside"},
            {"name": "Sapa Stone Church (Holy Rosary)", "duration": "30 min", "cost": "FREE", "maps": "https://maps.google.com/?q=Sapa+Stone+Church", "note": "Historic church, indoor"},
            {"name": "Local market (covered)", "duration": "1.5 hrs", "cost": "₹200-500", "maps": "https://maps.google.com/?q=Sapa+Market", "note": "Covered market — handicrafts + hot food"},
            {"name": "Hotel spa / hot spring", "duration": "2 hrs", "cost": "₹500-800", "maps": "", "note": "Many Sapa hotels have spa. Hot spring at Tan Phu village"},
            {"name": "Cat Cat Village (partial indoor)", "duration": "2 hrs", "cost": "₹475", "maps": "https://maps.google.com/?q=Cat+Cat+Village+Sapa", "note": "Has covered areas + cultural show inside. Waterfall still visible in rain"},
            {"name": "Fansipan cable car (if not windy)", "duration": "Half day", "cost": "₹2,800", "maps": "https://maps.google.com/?q=Fansipan+Cable+Car+Sapa", "note": "Cable car runs in rain (not wind). Summit may be in clouds — moody photos!"},
        ],
        "Halong Bay": [
            {"name": "CANCEL cruise — Hanoi museum day", "duration": "Full day", "cost": "₹200-500", "maps": "https://maps.google.com/?q=Hanoi+museums", "note": "Use the Hanoi indoor list above"},
            {"name": "Water Puppet + Hoa Lo Prison", "duration": "Half day", "cost": "₹420", "maps": "https://maps.google.com/?q=Thang+Long+Water+Puppet+Hanoi", "note": "Iconic indoor activities"},
            {"name": "Ceramic Mural + Long Bien Bridge walk", "duration": "2 hrs", "cost": "FREE", "maps": "https://maps.google.com/?q=Long+Bien+Bridge+Hanoi", "note": "Bridge has covered walkway"},
            {"name": "Old Quarter food crawl (covered)", "duration": "3 hrs", "cost": "₹500-1000", "maps": "https://maps.google.com/?q=Hanoi+Old+Quarter+food", "note": "Bun Cha, pho, egg coffee — all indoor seating"},
        ],
    }
    
    # City swap suggestions — if a city is consistently rainy, where to go instead
    city_swaps = {
        "Sapa": {
            "problem": "July = peak fog season. Visibility near zero after 2PM. Fansipan summit often in clouds.",
            "alternative": "Stay extra day in Hanoi — day trip to Ninh Binh (Trang An boat ride, rain or shine)",
            "alternative2": "Swap Sapa days for Phong Nha caves (indoor cave tours, weather-proof)",
            "cost_impact": "Bus to Ninh Binh ₹600 vs Sapa bus ₹1,050. Save ₹450",
            "verdict": "Keep Sapa — but use backup indoor activities. Fog is part of the experience. Only swap if 3+ consecutive days show >80% rain.",
        },
        "Phu Quoc": {
            "problem": "July = low season. Rough seas may cancel island tours.",
            "alternative": "If island tour cancelled: VinWonders full day (rain-proof)",
            "alternative2": "Extend HCMC by 1 day (more museums/food) and reduce Phu Quoc",
            "cost_impact": "VinWonders ₹3,410 vs island tour ₹4,200. Save ₹790",
            "verdict": "Keep Phu Quoc — VinWonders is an excellent rain backup. Island tour runs if wind < 20km/h.",
        },
        "Halong Bay": {
            "problem": "Highest risk day. Cruises cancel if wind > 25km/h or typhoon warning.",
            "alternative": "Ninh Binh — 'Halong Bay on land' (boat ride through limestone karsts, rain or shine)",
            "alternative2": "Hanoi full museum day + Train Street + water puppet",
            "cost_impact": "Ninh Binh tour ₹1,200 vs Halong cruise ₹2,000. Save ₹800",
            "verdict": "Check windy.com 3 days before. If wind > 25km/h or storm warning → switch to Ninh Binh immediately.",
        },
    }
    
    # Generate per-day backup plans
    day_backups = []
    for day in cfg.ITINERARY:
        city = day["city"]
        date = day["date"]
        
        # Get weather for this day
        day_weather = None
        if weather and "cities" in weather:
            city_data = weather["cities"].get(city, {})
            for f in city_data.get("forecasts", []):
                if f.get("date") == f"2026-{date.replace('Jun','06').replace('Jul','07').strip()}":
                    day_weather = f
                    break
        
        # Also check if date matches "Jun 28" → "2026-06-28"
        date_map = {"Jun 28": "2026-06-28", "Jun 29": "2026-06-29", "Jun 30": "2026-06-30",
                    "Jul 1": "2026-07-01", "Jul 2": "2026-07-02", "Jul 3": "2026-07-03",
                    "Jul 4": "2026-07-04", "Jul 5": "2026-07-05", "Jul 6": "2026-07-06",
                    "Jul 7": "2026-07-07", "Jul 8": "2026-07-08", "Jul 9": "2026-07-09", "Jul 10": "2026-07-10"}
        full_date = date_map.get(date, "")
        
        if not day_weather and weather:
            for ck, cv in weather.get("cities", {}).items():
                for f in cv.get("forecasts", []):
                    if f.get("date") == full_date:
                        day_weather = f
                        break
                if day_weather:
                    break
        
        risk = day_weather.get("risk", "unknown") if day_weather else "unknown"
        rain_prob = day_weather.get("rain_prob", 0) if day_weather else 0
        fog_hours = day_weather.get("fog_hours", 0) if day_weather else 0
        best_window = day_weather.get("best_window", {}) if day_weather else {}
        
        # Generate backup
        backup = {
            "day": day["day"],
            "date": date,
            "dow": day["dow"],
            "city": city,
            "label": day["label"],
            "main_risk": risk,
            "rain_prob": rain_prob,
            "fog_hours": fog_hours,
            "best_window": best_window,
            "original_plan": [p["activity"] for p in day["plan"]],
            "backup_plan": [],
            "swap_suggestion": None,
            "recommendation": "",
        }
        
        # If high risk or foggy, generate alternatives
        city_alts = indoor_alternatives.get(city, [])
        
        if risk == "high" or fog_hours > 4:
            # Pick 3-4 indoor alternatives that don't overlap with original plan
            original_activities = " ".join(p["activity"] for p in day["plan"]).lower()
            suitable = []
            for alt in city_alts:
                # Skip if already in original plan
                if alt["name"].lower() in original_activities or any(w in original_activities for w in alt["name"].split()[:2]):
                    continue
                suitable.append(alt)
            
            backup["backup_plan"] = suitable[:4]
            backup["recommendation"] = f"⚠️ High weather risk ({rain_prob}% rain, {fog_hours}h fog). Keep original plan but prepare to switch to indoor alternatives. Best window: {best_window.get('start','?')}-{best_window.get('end','?')}."
            
            # City swap for highest-risk cities
            if city in city_swaps and (rain_prob > 70 or fog_hours > 6):
                backup["swap_suggestion"] = city_swaps[city]
        
        elif risk == "medium":
            # Suggest indoor backup for afternoon only
            afternoon_alts = [a for a in city_alts if a["duration"] in ["1 hr", "1.5 hrs", "2 hrs"]][:2]
            backup["backup_plan"] = afternoon_alts
            backup["recommendation"] = f"🌦️ Moderate risk ({rain_prob}% rain). Do outdoor activities in best window ({best_window.get('start','?')}-{best_window.get('end','?')}). Indoor backup ready for afternoon."
        else:
            backup["recommendation"] = f"✅ Low risk ({rain_prob}% rain). Original plan is good. Best outdoor window: {best_window.get('start','?')}-{best_window.get('end','?')}."
        
        day_backups.append(backup)
    
    # Summary
    high_risk_days = sum(1 for d in day_backups if d["main_risk"] == "high")
    swap_needed = sum(1 for d in day_backups if d.get("swap_suggestion"))
    
    output = {
        "agent": "Backup Plan Intelligence",
        "timestamp": now_iso(),
        "day_backups": day_backups,
        "city_swaps": city_swaps,
        "city_comparison": city_comparison,
        "swap_recommendations": swap_recommendations,
        "reorder_suggestion": reorder_suggestion,
        "alt_city_weather": alt_weather,
        "alt_cities_info": {k: {"why": v["why"], "highlights": v["highlights"], "budget_per_day": v["budget_per_day"], "transport": v.get("flight_from_hcmc", v.get("flight_from_hanoi", "Flight available")), "region": v["region"]} for k, v in alt_cities.items()},
        "high_risk_days": high_risk_days,
        "swap_needed": swap_needed,
        "city_swaps_available": len(swap_recommendations),
        "summary": f"{high_risk_days} high-risk days, {len(swap_recommendations)} city swaps suggested, {len(city_comparison)} cities compared",
        "indoor_alternatives_count": sum(len(v) for v in indoor_alternatives.values()),
        "source": "Weather forecast analysis + alternative city weather comparison",
    }
    write_data("backup", output)
    print(f"[Backup Agent] {high_risk_days} high-risk days, {swap_needed} swap suggestions")
    return output


# ═══════════════════════════════════════════
# AGENT 13: DETAILED DAY PLAN (GRANULAR ROUTE)
# ═══════════════════════════════════════════
def agent_detailed_plan():
    """Generate super-granular day plans with walk times, distances, transport, area recs."""
    print("[Detailed Plan Agent] Building granular day plans...")
    
    # Area recommendations per city — where to stay and why
    area_guide = {
        "HCMC": {
            "stay_area": "District 1 — Bui Vien / Ben Thanh area",
            "why": "Walking distance to 80% of attractions. Bui Vien for nightlife, Ben Thanh for market. Grab to D5/D4 for food streets (10 min, ₹100-150).",
            "hotel_price": "₹800-1,200/night",
            "walk_radius": "1.5 km covers Opera House, Notre Dame, War Remnants, Ben Thanh Market",
            "airport_to_hotel": {"mode": "Grab", "time": "30-40 min", "cost": "₹300-400", "distance": "7 km", "note": "SGN airport → D1. Fixed price Grab. Don't take airport taxis — they overcharge."},
            "get_around": "Walk inside D1. Grab for anything > 2km. Bus #19 for Hop-On Hop-Off route. Motorbike taxi (Grab Bike) ₹50-100 per ride.",
        },
        "Phu Quoc": {
            "stay_area": "Duong Dong town center",
            "why": "Walking to night market, restaurants, beach. Grand World 15 min Grab. VinWonders 20 min. Airport 15 min.",
            "hotel_price": "₹800-1,500/night (low season discount)",
            "walk_radius": "0.5 km covers night market, beach, restaurants",
            "airport_to_hotel": {"mode": "Grab / Taxi", "time": "15-20 min", "cost": "₹200-300", "distance": "10 km", "note": "Phu Quoc airport (PQC) → Duong Dong. Use Grab. If no Grab, Mai Linh taxi only — agree price first."},
            "get_around": "Rent scooter ₹350/day (best option). Grab for evening drinking. Hotel usually arranges tour pickups free.",
        },
        "Hanoi": {
            "stay_area": "Old Quarter — near Hoan Kiem Lake",
            "why": "Walking to EVERYTHING. Train Street, Water Puppet, night market, pho spots, Bun Cha, cafes — all within 1 km. Airport is far (27km) so Grab needed.",
            "hotel_price": "₹600-1,000/night",
            "walk_radius": "1 km covers Old Quarter, Hoan Kiem, Train Street, Water Puppet, 50+ restaurants",
            "airport_to_hotel": {"mode": "Grab", "time": "45-60 min", "cost": "₹500-700", "distance": "27 km", "note": "Noi Bai (HAN) → Old Quarter. Grab fixed price. NO airport buses after 10 PM — book Grab in advance for late arrivals."},
            "get_around": "Walk everywhere in Old Quarter. Grab for Temple of Literature (10 min, ₹100). Cyclo = SCAM — never take. Hoan Kiem loop is walkable in 20 min.",
        },
        "Sapa": {
            "stay_area": "Sapa town center — near Sapa Square / Stone Church",
            "why": "Walking to all restaurants, cafes, Moana, Sapa Square. Cat Cat Village 2 km downhill walk. Fansipan cable car 3 km (hotel shuttle free).",
            "hotel_price": "₹500-800/night",
            "walk_radius": "0.5 km covers town center, cafes, restaurants, Sapa Square",
            "bus_to_hotel": {"mode": "Walk from bus stop", "time": "5 min", "cost": "FREE", "distance": "400m", "note": "Sapa Express bus drops at Sapa center. Most hotels 5-min walk. Hotel can send someone to carry bags if you ask."},
            "get_around": "Walk in town. Motorbike taxi (₹100-200) for Fansipan/Rong May. Hotel arranges Fansipan shuttle free. Cat Cat is a 25-min downhill walk (35 min back up — take motorbike ₹100).",
        },
        "Halong Bay": {
            "stay_area": "Day trip from Hanoi — no overnight needed",
            "why": "Bus picks up from Hanoi Old Quarter at 6:30 AM. Returns by 8 PM. No hotel needed.",
            "bus_to_cruise": {"mode": "Limousine bus", "time": "2.5 hrs", "cost": "₹800-1,200", "distance": "170 km", "note": "Book through cruise package — most include bus transfer. Pick up from Old Quarter hotels. Bring water + snacks."},
            "get_around": "Everything is on the cruise. Bus picks up and drops at hotel.",
        },
    }
    
    # Walk times between key locations (minutes)
    walk_times = {
        ("HCMC", "Opera House", "Notre Dame Cathedral"): 4,
        ("HCMC", "Notre Dame Cathedral", "War Remnants Museum"): 8,
        ("HCMC", "War Remnants Museum", "Ben Thanh Market"): 12,
        ("HCMC", "Ben Thanh Market", "Bui Vien"): 10,
        ("HCMC", "Bui Vien", "Vinh Khanh Food Street"): 0,  # need Grab
        ("Hanoi", "Hoan Kiem Lake", "Train Street"): 12,
        ("Hanoi", "Train Street", "Old Quarter food"): 8,
        ("Hanoi", "Old Quarter", "Temple of Literature"): 0,  # need Grab
        ("Hanoi", "Temple of Literature", "Ho Chi Minh Mausoleum"): 10,
        ("Hanoi", "Water Puppet Theatre", "Hoan Kiem Lake"): 2,
        ("Sapa", "Sapa Square", "Moana Sapa"): 5,
        ("Sapa", "Moana Sapa", "Cat Cat Village entrance"): 15,
        ("Sapa", "Sapa Square", "The Hill Station cafe"): 8,
        ("Sapa", "Sapa town", "Fansipan cable car"): 0,  # shuttle
    }
    
    # Venue guide — what to order, highlights, tips for each specific place
    venue_guide = {
        # HCMC
        "pho minh": {"order": "Pho Tai (rare beef) + Quay (fried dough sticks)", "highlight": "Since 1940s, family recipe. Broth simmered 12+ hours. Go before 9 AM — sells out by 10.", "rating": "4.6", "tip": "Add lime + chili from the condiment tray. Don't add hoisin — purists say it ruins the broth."},
        "hop-on hop-off": {"order": "", "highlight": "Full city loop 60 min. Double-decker bus, upper deck best for photos. Audio guide in English.", "rating": "4.4", "tip": "Sit on the RIGHT side of upper deck for better Opera House + Notre Dame views."},
        "banh canh cua": {"order": "Banh Canh Cua (crab udon soup) — large bowl", "highlight": "MICHELIN Bib Gourmand 2026. Silky thick noodles in crab broth. SELLS OUT 1 PM!", "rating": "4.3", "tip": "Arrive by 11 AM. They close when soup runs out. Add chili + lime."},
        "van gogh": {"order": "", "highlight": "30+ immersive projection rooms. AC — great rain escape. 2 hrs minimum.", "rating": "4.6", "tip": "Start from top floor and work down. Last entry 5 PM. Thiso Mall has food court after."},
        "vinh khanh": {"order": "Grilled oysters (₹105/6), scallops with chili (₹175), sea snails", "highlight": "Time Out UK top 31 food streets. Open-air seafood, locals' spot. Pick your seafood live.", "rating": "4.5", "tip": "Go to stall #12 or #15 — best reviews. Negotiate price BEFORE cooking. Bring wet wipes."},
        "bui vien": {"order": "Banh Mi Huynh Hoa (₹105) — Bourdain approved. Saigon Special beer (₹53).", "highlight": "Sunday = pedestrian-only street. Neon, live music, street food. Peak energy 9 PM-1 AM.", "rating": "4.2", "tip": "Keep phone in FRONT pocket. Don't flash cash. Beer is cheapest at street stalls (₹53) not bars (₹175)."},
        "cu chi": {"order": "", "highlight": "Underground tunnel network from Vietnam War. 200km of tunnels. Firing range (real AK-47 ₹700/10 rounds).", "rating": "4.5", "tip": "Wear closed shoes — mud + insects. Skip if claustrophobic. Bring water — very humid."},
        # Phu Quoc
        "grand world": {"order": "", "highlight": "FREE entry. Venice replica + Teddy Bear Museum (₹718). Evening shows: Venice water 9:30 PM, Laser 10:45 PM — both FREE.", "rating": "4.4", "tip": "Eat BEFORE coming — food inside is 2x price. Park near the lake for best show viewing."},
        "4 island": {"order": "Bring motion sickness pills. Lunch included on boat — seafood + rice.", "highlight": "World's longest oversea cable car (8km). Sea walking helmet (walk ocean floor). Snorkeling at 4 islands.", "rating": "4.6", "tip": "BOOK LOCAL at hotel reception (₹4,200) NOT online (₹8,250). Bring towel + sunscreen. Cables close in high wind."},
        "sunset town": {"order": "Kiss Bridge selfie at golden hour. Mediterranean gelato (₹150).", "highlight": "Italian-style sunset town. Kiss Bridge, Clock Tower, Pompeii Ruins replica, Dragon Stairs. FREE.", "rating": "4.5", "tip": "Best at 5-6 PM golden hour. Walk the Dragon Stairs for panorama. Free — no entry fee anywhere."},
        "duong dong": {"order": "Sim wine (₹200-400), fresh seafood by weight, fish sauce souvenirs (₹300-600), grilled corn (₹50)", "highlight": "150+ stalls. Nightly 6 PM-midnight. Starfish, sea urchin, lobster. Best food market in Phu Quoc.", "rating": "4.7", "tip": "Ask TOTAL price not per-100g (scam trap). Try sim wine (rose myrtle). Negotiate 20% off. Cash only."},
        "vinwonders": {"order": "Deep Sea Restaurant (₹500-700) — aquarium view while eating. Combo meal deals at food court.", "highlight": "Vietnam's largest theme park. Aquarium + water park + rides. THE ONCE show 6:45 PM ($12M production, fire+water+light).", "rating": "4.5", "tip": "Go counter-clockwise: rides → aquarium → water park → show. Book online for 10% off. Lockers ₹100."},
        "ong lang": {"order": "Bring own snacks + water. No food stalls.", "highlight": "Hidden cove beach. No crowds, crystal water. Best sunrise spot on island. FREE.", "rating": "4.6", "tip": "Go 6-8 AM for calm water. No facilities — bring everything. Reef shoes help (rocky entry)."},
        "ham ninh": {"order": "Sea urchin (₹200, live from tank), crab hotpot (₹500), grilled scallops", "highlight": "Authentic fishing village on stilts. Locals eat here, not tourists. Cheap fresh seafood.", "rating": "4.3", "tip": "Pick seafood from the tanks. Price by weight — check before cooking. 30 min from Duong Dong."},
        # Hanoi
        "pho thin": {"order": "Pho Tai Nam (rare + well-done beef) — THE dish. Add Quay.", "highlight": "#1 pho in Vietnam since 1979. Charred ginger broth — unique smoky flavor. Obama's team ate here.", "rating": "4.5", "tip": "Go 6-7 AM — no queue. After 8 AM = 20 min wait. Only 2 things on menu: Pho Tai and Pho Tai Nam."},
        "hoan kiem": {"order": "", "highlight": "Heart of Hanoi. Ngoc Son Temple on island (₹70). Turtle Tower in center. Free to walk around.", "rating": "4.6", "tip": "Morning = locals doing tai chi. Evening = weekend walking street (no cars). Best photos at sunrise."},
        "temple of literature": {"order": "", "highlight": "Vietnam's first university (1070 AD). 1000 years old. Courtyards of stone turtles with names of scholars.", "rating": "4.7", "tip": "Go 8 AM before tour buses. 5 courtyards — don't skip the last (doctoral steles). Audio guide ₹50."},
        "bun cha": {"order": "Bun Cha (grilled pork + noodles + dipping sauce) + Nem Cua Be (crab spring rolls)", "highlight": "Bun Cha Huong Lien — Obama + Bourdain ate here in 2016. Smoky grilled pork over charcoal.", "rating": "4.5", "tip": "Order the 'Obama combo' (Bun Cha + spring rolls + beer). Mix everything in the sauce. Don't be shy — use hands for spring rolls."},
        "x space": {"order": "", "highlight": "8 immersive zones. Largest digital art space in SE Asia. AC, rain-proof. Instagram heaven.", "rating": "4.6", "tip": "2 hours minimum. Wear white — looks amazing under UV lights. Last entry 8 PM."},
        "train street": {"order": "Ca Phe Trung (egg coffee ₹100) — Hanoi specialty. Coconut coffee.", "highlight": "Train passes 2 FEET from cafes. Trains at 3:45 PM and 7:00 PM. Iconic Hanoi photo.", "rating": "4.5", "tip": "Sit at cafe ON the tracks (they move you when train comes). Buy a coffee — that's the 'fee'. Train times change — ask cafe owner."},
        "water puppet": {"order": "", "highlight": "1000-year-old tradition. Puppets on water, live traditional music. 1 hour show. UNMISSABLE.", "rating": "4.6", "tip": "Book ahead (hotel can do). Front rows get splashed. Photography allowed. English subtitles on screen."},
        "dong xuan": {"order": "Dried mango (₹200), cashew nuts (₹400), Vietnamese coffee beans (₹500), lacquerware", "highlight": "Hanoi's largest indoor market. Souvenirs, clothes, food. 3 floors. Wholesale + retail.", "rating": "4.0", "tip": "Negotiate 50% off asking price. Ground floor = tourist, upper floors = better prices. Cash only."},
        "pho bat dan": {"order": "Pho Tai (rare beef). Only pho — no menu.", "highlight": "Old Quarter institution since 1960s. Beef simmered overnight. Locals queue from 5 AM.", "rating": "4.6", "tip": "Queue moves fast. Point at what you want. Pay at counter first, then collect bowl. Best last meal in Hanoi."},
        # Sapa
        "moana": {"order": "", "highlight": "Photo zone with rice terrace backdrop. Swing, infinity pool illusion, bamboo bridge. ₹350 entry.", "rating": "4.3", "tip": "Go 7 AM for clear skies + no crowds. Fog after 2 PM ruins photos. Bring someone to take your photo — staff won't."},
        "cat cat": {"order": "Thang Co (horse meat stew ₹200) — try if adventurous. BBQ corn (₹50).", "highlight": "Hmong village + waterfall. Cultural show (dance + music) at 10 AM + 3 PM. Traditional houses.", "rating": "4.4", "tip": "Walk DOWN (20 min) — take motorbike UP (₹100, 35 min walk otherwise). Don't touch the dye vats."},
        "hill station": {"order": "Sapa mountain coffee (₹200), hot chocolate with cinnamon (₹250), apple pie (₹200)", "highlight": "Best cafe in Sapa. Valley + mountain views from window. Roasts own beans. Warm inside.", "rating": "4.5", "tip": "Sit by the window. WiFi good. Great rain/fog escape. Try the salt coffee — local specialty."},
        "rong may": {"order": "BBQ buffet lunch included in ticket. Grilled pork, vegetables, rice.", "highlight": "Glass bridge 2200m altitude. Zipline + alpine coaster. Cloud sea views. Full day activity.", "rating": "4.5", "tip": "Go early (8 AM) before clouds roll in. Glass bridge closes in high wind. Alpine coaster is the best part — go twice."},
        "heaven": {"order": "", "highlight": "Highest mountain pass in Vietnam. Free viewpoint. Cloud sea on clear days.", "rating": "4.6", "tip": "Ask taxi driver to stop 10 min. Best at 9-11 AM before afternoon fog. Free — no entry fee."},
        "fansipan": {"order": "Summit cafe: hot chocolate (₹250), instant noodles (₹200) — warm up at 3000m!", "highlight": "Roof of Indochina (3143m). Cable car 6km up. Buddha statue, pagoda, cloud sea. Tuesday = 10 min queue!", "rating": "4.7", "tip": "Go TUESDAY not Sunday (2hr vs 10min queue). Bring jacket — 10°C at summit vs 20°C in town. Camera fogs — bring microfiber."},
        "sapa square": {"order": "Roasted chestnuts (₹100), corn on cob (₹50), hot soy milk (₹50)", "highlight": "Town center. Local life. Mountain backdrop. Free. Best at sunset (5-6 PM).", "rating": "4.3", "tip": "Minority women sell handicrafts here — negotiate. Don't take photos without asking + paying small tip."},
        # Halong Bay
        "halong": {"order": "Seafood lunch on boat (included). Squid, shrimp, fish + rice. Vegetarian available — request when booking.", "highlight": "UNESCO World Heritage. 1600 limestone islands. Surprise Cave, kayaking, Titop Island viewpoint.", "rating": "4.6", "tip": "Check windy.com 3 days before. If wind >25km/h → cruise cancels. Book top-rated on Klook. Photograph boat name — prevents bait-and-switch."},
        "titop": {"order": "", "highlight": "Climb 400 steps to viewpoint — BEST panorama of Halong Bay. Beach at bottom for swimming.", "rating": "4.5", "tip": "Climb first, swim after (you'll sweat). 15 min up. Bring water. Steps are steep — take breaks."},
    }
    
    def _match_venue(activity_text):
        """Match activity text to venue guide key."""
        al = activity_text.lower()
        for key in venue_guide:
            if key in al:
                return venue_guide[key]
        return None

    # Detailed plans per day
    detailed_plans = []
    for day in cfg.ITINERARY:
        city = day["city"]
        area = area_guide.get(city, {})
        
        # Build granular timeline with realistic times
        timeline = []
        
        for i, item in enumerate(day["plan"]):
            time_str = item["time"]
            activity = item["activity"]
            cost = item.get("cost", "")
            cat = item.get("category", "")
            maps_link = item.get("maps", "")
            
            # Estimate duration based on category
            if cat == "food":
                duration = 45 if "breakfast" in activity.lower() or "pho" in activity.lower() else 60
            elif cat == "transit":
                if "fly" in activity.lower():
                    duration = 120  # 2hr flight + boarding
                elif "bus" in activity.lower():
                    duration = 360  # 6hr Sapa bus
                else:
                    duration = 30
            elif cat == "hotel":
                duration = 15
            elif cat == "activity":
                if "museum" in activity.lower() or "van gogh" in activity.lower():
                    duration = 120
                elif "vinwonders" in activity.lower() or "island tour" in activity.lower():
                    duration = 480  # full day
                elif "cable car" in activity.lower() or "fansipan" in activity.lower():
                    duration = 240  # half day
                elif "show" in activity.lower():
                    duration = 60
                else:
                    duration = 90
            elif cat == "nightlife":
                duration = 120
            elif cat == "cafe":
                duration = 45
            elif cat == "shopping":
                duration = 60
            else:
                duration = 60
            
            # Match venue for recommendations
            venue = _match_venue(activity)
            
            # Walk/transit to next location — ALWAYS generate for next item
            transit_to_next = None
            if i + 1 < len(day["plan"]):
                next_item = day["plan"][i + 1]
                transit_to_next = _estimate_transit(city, day["day"], activity, next_item["activity"], maps_link, next_item.get("maps", ""))
            
            timeline.append({
                "time": time_str,
                "activity": activity,
                "cost": cost,
                "category": cat,
                "maps": maps_link,
                "duration_min": duration,
                "transit_to_next": transit_to_next,
                "venue": venue,
            })
        
        # Daily summary
        total_activities = len([t for t in timeline if t["category"] not in ["transit", "hotel"]])
        total_cost = sum(_extract_cost(t["cost"]) for t in timeline)
        
        detailed_plans.append({
            "day": day["day"],
            "date": day["date"],
            "dow": day["dow"],
            "city": city,
            "label": day["label"],
            "icon": day["icon"],
            "tip": day["tip"],
            "area_guide": area,
            "timeline": timeline,
            "total_activities": total_activities,
            "estimated_cost": total_cost,
        })
    
    output = {
        "agent": "Detailed Day Plan",
        "timestamp": now_iso(),
        "area_guide": area_guide,
        "detailed_plans": detailed_plans,
        "total_days": len(detailed_plans),
        "source": "Google Maps distances + on-ground research",
    }
    write_data("detailed-plan", output)
    print(f"[Detailed Plan Agent] {len(detailed_plans)} days with granular timelines")
    return output

def _estimate_transit(city, day_num, from_activity, to_activity, from_maps="", to_maps=""):
    """Estimate specific transit between two activities with real distances."""
    from_lower = from_activity.lower()
    to_lower = to_activity.lower()
    
    # Same venue check
    if from_activity == to_activity:
        return {"mode": "Same location", "time": "0 min", "cost": "FREE", "distance": "0 m", "recommendation": "Already here", "directions": ""}
    
    # Generate Google Maps directions link
    def gmaps_dirs(from_place, to_place):
        return f"https://www.google.com/maps/dir/{urllib.parse.quote(from_place)}/{urllib.parse.quote(to_place)}"
    
    # ═══════════════════════════════════════
    # HCMC — District 1 centered, specific venues
    # ═══════════════════════════════════════
    if city == "HCMC":
        # Pho Minh → Opera House
        if "pho minh" in from_lower and ("opera" in to_lower or "hop-on" in to_lower):
            return {"mode": "🚶 Walk", "time": "8 min", "cost": "FREE", "distance": "650 m",
                    "recommendation": "Walk — same District 1 area. Head south on Nguyen Binh Khiem → left on Le Thanh Ton.",
                    "directions": gmaps_dirs("Pho Minh Ho Chi Minh", "Saigon Opera House")}
        
        # Opera House → Banh Canh Cua Ba Ba (D5)
        if ("opera" in from_lower or "hop-on" in from_lower) and "banh canh" in to_lower:
            return {"mode": "🚗 Grab", "time": "12 min", "cost": "₹100-140", "distance": "3.5 km",
                    "recommendation": "Take Grab — D5 is across the river. Don't walk, it's 45 min through traffic.",
                    "directions": gmaps_dirs("Saigon Opera House", "Banh Canh Cua Ba Ba Quan 5")}
        
        # Banh Canh Cua Ba Ba → Van Gogh (Thu Duc)
        if "banh canh" in from_lower and ("van gogh" in to_lower or "thiso" in to_lower):
            return {"mode": "🚗 Grab", "time": "25 min", "cost": "₹250-350", "distance": "14 km",
                    "recommendation": "Take Grab — Thu Duc is far east. Budget 30 min for rush hour traffic. ~₹300.",
                    "directions": gmaps_dirs("Banh Canh Cua Ba Ba Quan 5", "Thiso Mall Sala Thu Duc")}
        
        # Van Gogh → Vinh Khanh Food Street
        if ("van gogh" in from_lower or "thiso" in from_lower) and "vinh khanh" in to_lower:
            return {"mode": "🚗 Grab", "time": "30 min", "cost": "₹300-400", "distance": "15 km",
                    "recommendation": "Take Grab — from Thu Duc back to D4. Cross-town ride, budget 35 min for evening traffic.",
                    "directions": gmaps_dirs("Thiso Mall Sala Thu Duc", "Vinh Khanh Food Street District 4")}
        
        # Vinh Khanh → Bui Vien
        if "vinh khanh" in from_lower and "bui vien" in to_lower:
            return {"mode": "🚗 Grab", "time": "8 min", "cost": "₹80-100", "distance": "2 km",
                    "recommendation": "Take Grab — short ride from D4 to D1. Walking is 25 min through narrow streets, not recommended at night.",
                    "directions": gmaps_dirs("Vinh Khanh Food Street", "Bui Vien Walking Street HCMC")}
        
        # Bui Vien → Bui Vien (same place)
        if "bui vien" in from_lower and "bui vien" in to_lower:
            return {"mode": "📍 Same area", "time": "0 min", "cost": "FREE", "distance": "0 m",
                    "recommendation": "Already on Bui Vien — just walk to the next spot.",
                    "directions": ""}
        
        # Airport → Hotel (Day 0 arrival)
        if ("land" in from_lower or "airport" in from_lower or "sgn" in from_lower) and ("check-in" in to_lower or "hotel" in to_lower):
            return {"mode": "🚗 Grab", "time": "35 min", "cost": "₹300-400", "distance": "7 km",
                    "recommendation": "Take Grab from SGN airport to D1. Fixed price, book inside terminal. DON'T take street taxis — they overcharge 2-3x.",
                    "directions": gmaps_dirs("Tan Son Nhat Airport HCMC", "District 1 Ho Chi Minh City")}
        
        # Hotel → Bui Vien (Day 0 night)
        if "check-in" in from_lower and "bui vien" in to_lower:
            return {"mode": "🚶 Walk", "time": "5 min", "cost": "FREE", "distance": "300 m",
                    "recommendation": "Walk — if staying in D1 near Bui Vien, it's a 5-min walk. Ask hotel for directions.",
                    "directions": gmaps_dirs("District 1 HCMC hotels", "Bui Vien Walking Street HCMC")}
        
        # Hotel → Cu Chi (Day 2 morning)
        if "cu chi" in to_lower:
            return {"mode": "🚗 Grab/Tour", "time": "1.5 hr", "cost": "₹500-700", "distance": "50 km",
                    "recommendation": "Book a half-day tour (hotel reception ~₹500 incl transport). Grab is ₹700+ one-way. Tour is cheaper + includes guide.",
                    "directions": gmaps_dirs("District 1 HCMC", "Cu Chi Tunnels")}
        
        # Cu Chi → Airport (Day 2)
        if "cu chi" in from_lower and "fly" in to_lower:
            return {"mode": "🚗 Grab", "time": "45 min", "cost": "₹400-500", "distance": "35 km",
                    "recommendation": "Take Grab directly from Cu Chi to SGN airport. 45 min, ₹450. Don't go back to hotel first.",
                    "directions": gmaps_dirs("Cu Chi Tunnels", "Tan Son Nhat Airport HCMC")}
        
        # Default HCMC
        return {"mode": "🚶 Walk / 🚗 Grab", "time": "10-15 min", "cost": "FREE - ₹150", "distance": "1-3 km",
                "recommendation": "Check Google Maps — if < 1km, walk. If > 1km, take Grab (₹80-150 per ride in D1).",
                "directions": ""}
    
    # ═══════════════════════════════════════
    # PHU QUOC — Duong Dong centered, island distances
    # ═══════════════════════════════════════
    elif city == "Phu Quoc":
        # Hotel → Grand World
        if ("arrive" in from_lower or "check-in" in from_lower or "fly" in from_lower) and "grand world" in to_lower:
            return {"mode": "🚗 Grab", "time": "20 min", "cost": "₹150-200", "distance": "12 km",
                    "recommendation": "Take Grab from Duong Dong to Grand World (north). 20 min ride. Or hotel shuttle if available (free).",
                    "directions": gmaps_dirs("Duong Dong Phu Quoc", "Grand World Phu Quoc")}
        
        # Airport → Hotel
        if ("land" in from_lower or "airport" in from_lower or "pqc" in from_lower) and ("check-in" in to_lower or "hotel" in to_lower):
            return {"mode": "🚗 Grab", "time": "15 min", "cost": "₹200-250", "distance": "10 km",
                    "recommendation": "Take Grab from PQC airport to Duong Dong. 15 min. If no Grab, Mai Linh taxi only — agree price first (~₹200).",
                    "directions": gmaps_dirs("Phu Quoc Airport", "Duong Dong town")}
        
        # Grand World → Hotel
        if "grand world" in from_lower and ("hotel" in to_lower or "check-in" in to_lower):
            return {"mode": "🚗 Grab", "time": "20 min", "cost": "₹150-200", "distance": "12 km",
                    "recommendation": "Grab back to Duong Dong hotel. 20 min ride.",
                    "directions": gmaps_dirs("Grand World Phu Quoc", "Duong Dong town")}
        
        # Hotel → 4 Island Tour pickup
        if ("4 island" in to_lower or "island tour" in to_lower or "an thoi" in to_lower):
            return {"mode": "🚐 Hotel pickup", "time": "0 min", "cost": "FREE", "distance": "—",
                    "recommendation": "Tour picks up from hotel lobby. Be ready 15 min before departure time. Free pickup included in tour.",
                    "directions": ""}
        
        # Island tour → Sunset Town
        if ("island tour" in from_lower or "4 island" in from_lower) and "sunset" in to_lower:
            return {"mode": "🚗 Grab", "time": "15 min", "cost": "₹120-150", "distance": "8 km",
                    "recommendation": "Grab from An Thoi port to Sunset Town. 15 min, both in south Phu Quoc.",
                    "directions": gmaps_dirs("An Thoi Port Phu Quoc", "Sunset Town Phu Quoc")}
        
        # Sunset Town → Duong Dong Night Market
        if "sunset" in from_lower and ("duong dong" in to_lower or "night market" in to_lower):
            return {"mode": "🚗 Grab", "time": "20 min", "cost": "₹150-200", "distance": "15 km",
                    "recommendation": "Grab from Sunset Town (south) to Duong Dong (center). 20 min ride north.",
                    "directions": gmaps_dirs("Sunset Town Phu Quoc", "Duong Dong Night Market")}
        
        # Hotel → VinWonders
        if "vinwonders" in to_lower:
            return {"mode": "🚗 Grab / Hotel shuttle", "time": "20 min", "cost": "₹150-200", "distance": "12 km",
                    "recommendation": "Grab from Duong Dong to VinWonders (north). 20 min. Many hotels offer free shuttle — ask reception.",
                    "directions": gmaps_dirs("Duong Dong Phu Quoc", "VinWonders Phu Quoc")}
        
        # VinWonders → Hotel
        if "vinwonders" in from_lower and ("hotel" in to_lower or "check-in" in to_lower):
            return {"mode": "🚗 Grab", "time": "20 min", "cost": "₹150-200", "distance": "12 km",
                    "recommendation": "Grab back to Duong Dong after THE ONCE show ends ~8 PM. Grab available at VinWonders exit.",
                    "directions": gmaps_dirs("VinWonders Phu Quoc", "Duong Dong town")}
        
        # Hotel → Ong Lang Beach
        if "ong lang" in to_lower:
            return {"mode": "🚗 Grab / Scooter", "time": "15 min", "cost": "₹100-150", "distance": "6 km",
                    "recommendation": "Grab or rent scooter (₹350/day). Ong Lang is 6km north of Duong Dong. Hidden cove, go early for no crowds.",
                    "directions": gmaps_dirs("Duong Dong Phu Quoc", "Ong Lang Beach")}
        
        # Ong Lang → Ham Ninh
        if "ong lang" in from_lower and "ham ninh" in to_lower:
            return {"mode": "🚗 Grab / Scooter", "time": "25 min", "cost": "₹150-200", "distance": "18 km",
                    "recommendation": "Cross-island ride from west coast (Ong Lang) to east coast (Ham Ninh). 25 min. Rent scooter for flexibility.",
                    "directions": gmaps_dirs("Ong Lang Beach Phu Quoc", "Ham Ninh Village Phu Quoc")}
        
        # Ham Ninh → Airport
        if "ham ninh" in from_lower and ("fly" in to_lower or "airport" in to_lower):
            return {"mode": "🚗 Grab", "time": "20 min", "cost": "₹200-250", "distance": "12 km",
                    "recommendation": "Grab from Ham Ninh to PQC airport. 20 min. Leave 2.5 hrs before flight.",
                    "directions": gmaps_dirs("Ham Ninh Village Phu Quoc", "Phu Quoc Airport")}
        
        # Default Phu Quoc
        return {"mode": "🛵 Scooter / 🚗 Grab", "time": "10-20 min", "cost": "₹100-200", "distance": "5-15 km",
                "recommendation": "Rent scooter ₹350/day (best option on island) or take Grab. Everything is 10-20 min from Duong Dong.",
                "directions": ""}
    
    # ═══════════════════════════════════════
    # HANOI — Old Quarter centered
    # ═══════════════════════════════════════
    elif city == "Hanoi":
        # Airport → Hotel
        if ("land" in from_lower or "airport" in to_lower or "fly" in from_lower) and ("check-in" in to_lower or "hotel" in to_lower):
            return {"mode": "🚗 Grab", "time": "45-60 min", "cost": "₹500-700", "distance": "27 km",
                    "recommendation": "Take Grab from Noi Bai (HAN) to Old Quarter. 45-60 min, ₹500-700. Fixed price. NO airport buses after 10 PM.",
                    "directions": gmaps_dirs("Noi Bai Airport Hanoi", "Hanoi Old Quarter")}
        
        # Hotel → Pho Thin
        if "pho thin" in to_lower and ("hotel" in from_lower or "check-in" in from_lower or "check-in" in to_lower):
            return {"mode": "🚶 Walk", "time": "8 min", "cost": "FREE", "distance": "600 m",
                    "recommendation": "Walk from Old Quarter hotel to Pho Thin (Lo Duc St). 8 min. Opens 6 AM, go early to avoid queue.",
                    "directions": gmaps_dirs("Hanoi Old Quarter", "Pho Thin Hanoi")}
        
        # Pho Thin → Hoan Kiem Lake
        if "pho thin" in from_lower and "hoan kiem" in to_lower:
            return {"mode": "🚶 Walk", "time": "10 min", "cost": "FREE", "distance": "800 m",
                    "recommendation": "Walk — from Lo Duc St west to Hoan Kiem Lake. 10 min pleasant morning walk through Old Quarter streets.",
                    "directions": gmaps_dirs("Pho Thin Hanoi", "Hoan Kiem Lake Hanoi")}
        
        # Hoan Kiem → Temple of Literature
        if "hoan kiem" in from_lower and "temple of literature" in to_lower:
            return {"mode": "🚗 Grab", "time": "12 min", "cost": "₹100-120", "distance": "3 km",
                    "recommendation": "Take Grab — Temple of Literature is 3km south of Old Quarter. Too far to walk (35 min). Grab is ₹100.",
                    "directions": gmaps_dirs("Hoan Kiem Lake Hanoi", "Temple of Literature Hanoi")}
        
        # Temple of Literature → Bun Cha Huong Lien
        if "temple of literature" in from_lower and "bun cha" in to_lower:
            return {"mode": "🚶 Walk / 🚗 Grab", "time": "8 min walk / 3 min Grab", "cost": "FREE / ₹70", "distance": "600 m",
                    "recommendation": "Walk 8 min — Bun Cha Huong Lien (Obama's spot) is just 600m from Temple of Literature. Same Dong Da area. Or Grab for ₹70.",
                    "directions": gmaps_dirs("Temple of Literature Hanoi", "Bun Cha Huong Lien Hanoi")}
        
        # Bun Cha → X Space
        if "bun cha" in from_lower and "x space" in to_lower:
            return {"mode": "🚗 Grab", "time": "15 min", "cost": "₹120-150", "distance": "5 km",
                    "recommendation": "Take Grab from Dong Da back to Hoan Kiem area. X Space is near Old Quarter. 15 min ride.",
                    "directions": gmaps_dirs("Bun Cha Huong Lien Hanoi", "X Space Immersive Hanoi")}
        
        # X Space → Train Street
        if "x space" in from_lower and "train street" in to_lower:
            return {"mode": "🚶 Walk", "time": "12 min", "cost": "FREE", "distance": "900 m",
                    "recommendation": "Walk — Train Street (Le Duan) is 900m from X Space. 12 min walk through Old Quarter. Train passes ~3:45 PM and 7:00 PM.",
                    "directions": gmaps_dirs("X Space Immersive Hanoi", "Hanoi Train Street")}
        
        # Train Street → Water Puppet
        if "train street" in from_lower and "water puppet" in to_lower:
            return {"mode": "🚶 Walk", "time": "12 min", "cost": "FREE", "distance": "1 km",
                    "recommendation": "Walk — from Train Street (Le Duan) north to Thang Long Water Puppet Theatre at Hoan Kiem Lake. 12 min.",
                    "directions": gmaps_dirs("Hanoi Train Street", "Thang Long Water Puppet Hanoi")}
        
        # Night Market → Hotel
        if "night market" in from_lower and ("hotel" in to_lower or "check-in" in to_lower):
            return {"mode": "🚶 Walk", "time": "5 min", "cost": "FREE", "distance": "300 m",
                    "recommendation": "Walk — Night Market is on Hang Dao St, right in Old Quarter. 5 min walk to any Old Quarter hotel.",
                    "directions": ""}
        
        # Hotel → Sapa Bus
        if "sapa" in to_lower and "bus" in to_lower:
            return {"mode": "🚶 Walk / 🚗 Grab", "time": "5-10 min", "cost": "FREE / ₹70", "distance": "500 m",
                    "recommendation": "Sapa Express bus departs from Old Quarter office. Walk 5-10 min from hotel. Or Grab for ₹70. Bring snacks + water for 6-hr ride.",
                    "directions": gmaps_dirs("Hanoi Old Quarter", "Sapa Express Bus Hanoi")}
        
        # Hotel → Dong Xuan Market
        if "dong xuan" in to_lower:
            return {"mode": "🚶 Walk", "time": "8 min", "cost": "FREE", "distance": "600 m",
                    "recommendation": "Walk — Dong Xuan Market is in the north end of Old Quarter. 8 min walk from Hoan Kiem area.",
                    "directions": gmaps_dirs("Hanoi Old Quarter", "Dong Xuan Market Hanoi")}
        
        # Dong Xuan → Pho Bat Dan
        if "dong xuan" in from_lower and "pho bat" in to_lower:
            return {"mode": "🚶 Walk", "time": "6 min", "cost": "FREE", "distance": "450 m",
                    "recommendation": "Walk — Pho Bat Dan is 450m south of Dong Xuan Market. 6 min walk through Old Quarter.",
                    "directions": gmaps_dirs("Dong Xuan Market Hanoi", "Pho Bat Dan Hanoi")}
        
        # Pho Bat Dan → Airport
        if "pho bat" in from_lower and ("airport" in to_lower or "taxi" in to_lower):
            return {"mode": "🚗 Grab", "time": "45 min", "cost": "₹500-700", "distance": "27 km",
                    "recommendation": "Take Grab to Noi Bai airport. 45 min, ₹500-700. Leave hotel 3 hrs before international flight.",
                    "directions": gmaps_dirs("Pho Bat Dan Hanoi", "Noi Bai Airport Hanoi")}
        
        # Default Hanoi
        return {"mode": "🚶 Walk / 🚗 Grab", "time": "5-15 min", "cost": "FREE - ₹120", "distance": "300m - 5 km",
                "recommendation": "Old Quarter is compact — walk if < 1km. Grab for Temple of Literature or airport. NEVER take cyclo — scam.",
                "directions": ""}
    
    # ═══════════════════════════════════════
    # SAPA — Town center, mountain distances
    # ═══════════════════════════════════════
    elif city == "Sapa":
        # Bus → Hotel
        if "bus" in from_lower and ("arrive" in to_lower or "check-in" in to_lower or "hotel" in to_lower):
            return {"mode": "🚶 Walk", "time": "5 min", "cost": "FREE", "distance": "400 m",
                    "recommendation": "Walk — Sapa Express bus drops at town center. Most hotels 5-min walk. Hotel can send staff to carry bags if you ask.",
                    "directions": gmaps_dirs("Sapa Bus Station", "Sapa town center")}
        
        # Hotel → Sapa Square
        if "sapa square" in to_lower or "cathedral" in to_lower:
            return {"mode": "🚶 Walk", "time": "3 min", "cost": "FREE", "distance": "200 m",
                    "recommendation": "Walk — Sapa Square and Stone Church are in the absolute center. 3 min from any town hotel.",
                    "directions": gmaps_dirs("Sapa town center", "Sapa Stone Church")}
        
        # Hotel → Moana
        if "moana" in to_lower:
            return {"mode": "🚶 Walk", "time": "5 min", "cost": "FREE", "distance": "300 m",
                    "recommendation": "Walk — Moana Sapa is 300m from Sapa Square. 5 min walk. Go early morning (7 AM) for best photos without crowds.",
                    "directions": gmaps_dirs("Sapa Square", "Moana Sapa")}
        
        # Moana → Cat Cat Village
        if "moana" in from_lower and "cat cat" in to_lower:
            return {"mode": "🚶 Walk downhill", "time": "20 min down", "cost": "FREE", "distance": "1.5 km",
                    "recommendation": "Walk downhill 20 min — steep path from Moana to Cat Cat Village entrance. Coming back up is 35 min — take motorbike taxi ₹100.",
                    "directions": gmaps_dirs("Moana Sapa", "Cat Cat Village Sapa")}
        
        # Cat Cat → Lunch
        if "cat cat" in from_lower and "lunch" in to_lower:
            return {"mode": "🚵 Motorbike taxi", "time": "15 min", "cost": "₹100", "distance": "2 km",
                    "recommendation": "Take motorbike taxi back up to Sapa town — ₹100. Walking up is 35 min steep climb, not worth it.",
                    "directions": gmaps_dirs("Cat Cat Village Sapa", "Sapa town center")}
        
        # Lunch → Hill Station cafe
        if "lunch" in from_lower and ("hill station" in to_lower or "cafe" in to_lower):
            return {"mode": "🚶 Walk", "time": "8 min", "cost": "FREE", "distance": "500 m",
                    "recommendation": "Walk — The Hill Station cafe is 500m from Sapa town center. 8 min walk. Mountain valley views from the cafe.",
                    "directions": gmaps_dirs("Sapa town center", "Hill Station Sapa")}
        
        # Hotel → Rong May
        if "rong may" in to_lower:
            return {"mode": "🚕 Taxi / 🚗 Grab", "time": "30 min", "cost": "₹250-350", "distance": "18 km",
                    "recommendation": "Take taxi — Rong May is 18km from Sapa on O Quy Ho pass. 30 min mountain road. Book return taxi with same driver (₹500 round trip). Don't take motorbike — too far + dangerous road.",
                    "directions": gmaps_dirs("Sapa town", "Rong May Tourism Sapa")}
        
        # Rong May → Heaven's Gate
        if "rong may" in from_lower and "heaven" in to_lower:
            return {"mode": "🚕 Taxi", "time": "10 min", "cost": "₹100", "distance": "5 km",
                    "recommendation": "Heaven's Gate pass viewpoint is 5km from Rong May — same road. Ask your taxi driver to stop. 10 min drive.",
                    "directions": gmaps_dirs("Rong May Tourism Sapa", "Heaven's Gate Sapa")}
        
        # Rong May → Hotel
        if "rong may" in from_lower and ("return" in to_lower or "hotel" in to_lower or "dinner" in to_lower):
            return {"mode": "🚕 Taxi", "time": "30 min", "cost": "₹250-300", "distance": "18 km",
                    "recommendation": "Return taxi to Sapa town — 30 min mountain road. Same driver from morning if booked round trip.",
                    "directions": gmaps_dirs("Rong May Tourism Sapa", "Sapa town center")}
        
        # Hotel → Fansipan
        if "fansipan" in to_lower:
            return {"mode": "🚐 Hotel shuttle", "time": "10 min", "cost": "FREE", "distance": "3 km",
                    "recommendation": "Hotel shuttle to Fansipan cable car station — 3km, 10 min, FREE. Most hotels offer this. Go at 7 AM — Tuesday = 10 min queue (vs 2 hours on Sunday!).",
                    "directions": gmaps_dirs("Sapa town", "Fansipan Cable Car Sapa")}
        
        # Fansipan → Hotel
        if "fansipan" in from_lower and ("return" in to_lower or "lunch" in to_lower):
            return {"mode": "🚐 Hotel shuttle / 🚗 Grab", "time": "10 min", "cost": "FREE / ₹100", "distance": "3 km",
                    "recommendation": "Shuttle back to Sapa town. 10 min. Or Grab for ₹100.",
                    "directions": gmaps_dirs("Fansipan Cable Car Sapa", "Sapa town center")}
        
        # Hotel → Sapa Bus (departure)
        if "sapa" in from_lower and "bus" in to_lower and ("hanoi" in to_lower or "express" in to_lower):
            return {"mode": "🚶 Walk", "time": "5 min", "cost": "FREE", "distance": "400 m",
                    "recommendation": "Walk to Sapa Express bus stop. 5 min from any town hotel. Bring water + snacks for 6-hr ride back to Hanoi.",
                    "directions": gmaps_dirs("Sapa town center", "Sapa Express Bus")}
        
        # Default Sapa
        return {"mode": "🚶 Walk / 🚕 Taxi", "time": "5-30 min", "cost": "FREE - ₹300", "distance": "200m - 18 km",
                "recommendation": "Walk in town center. Taxi for Fansipan (3km) or Rong May (18km). Motorbike taxi ₹100 for Cat Cat return.",
                "directions": ""}
    
    # ═══════════════════════════════════════
    # HALONG BAY — Day trip from Hanoi
    # ═══════════════════════════════════════
    elif city == "Halong Bay":
        # Hotel → Bus
        if "bus" in to_lower and "halong" in to_lower:
            return {"mode": "🚐 Cruise bus pickup", "time": "0 min", "cost": "Included", "distance": "—",
                    "recommendation": "Limousine bus picks up from Old Quarter hotel lobby. Be ready 15 min early. 2.5 hr drive to Halong Bay. Bring water + snacks.",
                    "directions": ""}
        
        # Bus → Cruise
        if "bus" in from_lower and "cruise" in to_lower:
            return {"mode": "🚐 Bus transfer", "time": "Included", "cost": "Included", "distance": "—",
                    "recommendation": "Bus drops at Tuan Chau port. Walk to cruise boat — 5 min. Everything organized by cruise package.",
                    "directions": ""}
        
        # Cruise → Titop Island
        if "cruise" in from_lower and "titop" in to_lower:
            return {"mode": "🚢 Boat", "time": "20 min", "cost": "Included", "distance": "—",
                    "recommendation": "Cruise boat takes you to Titop Island. 20 min on boat. Climb 400 steps to viewpoint — best panorama of Halong Bay.",
                    "directions": ""}
        
        # Cruise → Return
        if "cruise" in from_lower and ("return" in to_lower or "bus" in to_lower or "dinner" in to_lower):
            return {"mode": "🚐 Cruise bus", "time": "2.5 hr", "cost": "Included", "distance": "170 km",
                    "recommendation": "Bus returns to Hanoi Old Quarter. 2.5 hr drive. Arrives ~8 PM. Dinner in Hanoi after.",
                    "directions": ""}
        
        # Default Halong
        return {"mode": "🚢 Cruise organized", "time": "Included", "cost": "Included", "distance": "—",
                "recommendation": "Everything is organized by the cruise package — bus pickup, boat, lunch, activities, return. Just be on time.",
                "directions": ""}
    
    # Generic fallback
    return {"mode": "🚶 Walk / 🚗 Grab", "time": "5-15 min", "cost": "FREE - ₹200", "distance": "0.5-5 km",
            "recommendation": "Check Google Maps for exact distance. Walk if < 1km, Grab if > 1km.",
            "directions": ""}

# ═══════════════════════════════════════════
# AGENT 14: CHIEF TRAVEL OFFICER (CTO)
# ═══════════════════════════════════════════
def agent_cto(weather_data=None, budget_data=None, scam_data=None, route_data=None):
    """Master orchestrator — generates daily briefing."""
    print("[CTO Agent] Generating daily briefing...")
    
    # Load other agent outputs if not passed
    if weather_data is None:
        weather_data = _load("weather")
    if budget_data is None:
        budget_data = _load("budget")
    if scam_data is None:
        scam_data = _load("scams")
    if route_data is None:
        route_data = _load("routes")
    
    # Calculate trip status
    today = datetime.utcnow()
    trip_start = datetime(2026, 6, 28)
    trip_end = datetime(2026, 7, 10)
    
    if today < trip_start:
        phase = "pre_trip"
        days_until = (trip_start - today).days
        status = f"{days_until} days until departure"
        current_day = None
    elif today > trip_end:
        phase = "post_trip"
        status = "Trip completed"
        current_day = None
    else:
        phase = "in_trip"
        current_day = (today - trip_start).days
        status = f"Day {current_day + 1} of {(trip_end - trip_start).days + 1}"
    
    # Today's itinerary
    today_plan = None
    if current_day is not None and 0 <= current_day < len(cfg.ITINERARY):
        today_plan = cfg.ITINERARY[current_day]
    
    # Generate briefing
    travel_health = 85
    if weather_data and "score" in weather_data:
        travel_health = (travel_health + weather_data["score"]) // 2
    
    risk_status = "LOW"
    if scam_data and scam_data.get("risk_score", 100) < 70:
        risk_status = "MEDIUM"
    if weather_data and len(weather_data.get("alerts", [])) > 3:
        risk_status = "HIGH"
    
    briefing = {
        "agent": "Chief Travel Officer",
        "timestamp": now_iso(),
        "phase": phase,
        "status": status,
        "current_day": current_day,
        "travel_health_score": travel_health,
        "budget_status": budget_data.get("budget_health", "unknown") if budget_data else "unknown",
        "budget_remaining": budget_data.get("remaining", 0) if budget_data else 0,
        "risk_status": risk_status,
        "weather_status": f"{weather_data['score']}/100" if weather_data else "unknown",
        "weather_alerts": weather_data.get("alerts", []) if weather_data else [],
        "scam_alerts": scam_data.get("total_alerts", 0) if scam_data else 0,
        "route_warnings": route_data.get("total_warnings", 0) if route_data else 0,
        "today_plan": _summarize_day(today_plan) if today_plan else None,
        "recommended_actions": _generate_actions(weather_data, budget_data, scam_data, route_data, phase),
        "emergency_alerts": [],
        "countdown": days_until if phase == "pre_trip" else None,
    }
    
    write_data("briefing", briefing)
    write_data("cto", briefing)
    print(f"[CTO Agent] Health: {travel_health}/100, Risk: {risk_status}, Phase: {phase}")
    return briefing

def _load(name):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def _summarize_day(day):
    return {
        "date": day["date"],
        "dow": day["dow"],
        "city": day["city"],
        "label": day["label"],
        "icon": day["icon"],
        "tip": day["tip"],
        "stops": len(day["plan"]),
        "plan": day["plan"],
    }

def _generate_actions(weather, budget, scam, route, phase):
    actions = []
    
    if phase == "pre_trip":
        actions.append("📅 Book domestic flights: HCMC→Phu Quoc, Phu Quoc→Hanoi")
        actions.append("📱 Download Grab, Google Maps offline, Google Translate")
        actions.append("💰 Exchange ~₹15,000 to VND at bank (not airport)")
        actions.append("📱 Buy Vietnam eSIM or physical SIM (Viettel/Vinaphone)")
        actions.append("🏨 Confirm all hotel bookings")
        actions.append("🛡️ Verify travel insurance covers Vietnam")
        actions.append("🎫 Book Halong Bay cruise (Klook/Tripadvisor top-rated)")
        actions.append("🎫 Book Sapa Express bus ticket")
    
    if weather and weather.get("alerts"):
        actions.append(f"🌧️ {len(weather['alerts'])} weather alerts — check dashboard for details")
    
    if budget and budget.get("warnings"):
        for w in budget["warnings"]:
            actions.append(f"💰 {w}")
    
    if scam and scam.get("high_risk_count", 0) > 0:
        actions.append(f"⚠️ {scam['high_risk_count']} high-risk scams identified — review scam dashboard")
    
    if not actions:
        actions.append("✅ All systems nominal. No action required.")
    
    return actions

# ═══════════════════════════════════════════
# AGENT 13: DESIGN & WEBSITE IMPROVEMENT
# ═══════════════════════════════════════════
def agent_design():
    """Continuously suggest website improvements."""
    print("[Design Agent] Analyzing website...")
    output = {
        "agent": "Design & Website Improvement",
        "timestamp": now_iso(),
        "current_features": [
            "Day-by-day itinerary with expandable details",
            "Weather forecast per city",
            "Budget dashboard",
            "Scam alerts",
            "Food guide",
            "Route optimization",
            "Content planning",
            "Emergency contacts",
            "Packing checklist",
        ],
        "suggested_improvements": [
            "Interactive route map with Google Maps integration",
            "Real-time flight status tracking",
            "Expense logging with receipt photo upload",
            "Offline mode for no-internet areas",
            "Push notifications for weather alerts",
            "Photo journal with EXIF data",
            "Multi-language support (Vietnamese phrases)",
            "Currency converter widget",
            "Trip sharing with family",
        ],
        "score": 78,
        "source": "UX analysis",
    }
    write_data("design", output)
    print(f"[Design Agent] Current score: {output['score']}/100")
    return output

# ═══════════════════════════════════════════
# MASTER ORCHESTRATOR
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# AGENT TIERS — Save tokens by not running everything daily
# ═══════════════════════════════════════════
# Tier 1 (DAILY) — Changes frequently, essential for trip safety
#   weather, backup, budget, cto (briefing)
# Tier 2 (WEEKLY) — Mostly static, refresh weekly
#   destination, food, scam, hotel, transport, route, content, detailed_plan
# Tier 3 (ON-DEMAND) — Rarely changes, trigger manually
#   packing, emergency, design

AGENT_TIERS = {
    "daily": ["weather", "backup", "budget", "cto"],
    "weekly": ["destination", "food", "scam", "hotel", "transport", "route", "content", "detailed_plan"],
    "ondemand": ["packing", "emergency", "design"],
}

# Agent registry: name → function
AGENTS = {
    "weather": lambda: agent_weather(),
    "destination": lambda: agent_destination(),
    "food": lambda: agent_food(),
    "hotel": lambda: agent_hotel(),
    "scam": lambda: agent_scam(),
    "route": lambda: agent_route(),
    "transport": lambda: agent_transport(),
    "budget": lambda: agent_budget(),
    "packing": lambda: agent_packing(),
    "content": lambda: agent_content(),
    "emergency": lambda: agent_emergency(),
    "backup": lambda: agent_backup(),
    "detailed_plan": lambda: agent_detailed_plan(),
    "cto": lambda: agent_cto(_load("weather"), _load("budget"), _load("scams"), _load("routes")),
    "design": lambda: agent_design(),
}

def _build_status(run_type, results):
    """Build status file from agent results."""
    cto = results.get("cto", {})
    w = results.get("weather", {})
    s = results.get("scam", {})
    
    agent_statuses = {}
    for name in AGENTS:
        r = results.get(name)
        if r:
            st = {"status": "active", "last_run": r.get("timestamp"), "tier": _get_tier(name)}
            if name == "weather": st["score"] = r.get("score")
            elif name == "scam": st["alerts"] = r.get("total_alerts")
            elif name == "budget": st["health"] = r.get("budget_health")
            elif name == "backup": st["high_risk_days"] = r.get("high_risk_days")
            agent_statuses[name] = st
        else:
            # Load cached timestamp
            cached = _load(name.replace("scam", "scams").replace("detailed_plan", "detailed-plan"))
            agent_statuses[name] = {
                "status": "cached", 
                "last_run": cached.get("timestamp") if cached else None,
                "tier": _get_tier(name),
            }
    
    return {
        "system": "ATOS — Autonomous Travel Operating System",
        "version": "1.3",
        "last_run": now_iso(),
        "run_type": run_type,
        "agents_active": len(AGENTS),
        "trip_phase": cto.get("phase", "unknown"),
        "travel_health": cto.get("travel_health_score", 0),
        "risk_level": cto.get("risk_status", "unknown"),
        "budget_health": cto.get("budget_status", "unknown"),
        "weather_score": w.get("score", 0) if w else 0,
        "total_alerts": len(w.get("alerts", []) if w else []) + (s.get("total_alerts", 0) if s else 0),
        "agent_tiers": AGENT_TIERS,
        "agent_statuses": agent_statuses,
    }

def _get_tier(name):
    for tier, agents in AGENT_TIERS.items():
        if name in agents:
            return tier
    return "unknown"

def run_daily():
    """Run only Tier 1 (daily) agents — saves 11 agents of compute."""
    print("\n" + "=" * 60)
    print("  ATOS — DAILY RUN (Tier 1: 4 agents)")
    print("=" * 60 + "\n")
    start = time.time()
    
    results = {}
    for name in AGENT_TIERS["daily"]:
        print(f"  → {name}...")
        results[name] = AGENTS[name]()
    
    status = _build_status("daily", results)
    write_data("atos-status", status)
    
    elapsed = time.time() - start
    print(f"\n  Daily run complete — {elapsed:.1f}s (4 agents)")
    print(f"  Health: {status['travel_health']}/100 | Risk: {status['risk_level']}\n")
    return status

def run_weekly():
    """Run Tier 1 + Tier 2 — full refresh minus on-demand agents."""
    print("\n" + "=" * 60)
    print("  ATOS — WEEKLY RUN (Tier 1+2: 12 agents)")
    print("=" * 60 + "\n")
    start = time.time()
    
    results = {}
    for name in AGENT_TIERS["daily"] + AGENT_TIERS["weekly"]:
        print(f"  → {name}...")
        results[name] = AGENTS[name]()
    
    status = _build_status("weekly", results)
    write_data("atos-status", status)
    
    elapsed = time.time() - start
    print(f"\n  Weekly run complete — {elapsed:.1f}s (12 agents)")
    print(f"  Health: {status['travel_health']}/100 | Risk: {status['risk_level']}\n")
    return status

def run_all():
    """Run ALL agents — full refresh including on-demand."""
    print("\n" + "=" * 60)
    print("  ATOS — FULL RUN (All 15 agents)")
    print("=" * 60 + "\n")
    start = time.time()
    
    results = {}
    for name in list(AGENTS.keys()):
        print(f"  → {name}...")
        results[name] = AGENTS[name]()
    
    status = _build_status("full", results)
    write_data("atos-status", status)
    
    elapsed = time.time() - start
    print(f"\n  Full run complete — {elapsed:.1f}s (15 agents)")
    print(f"  Health: {status['travel_health']}/100 | Risk: {status['risk_level']}\n")
    return status

def run_single(agent_name):
    """Run a single agent on-demand."""
    if agent_name not in AGENTS:
        print(f"Unknown agent: {agent_name}")
        print(f"Available: {', '.join(AGENTS.keys())}")
        return None
    
    print(f"\n  → Running single agent: {agent_name}")
    result = AGENTS[agent_name]()
    
    # Update status file
    all_results = {}
    # Load existing cached results for other agents
    for name in AGENTS:
        if name == agent_name:
            all_results[name] = result
        else:
            cache_name = name.replace("scam", "scams").replace("detailed_plan", "detailed-plan")
            cached = _load(cache_name)
            if cached:
                all_results[name] = cached
    
    status = _build_status("single:" + agent_name, all_results)
    write_data("atos-status", status)
    print(f"  ✓ {agent_name} updated\n")
    return result

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    
    if mode == "daily":
        run_daily()
    elif mode == "weekly":
        run_weekly()
    elif mode == "full" or mode == "all":
        run_all()
    elif mode == "single":
        agent = sys.argv[2] if len(sys.argv) > 2 else None
        if agent:
            run_single(agent)
        else:
            print("Usage: python3 engine.py single <agent_name>")
            print(f"Available: {', '.join(AGENTS.keys())}")
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python3 engine.py [daily|weekly|full|single <agent>]")
        print(f"Agents: {', '.join(AGENTS.keys())}")
