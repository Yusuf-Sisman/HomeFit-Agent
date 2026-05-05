import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import pandas as pd
import concurrent.futures
import time
import re
import google.generativeai as genai

# ==========================================
# UI & CSS CONFIGURATION
# ==========================================
st.set_page_config(page_title="HomeFit Agent", layout="wide")

st.markdown("""
    <style>
    div[role="radiogroup"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; gap: 5px !important; justify-content: flex-end !important; }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label { cursor: pointer !important; margin: 0 !important; padding: 0 !important; }
    div[role="radiogroup"] > label p { font-size: 12px !important; margin: 0 !important; padding: 4px 8px !important; border-radius: 8px !important; transition: all 0.2s ease-in-out !important; line-height: 1 !important; }
    div[role="radiogroup"] label:has(input:not(:checked)) p { opacity: 0.3 !important; filter: grayscale(80%) !important; transform: scale(0.85) !important; background-color: transparent !important; border: 1px solid transparent !important; }
    div[role="radiogroup"] label:has(input:checked) p { opacity: 1.0 !important; filter: grayscale(0%) !important; transform: scale(1.1) !important; background-color: rgba(255, 255, 255, 0.15) !important; border: 1px solid rgba(255, 255, 255, 0.4) !important; box-shadow: 0px 2px 5px rgba(0,0,0,0.2) !important; }
    </style>
""", unsafe_allow_html=True)

LANG = {
    "EN": {
        "title": "🏠 HomeFit Agent",
        "search_title": "🔍 Search Address & Location",
        "search_hint": "💡 **Pro Tip:** Search for your street, then click your EXACT building on the map.",
        "search_ph": "e.g., Maslak, Sariyer",
        "search_btn": "Search Address",
        "not_found": "Address not found.",
        "select_closest": "Select the closest match:",
        "set_loc_btn": "Set Location",
        "prefs_title": "⚙️ Preferences",
        "legend": "❌ Ignore &nbsp;&nbsp;|&nbsp;&nbsp; ➖ Normal &nbsp;&nbsp;|&nbsp;&nbsp; ⭐ Crucial",
        "run_btn": "🚀 Run GeoAI Analysis",
        "err_no_cat": "Please select at least one facility!",
        "spin_msg": "Agent is executing spatial analysis and reasoning...",
        "map_title": "### Interactive Map",
        "target_home": "Target Home",
        "report_title": "### 🤖 Agent Report",
        "final_score": "Final Valuation Score",
        "penalty_txt": "Penalty Applied",
        "view_mode": "View Mode:",
        "view_opts": ["All Metrics", "Bird's-eye Only", "Walking Only", "Driving Only"],
        "nf": "Not Found",
        "new_search_btn": "🔄 New Search / Reset",
        "download_btn": "📥 Download Visual Report",
        "prompt_select": "Set your preferences on the left and click **Run GeoAI Analysis**.",
        "col_fac": "Facility",
        "col_score": "Suitability",
        "interp_title": "### 🧠 AI Agent Interpretation",
        "log_title": "### 📜 Agent Decision Log",
        "warn_search": "⚠️ Map is centered on the street. For exact results, please click on your specific building on the map!",
        "succ_click": "✅ Exact building location verified."
    },
    "TR": {
        "title": "🏠 HomeFit Ajanı",
        "search_title": "🔍 Adres ve Konum Ara",
        "search_hint": "💡 **İpucu:** Sokağınızı aratın, ardından haritadan TAM binanızın üzerine tıklayın.",
        "search_ph": "Örn: Maslak, Sarıyer",
        "search_btn": "Adresi Ara",
        "not_found": "Adres bulunamadı.",
        "select_closest": "Çıkan listeden en yakın adresi seçin:",
        "set_loc_btn": "Konumu Belirle",
        "prefs_title": "⚙️ Tercihler",
        "legend": "❌ Yok Say &nbsp;&nbsp;|&nbsp;&nbsp; ➖ Normal &nbsp;&nbsp;|&nbsp;&nbsp; ⭐ Çok Önemli",
        "run_btn": "🚀 GeoAI Analizini Başlat",
        "err_no_cat": "Lütfen en az bir tesis türü seçin!",
        "spin_msg": "Ajan mekansal analizi ve yorumlamayı yürütüyor...",
        "map_title": "### İnteraktif Harita",
        "target_home": "Hedef Ev",
        "report_title": "### 🤖 Ajan Raporu",
        "final_score": "Genel Değerlendirme Skoru",
        "penalty_txt": "Ceza Uygulandı",
        "view_mode": "Görünüm Modu:",
        "view_opts": ["Tüm Metrikler", "Sadece Kuş Bakışı", "Sadece Yürüme", "Sadece Araç"],
        "nf": "Bulunamadı",
        "new_search_btn": "🔄 Yeni Sorgu Yap",
        "download_btn": "📥 Görsel Raporu İndir",
        "prompt_select": "Soldan tercihlerinizi ayarlayın ve **GeoAI Analizini Başlat** butonuna tıklayın.",
        "col_fac": "Tesis",
        "col_score": "Uygunluk",
        "interp_title": "### 🧠 Yapay Zeka Ajanı Yorumu",
        "log_title": "### 📜 Ajan Karar Günlüğü",
        "warn_search": "⚠️ Harita sokak merkezine odaklandı. Kesin sonuç için lütfen haritadan tam binanızın üzerine tıklayın!",
        "succ_click": "✅ Bina konumu doğrulandı."
    }
}

