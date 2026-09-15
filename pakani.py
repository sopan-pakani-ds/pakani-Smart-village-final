import streamlit as st
from streamlit_folium import st_folium
import folium, json, os, random, qrcode, math
from folium.plugins import MarkerCluster, Fullscreen, LocateControl
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="पाकणी स्मार्ट गाव", layout="wide", page_icon="📍")

DB_FILE = "pakani_houses.json"
ADMIN_PASS = "pakani123"
VILLAGE_LAT, VILLAGE_LON = 17.72303, 75.77398

# --- Database ---
def create_dummy():
    f_names = ["तुकाराम","शिवाजी","बाळू","दत्तात्रय","हनुमंत","संजय","अमोल","विकास","सुनील","रमेश","पांडुरंग","महादेव","गणेश","अमित"]
    l_names = ["पाटील","शिंदे","जाधव","काळे","माने","देशमुख","गायकवाड","कदम","भोसले","मोरे","पवार"]
    landmarks = ["हनुमान मंदिराजवळ","शाळेजवळ","पाण्याच्या टाकीजवळ","बस स्टॉप जवळ","ग्रामपंचायत जवळ","मुख्य रस्ता"]
    data = []
    for i in range(65):
        data.append({
            "name": f"{random.choice(f_names)} {random.choice(l_names)}",
            "house_no": f"{100+i}",
            "landmark": random.choice(landmarks),
            "family_count": random.randint(2,8),
            "mobile": f"9{random.randint(100000000,999999999)}",
            "water": random.choice(["Yes","No"]),
            "lat": round(VILLAGE_LAT + random.uniform(-0.007,0.007),6),
            "lon": round(VILLAGE_LON + random.uniform(-0.007,0.007),6)
        })
    return data

if not os.path.exists(DB_FILE):
    with open(DB_FILE,"w",encoding="utf-8") as f:
        json.dump(create_dummy(), f, ensure_ascii=False, indent=2)

def load_data():
    with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
def save_data(d):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
def make_qr(link):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(link); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO(); img.save(buf, format="PNG")
    return buf.getvalue()
def distance_m(lat1,lon1,lat2,lon2):
    R=6371; dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(R*2*math.atan2(math.sqrt(a),math.sqrt(1-a))*1000)

houses = load_data()

# --- Sidebar ---
st.sidebar.title("📍 पाकणी स्मार्ट गाव")
st.sidebar.caption("Adachiwadi Model | Pin: 413255")
role = st.sidebar.radio("तुम्ही कोण आहात?", ["👤 पाहुणे (Guest)", "🔑 Admin (Sarpanch)"])

is_admin = False
if role == "🔑 Admin (Sarpanch)":
    pwd = st.sidebar.text_input("Password", type="password", placeholder="pakani123")
    if pwd == ADMIN_PASS:
        is_admin = True
        st.sidebar.success("Admin Login Success")
    elif pwd:
        st.sidebar.error("Wrong Password")

st.sidebar.divider()
map_type = st.sidebar.radio("🗺️ नकाशा प्रकार", ["🏘️ Street Map (रस्ता नकाशा)", "🛰️ Satellite (उपग्रह फोटो)"])
cluster_on = st.sidebar.checkbox("📍 जवळची घरं एकत्र दाखवा (Cluster)", value=False)

st.sidebar.divider()
st.sidebar.info("Purpose: गावात कोणाचेही घर 10 सेकंदात शोधणे\n\nScan -> Search -> Direction")

# --- Tabs ---
if is_admin:
    t1, t2, t3, t4 = st.tabs(["🗺️ MAP + SEARCH", "➕ घर जोडा", "📊 Dashboard", "🔳 QR बनवा"])
else:
    t1, t_info = st.tabs(["🗺️ Pakani Map", "ℹ️ माहिती"])

