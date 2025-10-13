import os, json, time, math, requests
from pathlib import Path
from typing import Optional, Tuple

ART_DIR = Path("/app/artifacts")
CFG_DIR = ART_DIR / "config"
CFG_DIR.mkdir(parents=True, exist_ok=True)
GEO_DIR = ART_DIR / "geo"
GEO_DIR.mkdir(parents=True, exist_ok=True)
CAL_FILE = CFG_DIR / "calibration.json"
LOG_FILE = GEO_DIR / "verify_log.jsonl"

GEO_PROVIDER = (os.getenv("GEO_PROVIDER") or "auto").lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_EPSILON_M = float(os.getenv("GEO_EPSILON_M") or 60)
TRUST_XFF = (os.getenv("TRUST_X_FORWARDED_FOR","true").lower() == "true")

def save_calibration(lat: float, lon: float, epsilon_m: float) -> dict:
    payload = {
        "lat": float(lat),
        "lon": float(lon),
        "epsilon_m": float(epsilon_m),
        "updated_at": int(time.time())
    }
    with open(CAL_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    return payload

def load_calibration() -> dict:
    if CAL_FILE.exists():
        with open(CAL_FILE) as f:
            return json.load(f)
    return {"lat": None, "lon": None, "epsilon_m": DEFAULT_EPSILON_M, "updated_at": None}

def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*(math.sin(dlambda/2)**2)
    return 2 * R * math.asin(math.sqrt(a))

def get_client_ip(headers, client_host: str) -> str:
    if TRUST_XFF:
        xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
        if xff:
            # XFF can contain multiple IPs: client, proxy1, proxy2...
            return xff.split(",")[0].strip()
    return client_host

class GeoProvider:
    def locate(self, ip: Optional[str]) -> Optional[Tuple[float,float,float]]:
        """Return (lat, lon, accuracy_m) or None on failure."""
        raise NotImplementedError

class GoogleGeo(GeoProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    def locate(self, ip: Optional[str]):
        # Using Google's Geolocation API with 'considerIp': True
        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={self.api_key}"
        payload = {"considerIp": True}
        try:
            r = requests.post(url, json=payload, timeout=5)
            if r.ok:
                data = r.json()
                loc = data.get("location", {})
                acc = data.get("accuracy", None)
                if "lat" in loc and "lng" in loc:
                    return float(loc["lat"]), float(loc["lng"]), float(acc or 5000.0)
        except Exception:
            return None
        return None

class IpApi(GeoProvider):
    def locate(self, ip: Optional[str]):
        # ip-api.com: http://ip-api.com/json/{ip}?fields=status,lat,lon
        target = ip or ""
        url = f"http://ip-api.com/json/{target}?fields=status,lat,lon"
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                data = r.json()
                if data.get("status") == "success":
                    lat, lon = float(data["lat"]), float(data["lon"])
                    # No accuracy provided; assume coarse accuracy.
                    return lat, lon, 1000.0
        except Exception:
            return None
        return None

class MockGeo(GeoProvider):
    def locate(self, ip: Optional[str]):
        # Center on Harvard Yard for local dev; accuracy is wide.
        return 42.3745, -71.1189, 800.0

def pick_provider() -> GeoProvider:
    if GEO_PROVIDER in ("google",):
        if GOOGLE_API_KEY:
            return GoogleGeo(GOOGLE_API_KEY)
        else:
            return IpApi()
    if GEO_PROVIDER in ("ipapi",):
        return IpApi()
    if GEO_PROVIDER in ("mock",):
        return MockGeo()
    # auto
    if GOOGLE_API_KEY:
        return GoogleGeo(GOOGLE_API_KEY)
    return IpApi()

PROVIDER = pick_provider()

def log_attempt(record: dict):
    record["ts"] = int(time.time())
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
