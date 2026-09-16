import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Fullscreen, MeasureControl
import json, os, io
import pandas as pd

st.set_page_config(page_title="Pakani Smart Map", layout="wide", page_icon="📍")

PAKANI_LAT, PAKANI_LON = 17.6205, 75.8820
APPROVED_FILE = "pakani_houses.json"
PENDING_FILE = "pakani_pending.json"
PASSWORD = "pakani123"

def load_json(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []
def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

if 'auto_lat' not in st.session_state: st.session_state.auto_lat = ""
if 'auto_lon' not in st.session_state: st.session_state.auto_lon = ""
if 'admin_lat' not in st.session_state: st.session_state.admin_lat = ""
if 'admin_lon' not in st.session_state: st.session_state.admin_lon = ""
if 'search_query' not in st.session_state: st.session_state.search_query = ""

houses = load_json(APPROVED_FILE)
pending = load_json(PENDING_FILE)

st.markdown("<h2 style='text-align:center;'>📍 पाकणी स्मार्ट व्हिलेज - Google Map Style</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️ MAP + Search", "🏠 Add My House", "🔐 Admin"])

# ================= TAB 1 - GOOGLE MAP LIKE =================
with tab1:
    # --- SEARCH + VOICE (WORKS ON STREAMLIT CLOUD) ---
    st.markdown("#### 🔍 Search + Voice")
    col_s1, col_s2 = st.columns([4,1])
    with col_s1:
        search_input = st.text_input("search", value=st.session_state.search_query, placeholder="Naam likho... Ex: Patil", label_visibility="collapsed", key="search_box")
    with col_s2:
        # HTML Voice Input - Works 100% on phone
        st.components.v1.html("""
            <button onclick="startDictation()" style="width:100%;height:38px;background:#FF4B4B;color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;">🎙️ Bolo</button>
            <script>
            function startDictation() {
                if (window.hasOwnProperty('webkitSpeechRecognition') || window.hasOwnProperty('SpeechRecognition')) {
                    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    var recognition = new SpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = "mr-IN";
                    recognition.start();
                    recognition.onresult = function(e) {
                        var text = e.results[0][0].transcript;
                        const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
                        if(input){
                            input.value = text;
                            input.dispatchEvent(new Event('input', {bubbles:true}));
                        }
                        recognition.stop();
                    };
                    recognition.onerror = function(e){ recognition.stop(); }
                } else { alert("Voice support nahi hai is browser me - Chrome use karo"); }
            }
            </script>
        """, height=45)

    final_search = search_input or st.session_state.search_query

    # PRIVACY FILTER
    def is_visible(house, search_text):
        privacy = house.get('privacy', 'Private')
        if privacy == 'Public': return True
        if privacy == 'Hidden': return False
        if privacy == 'Private':
            if not search_text: return False
            return search_text.lower() in house['name'].lower() or search_text.lower() in house.get('family','').lower()
        return True

    filtered = [h for h in houses if is_visible(h, final_search)]
    if final_search: st.success(f"Found: {len(filtered)} for '{final_search}'")
    else: st.info(f"Public Houses: {len(filtered)} | Search karo toh Private ghar bhi milenge")

    # GOOGLE MAP LIKE - MULTIPLE LAYERS
    m = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=18, control_scale=True, tiles=None)

    # 1. Normal Map
    folium.TileLayer('OpenStreetMap', name='🗺️ Normal Map').add_to(m)
    # 2. Satellite - Esri (Google jaisa)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='🛰️ Satellite - 3D View').add_to(m)
    # 3. Satellite with Labels - Google Hybrid Jaisa
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='🌍 Satellite + Labels (Google)').add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google', name='🚗 Google Road').add_to(m)
    folium.TileLayer('Stamen Terrain', name='⛰️ Terrain - 3D').add_to(m)

    LocateControl(auto_start=True, flyTo=True, strings={'title': 'Meri Location'}).add_to(m)
    Fullscreen(position='topleft', title='Full Screen - 3D Feel').add_to(m)
    MeasureControl().add_to(m)

    folium.Marker([PAKANI_LAT, PAKANI_LON], tooltip="Gram Panchayat - Pakani", icon=folium.Icon(color="green", icon="star", prefix='fa')).add_to(m)

    for h in filtered:
        folium.Marker([h['lat'], h['lon']],
            popup=folium.Popup(f"<b>{h['name']}</b><br>House:{h.get('house_no','')}<br>Ward:{h.get('ward','')}<br>Family:{h.get('family','')}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 Rasta Dekho (Google)</a>", max_width=250),
            tooltip=f"🏠 {h['name']}", icon=folium.Icon(color="red", icon="home", prefix='fa')).add_to(m)

    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    st_folium(m, width=1200, height=600, key="main_map_final")

