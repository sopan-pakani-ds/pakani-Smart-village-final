import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Fullscreen
import json, os
import pandas as pd

st.set_page_config(page_title="Pakani Smart Map", layout="wide", page_icon="📍")

PAKANI_LAT, PAKANI_LON = 17.6205, 75.8820
APPROVED_FILE = "pakani_houses.json"
PENDING_FILE = "pakani_pending.json"
PASSWORD = "pakani123"

def load_json(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'auto_lat' not in st.session_state: st.session_state.auto_lat = ""
if 'auto_lon' not in st.session_state: st.session_state.auto_lon = ""
if 'admin_lat' not in st.session_state: st.session_state.admin_lat = ""
if 'admin_lon' not in st.session_state: st.session_state.admin_lon = ""
if 'search_query' not in st.session_state: st.session_state.search_query = ""

houses = load_json(APPROVED_FILE)
pending = load_json(PENDING_FILE)

st.markdown("<h2 style='text-align:center;'>📍 पाकणी स्मार्ट व्हिलेज</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Google Map Style | Satellite + Voice Search</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️ MAP + Search", "🏠 Add My House", "🔐 Admin - King"])

# ================= TAB 1 - MAP FIXED =================
with tab1:
    col1, col2 = st.columns([4,1])
    with col1:
        search_input = st.text_input("search", placeholder="Naam search karo...", label_visibility="collapsed")
    with col2:
        st.components.v1.html("""
            <button onclick="startDictation()" style="width:100%;height:38px;background:#FF4B4B;color:white;border:none;border-radius:8px;font-size:16px;">🎙️ Bolo</button>
            <script>
            function startDictation(){
              var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
              if(!SR){ alert("Chrome me kholo"); return; }
              var r = new SR(); r.lang="mr-IN"; r.start();
              r.onresult = function(e){
                var t = e.results[0][0].transcript;
                var inp = window.parent.document.querySelector('input[type="text"]');
                if(inp){ inp.value=t; inp.dispatchEvent(new Event('input',{bubbles:true})); }
              }
            }
            </script>
        """, height=50)

    final_search = search_input

    def is_visible(h, s):
        p = h.get('privacy','Private')
        if p == 'Public': return True
        if p == 'Hidden': return False
        if p == 'Private':
            if not s: return False
            return s.lower() in h['name'].lower() or s.lower() in h.get('family','').lower()
        return True

    filtered = [h for h in houses if is_visible(h, final_search)]

    if final_search:
        st.success(f"Found {len(filtered)} for '{final_search}'")
    else:
        st.info(f"Public Houses: {len(filtered)} | Search karo toh Private bhi milenge")

    # --- MAP - 100% WORKING - NO STAMEN ERROR ---
    m = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=18, tiles=None, control_scale=True)

    folium.TileLayer('OpenStreetMap', name='🗺️ Normal').add_to(m)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='🛰️ Satellite').add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='🌍 Google Hybrid').add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google', name='🚗 Google Road').add_to(m)

    LocateControl(auto_start=True, flyTo=True).add_to(m)
    Fullscreen().add_to(m)

    folium.Marker([PAKANI_LAT, PAKANI_LON], tooltip="Gram Panchayat Pakani", icon=folium.Icon(color="green", icon="star")).add_to(m)

    for h in filtered:
        folium.Marker([h['lat'], h['lon']],
            popup=f"<b>{h['name']}</b><br>House:{h.get('house_no','')}<br>Ward:{h.get('ward','')}<br>Family:{h.get('family','')}<br>Privacy:{h.get('privacy','')}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 Rasta Dekho</a>",
            tooltip=f"🏠 {h['name']}", icon=folium.Icon(color="red", icon="home")).add_to(m)

    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    st_folium(m, width=1200, height=600, key="main_map")

