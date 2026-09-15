import streamlit as st
from streamlit_folium import st_folium
import folium, json, os, requests, base64, pandas as pd
from folium.plugins import Fullscreen, MarkerCluster
from io import BytesIO
import qrcode
import streamlit.components.v1 as components

st.set_page_config(page_title="Pakani REAL - All Patil Search", layout="wide", page_icon="📍")

DB_FILE = "pakani_houses_REAL.json"
ADMIN_PASS = "pakani123"
VILLAGE_LAT, VILLAGE_LON = 17.72303, 75.77398
APP_URL = "https://pakani-smart-village-final-1.streamlit.app"

def load_data():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE,"w",encoding="utf-8") as f: json.dump([],f,ensure_ascii=False)
    with open(DB_FILE,"r",encoding="utf-8") as f:
        try: return json.load(f)
        except: return []
def save_data(data):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
def make_qr_base64(text):
    qr = qrcode.make(text); buf = BytesIO(); qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
def get_blue_route(s_lat, s_lon, e_lat, e_lon):
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{s_lon},{s_lat};{e_lon},{e_lat}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=6).json()
        if r.get("routes"):
            coords = r["routes"][0]["geometry"]["coordinates"]
            route = [[lat, lon] for lon, lat in coords]
            return route, r["routes"][0]["distance"], r["routes"][0]["duration"]
    except: pass
    return None, 0, 0

houses = load_data()
if "admin" not in st.session_state: st.session_state.admin=False
if "clicked_lat" not in st.session_state: st.session_state.clicked_lat=VILLAGE_LAT
if "clicked_lon" not in st.session_state: st.session_state.clicked_lon=VILLAGE_LON
if "user_lat" not in st.session_state: st.session_state.user_lat=None
if "user_lon" not in st.session_state: st.session_state.user_lon=None
if "selected_house" not in st.session_state: st.session_state.selected_house=None
qp = st.query_params

# Sidebar Admin
st.sidebar.title("🔐 Admin")
if not st.session_state.admin:
    pwd = st.sidebar.text_input("Password", type="password", placeholder="pakani123")
    if st.sidebar.button("Login", use_container_width=True, type="primary"):
        if pwd.strip() == ADMIN_PASS.strip(): st.session_state.admin=True; st.rerun()
        else: st.sidebar.error("Wrong! pakani123")
else:
    st.sidebar.success("✅ Admin Logged")
    if st.sidebar.button("Logout"): st.session_state.admin=False; st.rerun()
    st.sidebar.caption(f"Clicked: {st.session_state.clicked_lat:.6f}, {st.session_state.clicked_lon:.6f}")
    with st.sidebar.form("add"):
        name=st.text_input("Name *"); hno=st.text_input("House No *"); lm=st.text_input("Landmark")
        lat=st.number_input("Lat", value=float(st.session_state.clicked_lat), format="%.6f")
        lon=st.number_input("Lon", value=float(st.session_state.clicked_lon), format="%.6f")
        if st.form_submit_button("✅ Add", type="primary", use_container_width=True):
            if name.strip() and hno.strip():
                houses.append({"name":name.strip(),"house_no":hno.strip(),"landmark":lm.strip(),"lat":float(lat),"lon":float(lon)})
                save_data(houses); st.sidebar.success("Added"); st.rerun()
    st.sidebar.divider()
    st.sidebar.subheader("📤 Bulk 1000 CSV")
    up = st.sidebar.file_uploader("CSV", type=["csv"])
    if up:
        df = pd.read_csv(up); st.sidebar.dataframe(df.head(2))
        if st.sidebar.button(f"Add {len(df)} houses"):
            c=0
            for _, r in df.iterrows():
                try: houses.append({"name":str(r['name']),"house_no":str(r['house_no']),"landmark":str(r.get('landmark','')),"lat":float(r['lat']),"lon":float(r['lon'])}); c+=1
                except: pass
            save_data(houses); st.sidebar.success(f"Added {c}"); st.rerun()
    sample="name,house_no,landmark,lat,lon\nतुकाराम पाटील,101,हनुमान मंदिर,17.72303,75.77398"
    st.sidebar.download_button("📥 Sample CSV", sample, "sample.csv")
    st.sidebar.metric("Total REAL", len(houses))
    if st.sidebar.button("❌ DELETE ALL"): save_data([]); st.rerun()

# Welcome for BIG QR
if qp.get("from")=="entrance_board":
    st.markdown("<div style='background:linear-gradient(90deg,#1a73e8,#0F9D58); color:white; padding:12px; border-radius:12px; text-align:center'><h3>🙏 पाकणी गावात स्वागत!</h3><p>नातेवाईकाचे नाव टाका - सर्व Patil दिसतील, तुमचा Patil निवडा + Blue Line</p></div>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center'>📍 पाकणी - All Patil Search + Blue Line</h2>", unsafe_allow_html=True)

components.html("""
<div style="text-align:center"><button onclick="getLoc()" style="background:#0F9D58; color:white; border:none; padding:9px 18px; border-radius:20px; cursor:pointer">📍 माझे लोकेशन</button><p id="locS" style="font-size:10px">Blue Line साठी</p>
<script>function getLoc(){const s=document.getElementById('locS'); if(navigator.geolocation){s.innerText='📡...'; navigator.geolocation.getCurrentPosition(p=>{const url=new URL(window.parent.location.href); url.searchParams.set('my_lat',p.coords.latitude); url.searchParams.set('my_lon',p.coords.longitude); window.parent.location.href=url.toString();});}}</script></div>
""", height=60)
if qp.get("my_lat"): st.session_state.user_lat=float(qp.get("my_lat")); st.session_state.user_lon=float(qp.get("my_lon"))

