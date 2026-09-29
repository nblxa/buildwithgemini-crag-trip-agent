# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uuid
from datetime import datetime
import httpx
from google.cloud import firestore, storage
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google import genai
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

MODEL = "gemini-3.6-flash"
PROJECT_ID = "qwiklabs-gcp-03-689eef206658"
STORAGE_BUCKET_NAME = "cragtrip-media-xxl67u"
SANDBOX_RESOURCE_NAME = "projects/697814514458/locations/us-east1/reasoningEngines/473104460269223936/sandboxEnvironments/2400779241202384896"
MEMORY_BANK_ID = "473104460269223936"


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


def save_user_vehicle_profile(
    user_id: str = "default_climber",
    fuel_consumption_l_per_100km: float = 7.5,
    passenger_capacity_climbers: int = 3,
    car_model: str = "Climber Car",
    notes: str = "Includes trunk space for crashpads and climbing packs"
) -> dict:
    """Saves or updates the user's personal car profile, including fuel consumption and climber capacity.

    Args:
        user_id: Identifier for the climber/user (defaults to 'default_climber').
        fuel_consumption_l_per_100km: Average fuel consumption in Liters per 100 km (e.g. 6.2, 8.0).
        passenger_capacity_climbers: Number of fully equipped climbers (with ropes, gear, packs, pads) that fit comfortably.
        car_model: Description or model of the vehicle (e.g. 'VW Golf', 'Skoda Octavia Combi', 'Campervan').
        notes: Special notes about trunk space, roof racks, or gear storage.

    Returns:
        Confirmation message and stored vehicle specifications.
    """
    db = get_firestore_client()
    profile_data = {
        "user_id": user_id,
        "fuel_consumption_l_per_100km": fuel_consumption_l_per_100km,
        "passenger_capacity_climbers": passenger_capacity_climbers,
        "car_model": car_model,
        "notes": notes,
    }
    db.collection("user_profiles").document(user_id).set({"vehicle": profile_data}, merge=True)
    return {
        "status": "success",
        "message": f"Saved vehicle profile for {user_id}: {car_model} ({fuel_consumption_l_per_100km} L/100km, holds {passenger_capacity_climbers} climbers with gear)."
    }


def get_user_vehicle_profile(user_id: str = "default_climber") -> dict:
    """Retrieves the user's remembered car profile (fuel economy, climber passenger capacity, car model).

    Args:
        user_id: Identifier for the user (defaults to 'default_climber').

    Returns:
        The vehicle specs, or default fallback values if not yet configured.
    """
    db = get_firestore_client()
    doc = db.collection("user_profiles").document(user_id).get()
    if doc.exists:
        data = doc.to_dict()
        if "vehicle" in data:
            return data["vehicle"]
    return {
        "user_id": user_id,
        "fuel_consumption_l_per_100km": 7.5,
        "passenger_capacity_climbers": 3,
        "car_model": "Standard vehicle (default)",
        "notes": "Default estimate (3 climbers with gear)"
    }


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client pinned to the hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_crags(discipline: str = "", country: str = "") -> list[dict]:
    """Lists climbing crags available in the database, optionally filtered by climbing discipline or country.

    Args:
        discipline: Optional climbing discipline to filter by, e.g. 'sport climbing', 'trad climbing', or 'bouldering'.
        country: Optional country to filter by, e.g. 'Germany', 'Austria', 'Switzerland', 'France'.

    Returns:
        A list of crag records containing name, country, location, disciplines, grade range, and description.
    """
    db = get_firestore_client()
    docs = db.collection("crags").stream()
    results = []
    disc_filter = discipline.lower().strip() if discipline else ""
    country_filter = country.lower().strip() if country else ""
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if disc_filter:
            item_disciplines = [d.lower() for d in data.get("disciplines", [])]
            if not any(disc_filter in d for d in item_disciplines):
                continue
        if country_filter:
            item_country = data.get("country", "").lower()
            item_loc = data.get("location", "").lower()
            if country_filter not in item_country and country_filter not in item_loc:
                continue
        results.append({
            "id": data.get("id"),
            "name": data.get("name"),
            "country": data.get("country", ""),
            "location": data.get("location"),
            "disciplines": data.get("disciplines"),
            "grade_range": data.get("grade_range"),
            "description": data.get("description"),
            "routes_count": len(data.get("routes", [])),
            "accommodations_count": len(data.get("accommodations", []))
        })
    return results


def get_crag_details(crag_id_or_name: str) -> dict:
    """Gets detailed info for a specific climbing crag, including routes, topos, and accommodations.

    Args:
        crag_id_or_name: The crag ID (e.g. 'rumney-meadows') or crag name.

    Returns:
        The complete crag dictionary with routes and accommodation options, or an error message.
    """
    db = get_firestore_client()
    # Try direct ID lookup
    doc = db.collection("crags").document(crag_id_or_name).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # Fallback to search by name match
    query_str = crag_id_or_name.lower()
    for item in db.collection("crags").stream():
        data = item.to_dict()
        if query_str in data.get("name", "").lower() or query_str in item.id.lower():
            data["id"] = item.id
            return data

    return {"error": f"Crag '{crag_id_or_name}' not found in database."}


