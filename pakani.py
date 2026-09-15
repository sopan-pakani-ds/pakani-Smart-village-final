import streamlit as st
import streamlit.components.v1 as components
import json, os, base64

st.set_page_config(page_title="Pakani Smart Map", layout="wide")

# --- LOAD HOUSES ---
FILE="pakani_houses.json"
houses=[]
if os.path.exists(FILE):
    try:
        with open(FILE,"r",encoding="utf-8") as f:
            houses=json.load(f)
    except:
        houses=[]

qp=st.query_params

# --- 1. ALWAYS SHOW WELCOME (No Condition) ---
st.markdown("""
<div style='background:linear-gradient(90deg,#1a73e8,#0F9D58); color:white; padding:12px; border-radius:12px; text-align:center; margin-bottom:10px;'>
<h3 style='margin:0; color:white;'>🙏 पाकणी गावात आपले स्वागत आहे!</h3>
<p style='margin:5px 0 0 0; font-size:14px;'>नातेवाईकाचे नाव किंवा घर नंबर टाका आणि Blue Line ने घरापर्यंत पोहोचा</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center'>📍 पाकणी - Smart Village Map</h2>", unsafe_allow_html=True)

# --- 2. LOCATION + SEARCH ---
c1,c2,c3=st.columns([2,6,1])
with c1:
    st.markdown('<a href="#" onclick="navigator.geolocation.getCurrentPosition(pos=>{const lat=pos.coords.latitude; const lon=pos.coords.longitude; window.location.href=window.location.pathname+`?lat=${lat}&lon=${lon}`})" style="background:#0F9D58; color:white; padding:10px 15px; border-radius:8px; text-decoration:none; display:block; text-align:center;">📍 माझे लोकेशन</a>', unsafe_allow_html=True)

with c2:
    search=st.text_input("", value=qp.get("voice_search","") or qp.get("house_qr",""), placeholder="🔍 नाव / घर नंबर शोधा", label_visibility="collapsed")

with c3:
    st.markdown("""
    <button onclick="var r=new(window.webkitSpeechRecognition||window.SpeechRecognition)(); r.lang='mr-IN'; r.onresult=function(e){var t=e.results[0][0].transcript; window.location.href=window.location.pathname+'?voice_search='+encodeURIComponent(t)}; r.start();"
    style="background:#1a73e8; color:white; border:none; padding:10px; border-radius:8px; width:100%;">🎙️ बोला</button>
    """, unsafe_allow_html=True)

# --- 3. FILTER LOGIC - ALL MATCHING COME ---
if search:
    filtered=[h for h in houses if search.lower() in f"{h.get('name','')} {h.get('house_no','')}".lower()]
else:
    filtered=houses

st.write(f"Found {len(filtered)} houses for '{search}'" if search else f"Total Houses: {len(houses)}")

# --- 4. MAP ---
user_lat=qp.get("lat")
user_lon=qp.get("lon")

# Prepare houses for JS
houses_js=json.dumps(filtered, ensure_ascii=False)

map_html=f"""
<div id="map" style="height:500px; width:100%; border-radius:12px;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map=L.map('map').setView([17.5, 75.5], 14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
var houses={houses_js};
var userLat={user_lat if user_lat else 'null'};
var userLon={user_lon if user_lon else 'null'};
var group=L.featureGroup().addTo(map);

if(userLat && userLon){{
    L.marker([userLat, userLon], {{icon: L.divIcon({{html:'📍', className:'', iconSize:[20,20]}})}}).addTo(map).bindPopup("You are here");
}}

houses.forEach(h=>{{
    var m=L.marker([h.lat, h.lon]).addTo(group);
    m.bindPopup(`<b>${{h.name}} #${{h.house_no}}</b><br><a href='?house_qr=${{h.house_no}}'>View</a> <br> <a href='#' onclick="if(userLat){{ var url=`https://www.google.com/maps/dir/${{userLat}},${{userLon}}/${{h.lat}},${{h.lon}}`; window.open(url)}}">🔵 Blue Line - Google Direction</a>`);
}});

if(houses.length>0) map.fitBounds(group.getBounds());
</script>
"""
components.html(map_html, height=520)

# --- 5. LIST WITH BLUE LINE ---
for h in filtered[:50]:
    col1,col2=st.columns([3,1])
    with col1:
        st.write(f"**{h.get('name')}** #{h.get('house_no')}")
    with col2:
        if user_lat and user_lon:
            st.link_button("🔵 Blue Line", f"https://www.google.com/maps/dir/{user_lat},{user_lon}/{h['lat']},{h['lon']}")
        else:
            st.caption("Click 📍 My Location first")

# --- SIDEBAR ADMIN ---
with st.sidebar:
    st.write("Admin Login")
    pwd=st.text_input("Password", type="password")
    if pwd=="pakani123":
        st.success("Logged In")
        st.write(f"Total Houses in File: {len(houses)}")
        # Simple Add
        name=st.text_input("Name")
        hno=st.text_input("House No")
        lat=st.text_input("Lat", value="17.5")
        lon=st.text_input("Lon", value="75.5")
        if st.button("Add House"):
            new={{"name":name, "house_no":hno, "lat":float(lat), "lon":float(lon)}}
            houses.append(new)
            with open(FILE,"w",encoding="utf-8") as f:
                json.dump(houses,f,ensure_ascii=False,indent=2)
            st.success("Added!")
            st.rerun()