# --- TAB 1: MAIN MAP ---
with t1:
    st.subheader("🗺️ पाकणी गाव - Google Map सारखा")

    # Voice + My Location JS
    st.components.v1.html("""
    <div style="text-align:center; margin-bottom:12px;">
        <button onclick="startVoice()" style="padding:12px 22px; background:#E65100; color:white; border:none; border-radius:25px; font-size:16px; font-weight:bold; cursor:pointer;">🎙️ नाव बोला (Voice)</button>
        <button onclick="getLoc()" style="padding:12px 22px; background:#1565C0; color:white; border:none; border-radius:25px; font-size:16px; font-weight:bold; margin-left:10px; cursor:pointer;">📍 माझे लोकेशन</button>
        <p id="vr" style="color:#2E7D32; font-weight:bold; margin-top:8px; font-size:15px;"></p>
    </div>
    <script>
    function startVoice(){
        var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
        if(!SR){document.getElementById('vr').innerText="Use Chrome browser"; return;}
        var r=new SR(); r.lang='mr-IN'; r.start();
        document.getElementById('vr').innerText="🎧 ऐकतोय... बोला...";
        r.onresult=function(e){
            var t=e.results[0][0].transcript;
            document.getElementById('vr').innerText="तुम्ही बोललात: "+t+" | Search मध्ये आपोआप येईल";
            var inputs=window.parent.document.querySelectorAll('input[type=\"text\"]');
            if(inputs.length>0){inputs[0].value=t; inputs[0].dispatchEvent(new Event('input',{bubbles:true}));}
        };
        r.onerror=function(e){document.getElementById('vr').innerText="पुन्हा बोला: "+e.error;};
    }
    function getLoc(){
        if(navigator.geolocation){
            document.getElementById('vr').innerText="📍 लोकेशन घेत आहे...";
            navigator.geolocation.getCurrentPosition(function(p){
                var la=p.coords.latitude, lo=p.coords.longitude;
                document.getElementById('vr').innerText="तुम्ही इथे आहात: "+la.toFixed(5)+", "+lo.toFixed(5)+" (नकाशावर निळा बिंदू येईल)";
            });
        }
    }
    </script>
    """, height=115)

    search = st.text_input("🔍 Google सारखं शोधा - नाव, आडनाव, घर नं, खूण", placeholder="उदा: पाटील / शिंदे / 142 / मंदिराजवळ", key="main_search")

    # Google-like search
    def g_search(data, q):
        if not q: return data
        q = q.lower().strip()
        words = q.split()
        scored=[]
        for h in data:
            text = f"{h['name']} {h['house_no']} {h['landmark']}".lower()
            score = sum(1 for w in words if w in text)
            # also check partial english-marathi
            if "patil" in q and "पाटील" in text: score+=1
            if "shinde" in q and "शिंदे" in text: score+=1
            if score>0: scored.append((h,score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored]

    filtered = g_search(houses, search)
    st.caption(f"📊 {len(filtered)} घरं सापडली" + (f" for '{search}'" if search else ""))

    # --- MAP ---
    m = folium.Map(location=[VILLAGE_LAT, VILLAGE_LON], zoom_start=17, tiles=None)

    if "Street" in map_type:
        folium.TileLayer('OpenStreetMap', name="Street Map").add_to(m)
    else:
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri Satellite', name="Satellite").add_to(m)
        folium.TileLayer('OpenStreetMap', name="Street Overlay", opacity=0.4).add_to(m)

    # Village boundary
    boundary = [[17.718,75.768],[17.718,75.780],[17.728,75.780],[17.728,75.768],[17.718,75.768]]
    folium.Polygon(locations=boundary, color="blue", weight=3, fill=True, fill_opacity=0.05, popup="पाकणी गाव हद्द").add_to(m)

    Fullscreen().add_to(m)
    LocateControl(auto_start=False, flyTo=True, strings={"title": "माझे लोकेशन"}).add_to(m)
    folium.LayerControl().add_to(m)

    # Markers
    if cluster_on:
        cluster = MarkerCluster().add_to(m)
        target = cluster
    else:
        target = m

    for h in filtered[:100]:
        html = f"""<b>🏠 {h['name']}</b><br>घर नं: {h['house_no']}<br>📍 {h['landmark']}<br>👨‍👩‍👧‍👦 {h['family_count']} लोक<br><br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank' style='background:#1976D2;color:white;padding:8px 14px;border-radius:6px;text-decoration:none;'>🧭 रस्ता पहा</a>"""
        folium.Marker([h['lat'], h['lon']], popup=