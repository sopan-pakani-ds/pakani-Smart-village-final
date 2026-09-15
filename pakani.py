import streamlit as st
import streamlit.components.v1 as components
import json, os, base64, math

st.set_page_config(page_title="Pakani Google Map", layout="wide")

FILE="pakani_houses.json"
if not os.path.exists(FILE):
    with open(FILE,"w",encoding="utf-8") as f: f.write("[]")
with open(FILE,"r",encoding="utf-8") as f:
    try: houses=json.load(f)
    except: houses=[]

qp=st.query_params

def haversine(lat1,lon1,lat2,lon2):
    R=6371
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(R*2*math.asin(math.sqrt(a)),2)

# 1. GOOGLE MAP STYLE HEADER
st.markdown("""
<div style='background:white; padding:10px; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,0.2); display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
<div style='background:#1a73e8; color:white; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold;'>P</div>
<div><b style='font-size:18px;'>Pakani</b><br><span style='color:gray; font-size:12px;'>🙏 गावात आपले स्वागत आहे!</span></div>
</div>
""", unsafe_allow_html=True)

# 2. GOOGLE LIKE SEARCH WITH AUTO-COMPLETE (Feature 1)
all_names = [f"{h.get('name')} - {h.get('house_no')}" for h in houses]
search = st.selectbox("🔍 Search", options=[""]+all_names, label_visibility="collapsed", placeholder="🔍 Search Pakani - नाव किंवा घर नंबर टाका")

# Extract actual search text
search_text = search.split(" - ")[0] if " - " in search else search
filtered = [h for h in houses if search_text.lower() in f"{h.get('name')} {h.get('house_no')}".lower()] if search_text else houses

user_lat = qp.get("lat")
user_lon = qp.get("lon")
try:
    u_lat = float(user_lat) if user_lat else None
    u_lon = float(user_lon) if user_lon else None
except:
    u_lat, u_lon = None, None

# 3. LOCATION BAR WITH DISTANCE (Feature 3)
c1,c2 = st.columns([1,1])
with c1:
    st.markdown(f'<a href="#" onclick="navigator.geolocation.getCurrentPosition(p=>{{window.location.href=window.location.pathname+`?lat=${{p.coords.latitude}}&lon=${{p.coords.longitude}}`}})" style="background:#1a73e8;color:white;padding:10px 18px;border-radius:24px;text-decoration:none;display:inline-block;">📍 My Location - माझे लोकेशन</a>', unsafe_allow_html=True)
with c2:
    if u_lat and u_lon and filtered:
        dist = haversine(u_lat, u_lon, filtered[0]['lat'], filtered[0]['lon'])
        st.info(f"📏 Nearest House: {dist} KM | 🚶 ~{int(dist*12)} min walk")

# 4. GOOGLE MAP EXACT - STREET + SATELLITE + STREET VIEW (Feature 2,4)
houses_js = json.dumps(filtered, ensure_ascii=False)

map_html = f"""
<div id="map" style="height:600px; width:100%; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,0.3);"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map', {{zoomControl:false}}).setView([17.6205,75.8820],16);
L.control.zoom({{position:'bottomright'}}).addTo(map);

// GOOGLE MAP TILES - EXACT GOOGLE LOOK
var googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{maxZoom:22}}).addTo(map);
var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{maxZoom:22}});
var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{maxZoom:22}});

L.control.layers({{"Google Map": googleStreets, "Google Satellite": googleSat, "Google Hybrid": googleHybrid}}, null, {{position:'topright'}}).addTo(map);

var houses = {houses_js};
var userLat = {u_lat if u_lat else 'null'};
var userLon = {u_lon if u_lon else 'null'};
var group = L.featureGroup().addTo(map);

if(userLat && userLon){{
    var blueIcon = L.divIcon({{
        html: '<div style="background:#1a73e8; width:18px; height:18px; border-radius:50%; border:3px solid white; box-shadow:0 0 10px rgba(26,115,232,0.8);"></div>',
        className:'', iconSize:[18,18]
    }});
    L.marker([userLat, userLon], {{icon: blueIcon}}).addTo(map).bindPopup("📍 You Are Here - तुम्ही येथे आहात");
}}

// RED PINS - GOOGLE STYLE
houses.forEach(h=>{{
    var distanceText = "";
    if(userLat && userLon){{
        var R=6371; var dLat=(h.lat-userLat)*Math.PI/180; var dLon=(h.lon-userLon)*Math.PI/180;
        var a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(userLat*Math.PI/180)*Math.cos(h.lat*Math.PI/180)*Math.sin(dLon/2)*Math.sin(dLon/2);
        var c=2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a)); var d=R*c;
        distanceText = `<br><span style="color:#1a73e8;">📏 ${{d.toFixed(2)}} KM away</span>`;
    }}
    var photo = h.photo? `<img src="${{h.photo}}" style="width:100%; height:110px; object-fit:cover; border-radius:8px; margin-top:6px;">` : '';
    var streetViewUrl = `https://www.google.com/maps/@${{h.lat}},${{h.lon}},3a,75y,0h,90t/data=!3m6!1e1!3m4!1s!2e0!7i16384!8i8192`;
    var popup = `<div style="width:230px; font-family:Roboto,sans-serif;">
        <b style="font-size:16px;">${{h.name}}</b><br>
        <span style="color:gray;">House #${{h.house_no}}</span>${{distanceText}}
        ${{photo}}
        <a href="https://www.google.com/maps/dir/${{userLat||''}},${{userLon||''}}/${{h.lat}},${{h.lon}}" target="_blank" style="background:#1a73e8; color:white; padding:10px; display:block; text-align:center; border-radius:24px; margin-top:8px; text-decoration:none; font-weight:bold;">🔵 Directions - Blue Line</a>
        <a href="${{streetViewUrl}}" target="_blank" style="background:#f8f9fa; color:#202124; padding:8px; display:block; text-align:center; border-radius:24px; margin-top:6px; text-decoration:none; border:1px solid #dadce0;">🏠 Street View - 360° पहा</a>
        <a href="https://www.google.com/maps/@${{h.lat}},${{h.lon}},80a,35y,0h,45t/data=!3m1!1e3" target="_blank" style="background:#202124; color:white; padding:8px; display:block; text-align:center; border-radius:24px; margin-top:6px; text-decoration:none;">🌍 3D View</a>
    </div>`;
    var pin = L.divIcon({{
        html: `<div style="background:#ea4335; width:32px; height:32px; border-radius:50% 50% 50% 0; transform:rotate(-45deg); border:2px solid white; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.4);"><span style="transform:rotate(45deg); color:white; font-weight:bold; font-size:11px;">${{h.house_no}}</span></div>`,
        className:'', iconSize:[32,32], iconAnchor:[16,32]
    }});
    L.marker([h.lat, h.lon], {{icon: pin}}).addTo(group).bindPopup(popup);
}});
if(houses.length>0) map.fitBounds(group.getBounds(), {{padding:[30,30]}});

// ADMIN: CLICK MAP TO GET LAT LON
map.on('click', function(e){{
    var lat = e.latlng.lat.toFixed(6);
    var lng = e.latlng.lng.toFixed(6);
    window.parent.postMessage({{type:'map_click', lat:lat, lon:lng}}, '*');
}});
</script>
"""
components.html(map_html, height=620)