def add_or_update_crag(
    crag_id: str,
    name: str,
    location: str,
    disciplines: list[str],
    grade_range: str,
    description: str
) -> dict:
    """Adds or updates a climbing crag destination in the Firestore database.

    Args:
        crag_id: Unique slug for the crag (e.g. 'red-river-gorge').
        name: Full name of the crag area.
        location: City/State/Country.
        disciplines: List of climbing disciplines, e.g. ['sport climbing', 'trad climbing'].
        grade_range: Grade difficulty range, e.g. '5.7 - 5.14a'.
        description: A summary of the rock type, style, and climbing conditions.

    Returns:
        Confirmation status and crag ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection("crags").document(crag_id)
    existing = doc_ref.get()
    crag_data = {
        "id": crag_id,
        "name": name,
        "location": location,
        "disciplines": disciplines,
        "grade_range": grade_range,
        "description": description,
    }
    if existing.exists:
        # Preserve existing routes and accommodations if present
        curr_dict = existing.to_dict()
        if "routes" in curr_dict:
            crag_data["routes"] = curr_dict["routes"]
        if "accommodations" in curr_dict:
            crag_data["accommodations"] = curr_dict["accommodations"]

    doc_ref.set(crag_data, merge=True)
    return {"status": "success", "message": f"Crag '{name}' ({crag_id}) saved successfully."}


def get_crag_weather(crag_name_or_location: str) -> dict:
    """Fetches real-time weather and climbing forecast for a crag or location using live atmospheric data.

    Args:
        crag_name_or_location: Name of the crag (e.g. 'Céüse', 'Frankenjura', 'Magic Wood') or city/region.

    Returns:
        A dictionary with current temperature, humidity, precipitation, wind speed, climbing condition rating,
        and daily forecast for upcoming days.
    """
    # 1. First check if it matches a known crag in Firestore to get exact location
    db = get_firestore_client()
    query_str = crag_name_or_location.lower()
    search_location = crag_name_or_location
    crag_title = crag_name_or_location

    for item in db.collection("crags").stream():
        data = item.to_dict()
        if query_str in data.get("name", "").lower() or query_str in item.id.lower():
            search_location = data.get("location", crag_name_or_location)
            crag_title = data.get("name", crag_name_or_location)
            break

    # Clean location query for geocoding (e.g. take the town/city name)
    geo_query = search_location.split(",")[0].strip()
    if "/" in geo_query:
        geo_query = geo_query.split("/")[0].strip()

    try:
        # Geocode the location via Open-Meteo Geocoding
        geo_resp = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": geo_query, "count": 1},
            timeout=5.0
        )
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            # Fallback to secondary token if first failed
            tokens = search_location.split(",")
            if len(tokens) > 1:
                geo_resp = httpx.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": tokens[1].strip(), "count": 1},
                    timeout=5.0
                )
                geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for location: {search_location}"}

        match = geo_data["results"][0]
        lat = match["latitude"]
        lon = match["longitude"]
        resolved_name = f"{match.get('name')}, {match.get('country')}"

        # Fetch current conditions & 4-day forecast
        forecast_resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "weather_code"],
                "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
                "timezone": "auto"
            },
            timeout=5.0
        )
        forecast_data = forecast_resp.json()
        current = forecast_data.get("current", {})
        daily = forecast_data.get("daily", {})

        precip = current.get("precipitation", 0.0)
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        # Climbing condition assessment
        if precip > 0.5:
            climbing_condition = "Poor (Rain / Wet Rock)"
        elif humidity and humidity > 85:
            climbing_condition = "Fair (High humidity / greasy holds)"
        elif temp and (temp < 3 or temp > 33):
            climbing_condition = "Marginal (Temperature too extreme)"
        else:
            climbing_condition = "Great (Dry rock, good friction)"

        # Prepare forecast overview
        days_forecast = []
        dates = daily.get("time", [])[:4]
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain_chances = daily.get("precipitation_probability_max", [])

        for i in range(len(dates)):
            days_forecast.append({
                "date": dates[i],
                "high_c": max_temps[i] if i < len(max_temps) else None,
                "low_c": min_temps[i] if i < len(min_temps) else None,
                "rain_prob_pct": rain_chances[i] if i < len(rain_chances) else None,
            })

        return {
            "crag": crag_title,
            "resolved_location": resolved_name,
            "coordinates": {"latitude": lat, "longitude": lon},
            "current_weather": {
                "temperature_c": temp,
                "humidity_pct": humidity,
                "precipitation_mm": precip,
                "wind_speed_kmh": wind,
                "climbing_condition": climbing_condition
            },
            "upcoming_forecast": days_forecast
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather: {str(e)}"}


def _geocode_place(place_name: str) -> dict | None:
    """Helper to geocode a place name or city into lat/lon coordinates."""
    # First check if it matches a crag in Firestore
    db = get_firestore_client()
    query_str = place_name.lower().strip()
    target_str = place_name

    for item in db.collection("crags").stream():
        data = item.to_dict()
        if query_str in data.get("name", "").lower() or query_str in item.id.lower():
            target_str = data.get("location", place_name)
            break

    geo_query = target_str.split(",")[0].strip()
    if "/" in geo_query:
        geo_query = geo_query.split("/")[0].strip()

    try:
        resp = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": geo_query, "count": 1},
            timeout=5.0
        )
        data = resp.json()
        if data.get("results"):
            res = data["results"][0]
            return {
                "name": f"{res.get('name')}, {res.get('country')}",
                "lat": res["latitude"],
                "lon": res["longitude"]
            }
        # Fallback to second token
        tokens = target_str.split(",")
        if len(tokens) > 1:
            resp = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": tokens[1].strip(), "count": 1},
                timeout=5.0
            )
            data = resp.json()
            if data.get("results"):
                res = data["results"][0]
                return {
                    "name": f"{res.get('name')}, {res.get('country')}",
                    "lat": res["latitude"],
                    "lon": res["longitude"]
                }
    except Exception:
        pass
    return None


def calculate_travel_logistics(
    origin_city: str,
    destination_crag: str,
    user_id: str = "default_climber",
    need_car_rental: bool = False,
    rental_days: int = 2
) -> dict:
    """Calculates comprehensive road travel logistics between an origin and a climbing crag.
    Includes driving distance, drive time, personalized fuel consumption (from remembered vehicle profile),
    autobahn vignettes (Austria, Switzerland), toll road estimates (France, Austria special tunnels/passes),
    and optional rental car costs.

    Args:
        origin_city: Starting city or home location, e.g. 'Munich', 'Zurich', 'Paris', 'Innsbruck', 'Frankfurt'.
        destination_crag: Destination crag name or area, e.g. 'Frankenjura', 'Zillertal', 'Céüse', 'Magic Wood'.
        user_id: Identifier to look up the climber's saved vehicle profile (fuel consumption, passenger gear capacity).
        need_car_rental: Whether to include a ballpark car rental estimate for the trip.
        rental_days: Number of rental days to calculate if car rental is requested (default 2).

    Returns:
        A dictionary containing driving metrics, fuel cost with remembered vehicle specs, autobahn vignettes,
        toll estimates, vehicle passenger/gear capacity, optional car rental breakdown, and trip feasibility.
    """
    origin_geo = _geocode_place(origin_city)
    if not origin_geo:
        return {"error": f"Could not find coordinates for origin: {origin_city}"}

    dest_geo = _geocode_place(destination_crag)
    if not dest_geo:
        return {"error": f"Could not find coordinates for destination: {destination_crag}"}

    try:
        # 1. Fetch user vehicle profile
        vehicle = get_user_vehicle_profile(user_id)
        fuel_consumption_rate = vehicle.get("fuel_consumption_l_per_100km", 7.5)
        capacity_climbers = vehicle.get("passenger_capacity_climbers", 3)
        car_model = vehicle.get("car_model", "Standard car")

        # 2. Call OSRM routing API (lon,lat format)
        url = f"https://router.project-osrm.org/route/v1/driving/{origin_geo['lon']},{origin_geo['lat']};{dest_geo['lon']},{dest_geo['lat']}?overview=false"
        resp = httpx.get(url, timeout=7.0)
        route_data = resp.json()

        if route_data.get("code") != "Ok" or not route_data.get("routes"):
            return {"error": f"Could not compute road route between {origin_city} and {destination_crag}."}

        route = route_data["routes"][0]
        distance_meters = route.get("distance", 0.0)
        duration_seconds = route.get("duration", 0.0)

        dist_km = round(distance_meters / 1000.0, 1)
        dist_miles = round(dist_km * 0.621371, 1)

        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # 3. Fuel calculation using user vehicle profile
        fuel_liters = round((dist_km / 100.0) * fuel_consumption_rate, 1)
        fuel_cost_eur = round(fuel_liters * 1.80, 2)
        round_trip_fuel_eur = round(fuel_cost_eur * 2, 2)

        # 4. Autobahn Vignettes & Tolls calculation (CH, AT, FR)
        origin_text = origin_geo["name"].lower()
        dest_text = dest_geo["name"].lower()
        vignettes_tolls = []
        toll_total_one_way = 0.0

        # Switzerland Vignette: required if driving into/through Switzerland on national highways (CHF 40 ≈ €42 annual)
        if "switzerland" in dest_text or "switzerland" in origin_text:
            vignettes_tolls.append({
                "country": "Switzerland (CH)",
                "type": "Autobahn Vignette",
                "cost_eur": 42.0,
                "notes": "Mandatory e-vignette / sticker valid for full calendar year (CHF 40 / ~€42)"
            })
            toll_total_one_way += 42.0

        # Austria Vignette: 1-day (~€8.60) or 10-day vignette (~€11.50)
        if "austria" in dest_text or "austria" in origin_text:
            vignettes_tolls.append({
                "country": "Austria (AT)",
                "type": "Autobahn Vignette (10-Day)",
                "cost_eur": 11.50,
                "notes": "Mandatory vignette for Austrian motorways (Asfinag 10-day digital or sticker: €11.50; 1-day: €8.60)"
            })
            toll_total_one_way += 11.50
            # Special section toll check (e.g. Brenner, Arlberg, Felbertauern)
            if "tyrol" in dest_text or "ginzling" in dest_text or "zillertal" in dest_text:
                vignettes_tolls.append({
                    "country": "Austria (AT)",
                    "type": "Section / Valley Toll",
                    "cost_eur": 10.0,
                    "notes": "Optional alpine pass / mountain access road toll (e.g. Schlegeis Alpine Road in Zillertal)"
                })
                toll_total_one_way += 10.0

        # France Autoroute Tolls: distance-based toll (péage)
        is_french_crag = "france" in dest_text or "france" in destination_crag.lower()
        if is_french_crag:
            # Distance-based estimate: €25 - €45 depending on drive distance through France
            if dist_km > 500:
                est_toll = 38.0
            elif dist_km > 250:
                est_toll = 28.0
            else:
                est_toll = 18.0

            vignettes_tolls.append({
                "country": "France (FR)",
                "type": "Autoroute Péage (Toll Road)",
                "cost_eur": est_toll,
                "notes": f"Estimated distance-based French motorway toll one-way to {destination_crag} (ticket/telepass péage)"
            })
            toll_total_one_way += est_toll

        # 5. Optional Car Rental (Ballpark figures in Europe: Compact/Estate ~€45-€65/day)
        car_rental_info = None
        if need_car_rental:
            daily_rate_eur = 55.0  # Compact / Estate suitable for crashpads/gear
            rental_total = round(daily_rate_eur * rental_days, 2)
            car_rental_info = {
                "rental_requested": True,
                "recommended_class": "Compact Wagon / Estate (e.g., VW Golf Variant, Skoda Octavia) for gear storage",
                "days": rental_days,
                "estimated_daily_rate_eur": daily_rate_eur,
                "estimated_rental_total_eur": rental_total,
                "climber_gear_capacity": 3,
                "notes": "Includes standard CDW insurance. Reserve with roof rack if carrying oversized bouldering pads."
            }

        # 6. Trip feasibility rating
        if hours <= 3:
            feasibility = "Excellent for day trips or quick weekend getaways"
        elif hours <= 5:
            feasibility = "Great for regular 2-3 day weekend climbing trips"
        elif hours <= 8:
            feasibility = "Best suited for extended long weekends (3-4+ days)"
        else:
            feasibility = "Recommended for week-long vacations or multi-day road trips"

        # 7. Total trip transport cost estimate
        total_one_way_transport = round(fuel_cost_eur + toll_total_one_way, 2)
        total_round_trip_transport = round(round_trip_fuel_eur + (toll_total_one_way * 2), 2)
        if car_rental_info:
            total_round_trip_transport = round(total_round_trip_transport + car_rental_info["estimated_rental_total_eur"], 2)

        # Per climber split cost
        cost_per_climber = round(total_round_trip_transport / capacity_climbers, 2)

        return {
            "origin": origin_geo["name"],
            "destination": dest_geo["name"],
            "driving_distance": {
                "kilometers": dist_km,
                "miles": dist_miles
            },
            "driving_duration": {
                "formatted": duration_str,
                "total_hours": round(duration_seconds / 3600.0, 2)
            },
            "vehicle_profile": {
                "car_model": car_model,
                "fuel_consumption_l_per_100km": fuel_consumption_rate,
                "passenger_capacity_climbers": capacity_climbers,
                "gear_capacity_notes": f"Fits {capacity_climbers} fully equipped climbers with ropes, racks, and packs."
            },
            "fuel_cost": {
                "liters_one_way": fuel_liters,
                "cost_one_way_eur": fuel_cost_eur,
                "cost_round_trip_eur": round_trip_fuel_eur
            },
            "vignettes_and_tolls": vignettes_tolls,
            "car_rental_estimate": car_rental_info,
            "total_estimated_costs": {
                "round_trip_transport_eur": total_round_trip_transport,
                "cost_split_per_climber_eur": cost_per_climber,
                "split_among_climbers": capacity_climbers
            },
            "trip_feasibility": feasibility
        }
    except Exception as e:
        return {"error": f"Error calculating route: {str(e)}"}


def _fetch_location_map(lat: float, lon: float, zoom: int = 12, w_tiles: int = 2, h_tiles: int = 2) -> str | None:
    """Stitches OpenStreetMap tiles around the crag coordinates and draws a location marker pin."""
    import math
    import urllib.request
    from PIL import Image, ImageDraw

    try:
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

        map_img = Image.new('RGB', (w_tiles * 256, h_tiles * 256))
        for dx in range(w_tiles):
            for dy in range(h_tiles):
                x = xtile + dx - 1
                y = ytile + dy - 1
                url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                req = urllib.request.Request(url, headers={'User-Agent': 'CragTrip/1.0 (map-generator)'})
                try:
                    with urllib.request.urlopen(req, timeout=4.0) as r:
                        t_img = Image.open(r)
                        map_img.paste(t_img, (dx * 256, dy * 256))
                except Exception:
                    pass

        # Draw a pin on the map
        draw = ImageDraw.Draw(map_img)
        cx = int(w_tiles * 128)
        cy = int(h_tiles * 128)
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(229, 62, 62), outline=(255, 255, 255), width=3)
        draw.polygon([(cx - 7, cy + 5), (cx + 7, cy + 5), (cx, cy + 18)], fill=(229, 62, 62))

        temp_map_path = f"/tmp/crag_map_{uuid.uuid4().hex[:6]}.png"
        map_img.save(temp_map_path, "PNG")
        return temp_map_path
    except Exception:
        return None


def _render_trip_path_map(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> str | None:
    """Renders the actual driving route path between origin and crag on an OpenStreetMap overview map."""
    import math
    import urllib.request
    from PIL import Image, ImageDraw

    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
        resp = httpx.get(url, timeout=7.0)
        route_data = resp.json()
        if route_data.get("code") != "Ok" or not route_data.get("routes"):
            return None

        coords = route_data["routes"][0]["geometry"]["coordinates"] # [lon, lat]
        if not coords:
            return None

        step = max(1, len(coords) // 180)
        sampled = coords[::step]
        if sampled[-1] != coords[-1]:
            sampled.append(coords[-1])

        all_lats = [c[1] for c in sampled]
        all_lons = [c[0] for c in sampled]
        min_lat, max_lat = min(all_lats), min(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        for c in sampled:
            min_lat = min(min_lat, c[1])
            max_lat = max(max_lat, c[1])
            min_lon = min(min_lon, c[0])
            max_lon = max(max_lon, c[0])

        max_span = max(max_lat - min_lat, max_lon - min_lon)
        if max_span > 6.0: zoom = 6
        elif max_span > 3.0: zoom = 7
        elif max_span > 1.5: zoom = 8
        elif max_span > 0.8: zoom = 9
        else: zoom = 10

        n = 2.0 ** zoom
        min_xtile = int((min_lon + 180.0) / 360.0 * n) - 1
        max_xtile = int((max_lon + 180.0) / 360.0 * n) + 1
        min_ytile = int((1.0 - math.asinh(math.tan(math.radians(max_lat))) / math.pi) / 2.0 * n) - 1
        max_ytile = int((1.0 - math.asinh(math.tan(math.radians(min_lat))) / math.pi) / 2.0 * n) + 1

        if (max_xtile - min_xtile + 1) > 6:
            max_xtile = min_xtile + 5
        if (max_ytile - min_ytile + 1) > 6:
            max_ytile = min_ytile + 5

        w_tiles = max_xtile - min_xtile + 1
        h_tiles = max_ytile - min_ytile + 1
        map_img = Image.new('RGB', (w_tiles * 256, h_tiles * 256), (242, 244, 247))

        for x in range(min_xtile, max_xtile + 1):
            for y in range(min_ytile, max_ytile + 1):
                t_url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                req = urllib.request.Request(t_url, headers={'User-Agent': 'CragTrip/1.0 (path-map)'})
                try:
                    with urllib.request.urlopen(req, timeout=3.0) as r:
                        tile = Image.open(r)
                        map_img.paste(tile, ((x - min_xtile) * 256, (y - min_ytile) * 256))
                except Exception:
                    pass

        def to_px(lon, lat):
            x_tile_exact = (lon + 180.0) / 360.0 * n
            y_tile_exact = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
            return ((x_tile_exact - min_xtile) * 256, (y_tile_exact - min_ytile) * 256)

        draw = ImageDraw.Draw(map_img)
        points = [to_px(c[0], c[1]) for c in sampled]

        # Draw road trace
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=(30, 58, 138), width=5)
            draw.line([points[i], points[i+1]], fill=(59, 130, 246), width=3)

        # Origin point (emerald green circle)
        ox, oy = to_px(origin_lon, origin_lat)
        draw.ellipse([ox - 8, oy - 8, ox + 8, oy + 8], fill=(34, 197, 94), outline=(255, 255, 255), width=2)

        # Destination point (crimson red pin)
        dx, dy = to_px(dest_lon, dest_lat)
        draw.ellipse([dx - 8, dy - 8, dx + 8, dy + 8], fill=(239, 68, 68), outline=(255, 255, 255), width=2)

        # Crop to route bounding box with comfortable padding
        px_xs = [p[0] for p in points]
        px_ys = [p[1] for p in points]
        pad = 28
        box = (
            max(0, int(min(px_xs) - pad)),
            max(0, int(min(px_ys) - pad)),
            min(map_img.width, int(max(px_xs) + pad)),
            min(map_img.height, int(max(px_ys) + pad))
        )
        cropped = map_img.crop(box)
        temp_path = f"/tmp/trip_route_{uuid.uuid4().hex[:6]}.png"
        cropped.save(temp_path, "PNG")
        return temp_path
    except Exception:
        return None


def _fetch_crag_photo(crag_query: str) -> str | None:
    """Searches Wikimedia Commons for authentic high-resolution climbing photography of the crag."""
    import urllib.request
    import urllib.parse
    import json
    from PIL import Image

    # Try specific queries
    queries = [
        f"{crag_query.split('-')[0].strip()} climbing",
        f"{crag_query.split('-')[0].strip()} crag",
        "rock climbing Alps limestone",
        "rock climbing bouldering"
    ]

    for q in queries:
        try:
            search_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch="
                f"{urllib.parse.quote(q)}&srnamespace=6&format=json&srlimit=1"
            )
            req = urllib.request.Request(search_url, headers={'User-Agent': 'CragTrip/1.0 (photo-fetcher)'})
            with urllib.request.urlopen(req, timeout=4.0) as r:
                d = json.loads(r.read().decode('utf-8'))
                items = d.get('query', {}).get('search', [])
                if not items:
                    continue
                file_title = items[0]['title']

            info_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&titles="
                f"{urllib.parse.quote(file_title)}&prop=imageinfo&iiprop=url&iiurlwidth=900&format=json"
            )
            req2 = urllib.request.Request(info_url, headers={'User-Agent': 'CragTrip/1.0'})
            with urllib.request.urlopen(req2, timeout=4.0) as r2:
                d2 = json.loads(r2.read().decode('utf-8'))
                pages = d2.get('query', {}).get('pages', {})
                for _, pinfo in pages.items():
                    ii = pinfo.get('imageinfo', [{}])[0]
                    img_url = ii.get('thumburl') or ii.get('url')
                    if img_url:
                        req3 = urllib.request.Request(img_url, headers={'User-Agent': 'CragTrip/1.0'})
                        with urllib.request.urlopen(req3, timeout=5.0) as r_img:
                            pil_img = Image.open(r_img)
                            # Convert to RGB if needed (e.g. RGBA)
                            if pil_img.mode in ("RGBA", "P"):
                                pil_img = pil_img.convert("RGB")
                            temp_photo_path = f"/tmp/crag_photo_{uuid.uuid4().hex[:6]}.jpg"
                            pil_img.save(temp_photo_path, "JPEG", quality=85)
                            return temp_photo_path
        except Exception:
            continue
    return None


def compile_trip_itinerary_asset(
    trip_title: str,
    crag_name: str,
    climbers: list[str],
    origin_city: str = "Munich",
    target_routes: list[str] = None,
    trip_dates: str = "Upcoming Weekend",
    accommodation_name: str = "",
    packing_items: list[str] = None,
    language: str = "en"
) -> dict:
    """Compiles a complete, publication-quality climbing trip brochure PDF featuring location photos,
    OpenStreetMap locator maps, crag details, classic routes, live weather, driving logistics & tolls,
    and a gear packing checklist, then publishes it to Cloud Storage for friends.

    Args:
        trip_title: Name of the trip, e.g. 'Zillertal Granite Bouldering & Sport Trip'.
        crag_name: Name of the destination crag (e.g. 'Zillertal', 'Céüse', 'Frankenjura').
        climbers: List of climbers attending the trip (e.g. ['Alex', 'Sarah', 'Lukas']).
        origin_city: Starting city for driving logistics (default 'Munich').
        target_routes: Optional list of specific climbs or projects to attempt.
        trip_dates: Dates or weekend of the trip (e.g. 'Oct 4 - Oct 6, 2026').
        accommodation_name: Chosen lodging or campsite.
        packing_items: Optional custom gear checklist items.
        language: Language of brochure ('en', 'de' for German, 'ru' for Russian).

    Returns:
        A dictionary with the public PDF download URL, document filename, and itinerary summary.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register Unicode font supporting Latin-1, German Umlauts, and Cyrillic
    font_regular = "DejaVuSans"
    font_bold = "DejaVuSans-Bold"
    font_oblique = "DejaVuSans"
    try:
        reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        pdfmetrics.registerFont(TTFont("DejaVuSans", reg_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
        pdfmetrics.registerFontFamily(
            "DejaVuSans",
            normal="DejaVuSans",
            bold="DejaVuSans-Bold",
            italic="DejaVuSans",
            boldItalic="DejaVuSans-Bold"
        )
    except Exception as e:
        print("Font registration warning:", e)
        font_regular = "Helvetica"
        font_bold = "Helvetica-Bold"
        font_oblique = "Helvetica-Oblique"

    lang = language.lower() if language else "en"

    # 1. Fetch crag details from Firestore
    crag = get_crag_details(crag_name)
    crag_title = crag.get("name", crag_name)
    crag_loc = crag.get("location", "Europe")
    crag_desc = crag.get("description", "World-class climbing area.")
    routes_list = crag.get("routes", [])

    # Localize known crag descriptions for RU and DE while preserving original geographic place names
    if lang == "ru":
        if "zillertal" in crag_name.lower():
            crag_desc = "Величественные гранитные валуны и стены вдоль ледниковой альпийской реки в Тироле. Район славится пассивами, мизерами и потрясающей горной атмосферой."
        elif "frankenjura" in crag_name.lower():
            crag_desc = "Легендарный мекка спортивного скалолазания в Баварии с тысячами карстовых известняковых скал в густых лесах. Знаменит дырочными карманами и крутыми нависаниями."
        elif "céüse" in crag_name.lower() or "ceuse" in crag_name.lower():
            crag_desc = "Всемирно известная известняковая полоса на высоте 2000 м в Верхних Альпах. Идеальный серый и синий известняк с карманами и колонетами."
    elif lang == "de":
        if "zillertal" in crag_name.lower():
            crag_desc = "Beeindruckende Granitblöcke und Wände entlang der Ziller im Tiroler Alpenpanorama. Bekannt für Reibung, Aufleger und atemberaubende alpine Kulisse."
        elif "frankenjura" in crag_name.lower():
            crag_desc = "Das Herz des mitteleuropäischen Sportkletterns in den dichten Wäldern Frankens. Weltberühmt für Lochkletterei, Leisten und traditionsreiche Routen."
        elif "céüse" in crag_name.lower() or "ceuse" in crag_name.lower():
            crag_desc = "Die weltberühmte Kalkstein-Krone auf fast 2.000 m Höhe in den Haute-Alpes. Bietet herausragenden blauen und grauen Kalk mit Taschen und Tufas."

    # 2. Fetch live weather & condition
    weather = get_crag_weather(crag_name)
    coords = weather.get("coordinates", {})
    lat = coords.get("latitude", 47.0)
    lon = coords.get("longitude", 11.0)
    current_weather = weather.get("current_weather", {})
    temp = current_weather.get("temperature_c", "N/A")
    cond = current_weather.get("climbing_condition", "Good")

    # Localize rock condition string
    if lang == "ru":
        if "Dry rock" in cond or "Great" in cond:
            cond = "Отличные (Сухие скалы, высокий коэффициент трения)"
        elif "Sub-optimal" in cond or "Damp" in cond:
            cond = "Влажно / Скользко (Возможна сырость)"
        elif "Fair" in cond:
            cond = "Хорошие (Приемлемое трение)"
    elif lang == "de":
        if "Dry rock" in cond or "Great" in cond:
            cond = "Optimal (Trockener Fels, hervorragende Reibung)"
        elif "Sub-optimal" in cond or "Damp" in cond:
            cond = "Suboptimal (Feuchter Fels)"
        elif "Fair" in cond:
            cond = "Mäßig / Akzeptabel"

    # 3. Fetch travel logistics & coordinates
    origin_geo = _geocode_place(origin_city)
    origin_lat = origin_geo["lat"] if origin_geo else 48.137
    origin_lon = origin_geo["lon"] if origin_geo else 11.575

    logistics = calculate_travel_logistics(origin_city=origin_city, destination_crag=crag_name)
    dist = logistics.get("driving_distance", {}).get("kilometers", "N/A")
    duration = logistics.get("driving_duration", {}).get("formatted", "N/A")
    total_cost = logistics.get("total_estimated_costs", {}).get("round_trip_transport_eur", "N/A")
    per_climber = logistics.get("total_estimated_costs", {}).get("cost_split_per_climber_eur", "N/A")
    vignettes = logistics.get("vignettes_and_tolls", [])

    # Localize duration string (e.g. 2h 9m -> 2 ч 9 мин or 2 Std. 9 Min.)
    if duration and "h" in str(duration):
        parts = str(duration).split()
        h_val = parts[0].replace("h", "")
        m_val = parts[1].replace("m", "") if len(parts) > 1 else "0"
        if lang == "ru":
            duration = f"{h_val} ч {m_val} мин"
        elif lang == "de":
            duration = f"{h_val} Std. {m_val} Min."

    # Localize vignette & toll descriptions
    if lang == "ru":
        for v in vignettes:
            v_type = v.get("type", "")
            if "10-Day" in v_type or "Vignette" in v_type:
                v["type"] = "Автобан-виньетка (10 дней)"
            elif "Section" in v_type or "Valley" in v_type:
                v["type"] = "Альпийская платная дорога / перевал"
            elif "Péage" in v_type or "Toll" in v_type:
                v["type"] = "Платная автомагистраль (Péage)"
    elif lang == "de":
        for v in vignettes:
            v_type = v.get("type", "")
            if "10-Day" in v_type or "Vignette" in v_type:
                v["type"] = "Autobahnvignette (10 Tage)"
            elif "Section" in v_type or "Valley" in v_type:
                v["type"] = "Alpenstraße / Mautstrecke"
            elif "Péage" in v_type or "Toll" in v_type:
                v["type"] = "Autobahn-Maut (Péage)"

    # 4. Fetch Crag Photo, Approach Map, and Road Route Path Map
    photo_file = _fetch_crag_photo(crag_title)
    map_file = _fetch_location_map(lat=lat, lon=lon, zoom=12)
    route_file = _render_trip_path_map(origin_lat=origin_lat, origin_lon=origin_lon, dest_lat=lat, dest_lon=lon)

    # 5. Build Brochure PDF
    doc_id = uuid.uuid4().hex[:8]
    slug = crag_name.lower().replace(" ", "-")[:16]
    pdf_filename = f"trip_brochure_{slug}_{doc_id}.pdf"
    pdf_local_path = f"/tmp/{pdf_filename}"

    doc = SimpleDocTemplate(
        pdf_local_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=26,
        bottomMargin=26
    )
    i18n = {
        "en": {
            "dest": "DESTINATION",
            "dates": "Dates",
            "crew": "Crew",
            "from": "From",
            "default_crew": "Climbing Team",
            "crag_atmosphere": "Scenic Crag Atmosphere",
            "drive_path": "Drive Path ({origin} ➔ Crag)",
            "local_pin": "Local Approach & Pin ({lat:.2f}, {lon:.2f})",
            "sec1_title": "📍 Crag Character & Live Climbing Conditions",
            "overview": "Overview",
            "live_temp": "Live Temp",
            "rock_cond": "Rock Condition",
            "telemetry": "Atmospheric Telemetry",
            "verified_dry": "Verified Dry Rock",
            "sec2_title": "🚗 Travel Logistics, Highway Tolls & Cost Split",
            "start_city": "Starting City",
            "rt_dist": "Round-Trip Distance",
            "drive_duration": "Drive Duration (One-Way)",
            "rt_total": "Round-Trip Transport Total",
            "tolls_lbl": "Autobahn Vignettes / Tolls",
            "split_lbl": "Split Cost Per Person",
            "per_climber": "/ climber",
            "none": "None",
            "sec3_title": "🎯 Recommended Classic Routes & Topo Highlights",
            "th_route": "Route / Sector",
            "th_grade": "Grade",
            "th_type": "Type",
            "th_beta": "Topo Beta & Description",
            "local_classics": "Local Classics",
            "check_guidebook": "Check local area guidebook",
            "sec4_camp": "🏕️ <b>Basecamp / Accommodation</b>",
            "camp_tip": "💡 <i>Reserve campsite or hut ahead of time during peak season.</i>",
            "default_camp": "Local campsite / guesthouse",
            "sec4_gear": "🎒 <b>Gear Packing Checklist</b>",
            "default_gear": [
                "Climbing shoes & chalk bag",
                "Harness & locking carabiners",
                "Dynamic rope (70m/80m) & rope bag",
                "Quickdraws / Trad cams & nuts",
                "Helmets & crashpads",
                "First aid kit, headlamp & rain shells"
            ],
            "footer": "Generated by CragTrip AI Concierge • Doc ID: {doc_id} • Map © OpenStreetMap contributors"
        },
        "de": {
            "dest": "REISEZIEL",
            "dates": "Termin",
            "crew": "Kletter-Crew",
            "from": "Abfahrt",
            "default_crew": "Kletterteam",
            "crag_atmosphere": "Felslandschaft & Klettergebiet",
            "drive_path": "Anfahrtsroute ({origin} ➔ Klettergebiet)",
            "local_pin": "Zustieg & Fels-Standort ({lat:.2f}, {lon:.2f})",
            "sec1_title": "📍 Felscharakter & Aktuelle Kletterbedingungen",
            "overview": "Gebietsübersicht",
            "live_temp": "Aktuelle Temp.",
            "rock_cond": "Felszustand",
            "telemetry": "Wetter-Telemetrie",
            "verified_dry": "Trockener Fels bestätigt",
            "sec2_title": "🚗 Reise-Logistik, Mautgebühren & Kostenaufteilung",
            "start_city": "Startort",
            "rt_dist": "Gesamte Fahrstrecke (Hin & Zurück)",
            "drive_duration": "Fahrzeit (einfache Fahrt)",
            "rt_total": "Gesamte Transportkosten (Hin & Zurück)",
            "tolls_lbl": "Autobahn-Vignetten / Maut",
            "split_lbl": "Kosten pro Person",
            "per_climber": "/ Person",
            "none": "Keine",
            "sec3_title": "🎯 Top-Routenempfehlungen & Topo-Highlights",
            "th_route": "Route / Sektor",
            "th_grade": "Schwierigkeit",
            "th_type": "Kletterstil",
            "th_beta": "Topo-Details & Routenbeschreibung",
            "local_classics": "Lokale Gebietsklassiker",
            "check_guidebook": "Siehe Gebietstopo / Kletterführer",
            "sec4_camp": "🏕️ <b>Basislager / Unterkunft</b>",
            "camp_tip": "💡 <i>Campingplatz oder Hütte in der Hauptsaison frühzeitig reservieren.</i>",
            "default_camp": "Campingplatz vor Ort / Berggasthaus",
            "sec4_gear": "🎒 <b>Ausrüstungs-Packliste</b>",
            "default_gear": [
                "Kletterschuhe & Chalkbag",
                "Klettergurt & Schraubkarabiner",
                "Einfachseil (70m/80m) & Seilsack",
                "Expressen-Set / Klemmkeile & Friends",
                "Kletterhelme & Crashpads",
                "Erste-Hilfe-Set, Stirnlampe & Hardshell"
            ],
            "footer": "Erstellt von CragTrip AI Concierge • Dok-ID: {doc_id} • Kartendaten © OpenStreetMap Mitwirkende"
        },
        "ru": {
            "dest": "ЛОКАЦИЯ",
            "dates": "Даты поездки",
            "crew": "Команда",
            "from": "Выезд из",
            "default_crew": "Связка скалолазов",
            "crag_atmosphere": "Атмосфера района и скалы",
            "drive_path": "Маршрут на авто ({origin} ➔ Скалы)",
            "local_pin": "Локация и подход ({lat:.2f}, {lon:.2f})",
            "sec1_title": "📍 Характер района и погодные условия",
            "overview": "Обзор района",
            "live_temp": "Температура",
            "rock_cond": "Состояние скал",
            "telemetry": "Метеосводка",
            "verified_dry": "Сухой трение-профиль",
            "sec2_title": "🚗 Логистика, платные дороги и бюджет",
            "start_city": "Город отправления",
            "rt_dist": "Дистанция (туда и обратно)",
            "drive_duration": "Время в пути (в одну сторону)",
            "rt_total": "Общие транспортные расходы",
            "tolls_lbl": "Виньетки / Платные автомагистрали",
            "split_lbl": "Расходы на человека",
            "per_climber": "/ участник",
            "none": "Отсутствуют",
            "sec3_title": "🎯 Классические маршруты и гайдбук",
            "th_route": "Маршрут / Сектор",
            "th_grade": "Категория",
            "th_type": "Стиль",
            "th_beta": "Описание и бета",
            "local_classics": "Классика района",
            "check_guidebook": "См. локальный скалолазный гайдбук",
            "sec4_camp": "🏕️ <b>Базовый лагерь / Проживание</b>",
            "camp_tip": "💡 <i>Бронируйте кемпинг или шале заранее в сезон.</i>",
            "default_camp": "Локальный кемпинг / гестхаус",
            "sec4_gear": "🎒 <b>Чек-лист снаряжения</b>",
            "default_gear": [
                "Скальные туфли и мешочек с магнезией",
                "Страховочная система и муфтованные карабины",
                "Динамическая веревка (70/80м) и сумка для веревки",
                "Комплект оттяжек / френды и закладки",
                "Каски и крэшпады",
                "Аптечка первой помощи, налобный фонарь и мембранка"
            ],
            "footer": "Сформировано CragTrip AI Concierge • ID документа: {doc_id} • Карты © OpenStreetMap"
        }
    }

    t = i18n.get(lang, i18n["en"])

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'BrochureHeader',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#FFFFFF')
    )
    header_sub = ParagraphStyle(
        'BrochureSub',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#ED8936')
    )
    header_meta = ParagraphStyle(
        'BrochureMeta',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#E2E8F0')
    )
    h2_style = ParagraphStyle(
        'BrochureH2',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1A365D'),
        spaceBefore=4,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'BrochureBody',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#2D3748')
    )
    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName=font_oblique,
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.HexColor('#718096')
    )

    elements = []

    # HERO BANNER TABLE
    crew_str = ', '.join(climbers) if climbers else t["default_crew"]
    banner_cell = [
        Paragraph(f"🧗 {trip_title}", header_style),
        Paragraph(f"{t['dest']}: {crag_title.upper()} • {crag_loc.upper()}", header_sub),
        Paragraph(f"{t['dates']}: <b>{trip_dates}</b> | {t['crew']}: <b>{crew_str}</b> | {t['from']}: <b>{origin_city}</b>", header_meta)
    ]
    banner_table = Table([[banner_cell]], colWidths=[540])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A365D')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 8))

    # VISUAL SHOWCASE: PHOTO, DRIVING ROUTE MAP & LOCAL CRAG MAP
    media_cells = []
    caption_cells = []

    if photo_file:
        media_cells.append(RLImage(photo_file, width=175, height=130))
        caption_cells.append(Paragraph(t["crag_atmosphere"], caption_style))
    if route_file:
        media_cells.append(RLImage(route_file, width=175, height=130))
        caption_cells.append(Paragraph(t["drive_path"].format(origin=origin_city), caption_style))
    if map_file:
        media_cells.append(RLImage(map_file, width=175, height=130))
        caption_cells.append(Paragraph(t["local_pin"].format(lat=lat, lon=lon), caption_style))

    if media_cells:
        col_w = 540 / len(media_cells)
        visual_table = Table([media_cells, caption_cells], colWidths=[col_w] * len(media_cells))
        visual_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 2),
            ('TOPPADDING', (0,1), (-1,1), 2),
        ]))
        elements.append(visual_table)
        elements.append(Spacer(1, 8))

    # SECTION 1: CRAG PROFILE & LIVE WEATHER
    elements.append(Paragraph(t["sec1_title"], h2_style))
    elements.append(Paragraph(f"<b>{t['overview']}:</b> {crag_desc}", body_style))
    elements.append(Spacer(1, 3))

    weather_banner = Table([
        [
            Paragraph(f"<b>{t['live_temp']}:</b> {temp}°C", body_style),
            Paragraph(f"<b>{t['rock_cond']}:</b> {cond}", body_style),
            Paragraph(f"<b>{t['telemetry']}:</b> {t['verified_dry']}", body_style)
        ]
    ], colWidths=[180, 180, 180])
    weather_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
    ]))
    elements.append(weather_banner)
    elements.append(Spacer(1, 6))

    # SECTION 2: TRAVEL LOGISTICS, VIGNETTES & TOLLS
    elements.append(Paragraph(t["sec2_title"], h2_style))
    toll_summary = "; ".join([f"{v['type']} ({v['cost_eur']}€)" for v in vignettes]) if vignettes else t["none"]
    logistics_data = [
        [t["start_city"], origin_city, t["rt_dist"], f"~{dist * 2 if isinstance(dist, (int, float)) else dist} km"],
        [t["drive_duration"], duration, t["rt_total"], f"~€{total_cost}"],
        [t["tolls_lbl"], toll_summary, t["split_lbl"], f"~€{per_climber} {t['per_climber']}"]
    ]
    log_table = Table(logistics_data, colWidths=[135, 135, 135, 135])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2D3748')),
        ('FONTNAME', (0,0), (-1,-1), font_regular),
        ('FONTNAME', (0,0), (0,-1), font_bold),
        ('FONTNAME', (2,0), (2,-1), font_bold),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(log_table)
    elements.append(Spacer(1, 6))

    # SECTION 3: TARGET ROUTES & TOPOS
    elements.append(Paragraph(t["sec3_title"], h2_style))
    routes_rows = [[t["th_route"], t["th_grade"], t["th_type"], t["th_beta"]]]
    
    def _translate_route_meta(r_type, r_desc):
        if lang == "ru":
            t_map = {"sport": "Спорт", "boulder": "Боулдер", "trad": "Трэд", "Project": "Проект"}
            r_type = t_map.get(r_type.lower(), r_type)
            if "Classic high-friction" in r_desc:
                r_desc = "Классический гранит на трение на башнях Wig/Wam."
            elif "World-famous endurance" in r_desc:
                r_desc = "Знаменитая выносливостная линия мирового уровня (первопроход Якоб Шуберт)."
            elif "blocks scattered along" in r_desc:
                r_desc = "Гнейсовые и гранитные валуны вдоль живописной горной реки."
            elif r_desc == "Climber target line":
                r_desc = "Целевой проект связки"
        elif lang == "de":
            t_map = {"sport": "Sport", "boulder": "Bouldern", "trad": "Trad", "Project": "Projekt"}
            r_type = t_map.get(r_type.lower(), r_type)
            if "Classic high-friction" in r_desc:
                r_desc = "Klassische Reibungskletterei auf Granit an den Wig/Wam Türmen."
            elif "World-famous endurance" in r_desc:
                r_desc = "Weltberühmte Ausdauertour von Jörg Verhoeven, Erstbegehung Jakob Schubert."
            elif "blocks scattered along" in r_desc:
                r_desc = "Gneis- und Granitblöcke verstreut entlang des Gebirgsflusses."
            elif r_desc == "Climber target line":
                r_desc = "Individuelles Projektziel"
        return r_type, r_desc

    if target_routes:
        for r_name in target_routes:
            matched = next((r for r in routes_list if r_name.lower() in r.get("name", "").lower()), None)
            if matched:
                rt_type, rt_desc = _translate_route_meta(matched.get("type", "sport"), matched.get("description", ""))
                routes_rows.append([matched.get("name"), matched.get("grade"), rt_type, rt_desc[:65]])
            else:
                rt_type, rt_desc = _translate_route_meta("Project", "Climber target line")
                routes_rows.append([r_name, "-", rt_type, rt_desc])
    elif routes_list:
        for r in routes_list[:4]:
            rt_type, rt_desc = _translate_route_meta(r.get("type", "sport"), r.get("description", ""))
            routes_rows.append([r.get("name"), r.get("grade"), rt_type, rt_desc[:65]])
    else:
        routes_rows.append([t["local_classics"], "Various", "Sport/Trad", t["check_guidebook"]])

    route_table = Table(routes_rows, colWidths=[130, 65, 55, 290])
    route_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DD6B20')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), font_regular),
        ('FONTNAME', (0,0), (-1,0), font_bold),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F7FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(route_table)
    elements.append(Spacer(1, 6))

    # SECTION 4: BASECAMP & PACKING LIST SIDE-BY-SIDE
    acc_text = accommodation_name if accommodation_name else (
        crag.get("accommodations", [{}])[0].get("name", t["default_camp"])
    )
    acc_cell = [
        Paragraph(t["sec4_camp"], body_style),
        Paragraph(f"{acc_text}", body_style),
        Spacer(1, 3),
        Paragraph(t["camp_tip"], caption_style)
    ]

    checklist = packing_items if packing_items else t["default_gear"]
    check_cell = [
        Paragraph(t["sec4_gear"], body_style),
        Paragraph("<br/>".join([f"• [  ] {item}" for item in checklist]), body_style)
    ]

    split_table = Table([[acc_cell, check_cell]], colWidths=[265, 275])
    split_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#F7FAFC')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#F7FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(split_table)
    elements.append(Spacer(1, 6))

    # FOOTER
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#CBD5E0'), spaceAfter=4))
    elements.append(Paragraph(
        t["footer"].format(doc_id=doc_id),
        ParagraphStyle('Footer', parent=styles['Italic'], fontName=font_oblique, fontSize=7, textColor=colors.HexColor('#718096'), alignment=1)
    ))

    # BACKGROUND GRADIENT CANVAS PAINTER
    def _draw_page_gradient_background(canvas_obj, document_obj):
        """Paints a soft alpine sky gradient and luxury colored accent border."""
        canvas_obj.saveState()
        w, h = letter
        steps = 80
        r1, g1, b1 = (0.92, 0.95, 0.99) # Alpine pale slate blue
        r2, g2, b2 = (0.98, 0.99, 1.00) # Crisp white top
        step_h = h / steps
        for i in range(steps):
            t = i / float(steps)
            r = r1 + (r2 - r1) * t
            g = g1 + (g2 - g1) * t
            b = b1 + (b2 - b1) * t
            canvas_obj.setFillColor(colors.Color(r, g, b))
            canvas_obj.rect(0, h * (1.0 - (i + 1) / float(steps)), w, step_h + 1.0, stroke=0, fill=1)

        # Warm amber top accent line
        canvas_obj.setFillColor(colors.HexColor('#ED8936'))
        canvas_obj.rect(0, h - 5, w, 5, stroke=0, fill=1)
        # Deep navy bottom base line
        canvas_obj.setFillColor(colors.HexColor('#1A365D'))
        canvas_obj.rect(0, 0, w, 4, stroke=0, fill=1)
        canvas_obj.restoreState()

    # Build PDF with background painter callback
    doc.build(elements, onFirstPage=_draw_page_gradient_background, onLaterPages=_draw_page_gradient_background)

    # Clean up temp image files
    for tmp_f in [photo_file, map_file, route_file]:
        if tmp_f and os.path.exists(tmp_f):
            os.remove(tmp_f)

    # 6. Upload to Cloud Storage bucket (public)
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(STORAGE_BUCKET_NAME)
    blob = bucket.blob(f"itineraries/{pdf_filename}")
    blob.upload_from_filename(pdf_local_path, content_type="application/pdf")
    public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/itineraries/{pdf_filename}"

    # Cleanup local temp pdf
    if os.path.exists(pdf_local_path):
        os.remove(pdf_local_path)

    return {
        "status": "success",
        "itinerary_title": trip_title,
        "destination": crag_title,
        "trip_dates": trip_dates,
        "climbers": climbers,
        "pdf_download_url": public_url,
        "message": f"Trip brochure PDF compiled with photos, driving route path, and logistics! Shareable URL: {public_url}"
    }