c1,c2=st.columns([3,1])
with c1: search=st.text_input("", value=qp.get("voice_search","") or qp.get("house_qr",""), placeholder="🔍 Patil टाका - सर्व Patil येतील", label_visibility="collapsed")
with c2:
    components.html("""
    <button id="vBtn" style="background:#1a73e8; color:white; border:none; padding:9px; border-radius:20px; width:100%">🎙️ बोला</button>
    <script>const b=document.getElementById('vBtn'); b.onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR)return; const rec=new SR(); rec.lang='mr-IN'; rec.start(); rec.onresult=(e)=>{const t=e.results[0][0].transcript; const url=new URL(window.parent.location.href); url.searchParams.set('voice_search',t); window.parent.location.href=url.toString();};}</script>
    """, height=50)

# SEARCH LOGIC - ALL PATIL COME
filtered = [h for h in houses if search.lower() in f"{h['name']} {h['house_no']} {h.get('landmark','')}".lower()] if search else houses

if search:
    if len(filtered)==0:
        st.error(f"❌ '{search}' नावाचे 0 घर सापडले")
    elif len(filtered)==1:
        st.success(f"✅ 1 घर सापडले: {filtered[0]['name']} #{filtered[0]['house_no']}")
    else:
        st.warning(f"🔍 '{search}' साठी {len(filtered)} घरे सापडली - खाली तुमचे घर निवडा (उदा. सर्व Patil)")

if qp.get("selected"):
    f=[h for h in houses if h['house_no']==qp.get("selected")]
    if f: st.session_state.selected_house=f[0]

# MAP
m=folium.Map(location=[VILLAGE_LAT,VILLAGE_LON], zoom_start=18, tiles=None)
folium.TileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google').add_to(m)
Fullscreen().add_to(m)
if st.session_state.user_lat: folium.Marker([st.session_state.user_lat, st.session_state.user_lon], popup="तुम्ही", icon=folium.Icon(color="blue", icon="user")).add_to(m)

blue_coords=None; dist_km=0
if st.session_state.selected_house and st.session_state.user_lat:
    h=st.session_state.selected_house
    blue_coords, dist, _ = get_blue_route(st.session_state.user_lat, st.session_state.user_lon, h['lat'], h['lon'])
    if blue_coords:
        folium.PolyLine(blue_coords, color="white", weight=12, opacity=0.5).add_to(m)
        folium.PolyLine(blue_coords, color="#1a73e8", weight=6).add_to(m)
        m.fit_bounds([[st.session_state.user_lat, st.session_state.user_lon],[h['lat'],h['lon']]])
        dist_km=dist/1000

cluster=MarkerCluster().add_to(m)
for h in filtered:
    is_sel=st.session_state.selected_house and h['house_no']==st.session_state.selected_house['house_no']
    folium.Marker([h['lat'],h['lon']], popup=f"{h['name']} #{h['house_no']}", icon=folium.Icon(color="green" if is_sel else "red", icon="home")).add_to(cluster)

map_data=st_folium(m, height=480, width=1200, returned_objects=["last_object_clicked"])
if map_data and map_data.get("last_object_clicked"):
    st.session_state.clicked_lat=map_data["last_object_clicked"]["lat"]; st.session_state.clicked_lon=map_data["last_object_clicked"]["lng"]
    if houses:
        nearest=min(houses, key=lambda x: abs(x['lat']-st.session_state.clicked_lat)+abs(x['lon']-st.session_state.clicked_lon))
        if abs(nearest['lat']-st.session_state.clicked_lat)<0.0005: st.session_state.selected_house=nearest; st.rerun()

if st.session_state.selected_house:
    h=st.session_state.selected_house; st.divider()
    with st.container(border=True):
        a,b,c=st.columns([2,1,1])
        with a: st.markdown(f"### 🏠 {h['name']} `#{h['house_no']}`"); st.write(h.get('landmark',''))
        with b:
            qr=make_qr_base64(f"{APP_URL}?house_qr={h['house_no']}")
            st.markdown(f"<img src='data:image/png;base64,{qr}' width='90'><br>QR #{h['house_no']}", unsafe_allow_html=True)
        with c:
            st.link_button("🧭 Google Dir", f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}", type="primary", use_container_width=True)
            if blue_coords: st.success(f"🔵 {dist_km:.2f} km")
            if st.button("❌ Clear", use_container_width=True): st.session_state.selected_house=None; st.rerun()

st.divider()
st.subheader("📋 Houses List - All Patil Logic")
for h in filtered[:20]:
    with st.container(border=True):
        a,b=st.columns([4,1])
        with a: st.write(f"**{h['name']}** #{h['house_no']} - {h.get('landmark','')}")
        with b:
            if st.button("🔵 Blue", key=f"b_{h['house_no']}_{h['name']}", use_container_width=True): st.session_state.selected_house=h; st.rerun()

# BIG QR
st.divider()
entrance_url=f"{APP_URL}?from=entrance_board"
big_qr=make_qr_base64(entrance_url)
st.markdown(f"<div style='text-align:center; border:2px dashed blue; padding:12px; border-radius:12px'><img src='data:image/png;base64,{big_qr}' width='180'><br><b>BIG QR - Entrance</b><br><a href='https://api.qrserver.com/v1/create-qr-code/?size=1000x1000&data={entrance_url}' target='_blank'>📥 Download for Print</a></div>", unsafe_allow_html=True)