# ==========================================
# LLM AYARLARI (HAFIZALI OTOMATİK MODEL KEŞFİ)
# ==========================================
@st.cache_resource(show_spinner=False)
def init_llm_model():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Modelleri sadece uygulama ilk açıldığında 1 kere listeler ve hafızaya yazar!
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if available_models:
            chosen_model_name = next((m for m in available_models if 'flash' in m), available_models[0])
            return genai.GenerativeModel(chosen_model_name)
        return None
    except Exception as e:
        print(f"GenAI Config Error: {e}")
        return None

llm_model = init_llm_model()
# ==========================================
# HELPER FUNCTIONS
# ==========================================
def md_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return text.replace("\n", "<br>")

def get_cat_config(cat_name):
    c = cat_name.lower()
    if "hospital" in c or "hastane" in c: return {"color": "green", "icon": "h-square", "prefix":"fa", "emoji": "🏥"}
    if "pharmacy" in c or "eczane" in c: return {"color": "red", "icon": "medkit", "prefix":"fa", "emoji": "💊"}
    if "veterin" in c: return {"color": "purple", "icon": "paw", "prefix":"fa", "emoji": "🐾"}
    if "metro" in c: return {"color": "blue", "icon": "subway", "prefix":"fa", "emoji": "🚇"}
    if "tram" in c: return {"color": "blue", "icon": "train", "prefix":"fa", "emoji": "🚋"}
    if "bus" in c or "otobüs" in c: return {"color": "blue", "icon": "bus", "prefix":"fa", "emoji": "🚌"}
    if "supermarket" in c or "market" in c: return {"color": "orange", "icon": "shopping-cart", "prefix":"fa", "emoji": "🛒"}
    if "park" in c: return {"color": "cadetblue", "icon": "tree", "prefix":"fa", "emoji": "🌳"}
    if "school" in c or "okul" in c or "lise" in c or "anaokulu" in c or "ortaokul" in c: return {"color": "lightred", "icon": "graduation-cap", "prefix":"fa", "emoji": "🏫"}
    if "mosque" in c or "cami" in c: return {"color": "darkgreen", "icon": "moon-o", "prefix":"fa", "emoji": "🕌"}
    if "church" in c or "kilise" in c: return {"color": "lightgray", "icon": "plus", "prefix":"fa", "emoji": "⛪"}
    if "synagogue" in c or "sinagog" in c: return {"color": "darkblue", "icon": "star", "prefix":"fa", "emoji": "🕍"}
    if "cemevi" in c: return {"color": "orange", "icon": "users", "prefix":"fa", "emoji": "📿"}
    return {"color": "gray", "icon": "info-circle", "prefix":"fa", "emoji": "📍"}

def format_duration(seconds):
    if seconds is None: return "--"
    if seconds < 60: return "<1 min"
    return f"{int(seconds // 60)} min"