# ADMIN - HOW TO ADD LOCATION EASY
with st.sidebar:
    st.markdown("### 🔐 Admin - Add Houses")
    st.caption("How to add location: 1) Click My Location 2) Go to house 3) Click Map or Use Current Location Button")
    pwd = st.text_input("Password", type="password")
    if pwd=="pakani123":
        st.success(f"Total: {len(houses)} Houses")

        # NEW: GET LOCATION FROM MAP CLICK
        st.markdown("#### 📍 Add House Location - 3 Easy Ways")
        way = st.radio("Choose Way:", ["Way 1: Use My Current Location", "Way 2: Click on Map (Auto)", "Way 3: Type Manually"])

        auto_lat = qp.get("admin_lat") or "17.6205"
        auto_lon = qp.get("admin_lon") or "75.8820"

        if way == "Way 1: Use My Current Location":
            st.markdown(f'<a href="#" onclick="navigator.geolocation.getCurrentPosition(p=>{{window.location.href=window.location.pathname+`?admin_lat=${{p.coords.latitude}}&admin_lon=${{p.coords.longitude}}`}})" style="background:#0F9D58;color:white;padding:8px 14px;border-radius:8px;text-decoration:none;">📍 Get My Current House Location</a>', unsafe_allow_html=True)
            st.write(f"Lat: {auto_lat}, Lon: {auto_lon}")
            lat_val = str(auto_lat)
            lon_val = str(auto_lon)
        elif way == "Way 2: Click on Map (Auto)":
            st.info("Click anywhere on map above, then copy lat lon from URL? For now use Way 1 or 3")
            lat_val = st.text_input("Lat from Map Click", value=str(auto_lat))
            lon_val = st.text_input("Lon from Map Click", value=str(auto_lon))
        else:
            lat_val = st.text_input("Latitude", value="17.6205")
            lon_val = st.text_input("Longitude", value="75.8820")

        name = st.text_input("Full Name")
        hno = st.text_input("House No")
        pf = st.file_uploader("House Photo", type=["jpg","png","jpeg"])
        pb=""
        if pf:
            pb="data:image/jpeg;base64,"+base64.b64encode(pf.read()).decode()
            st.image(pb, width=150)

        if st.button("💾 Save House"):
            try:
                houses.append({"name":name,"house_no":hno,"lat":float(lat_val),"lon":float(lon_val),"photo":pb})
                with open(FILE,"w",encoding="utf-8") as f: json.dump(houses,f,ensure_ascii=False,indent=2)
                st.success(f"Saved {name}!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.divider()
        st.markdown("#### 📤 Bulk 1000 - Paste")
        bulk = st.text_area("Paste: Name,HouseNo,Lat,Lon", height=150, placeholder="Sunil Patil,101,17.6205,75.8820")
        if bulk and st.button("Save All 1000"):
            nh=[]
            for line in bulk.split("\n"):
                p=[x.strip() for x in line.split(",")]
                if len(p)>=4:
                    try: nh.append({"name":p[0],"house_no":p[1],"lat":float(p[2]),"lon":float(p[3]),"photo":""})
                    except: pass
            houses.extend(nh)
            with open(FILE,"w",encoding="utf-8") as f: json.dump(houses,f,ensure_ascii=False,indent=2)
            st.success(f"Added {len(nh)}")
            st.rerun()