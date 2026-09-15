import streamlit as st
import streamlit.components.v1 as components
import json, os, base64
import pandas as pd

st.set_page_config(page_title="Pakani 3D Smart Map", layout="wide")

FILE="pakani_houses.json"
houses=[]
if os.path.exists(FILE):
    try:
        with open(FILE,"r",encoding="utf-8") as f:
            houses=json.load(f)
    except:
        houses=[]

qp=st.query_params

# 1. ALWAYS WELCOME - NO PATIL WORD
st.markdown("""
<div style='background:linear-gradient(90deg,#1a73e8,#0F9D58); color:white; padding:14px; border-radius:12px; text-align:center; margin-bottom:8px;'>
<h3 style='margin:0;color:white;'>🙏 पाकणी गावात आपले स्वागत आहे!</h3>
<p style='margin:5px 0 0 0; font-size:14px;'>नाव किंवा घर नंबर टाका, फोटो पहा, Satellite + 3D Map + Blue Line ने घरापर्यंत जा</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center'>📍 पाकणी - Smart Village 3D Map</h3>", unsafe_allow_html=True)

# 2. LOCATION + SEARCH
c1,c2,c3=st.columns([2,6,1])
with c1:
    st.markdown('<a href="#" onclick="navigator.geolocation.getCurrentPosition(p=>{window.location.href=window.location.pathname+`?lat=${p.coords.latitude}&lon=${p.coords.longitude}`})" style="background:#0F9D58;color:white;padding:10px 15px;border-radius:8px;text-decoration:none;display:block;text-align:center; font-weight:bold;">📍 माझे लोकेशन</a>', unsafe_allow_html=True)
with c2:
    search=st.text_input("", value=qp.get("voice_search","") or qp.get("house_qr",""), placeholder="🔍 नाव / घर नंबर शोधा", label_visibility="collapsed")
with c3:
    st.markdown("""<button onclick="var r=new(window.webkitSpeechRecognition||window.SpeechRecognition)();r.lang='mr-IN';r.onresult=e=>{window.location.href=window.location.pathname+'?voice_search='+encodeURIComponent(e.results[0][0].transcript)};r.start();" style="background:#1a73e8;color:white;border:none;padding:10px;border-radius:8px;width:100%; font-weight:bold;">🎙️ बोला</button>""", unsafe_allow_html=True)

# 3. FILTER - ALL MATCHING HOUSES COME
if search:
    filtered=[h for h in houses if search.lower() in f"{h.get('name','')} {h.get('house_no','')}".lower()]
else:
    filtered=houses

st.caption(f"✅ Found {len(filtered)} houses for '{search}'" if search else f"Total Houses: {len(houses)}")

user_lat=qp.get("lat")
user_lon=qp.get("lon")
houses_js=json.dumps(filtered, ensure_ascii=False)

# 4. REAL MAP - SATELLITE + STREET + 3D + PHOTO POPUP
map_html = f"""
<div id="map" style="height:650px; width:100%; border-radius:12px; border:2px solid #1a73e8;"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([17.62, 75.88], 15);
var street = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:22}}).addTo(map);
var satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{maxZoom:22}});
var hybrid = L.layerGroup([
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}'),
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_only_labels/{{z}}/{{x}}/{{y}}{{r}}.png')
]);
var baseMaps = {{"Street Map": street, "Satellite Image": satellite, "Hybrid + Road": hybrid}};
L.control.layers(baseMaps, null, {{position:'topright'}}).addTo(map);

var houses = {houses_js};
var userLat = {user_lat if user_lat else 'null'};
var userLon = {user_lon if user_lon else 'null'};
var group = L.featureGroup().addTo(map);

if(userLat && userLon){{
    L.marker([userLat, userLon], {{icon: L.divIcon({{html:'<div style=background:#0F9D58;color:white;padding:7px 12px;border-radius:20px;border:3px solid white;font-weight:bold;>📍 YOU</div>', className:''}})}}).addTo(map).bindPopup("Your Location");
}}

