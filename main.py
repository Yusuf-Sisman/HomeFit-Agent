from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
from geopy.distance import geodesic
import concurrent.futures
import time
from google import genai
import os

# ==========================================
# 1. YAPAY ZEKA VE API AYARLARI
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

try:
    if not GEMINI_API_KEY:
        print("KRİTİK HATA: API Anahtarı bulunamadı!")
        ai_client = None
    else:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"GenAI Config Error: {e}")
    ai_client = None

try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"GenAI Config Error: {e}")
    ai_client = None

app = FastAPI(title="HomeFit API")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 2. VERİ YAPILARI VE ÖNBELLEK
# ==========================================
class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    prefs: dict = {}
    lang: str = "TR"

osm_cache = {}
osrm_cache = {}

# ==========================================
# 3. OSM VE OSRM FONKSİYONLARI
# ==========================================
def get_facilities_from_osm(lat, lon, tags, radius=3000, retries=3):
    cache_key = f"{lat}_{lon}_{str(tags)}"
    if cache_key in osm_cache: return osm_cache[cache_key]

    overpass_url = "http://overpass-api.de/api/interpreter"
    headers = {'User-Agent': 'HomeFitAgent/FastAPI'}
    tag_str = "".join([f'["{k}"="{v}"]' for k, v in tags.items()])
    overpass_query = f"[out:json][timeout:25];(node{tag_str}(around:{radius},{lat},{lon});way{tag_str}(around:{radius},{lat},{lon});relation{tag_str}(around:{radius},{lat},{lon}););out center;"
    
    for attempt in range(retries):
        try:
            response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                result = [(e['lat'], e['lon']) if e['type'] == 'node' else (e['center']['lat'], e['center']['lon']) for e in data.get('elements', [])]
                osm_cache[cache_key] = result
                return result
            elif response.status_code == 429: time.sleep(1.5 * (attempt + 1))
            else: break
        except: time.sleep(1)
    return []

def get_network_data(lat1, lon1, lat2, lon2, retries=2):
    cache_key = f"{lat1}_{lon1}_{lat2}_{lon2}"
    if cache_key in osrm_cache: return osrm_cache[cache_key]

    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 'Ok':
                    drive_dist = data['routes'][0]['distance'] 
                    result = (drive_dist * 0.95, (drive_dist * 0.95) / 1.38, drive_dist, data['routes'][0]['duration'])
                    osrm_cache[cache_key] = result
                    return result
            elif response.status_code == 429: time.sleep(1)
        except: time.sleep(0.5)
    return None, None, None, None

def format_duration(seconds):
    if seconds is None: return "--"
    if seconds < 60: return "<1 dk"
    return f"{int(seconds // 60)} dk"

def get_score_from_distance(distance):
    if distance <= 300: return 100
    elif distance <= 600: return 80
    elif distance <= 1200: return 60
    elif distance <= 2500: return 40
    return 0

def process_single_category(cat_name, info, user_lat, user_lon):
    try:
        weight = info["weight"]
        facilities = get_facilities_from_osm(user_lat, user_lon, info["tags"])
        
        if facilities:
            distances_with_coords = [(geodesic((user_lat, user_lon), f_point).meters, f_point) for f_point in facilities]
            distances_with_coords.sort(key=lambda x: x[0])
            min_be_dist, nearest_coord = distances_with_coords[0]
            
            walk_dist, walk_dur, drive_dist, drive_dur = get_network_data(user_lat, user_lon, nearest_coord[0], nearest_coord[1])
            if walk_dist is None:
                walk_dist, drive_dist = min_be_dist * 1.3, min_be_dist * 1.4
                walk_dur, drive_dur = walk_dist / 1.38, drive_dist / 8.33 
            
            score = get_score_from_distance(walk_dist)
            metrics = {
                "bird": round(min_be_dist, 1), 
                "walk_d": round(walk_dist, 1), 
                "walk_t": format_duration(walk_dur), 
                "drive_d": round(drive_dist, 1), 
                "drive_t": format_duration(drive_dur)
            }
        else:
            score, nearest_coord, metrics = (-50 if weight == 2 else 0), None, None
            
        return cat_name, score, weight, nearest_coord, metrics
    except Exception as e:
        print(f"Hata oluştu ({cat_name}): {e}")
        return cat_name, 0, info["weight"], None, None

# ==========================================
# 4. API UÇ NOKTALARI (ENDPOINTS)
# ==========================================
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/api/analyze")
async def analyze_location(req: AnalyzeRequest):
    results = {}
    total_weighted_score, total_weight = 0, 0
    
    if not req.prefs:
        return {"status": "error", "message": "Kategori seçilmedi."}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_single_category, c_name, info, req.lat, req.lon) for c_name, info in req.prefs.items()]
        for future in concurrent.futures.as_completed(futures):
            cat_name, score, weight, nearest_coord, metrics = future.result()
            total_weighted_score += (score * weight)
            total_weight += weight
            results[cat_name] = {"score": score, "nearest": nearest_coord, "metrics": metrics}
            
    final_score = round(max(0, total_weighted_score / total_weight if total_weight > 0 else 0), 2)
    
    return {
        "status": "success",
        "final_score": final_score,
        "details": results
    }

@app.post("/api/interpret")
async def get_ai_interpretation(req: dict):
    if not ai_client:
        return {"interpretation": "LLM Ayarları eksik veya API Anahtarı hatalı."}

    final_score = req.get("final_score", 0)
    details = req.get("details", {})
    lang = req.get("lang", "TR")

    raw_data = f"Genel Skor: {final_score}/100\n"
    for cat, data in details.items():
        if data.get('metrics'):
            raw_data += f"- {cat}: Puanı {max(0, data['score'])}, Yürüme: {data['metrics']['walk_d']}m, Araç: {data['metrics']['drive_d']}m\n"

    if lang == "TR":
        prompt = f"""
        Sen uzman bir gayrimenkul ve GIS asistanısın. Müşterin bir ev seçti ve şu veriler elde edildi:
        {raw_data}
        Görevlerin:
        1. 2 veya 3 paragraflık profesyonel bir değerlendirme yaz.
        2. Mesafelerin günlük yaşam kalitesini nasıl etkileyeceğini yorumla.
        3. Sonuna 1 cümlelik genel özet ekle. Düz metin yaz.
        """
    else:
        prompt = f"""
        You are an expert real estate and GIS assistant. Your client selected a home location with these metrics:
        {raw_data}
        Tasks:
        1. Write a 2-3 paragraph professional evaluation.
        2. Interpret how these distances affect daily life quality.
        3. Add a 1-sentence final verdict at the end. Use plain text.
        """
# --- HATA YÖNETİMİ VE YENİDEN DENEME ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ai_client.models.generate_content(
                model='gemini-1.5-flash', # 2.0 veya 2.5 yerine 1.5 daha stabildir
                contents=prompt
            )
            return {"interpretation": response.text}
        
        except Exception as e:
            # Eğer hata 503 (Yoğunluk) veya 429 (Çok fazla istek) ise bekle ve tekrar dene
            if "503" in str(e) or "429" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(3) # 3 saniye bekle
                    continue
            
            return {"interpretation": f"Yapay Zeka şu an çok yoğun. Lütfen birkaç dakika sonra tekrar deneyin. (Hata: {e})"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
