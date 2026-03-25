import datetime
import json
import math
import os


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
RULES_FILE = os.path.join(DATA_DIR, "attendance_rules.json")
DEFAULT_RADIUS_METERS = 5.0
DEFAULT_RULES = {
    "location_name": "",
    "latitude": None,
    "longitude": None,
    "radius_meters": DEFAULT_RADIUS_METERS,
    "start_time": "",
    "end_time": "",
    "updated_at": ""
}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _normalized_rules(data):
    rules = dict(DEFAULT_RULES)
    if isinstance(data, dict):
        rules.update(data)

    try:
        radius = float(rules.get("radius_meters") or DEFAULT_RADIUS_METERS)
    except (TypeError, ValueError):
        radius = DEFAULT_RADIUS_METERS

    rules["radius_meters"] = radius if radius > 0 else DEFAULT_RADIUS_METERS
    rules["location_name"] = str(rules.get("location_name") or "").strip()
    rules["start_time"] = str(rules.get("start_time") or "").strip()
    rules["end_time"] = str(rules.get("end_time") or "").strip()

    for key in ("latitude", "longitude"):
        value = rules.get(key)
        if value in ("", None):
            rules[key] = None
            continue

        try:
            rules[key] = float(value)
        except (TypeError, ValueError):
            rules[key] = None

    return rules


def load_attendance_rules():
    if not os.path.exists(RULES_FILE):
        return dict(DEFAULT_RULES)

    try:
        with open(RULES_FILE, "r", encoding="utf-8") as file:
            return _normalized_rules(json.load(file))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_RULES)


def save_attendance_rules(location_name, latitude, longitude, start_time, end_time):
    _ensure_data_dir()

    cleaned_location = str(location_name or "").strip()

    try:
        cleaned_latitude = float(latitude)
        cleaned_longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude are required.")

    if not (-90 <= cleaned_latitude <= 90):
        raise ValueError("Latitude must be between -90 and 90.")

    if not (-180 <= cleaned_longitude <= 180):
        raise ValueError("Longitude must be between -180 and 180.")

    cleaned_start_time = _parse_time_value(start_time, "Start time").strftime("%H:%M")
    cleaned_end_time = _parse_time_value(end_time, "End time").strftime("%H:%M")

    if cleaned_start_time >= cleaned_end_time:
        raise ValueError("End time must be later than start time.")

    rules = {
        "location_name": cleaned_location,
        "latitude": cleaned_latitude,
        "longitude": cleaned_longitude,
        "radius_meters": DEFAULT_RADIUS_METERS,
        "start_time": cleaned_start_time,
        "end_time": cleaned_end_time,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds")
    }

    with open(RULES_FILE, "w", encoding="utf-8") as file:
        json.dump(rules, file, indent=2)

    return rules


def get_public_attendance_rules():
    rules = load_attendance_rules()
    return {
        "location_name": rules["location_name"],
        "latitude": rules["latitude"],
        "longitude": rules["longitude"],
        "radius_meters": rules["radius_meters"],
        "start_time": rules["start_time"],
        "end_time": rules["end_time"],
        "updated_at": rules["updated_at"],
        "location_configured": rules["latitude"] is not None and rules["longitude"] is not None,
        "time_window_configured": bool(rules["start_time"] and rules["end_time"])
    }


def evaluate_attendance_rules(student_latitude, student_longitude, now=None):
    rules = load_attendance_rules()

    if rules["latitude"] is None or rules["longitude"] is None:
        return {
            "ok": False,
            "reason": "location_not_configured",
            "message": "Attendance location is not configured by the admin yet."
        }

    if not rules["start_time"] or not rules["end_time"]:
        return {
            "ok": False,
            "reason": "time_not_configured",
            "message": "Attendance time window is not configured by the admin yet."
        }

    try:
        student_latitude = float(student_latitude)
        student_longitude = float(student_longitude)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "reason": "location_missing",
            "message": "Your live location is required to mark attendance."
        }

    current_time = (now or datetime.datetime.now()).time()
    start_time = _parse_time_value(rules["start_time"], "Start time")
    end_time = _parse_time_value(rules["end_time"], "End time")

    if current_time < start_time or current_time > end_time:
        return {
            "ok": False,
            "reason": "outside_time_window",
            "message": f"Attendance is only allowed between {rules['start_time']} and {rules['end_time']}."
        }

    distance_meters = calculate_distance_meters(
        student_latitude,
        student_longitude,
        rules["latitude"],
        rules["longitude"]
    )

    if distance_meters > rules["radius_meters"]:
        location_label = rules["location_name"] or "the attendance location"
        return {
            "ok": False,
            "reason": "outside_location_radius",
            "message": f"You must be within 5 meters of {location_label} to mark attendance.",
            "distance_meters": round(distance_meters, 2)
        }

    return {
        "ok": True,
        "reason": "allowed",
        "message": "Attendance rules satisfied.",
        "distance_meters": round(distance_meters, 2)
    }


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    earth_radius_meters = 6371000

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_meters * c


def _parse_time_value(value, label):
    try:
        return datetime.datetime.strptime(str(value).strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"{label} must use HH:MM format.") from exc