# ================= TAB 2 - VILLAGER =================
with tab2:
    st.subheader("🏠 माझे घर जोडा")
    st.warning("Map pe apne ghar pe CLICK karo - Location auto lock hoga - Private rahega")

    m2 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    LocateControl(auto_start=True).add_to(m2)
    Fullscreen().add_to(m2)
    data2 = st_folium(m2, width=1200, height=350, returned_objects=["last_clicked"], key="map2")

    if data2.get("last_clicked"):
        st.session_state.auto_lat = str(data2["last_clicked"]["lat"])
        st.session_state.auto_lon = str(data2["last_clicked"]["lng"])

    if st.session_state.auto_lat:
        st.success(f"✅ Locked: {st.session_state.auto_lat}, {st.session_state.auto_lon}")
    else:
        st.info("📍 Map pe CLICK karo")

    with st.form("villager_form"):
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
                st.error("Map pe click karo!")
            else:
                pending.append({"name":name,"house_no":house_no,"ward":ward,"mobile":mobile,"family":family,"lat":float(st.session_state.auto_lat),"lon":float(st.session_state.auto_lon),"privacy":"Private"})
                save_json(PENDING_FILE, pending)
                st.success(f"✅ {name} sent - Admin approve karega")
                st.balloons()
                st.session_state.auto_lat=""; st.session_state.auto_lon=""

# ================= TAB 3 - ADMIN KING =================
with tab3:
    pwd = st.text_input("Admin Password", type="password")
    if pwd == PASSWORD:
        st.success(f"ADMIN ON | Total {len(houses)} | Pending {len(pending)}")
        t1, t2, t3a = st.tabs(["✅ Pending", "➕ Direct Add", "🔒 Privacy Control"])

        with t1:
            if not pending: st.info("No pending")
            for i, h in enumerate(pending[:]):
                with st.container(border=True):
                    st.write(f"**{h['name']}** | Ward:{h.get('ward','')} | Family:{h.get('family','')}")
                    p_choice = st.selectbox("Privacy", ["Private","Public","Hidden"], key=f"p_{i}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"a_{i}"):
                        h['privacy']=p_choice
                        houses.append(h)
                        pending.remove(h)
                        save_json(APPROVED_FILE, houses)
                        save_json(PENDING_FILE, pending)
                        st.rerun()
                    if c2.button("❌ Reject", key=f"r_{i}"):
                        pending.remove(h)
                        save_json(PENDING_FILE, pending)
                        st.rerun()

        with t2:
            m3 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
            LocateControl(auto_start=True).add_to(m3)
            data3 = st_folium(m3, width=1200, height=300, returned_objects=["last_clicked"], key="m3")
            if data3.get("last_clicked"):
                st.session_state.admin_lat = str(data3["last_clicked"]["lat"])
                st.session_state.admin_lon = str(data3["last_clicked"]["lng"])
            if st.session_state.admin_lat: st.success(f"✅ {st.session_state.admin_lat}, {st.session_state.admin_lon}")
            with st.form("admin_add"):
                aname = st.text_input("Name *")
                ahouse = st.text_input("House No")
                award = st.text_input("Ward")
                afam = st.text_area("Family")
                apriv = st.selectbox("Privacy - King Power", ["Private","Public","Hidden"])
                if st.form_submit_button("Add Direct"):
                    if not aname or not st.session_state.admin_lat: st.error("Map click karo")
                    else:
                        houses.append({"name":aname,"house_no":ahouse,"ward":award,"family":afam,"lat":float(st.session_state.admin_lat),"lon":float(st.session_state.admin_lon),"privacy":apriv})
                        save_json(APPROVED_FILE, houses)
                        st.success("Added")

        with t3a:
            st.subheader("🔒 Sirf Admin Privacy Change Kar Sakta Hai")
            for idx, h in enumerate(houses):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3,2,1])
                    c1.write(f"**{h['name']}** - Now: {h.get('privacy','Private')}")
                    new_p = c2.selectbox("Change", ["Public","Private","Hidden"], index=["Public","Private","Hidden"].index(h.get('privacy','Private')), key=f"ch_{idx}")
                    if c3.button("Save", key=f"sv_{idx}"):
                        houses[idx]['privacy']=new_p
                        save_json(APPROVED_FILE, houses)
                        st.rerun()
    elif pwd:
        st.error("Wrong Password")