import streamlit as st
from streamlit_folium import st_folium
import folium, json, os, random
from folium.plugins import Fullscreen, LocateControl, MarkerCluster
import streamlit.components.v1 as components

st.set_page_config(page_title="Pakani - Admin Only", layout="wide", page_icon="📍")

DB_FILE = "pakani_houses.json"
ADMIN_PASS = "pakani123"
VILLAGE_LAT, VILLAGE_LON = 17.72303, 75.77398

def load_data():
    if not os.path.exists(DB_FILE):
        fn=["तुकाराम","शिवाजी","बाळू","दत्तात्रय"]; ln=["पाटील","शिंदे","जाधव"]
        d=[{"name":f"{random.choice(fn)} {random.choice(ln)}","house_no":f"{100+i}","landmark":"मंदिराजवळ","lat":VILLAGE_LAT+random.uniform(-0.008,0.008),"lon":VILLAGE_LON+random.uniform(-0.008,0.008)} for i in range(60)]
        with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
    with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)

def save_data(data):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)

houses = load_data()

# --- ADMIN LOGIN SIDEBAR ---
st.sidebar.title("🔐 Admin Panel")
st.sidebar.caption("Only Admin can add house")

if "admin" not in st.session_state:
    st.session_state.admin = False

if not st.session_state.admin:
    pwd = st.sidebar.text_input("Admin Password", type="password", placeholder="pakani123")
    if st.sidebar.button("Login", use_container_width=True):
        if pwd == ADMIN_PASS:
            st.session_state.admin = True
            st.sidebar.success("✅ Admin Login Success")
            st.rerun()
        else:
            st.sidebar.error("❌ Wrong Password")
    st.sidebar.info("Villagers can only VIEW and SEARCH. Only Admin can ADD house.")
else:
    st.sidebar.success("✅ Admin Logged In")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.admin = False
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("🏠 Add New House - Pakani")
    with st.sidebar.form("add_house"):
        name = st.text_input("Full Name", placeholder="तुकाराम पाटील")
        hno = st.text_input("House No", placeholder="142")
        landmark = st.text_input("Landmark", placeholder="हनुमान मंदिराजवळ")
        lat = st.number_input("Latitude", value=VILLAGE_LAT, format="%.6f")
        lon = st.number_input("Longitude", value=VILLAGE_LON, format="%.6f")
        st.caption("Tip: Click on map to get lat/lon, then type here")
        add_btn = st.form_submit_button("➕ Add House", use_container_width=True, type="primary")
        if add_btn:
            if name and hno:
                houses.append({"name":name,"house_no":hno,"landmark":landmark,"lat":lat,"lon":lon})
                save_data(houses)
                st.sidebar.success(f"✅ {name} Added!")
                st.rerun()
            else:
                st.sidebar.error("Name and House No required")

    st.sidebar.divider()
    st.sidebar.write(f"Total Houses: {len(houses)}")
    if st.sidebar.button("🗑️ Delete Last House (Admin)", use_container_width=True):
        if houses:
            houses.pop()
            save_data(houses)
            st.sidebar.warning("Last house deleted")
            st.rerun()

# --- MAIN APP - GOOGLE MAPS STYLE ---
st.markdown("<h2 style='text-align:center'>📍 पाकणी Smart Village - Google Maps</h2>", unsafe_allow_html=True)

# Voice Search Button
components.html("""
<div style="text-align:center">
  <button id="voiceBtn" style="background:#1a73e8; color:white; border:none; padding:12px 28px; border-radius:24px; font-size:16px; cursor:pointer">
    🎙️ बोला - नाव बोला
  </button>
  <p id="status" style="color:#1a73e8; margin-top:6px; font-size:13px">बोला - उदा. 'पाटील'</p>
  <script>
    const btn=document.getElementById('voiceBtn'); const status=document.getElementById('status');
    btn.onclick=()=>{
      const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
      if(!SR){status.innerText='Chrome मध्येच चालते'; return;}
      const rec=new SR(); rec.lang='mr-IN'; status.innerText='🎧 ऐकतोय...'; btn.style.background='#ea4335'; rec.start();
      rec.onresult=(e)=>{ const t=e.results[0][0].transcript; status.innerText='✅ '+t; const url=new URL(window.parent.location.href); url.searchParams.set('voice_search',t); window.parent.location.href=url.toString(); };
      rec.onerror=()=>{status.innerText='❌ परत प्रयत्न करा'; btn.style.background='#1a73e8';};
      rec.onend=()=>{btn.style.background='#1a73e8';};
    }
  </script>
</div>
""", height=80)

voice = st.query_params.get("voice_search","")
search_default = voice if voice else ""

c1,c2,c3 = st.columns([1,2,1])
with c2:
    search = st.text_input("", value=search_default, placeholder="🔍 टाइप करा किंवा 🎙️ बोला", label_visibility="collapsed")

filtered = [h for h in houses if search.lower() in f"{h['name']} {h['house_no']}".lower()] if search else houses

map_type = st.radio("", ["🗺️ Map", "🛰️ Satellite", "🏔️ Terrain 3D"], horizontal=True, label_visibility="collapsed")
st.caption(f"✅ {len(filtered)} घरे | {'🔐 Admin Mode' if st.session_state.admin else '👁️ View Only Mode'}")

# Map
m = folium.Map(location=[VILLAGE_LAT, VILLAGE_LON], zoom_start=18, tiles=None)
if "Map" in map_type:
    folium.TileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google Map').add_to(m)
elif "Satellite" in map_type:
    folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Satellite').add_to(m)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Hybrid', opacity=0.6).add_to(m)
else:
    folium.TileLayer('https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', attr='Terrain').add_to(m)

Fullscreen(position="topright").add_to(m)
LocateControl(position="topright", flyTo=True, strings={"title":"📍 माझे लोकेशन"}).add_to(m)

cluster = MarkerCluster().add_to(m)
for h in filtered[:120]:
    dir_url = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
    folium.Marker([h['lat'],h['lon']], popup=f"<b>{h['name']}</b><br>#{h['house_no']}<br><a href='{dir_url}' target='_blank'>🧭 Directions</a>", tooltip=h['name'], icon=folium.Icon(color="red", icon="home")).add_to(cluster)

map_data = st_folium(m, height=550, width=1200, returned_objects=["last_object_clicked"])

if map_data and map_data.get("last_object_clicked") and st.session_state.admin:
    st.info(f"Admin: Clicked Lat: {map_data['last_object_clicked']['lat']:.6f}, Lon: {map_data['last_object_clicked']['lng']:.6f} - Use this in sidebar form")

# List
st.divider()
st.subheader(f"📋 {len(filtered)} Houses")
for h in filtered[:15]:
    with st.container(border=True):
        a,b = st.columns([4,1])
        with a: st.markdown(f"**{h['name']}** `#{h['house_no']}` - {h['landmark']}")
        with b: st.link_button("🧭 दिशा", f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}", use_container_width=True)

if not st.session_state.admin:
    st.warning("🔒 Only Admin can add house. Villagers can only search and view - Like Google Maps.")
else:
    st.success("🔓 Admin Mode ON - You can add houses from sidebar")

st.caption("Pakani Village | Voice Search 🎙️ | 3D Terrain | Admin Only Add")