houses.forEach(h=>{{
    var photoHtml = h.photo? `<img src="${{h.photo}}" style="width:100%; height:130px; object-fit:cover; border-radius:8px; margin-top:6px; border:1px solid #ccc;">` : `<div style="background:#f0f0f0; padding:12px; border-radius:8px; text-align:center; margin-top:6px;">📷 No Photo</div>`;
    var popup = `<div style="width:240px; font-family:sans-serif;">
        <b style="font-size:16px;">${{h.name}}</b><br><span>House No: <b>${{h.house_no}}</b></span>
        ${{photoHtml}}
        <a href="https://www.google.com/maps/dir/${{userLat || ''}},${{userLon || ''}}/${{h.lat}},${{h.lon}}" target="_blank" style="background:#1a73e8; color:white; padding:9px; display:block; text-align:center; border-radius:8px; margin-top:8px; text-decoration:none; font-weight:bold;">🔵 Blue Line Navigation</a>
        <a href="https://www.google.com/maps/@${{h.lat}},${{h.lon}},80a,35y,0h,45t/data=!3m1!1e3" target="_blank" style="background:#000; color:white; padding:7px; display:block; text-align:center; border-radius:8px; margin-top:6px; text-decoration:none;">🏠 3D View in Google Earth</a>
    </div>`;
    var icon = L.divIcon({{html:`<div style="background:#e53935; width:36px; height:36px; border-radius:50%; border:3px solid white; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:11px; box-shadow:0 2px 6px rgba(0,0,0,0.5);">${{h.house_no}}</div>`, className:'', iconSize:[36,36]}});
    L.marker([h.lat, h.lon], {{icon: icon}}).addTo(group).bindPopup(popup);
}});
if(houses.length>0) map.fitBounds(group.getBounds(), {{padding:[30,30]}});
</script>
"""
components.html(map_html, height=680)

# 5. LIST WITH PHOTO + BLUE LINE
st.markdown("### 🏠 Houses")
for h in filtered[:100]:
    with st.container(border=True):
        c1,c2,c3=st.columns([1,2,1])
        with c1:
            if h.get("photo"): st.image(h["photo"], width=130)
            else: st.write("📷 No Photo")
        with c2:
            st.markdown(f"**{h.get('name')}**")
            st.caption(f"House No: {h.get('house_no')}")
        with c3:
            if user_lat and user_lon:
                st.link_button("🔵 Blue Line", f"https://www.google.com/maps/dir/{user_lat},{user_lon}/{h['lat']},{h['lon']}")
                st.link_button("🏠 3D", f"https://www.google.com/maps/@{h['lat']},{h['lon']},80a,35y,0h,45t/data=!3m1!1e3")
            else:
                st.caption("📍 Location ON करा")

# 6. ADMIN - BULK 1000 HOUSES
with st.sidebar:
    st.markdown("## 🔐 Admin Login")
    pwd=st.text_input("Password", type="password")
    if pwd=="pakani123":
        st.success(f"Total Houses: {len(houses)}")
        tab1, tab2 = st.tabs(["➕ Single", "📤 Bulk 1000"])

        with tab1:
            name=st.text_input("Full Name", key="n1")
            hno=st.text_input("House No", key="h1")
            lat=st.text_input("Latitude", value="17.6205", key="lat1")
            lon=st.text_input("Longitude", value="75.8820", key="lon1")
            photo_file=st.file_uploader("🏠 Photo", type=["jpg","png","jpeg"], key="p1")
            photo_b64=""
            if photo_file:
                photo_b64 = "data:image/jpeg;base64," + base64.b64encode(photo_file.read()).decode()
                st.image(photo_b64, width=200)
            if st.button("💾 Save Single House"):
                new={"name":name, "house_no":hno, "lat":float(lat), "lon":float(lon), "photo":photo_b64}
                houses.append(new)
                with open(FILE,"w",encoding="utf-8") as f: json.dump(houses,f,ensure_ascii=False,indent=2)
                st.success("Saved!"); st.rerun()

        with tab2:
            st.markdown("#### Bulk Add 1000 Houses")
            st.code("name,house_no,lat,lon\nSunil Patil,101,17.6201,75.8821\nAnil Pawar,102,17.6202,75.8822", language="csv")
            csv_file=st.file_uploader("Upload CSV File", type=["csv"], key="csv")
            if csv_file:
                try:
                    df=pd.read_csv(csv_file)
                    st.dataframe(df.head(10))
                    st.info(f"Found {len(df)} houses")
                    if st.button(f"💾 Save All {len(df)} Houses"):
                        new_houses=[]
                        for _,row in df.iterrows():
                            new_houses.append({"name":str(row['name']), "house_no":str(row['house_no']), "lat":float(row['lat']), "lon":float(row['lon']), "photo":""})
                        houses.extend(new_houses)
                        with open(FILE,"w",encoding="utf-8") as f: json.dump(houses,f,ensure_ascii=False,indent=2)
                        st.success(f"Added {len(new_houses)} Houses!"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

            st.write("OR Paste List")
            bulk_text=st.text_area("Paste: Name, HouseNo, Lat, Lon (one per line)", height=150, placeholder="Sunil Patil, 101, 17.6201, 75.8821\nAnil Pawar, 102, 17.6202, 75.8822")
            if bulk_text and st.button("💾 Save Pasted List"):
                try:
                    new_houses=[]
                    for line in bulk_text.strip().split("\n"):
                        parts=[p.strip() for p in line.split(",")]
                        if len(parts)>=4:
                            new_houses.append({"name":parts[0], "house_no":parts[1], "lat":float(parts[2]), "lon":float(parts[3]), "photo":""})
                    houses.extend(new_houses)
                    with open(FILE,"w",encoding="utf-8") as f: json.dump(houses,f,ensure_ascii=False,indent=2)
                    st.success(f"Added {len(new_houses)}!"); st.rerun()
                except Exception as e:
                    st.error(str(e))

            st.divider()
            if st.button("🗑️ Delete All Houses"):
                with open(FILE,"w") as f: f.write("[]")
                st.rerun()