# ==========================================
# MODULE 2: GEOSPATIAL DATA RETRIEVER (CACHED)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_facilities_from_osm(lat, lon, tags, radius=3000, retries=3):
    overpass_url = "http://overpass-api.de/api/interpreter"
    headers = {'User-Agent': 'HomeFitAgent/19.0'}
    tag_str = "".join([f'["{k}"="{v}"]' for k, v in tags.items()])
    overpass_query = f"[out:json][timeout:25];(node{tag_str}(around:{radius},{lat},{lon});way{tag_str}(around:{radius},{lat},{lon});relation{tag_str}(around:{radius},{lat},{lon}););out center;"
    
    for attempt in range(retries):
        try:
            response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return [(e['lat'], e['lon']) if e['type'] == 'node' else (e['center']['lat'], e['center']['lon']) for e in data.get('elements', [])]
            elif response.status_code == 429: time.sleep(1.5 * (attempt + 1))
            else: break
        except: time.sleep(1)
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_network_data(lat1, lon1, lat2, lon2, retries=2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 'Ok':
                    drive_dist = data['routes'][0]['distance'] 
                    return drive_dist * 0.95, (drive_dist * 0.95) / 1.38, drive_dist, data['routes'][0]['duration'] 
            elif response.status_code == 429: time.sleep(1)
        except: time.sleep(0.5)
    return None, None, None, None

# ==========================================
# MODULE 3: SPATIAL ACCESSIBILITY ANALYZER
# ==========================================
def process_single_category(cat_name, info, user_lat, user_lon):
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
        metrics = {"bird": round(min_be_dist, 1), "walk_d": round(walk_dist, 1), "walk_t": format_duration(walk_dur), "drive_d": round(drive_dist, 1), "drive_t": format_duration(drive_dur)}
    else:
        score, nearest_coord, metrics = (-50 if weight == 2 else 0), None, None
        
    return cat_name, score, weight, nearest_coord, metrics

def get_score_from_distance(distance):
    if distance <= 300: return 100
    elif distance <= 600: return 80
    elif distance <= 1200: return 60
    elif distance <= 2500: return 40
    return 0

# ==========================================
# MODULE 4: SCORING & RECOMMENDATION ENGINE
# ==========================================
def home_fit_agent_decision(user_lat, user_lon, selected_categories):
    results = {}
    total_weighted_score, total_weight = 0, 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_single_category, c_name, info, user_lat, user_lon) for c_name, info in selected_categories.items()]
        for future in concurrent.futures.as_completed(futures):
            cat_name, score, weight, nearest_coord, metrics = future.result()
            total_weighted_score += (score * weight)
            total_weight += weight
            results[cat_name] = {"score": score, "nearest": nearest_coord, "metrics": metrics}
            
    final_score = total_weighted_score / total_weight if total_weight > 0 else 0
    return round(max(0, final_score), 2), results

def generate_agent_interpretation(final_score, details, lang="TR"):
    if not details or llm_model is None:
        return "LLM API Key eksik, uygun model bulunamadı veya analiz sonucu üretilemedi." if lang == "TR" else "LLM API Key missing, model not found, or no analysis results."

    raw_data = f"Genel Skor: {final_score}/100\n"
    for cat, data in details.items():
        if data['metrics']:
            raw_data += f"- {cat}: Puanı {max(0, data['score'])}, Yürüme: {data['metrics']['walk_d']}m, Araç: {data['metrics']['drive_d']}m\n"

    if lang == "TR":
        prompt = f"""
        Sen uzman bir gayrimenkul, şehir planlama ve coğrafi bilgi sistemleri (GIS) asistanısın. 
        Müşterin bir ev konumu seçti ve aşağıdaki analiz verileri elde edildi:
        
        {raw_data}
        
        Görevlerin:
        1. Bu verileri kullanarak müşteriye 2 veya 3 paragraflık, profesyonel ama samimi bir değerlendirme yaz.
        2. Sadece sayıları tekrar etme; bu mesafelerin günlük yaşam kalitesini (yürüme kolaylığı, trafik, acil durumlar, sosyalleşme vb.) nasıl etkileyeceğini yorumla.
        3. Metnin sonuna 1 cümlelik kısa bir genel özet (tavsiye) ekle.
        """
    else:
        prompt = f"""
        You are an expert real estate, urban planning, and GIS AI assistant. 
        Your client selected a home location and the following analysis data was generated:
        
        {raw_data}
        
        Tasks:
        1. Write a 2 or 3 paragraph professional yet friendly evaluation for the client based on this data.
        2. Do not just repeat numbers; interpret how these distances affect daily life quality (walkability, emergencies, socializing, etc.).
        3. Add a 1-sentence final verdict/recommendation at the end.
        """

    try:
        response = llm_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"LLM Yanıt veremedi. Hata: {e}"