def generate_crag_visual(
    prompt: str,
    item_name: str,
    tool_context: ToolContext = None
) -> dict:
    """Generates a scenic climbing visualization, approach preview sketch, or crag atmosphere artwork
    using the gemini-3.1-flash-lite-image model in the global region.
    
    The generated image is saved to the session's artifacts panel and uploaded directly to Cloud Storage.

    Args:
        prompt: Detailed description for generating the climbing scene (e.g. 'A scenic aerial view of limestone walls and overhangs at Falaises de Céüse during sunset, golden hour lighting').
        item_name: Name of the crag, route, or item being visualized (e.g. 'Céüse', 'Frankenjura', 'Action Directe').
        tool_context: ADK ToolContext injected automatically by the runtime.

    Returns:
        A dictionary with the public HTTPS Cloud Storage URL, filename, and status details.
    """
    # 1. Initialize Vertex AI client in global region
    genai_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global"
    )

    # 2. Call gemini-3.1-flash-lite-image model
    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    # 3. Extract generated image bytes
    image_bytes = None
    mime_type = "image/png"
    for part in (response.parts or []):
        if part.inline_data and part.inline_data.data:
            image_bytes = part.inline_data.data
            mime_type = part.inline_data.mime_type or "image/png"
            break

    if not image_bytes:
        return {
            "status": "error",
            "message": "Model did not return any image data in the response."
        }

    # Determine file extension based on MIME type
    ext = "jpg" if "jpeg" in mime_type else "png"
    slug = "".join(c if c.isalnum() else "_" for c in item_name.lower()).strip("_")[:24] or "crag"
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{slug}_{unique_id}.{ext}"

    # 4. Save to ADK ToolContext artifacts (shows up in Playground Artifacts panel)
    if tool_context:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(
                filename=filename,
                artifact=artifact_part,
                custom_metadata={
                    "item_name": item_name,
                    "prompt": prompt,
                    "model": "gemini-3.1-flash-lite-image",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            print("Warning: Failed to save artifact in tool_context:", e)

    # 5. Upload bytes directly to public Cloud Storage bucket without local file
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(STORAGE_BUCKET_NAME)
    blob_path = f"generated_images/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{blob_path}"

    return {
        "status": "success",
        "item_name": item_name,
        "filename": filename,
        "image_url": public_url,
        "mime_type": mime_type,
        "message": f"Successfully generated scenic image for '{item_name}'! Public URL: {public_url}"
    }


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "CragTrip, an expert rock climbing trip planner and concierge. "
        "You remember the user's stated climbing preferences, gear inventory, vehicle specs, and trip facts across conversations to personalize your responses. "
        "Help climbers discover climbing spots, inspect routes and topos, check live weather and climbing conditions, "
        "calculate driving logistics (including fuel, autobahn vignettes in AT/CH, road tolls in FR, car rental estimates, and climber gear capacity), "
        "compile and publish shareable trip itinerary PDFs to Cloud Storage, "
        "generate scenic climbing and crag visual artwork using the image generation tool, "
        "safely execute Python code in your Agent Engine sandbox environment to perform complex math, data analysis, conversions, or packing optimizations, "
        "remember user vehicle profiles in Firestore, inspect accommodations, and record new crags in the Firestore database using your tools."
    ),
    workflow_description="Analyze the climber's request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME
    ),
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
    tools=[
        PreloadMemoryTool(),
        list_crags,
        get_crag_details,
        get_crag_weather,
        calculate_travel_logistics,
        compile_trip_itinerary_asset,
        save_user_vehicle_profile,
        get_user_vehicle_profile,
        add_or_update_crag,
        generate_crag_visual
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