# ================= TAB 2 VILLAGER =================
with tab2:
    st.subheader("🏠 माझे घर जोडा")
    st.info("Map pe apne ghar pe CLICK karo -> Location auto lock hoga")
    m2 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    LocateControl(auto_start=True).add_to(m2)
    Fullscreen().add_to(m2)
    data2 = st_folium(m2, width=1200, height=400, returned_objects=["last_clicked"], key="map2_final")
    if data2.get("last_clicked"):
        st.session_state.auto_lat = str(data2["last_clicked"]["lat"])
        st.session_state.auto_lon = str(data2["last_clicked"]["lng"])
    if st.session_state.auto_lat: st.success(f"✅ Locked: {st.session_state.auto_lat}, {st.session_state.auto_lon}")

    with st.form("villager_form_final"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *")
            house_no = st.text_input("House No")
            mobile = st.text_input("Mobile")
        with c2:
            ward = st.text_input("Ward / Galli")
            family = st.text_area("Family Members")
        if st.form_submit_button("📤 Admin ko Bhejo", use_container_width=True):
            if not name or not st.session_state.auto_lat:
                st.error("Pehle Map pe CLICK karo!")
            else:
                pending.append({"name": name, "house_no": house_no, "ward": ward, "mobile": mobile, "family": family, "lat": float(st.session_state.auto_lat), "lon": float(st.session_state.auto_lon), "privacy": "Private"})
                save_json(PENDING_FILE, pending)
                st.success(f"✅ {name} - Admin approve karega")
                st.balloons()
                st.session_state.auto_lat = ""; st.session_state.auto_lon = ""

# ================= TAB 3 ADMIN =================
with tab3:
    pwd = st.text_input("Admin Password", type="password")
    if pwd == PASSWORD:
        st.success(f"ADMIN KING | Total {len(houses)} | Pending {len(pending)}")
        t1, t2, t3a = st.tabs(["✅ Pending", "➕ Direct Add", "🔒 Privacy Control"])
        with t1:
            for i, h in enumerate(pending[:]):
                with st.container(border=True):
                    st.write(f"**{h['name']}** | W:{h.get('ward','')} | F:{h.get('family','')}")
                    p_choice = st.selectbox("Set Privacy", ["Private","Public","Hidden"], key=f"p_{i}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"ap{i}"):
                        h['privacy']=p_choice; houses.append(h); pending.remove(h)
                        save_json(APPROVED_FILE, houses); save_json(PENDING_FILE, pending); st.rerun()
                    if c2.button("❌ Reject", key=f"re{i}"):
                        pending.remove(h); save_json(PENDING_FILE, pending); st.rerun()
        with t2:
            m3 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
            data3 = st_folium(m3, width=1200, height=300, returned_objects=["last_clicked"], key="m3_final")
            if data3.get("last_clicked"):
                st.session_state.admin_lat = str(data3["last_clicked"]["lat"])
                st.session_state.admin_lon = str(data3["last_clicked"]["lng"])
            if st.session_state.admin_lat: st.success(f"✅ {st.session_state.admin_lat}, {st.session_state.admin_lon}")
            with st.form("admin_direct_final"):
                aname = st.text_input("Name *")
                ahouse = st.text_input("House No")
                award = st.text_input("Ward")
                afam = st.text_area("Family")
                aprivacy = st.selectbox("Privacy", ["Private","Public","Hidden"])
                if st.form_submit_button("Add"):
                    if not aname or not st.session_state.admin_lat: st.error("Map click karo")
                    else:
                        houses.append({"name":aname,"house_no":ahouse,"ward":award,"family":afam,"lat":float(st.session_state.admin_lat),"lon":float(st.session_state.admin_lon),"privacy":aprivacy})
                        save_json(APPROVED_FILE, houses); st.success("Added")
        with t3a:
            for idx, h in enumerate(houses):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3,2,1])
                    c1.write(f"**{h['name']}** - Now: {h.get('privacy','Private')}")
                    new_p = c2.selectbox("Change", ["Public","Private","Hidden"], index=["Public","Private","Hidden"].index(h.get('privacy','Private')), key=f"ch_{idx}")
                    if c3.button("Save", key=f"sv_{idx}"):
                        houses[idx]['privacy']=new_p; save_json(APPROVED_FILE, houses); st.rerun()