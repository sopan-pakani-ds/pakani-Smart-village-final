import streamlit as st
from streamlit_folium import st_folium
import folium, json, os, random, qrcode
from folium.plugins import MarkerCluster, Fullscreen, LocateControl
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="पाकणी स्मार्ट गाव", layout="wide", page_icon="📍")

DB_FILE = "pakani_houses.json"
ADMIN_PASS = "pakani123"
VILLAGE_LAT, VILLAGE_LON = 17.72303, 75.77398

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
    with open(DB_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DB_FILE,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def make_qr(link):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

houses = load_data()

# Sidebar
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
map_type = st.sidebar.radio("🗺️ नकाशा प्रकार", ["🏘️ Street Map", "🛰️ Satellite"])
cluster_on = st.sidebar.checkbox("📍 क्लस्टर करा", value=False)

# Tabs
if is_admin:
    t1, t2, t3, t4 = st.tabs(["🗺️ MAP + SEARCH", "➕ घर जोडा", "📊 Dashboard", "🔳 QR"])
else:
    t1, t_info = st.tabs(["🗺️ Pakani Map", "ℹ️ माहिती"])

with t1:
    st.subheader("🗺️ पाकणी गाव - Google Map सारखा")

    st.components.v1.html("""
    <div style="text-align:center; margin-bottom:12px;">
        <button onclick="startVoice()" style="padding:12px 22px; background:#E65100; color:white; border:none; border-radius:25px; font-size:16px; font-weight:bold; cursor:pointer;">🎙️ नाव बोला</button>
        <button onclick="getLoc()" style="padding:12px 22px; background:#1565C0; color:white; border:none; border-radius:25px; font-size:16px; font-weight:bold; margin-left:10px; cursor:pointer;">📍 माझे लोकेशन</button>
        <p id="vr" style="color:#2E7D32; font-weight:bold; margin-top:8px;"></p>
    </div>
    <script>
    function startVoice(){
        var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
        if(!SR){document.getElementById('vr').innerText="Use Chrome"; return;}
        var r=new SR(); r.lang='mr-IN'; r.start();
        document.getElementById('vr').innerText="🎧 ऐकतोय...";
        r.onresult=function(e){
            var t=e.results[0][0].transcript;
            document.getElementById('vr').innerText="बोललात: "+t;
            var inputs=window.parent.document.querySelectorAll('input[type="text"]');
            if(inputs.length>0){inputs[0].value=t; inputs[0].dispatchEvent(new Event('input',{bubbles:true}));}
        };
    }
    function getLoc(){
        if(navigator.geolocation){
            document.getElementById('vr').innerText="📍 लोकेशन घेत आहे...";
            navigator.geolocation.getCurrentPosition(function(p){
                var la=p.coords.latitude, lo=p.coords.longitude;
                document.getElementById('vr').innerText="तुम्ही इथे आहात: "+la.toFixed(5)+", "+lo.toFixed(5);
            });
        }
    }
    </script>
    """, height=115)

    search = st.text_input("🔍 शोधा - नाव, आडनाव, घर नं", placeholder="पाटील / शिंदे / 142", key="main_search")

    def g_search(data, q):
        if not q:
            return data
        q = q.lower().strip()
        words = q.split()
        scored=[]
        for h in data:
            text = f"{h['name']} {h['house_no']} {h['landmark']}".lower()
            score = 0
            for w in words:
                if w in text:
                    score += 1
            if score>0:
                scored.append((h,score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored]

    filtered = g_search(houses, search)
    st.caption(f"{len(filtered)} घरे सापडली")

    m = folium.Map(location=[VILLAGE_LAT, VILLAGE_LON], zoom_start=17, tiles=None)

    if "Street" in map_type:
        folium.TileLayer('OpenStreetMap', name="Street").add_to(m)
    else:
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Satellite',
            name="Satellite"
        ).add_to(m)

    boundary = [[17.718,75.768],[17.718,75.780],[17.728,75.768],[17.718,75.768]]
    folium.Polygon(locations=boundary, color="blue", weight=3, fill=True, fill_opacity=0.05, popup="पाकणी हद्द").add_to(m)

    Fullscreen().add_to(m)
    LocateControl(auto_start=False, flyTo=True).add_to(m)
    folium.LayerControl().add_to(m)

    if cluster_on:
        cluster = MarkerCluster().add_to(m)
        target = cluster
    else:
        target = m

    for h in filtered[:100]:
        popup_text = f"{h['name']} - घर नं {h['house_no']}"
        link = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
        popup_html = f"<b>{h['name']}</b><br>घर: {h['house_no']}<br>{h['landmark']}<br><a href='{link}' target='_blank'>दिशा पहा</a>"
        folium.Marker(
            location=[h['lat'], h['lon']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=popup_text,
            icon=folium.Icon(color="red", icon="home")
        ).add_to(target)

    st_folium(m, width=1000, height=520, returned_objects=[])

    st.divider()
    for h in filtered[:30]:
        with st.container(border=True):
            c1, c2 = st.columns([3,1])
            with c1:
                st.markdown(f"**🏠 {h['name']}** | घर नं: `{h['house_no']}` | {h['landmark']}")
            with c2:
                g_link = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
                st.link_button("🧭 दिशा", g_link, use_container_width=True, type="primary")

if is_admin:
    with t2:
        st.subheader("➕ नवीन घर जोडा")
        name = st.text_input("नाव *")
        house_no = st.text_input("घर नं *")
        landmark = st.text_input("खूण")
        c1,c2,c3 = st.columns(3)
        with c1: family_count = st.number_input("सदस्य",1,20,4)
        with c2: mobile = st.text_input("मोबाईल")
        with c3: water = st.selectbox("नळ", ["Yes","No"])
        lat = st.number_input("Lat", value=VILLAGE_LAT, format="%.6f")
        lon = st.number_input("Lon", value=VILLAGE_LON, format="%.6f")
        if st.button("✅ सेव्ह करा", type="primary", use_container_width=True):
            if name and house_no:
                houses.append({"name":name,"house_no":house_no,"landmark":landmark,"family_count":family_count,"mobile":mobile,"water":water,"lat":lat,"lon":lon})
                save_data(houses)
                st.success("Saved!")
                st.balloons()
    with t3:
        st.subheader("📊 Dashboard")
        total_p = sum([h.get('family_count',0) for h in houses])
        c1,c2 = st.columns(2)
        c1.metric("घरे", len(houses))
        c2.metric("लोकसंख्या", total_p)
        st.dataframe(pd.DataFrame(houses), use_container_width=True)
        if st.button("🗑️ Dummy Delete"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.rerun()
    with t4:
        st.subheader("🔳 QR")
        typ = st.radio("QR प्रकार", ["🏠 घराचा QR", "🏛️ गावाचा QR"])
        if typ == "🏠 घराचा QR":
            sel = st.selectbox("घर निवडा", [f"{h['house_no']} - {h['name']}" for h in houses])
            idx = [f"{h['house_no']} - {h['name']}" for h in houses].index(sel)
            h = houses[idx]
            link = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
            qr = make_qr(link)
            st.image(qr, width=250)
            st.download_button("📥 Download", qr, file_name=f"QR_{h['house_no']}.png")
        else:
            link = st.text_input("Live Link", value="https://pakani-smart-village-final-i7wl8jzd9ftr5mdskvwwm6.streamlit.app/")
            if link:
                qr = make_qr(link)
                st.image(qr, width=300)
                st.download_button("📥 Entry QR", qr, file_name="Pakani_Entry_QR.png")
else:
    with t_info:
        st.write("Purpose: गावात घर शोधणे 10 सेकंदात")