def generate_agent_decision_log(selected_categories, lang="EN"):
    selected_count = len(selected_categories)
    crucial = [cat for cat, info in selected_categories.items() if info["weight"] == 2]
    normal = [cat for cat, info in selected_categories.items() if info["weight"] == 1]

    if lang == "EN":
        return f"1. The agent received **{selected_count} selected facility categories** from the user.\n2. Categories marked as ignored were excluded from the analysis.\n3. The agent identified **{len(crucial)} crucial** and **{len(normal)} normal** preference categories.\n4. For each selected category, the agent retrieved relevant OpenStreetMap POI data.\n5. The nearest facility was identified using geodesic distance.\n6. Network-based accessibility metrics were estimated for walking and driving.\n7. A weighted suitability score was calculated based on the user's preference levels."
    else:
        return f"1. Ajan, kullanıcıdan **{selected_count} adet seçili tesis kategorisi** aldı.\n2. 'Yok Say' olarak işaretlenen kategoriler analizden dışlandı.\n3. Ajan, **{len(crucial)} çok önemli** ve **{len(normal)} normal** tercih kategorisi belirledi.\n4. Seçilen her kategori için OpenStreetMap'ten ilgili POI verileri çekildi.\n5. Kuş uçuşu mesafe kullanılarak en yakın tesisler tespit edildi.\n6. Yürüme ve araç kullanımı için ağ tabanlı erişilebilirlik metrikleri hesaplandı.\n7. Kullanıcının tercih seviyelerine dayalı olarak ağırlıklı bir uygunluk skoru üretildi."

# ==========================================
# UI RENDER LOGIC
# ==========================================
col1, col2 = st.columns([8, 2])
with col2:
    selected_lang = st.radio("Language / Dil", ["EN", "TR"], horizontal=True, label_visibility="collapsed")

t = LANG[selected_lang]

if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'user_lat' not in st.session_state: st.session_state.user_lat = 41.1044
if 'user_lon' not in st.session_state: st.session_state.user_lon = 29.0284
if 'address_options' not in st.session_state: st.session_state.address_options = None
if 'loc_method' not in st.session_state: st.session_state.loc_method = "default"

st.title(t["title"])

with st.expander(t["search_title"], expanded=True):
    st.caption(t["search_hint"])
    col_s1, col_s2 = st.columns([4, 1])
    search_query = col_s1.text_input("Adres", label_visibility="collapsed", placeholder=t["search_ph"])
    
    if col_s2.button(t["search_btn"]):
        geolocator = Nominatim(user_agent="homefit_explorer")
        locations = geolocator.geocode(search_query, exactly_one=False, limit=8, country_codes="tr")
        if locations: st.session_state.address_options = {loc.address: loc for loc in locations}
        else:
            st.error(t["not_found"])
            st.session_state.address_options = None

    if st.session_state.address_options:
        st.write("---")
        selected_address_name = st.selectbox(t["select_closest"], list(st.session_state.address_options.keys()))
        if st.button(t["set_loc_btn"]):
            selected_loc = st.session_state.address_options[selected_address_name]
            st.session_state.user_lat, st.session_state.user_lon = selected_loc.latitude, selected_loc.longitude
            st.session_state.analysis_results = None
            st.session_state.address_options = None 
            st.session_state.loc_method = "search"
            st.rerun()

# ----------------- SIDEBAR (PREFERENCE INTERPRETER) -----------------
st.sidebar.header(t["prefs_title"])
st.sidebar.markdown(f"<div style='background-color:#1e1e1e; padding:12px; border-radius:8px; text-align:center; font-size:15px; margin-bottom:20px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);'><b>{t['legend']}</b></div>", unsafe_allow_html=True)
selected_prefs = {}

def render_pref(label_en, label_tr, base_tags=None, opts_dict=None):
    disp_label = label_en if selected_lang == "EN" else label_tr
    c1, c2 = st.sidebar.columns([1, 1])
    with c1: st.markdown(f"<div style='margin-top:12px; font-size:16px; white-space: nowrap;'><b>{disp_label}</b></div>", unsafe_allow_html=True)
    with c2: imp = st.radio(f"w_{label_en}", ["❌", "➖", "⭐"], horizontal=True, label_visibility="collapsed")
    weight = {"❌": 0, "➖": 1, "⭐": 2}[imp]

    if weight > 0:
        if opts_dict:
            opt_keys = list(opts_dict.keys())
            selected_subs = st.sidebar.multiselect(" ", opt_keys, default=[opt_keys[0]], key=f"sel_{label_en}", label_visibility="collapsed")
            for sub in selected_subs: selected_prefs[f"{disp_label} ({sub.split('/')[0].strip()})"] = {"tags": opts_dict[sub], "weight": weight}
        else: selected_prefs[disp_label] = {"tags": base_tags, "weight": weight}
            
    st.sidebar.markdown("<hr style='margin: 10px 0; border-top: 1px dashed #333;'>", unsafe_allow_html=True)

