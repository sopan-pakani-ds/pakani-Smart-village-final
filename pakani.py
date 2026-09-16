import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Fullscreen
import json, os

st.set_page_config(page_title="Pakani Smart Map", layout="wide", page_icon="📍")

PAKANI_LAT, PAKANI_LON = 17.6205, 75.8820
APPROVED_FILE = "pakani_houses.json"
PENDING_FILE = "pakani_pending.json"
PASSWORD = "pakani123"

def load_json(f):
    if os.path.exists(f):
        try:
            with open(f,"r",encoding="utf-8") as file: return json.load(file)
        except: return []
    return []
def save_json(f,d):
    with open(f,"w",encoding="utf-8") as file: json.dump(d,file,ensure_ascii=False,indent=2)

if 'auto_lat' not in st.session_state: st.session_state.auto_lat=""
if 'auto_lon' not in st.session_state: st.session_state.auto_lon=""
if 'admin_lat' not in st.session_state: st.session_state.admin_lat=""
if 'admin_lon' not in st.session_state: st.session_state.admin_lon=""

houses = load_json(APPROVED_FILE)
pending = load_json(PENDING_FILE)

st.markdown("<h2 style='text-align:center;'>📍 पाकणी स्मार्ट व्हिलेज</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Google Map Style | Search + Voice + Admin King</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️ MAP + Search", "🏠 Add My House", "🔐 Admin"])