render_pref("Hospital", "Hastane", base_tags={"amenity": "hospital"})
render_pref("Pharmacy", "Eczane", base_tags={"amenity": "pharmacy"})
render_pref("Veterinary", "Veteriner", base_tags={"amenity": "veterinary"})
render_pref("Supermarket", "Market", base_tags={"shop": "supermarket"})
render_pref("Park", "Park", base_tags={"leisure": "park"})
render_pref("Public Transit", "Toplu Taşıma", opts_dict={"Bus / Otobüs": {"highway": "bus_stop"}, "Metro / Subway": {"station": "subway"}, "Tram / Tramvay": {"railway": "tram_stop"}})
render_pref("School", "Okul", opts_dict={"Kindergarten / Anaokulu": {"amenity": "kindergarten"}, "Primary / İlkokul": {"amenity": "school", "school": "primary"}, "Middle / Ortaokul": {"amenity": "school", "school": "secondary"}, "High / Lise": {"amenity": "school"}})
render_pref("Worship", "İbadethane", opts_dict={"Mosque / Cami": {"amenity": "place_of_worship", "religion": "muslim"}, "Church / Kilise": {"amenity": "place_of_worship", "religion": "christian"}, "Synagogue / Sinagog": {"amenity": "place_of_worship", "religion": "jewish"}, "Cemevi": {"amenity": "place_of_worship", "religion": "alevi"}})

# KOTA KORUMASI: Yalnızca butona tıklandığında LLM çalışır ve hafızaya kaydedilir
if st.sidebar.button(t["run_btn"], use_container_width=True):
    if not selected_prefs: st.sidebar.error(t["err_no_cat"])
    else:
        with st.spinner(t["spin_msg"]):
            score, details = home_fit_agent_decision(st.session_state.user_lat, st.session_state.user_lon, selected_prefs)
            llm_yorum = generate_agent_interpretation(score, details, selected_lang)
            st.session_state.analysis_results = {
                "score": score, 
                "details": details, 
                "selected_prefs": selected_prefs,
                "llm_yorum": llm_yorum
            }

# ----------------- MAIN LAYOUT -----------------
col_map, col_res = st.columns([2, 3]) 

if st.session_state.loc_method == "search":
    st.warning(t["warn_search"])
elif st.session_state.loc_method == "map_click":
    st.success(t["succ_click"])

m = folium.Map(location=[st.session_state.user_lat, st.session_state.user_lon], zoom_start=15)
folium.Marker([st.session_state.user_lat, st.session_state.user_lon], popup=f"<b>{t['target_home']}</b>", icon=folium.Icon(color='black', icon='home')).add_to(m)

if st.session_state.analysis_results:
    for cat, data in st.session_state.analysis_results["details"].items():
        if data["nearest"]:
            cfg = get_cat_config(cat)
            folium.Marker(location=data["nearest"], popup=cat, icon=folium.Icon(color=cfg["color"], icon=cfg["icon"], prefix=cfg["prefix"])).add_to(m)
            folium.PolyLine(locations=[[st.session_state.user_lat, st.session_state.user_lon], data["nearest"]], color=cfg["color"], weight=2, opacity=0.5, dash_array='5').add_to(m)

with col_map:
    st.write(t["map_title"])
    map_display = st_folium(m, width=500, height=550, key="main_map")
    if map_display['last_clicked']:
        if st.session_state.analysis_results is None:
            nl, nln = map_display['last_clicked']['lat'], map_display['last_clicked']['lng']
            if nl != st.session_state.user_lat:
                st.session_state.user_lat, st.session_state.user_lon = nl, nln
                st.session_state.loc_method = "map_click"
                st.rerun()