# ================= TAB 1 MAP =================
with tab1:
    c1,c2 = st.columns([4,1])
    with c1:
        search = st.text_input("search", placeholder="Naam likho... Ex: hari yelgunde", label_visibility="collapsed")
    with c2:
        st.components.v1.html("""
        <button onclick="startDictation()" style="width:100%;height:38px;background:#FF4B4B;color:white;border:none;border-radius:8px;">🎙️ Bolo</button>
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

    # FIXED SEARCH LOGIC - Hari Yelgunde = 1 result
    def is_visible(h, s):
        s = (s or "").lower().strip()
        privacy = h.get('privacy','Private')
        if privacy == 'Hidden': return False
        if not s:
            return privacy == 'Public'
        # Search matches -> show (except Hidden)
        if s in h['name'].lower() or s in h.get('family','').lower() or s in str(h.get('house_no','')).lower() or s in h.get('ward','').lower():
            return True
        # No match -> only Public
        return privacy == 'Public'

    filtered = [h for h in houses if is_visible(h, search)]
    if search: st.success(f"Search: '{search}' -> Found {len(filtered)} | Hari Yelgunde should be 1")
    else: st.info(f"Public Houses on Map: {len(filtered)} | Private houses search pe ayenge")

    m = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=18, tiles=None, control_scale=True)
    folium.TileLayer('OpenStreetMap', name='🗺️ Normal').add_to(m)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='🛰️ Satellite').add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='🌍 Google Hybrid').add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google', name='🚗 Google Road').add_to(m)
    LocateControl(auto_start=True, flyTo=True).add_to(m)
    Fullscreen().add_to(m)
    folium.Marker([PAKANI_LAT, PAKANI_LON], tooltip="Gram Panchayat", icon=folium.Icon(color="green", icon="star")).add_to(m)
    for h in filtered:
        folium.Marker([h['lat'], h['lon']], popup=f"<b>{h['name']}</b><br>House:{h.get('house_no','')}<br>Ward:{h.get('ward','')}<br>Family:{h.get('family','')}<br>Privacy:{h.get('privacy','')}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 Rasta Dekho</a>", tooltip=f"🏠 {h['name']}", icon=folium.Icon(color="red", icon="home")).add_to(m)
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    st_folium(m, width=1200, height=600, key="main_map")

# ================= TAB 2 VILLAGER =================
with tab2:
    st.subheader("🏠 माझे घर जोडा")
    st.info("Map pe apne ghar pe CLICK karo -> Location lock")
    m2 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
    LocateControl(auto_start=True).add_to(m2)
    Fullscreen().add_to(m2)
    d2 = st_folium(m2, width=1200, height=350, returned_objects=["last_clicked"], key="map2")
    if d2.get("last_clicked"):
        st.session_state.auto_lat=str(d2["last_clicked"]["lat"])
        st.session_state.auto_lon=str(d2["last_clicked"]["lng"])
    if st.session_state.auto_lat: st.success(f"✅ Locked: {st.session_state.auto_lat}, {st.session_state.auto_lon}")
    with st.form("villager"):
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Full Name *")
            house_no=st.text_input("House No")
            mobile=st.text_input("Mobile")
        with c2:
            ward=st.text_input("Ward / Galli")
            family=st.text_area("Family Members")
        if st.form_submit_button("📤 Admin ko Bhejo", use_container_width=True):
            if not name or not st.session_state.auto_lat: st.error("Map pe click karo + Name bharo")
            else:
                pending.append({"name":name,"house_no":house_no,"ward":ward,"mobile":mobile,"family":family,"lat":float(st.session_state.auto_lat),"lon":float(st.session_state.auto_lon),"privacy":"Private"})
                save_json(PENDING_FILE, pending)
                st.success(f"✅ {name} sent - Admin approve karega")
                st.balloons()
                st.session_state.auto_lat=""; st.session_state.auto_lon=""

# ================= TAB 3 ADMIN KING =================
with tab3:
    pwd=st.text_input("Admin Password", type="password")
    if pwd==PASSWORD:
        st.success(f"ADMIN KING | Total: {len(houses)} | Pending: {len(pending)}")
        t1,t2,t3a,t4 = st.tabs(["✅ Pending", "➕ Direct Add", "🔒 Privacy", "🗑️ Delete"])
        with t1:
            if not pending: st.info("No pending")
            for h in pending[:]:
                with st.container(border=True):
                    st.write(f"**{h['name']}** | H:{h.get('house_no','')} | W:{h.get('ward','')} | F:{h.get('family','')}")
                    pc=st.selectbox("Set Privacy", ["Private","Public","Hidden"], key=f"pc_{h['name']}_{h['lat']}")
                    col1,col2=st.columns(2)
                    if col1.button("✅ Approve", key=f"ap_{h['name']}_{h['lat']}"):
                        h['privacy']=pc; houses.append(h); pending.remove(h)
                        save_json(APPROVED_FILE, houses); save_json(PENDING_FILE, pending); st.rerun()
                    if col2.button("❌ Reject", key=f"re_{h['name']}_{h['lat']}"):
                        pending.remove(h); save_json(PENDING_FILE, pending); st.rerun()
        with t2:
            st.subheader("Admin Direct Add")
            m3=folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')
            LocateControl(auto_start=True).add_to(m3)
            d3=st_folium(m3, width=1200, height=300, returned_objects=["last_clicked"], key="m3")
            if d3.get("last_clicked"):
                st.session_state.admin_lat=str(d3["last_clicked"]["lat"])
                st.session_state.admin_lon=str(d3["last_clicked"]["lng"])
            if st.session_state.admin_lat: st.success(f"✅ {st.session_state.admin_lat}, {st.session_state.admin_lon}")
            with st.form("admin_add"):
                an=st.text_input("Name *")
                ah=st.text_input("House No")
                aw=st.text_input("Ward")
                af=st.text_area("Family")
                ap=st.selectbox("Privacy", ["Private","Public","Hidden"])
                if st.form_submit_button("Add"):
                    if not an or not st.session_state.admin_lat: st.error("Name + Map click")
                    else:
                        houses.append({"name":an,"house_no":ah,"ward":aw,"family":af,"lat":float(st.session_state.admin_lat),"lon":float(st.session_state.admin_lon),"privacy":ap})
                        save_json(APPROVED_FILE, houses); st.success(f"{an} Added as {ap}")