with col_res:
    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        st.write(t["report_title"])
        
        s_color = "normal" if res['score'] > 0 else "inverse"
        st.metric(t["final_score"], f"{res['score']}/100", delta=t["penalty_txt"] if res['score'] <= 0 else None, delta_color=s_color)
        
        v_mode = st.radio(t["view_mode"], t["view_opts"], horizontal=True)
        
        df_data = []
        for cat, data in res['details'].items():
            metrics = data['metrics']
            cfg = get_cat_config(cat)
            visual_score = max(0, data['score']) 
            row = {t["col_fac"]: f"{cfg['emoji']} {cat}", t["col_score"]: visual_score}
            
            if metrics:
                if v_mode in [t["view_opts"][0], t["view_opts"][1]]: row["Bird's-eye" if selected_lang=="EN" else "Kuş Bakışı"] = f"{metrics['bird']}m"
                if v_mode in [t["view_opts"][0], t["view_opts"][2]]: row["Walking" if selected_lang=="EN" else "Yürüme"] = f"{metrics['walk_d']}m ({metrics['walk_t']})"
                if v_mode in [t["view_opts"][0], t["view_opts"][3]]: row["Driving" if selected_lang=="EN" else "Araç"] = f"{metrics['drive_d']}m ({metrics['drive_t']})"
            else:
                nf_txt = t["nf"]
                if v_mode in [t["view_opts"][0], t["view_opts"][1]]: row["Bird's-eye" if selected_lang=="EN" else "Kuş Bakışı"] = nf_txt
                if v_mode in [t["view_opts"][0], t["view_opts"][2]]: row["Walking" if selected_lang=="EN" else "Yürüme"] = nf_txt
                if v_mode in [t["view_opts"][0], t["view_opts"][3]]: row["Driving" if selected_lang=="EN" else "Araç"] = nf_txt
            df_data.append(row)
            
        st.dataframe(pd.DataFrame(df_data), column_config={t["col_score"]: st.column_config.ProgressColumn(t["col_score"], format="%d", min_value=0, max_value=100)}, hide_index=True, use_container_width=True)
        
        # --- AGENT INTERPRETATION & LOGGING (HAFIZADAN OKUNUR) ---
        agent_interp_text = res.get("llm_yorum", "LLM yanıtı hafızadan okunamadı.")
        agent_log_text = generate_agent_decision_log(res["selected_prefs"], selected_lang)
        
        st.markdown("---")
        st.markdown(t["interp_title"])
        st.info(agent_interp_text)
        
        st.markdown(t["log_title"])
        with st.expander("🔍 View Process Log", expanded=False):
            st.markdown(agent_log_text)
            
        # ==========================================
        # GÖRSEL RAPOR ÇIKTISI ALMA (HTML)
        # ==========================================
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>HomeFit Visual Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.05); }}
                h2 {{ color: #1e293b; text-align: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-top: 0; }}
                .score-box {{ background-color: #f0fdf4; color: #166534; padding: 15px; border-radius: 8px; font-size: 22px; font-weight: bold; text-align: center; margin: 20px 0; border: 1px solid #bbf7d0; }}
                .agent-box {{ background-color: #eff6ff; color: #1e3a8a; padding: 20px; border-radius: 8px; font-size: 14px; margin: 20px 0; border-left: 5px solid #3b82f6; }}
                .content-wrapper {{ display: flex; flex-direction: row; gap: 30px; align-items: flex-start; margin-top: 20px; }}
                .map-container {{ flex: 1; min-width: 400px; max-width: 500px; height: 500px; border: 2px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
                .table-container {{ flex: 2; overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                th, td {{ border: 1px solid #e2e8f0; padding: 12px 15px; text-align: left; }}
                th {{ background-color: #f1f5f9; color: #334155; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f8fafc; }}
                .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>{t['title']} - Visual Report</h2>
                <div class="score-box">Final Location Score: {res['score']} / 100</div>
                
                <div class="agent-box">
                    <h3 style="margin-top:0;">🧠 AI Agent Interpretation</h3>
                    <p>{md_to_html(agent_interp_text)}</p>
                </div>

                <div class="content-wrapper">
                    <div class="map-container">
                        {m.get_root().render()}
                    </div>
                    <div class="table-container">
                        {pd.DataFrame(df_data).to_html(index=False, justify='left', escape=False)}
                    </div>
                </div>
                
                <div class="footer">Generated by HomeFit Agent GeoAI Engine • Data © OpenStreetMap contributors</div>
            </div>
            <script>
                window.onload = function() {{ setTimeout(function(){{ window.print(); }}, 500); }}
            </script>
        </body>
        </html>
        """

        b1, b2 = st.columns([1, 1])
        with b1:
            st.download_button(
                label=t["download_btn"],
                data=html_content,
                file_name="HomeFit_Visual_Report.html",
                mime="text/html",
                use_container_width=True
            )
        with b2:
            if st.button(t["new_search_btn"], use_container_width=True):
                st.session_state.analysis_results = None
                st.rerun()
    else:
        st.info(t["prompt_select"])
