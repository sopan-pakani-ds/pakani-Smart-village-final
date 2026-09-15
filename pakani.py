import streamlit as st
from streamlit_folium import st_folium
import folium, json, os, random, qrcode
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="पाकणी स्मार्ट गाव", layout="wide", page_icon="📍")

DB_FILE = "pakani_houses.json"
ADMIN_PASS = "pakani123"

def create_dummy():
    base_lat, base_lon = 17.72303, 75.77398
    f_names = ["तुकाराम","शिवाजी","बाळू","दत्तात्रय","हनुमंत","संजय","अमोल","विकास","सुनील","रमेश"]
    l_names = ["पाटील","शिंदे","जाधव","काळे","माने","देशमुख","गायकवाड","कदम"]
    landmarks = ["हनुमान मंदिराजवळ","शाळेजवळ","पाण्याच्या टाकीजवळ","बस स्टॉप जवळ","ग्रामपंचायत जवळ"]
    data = []
    for i in range(50):
        data.append({
            "name": f"{random.choice(f_names)} {random.choice(l_names)}",
            "house_no": f"{100+i}",
            "landmark": random.choice(landmarks),
            "family_count": random.randint(2,8),
            "mobile": f"9{random.randint(100000000,999999999)}",
            "water": random.choice(["Yes","No"]),
            "lat": round(base_lat + random.uniform(-0.005,0.005),6),
            "lon": round(base_lon + random.uniform(-0.005,0.005),6)
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

houses = load_data()

# Sidebar
st.sidebar.title("📍 पाकणी स्मार्ट गाव")
st.sidebar.caption("Pin: 413255 | Adachiwadi Model")
role = st.sidebar.radio("तुम्ही कोण?", ["👤 पाहुणे (Guest)", "🔑 Admin"])
is_admin = False
if role == "🔑 Admin":
    pwd = st.sidebar.text_input("Password", type="password", placeholder="pakani123")
    if pwd == ADMIN_PASS:
        is_admin = True
        st.sidebar.success("Admin Login OK")
    elif pwd: st.sidebar.error("Wrong Password")

if is_admin:
    t1, t2, t3, t4 = st.tabs(["🔍 शोधा", "➕ जोडा", "📊 Dashboard", "🔳 QR बनवा"])
else:
    t1, t4_info = st.tabs(["🔍 घर शोधा", "ℹ️ माहिती"])

with t1:
    st.title("📍 पाकणी गाव - घर शोधा")
    st.components.v1.html("""
    <div style="text-align:center"><button onclick="startVoice()" style="padding:12px 20px; background:#E65100; color:white; border:none; border-radius:10px; font-size:18px;">🎙️ नाव बोला</button><p id="vr" style="color:green;font-weight:bold;"></p></div>
    <script>function startVoice(){var r=new(window.SpeechRecognition||window.webkitSpeechRecognition)();r.lang='mr-IN';r.start();r.onresult=function(e){var t=e.results[0][0].transcript;document.getElementById('vr').innerText="बोललात: "+t;}}</script>
    """, height=90)
    search = st.text_input("🔍 नाव / घर नं टाका", placeholder="उदा: पाटील, 142")
    filtered = [h for h in houses if search.lower() in h['name'].lower() or search in h['house_no']] if search else houses
    m = folium.Map(location=[17.72303, 75.77398], zoom_start=16)
    for h in filtered:
        popup = f"<b>{h['name']}</b><br>घर नं: {h['house_no']}<br>{h['landmark']}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 दिशा</a>"
        folium.Marker([h['lat'], h['lon']], popup=folium.Popup(popup, max_width=250), tooltip=h['name'], icon=folium.Icon(color="red", icon="home")).add_to(m)
    st_folium(m, width=700, height=400, returned_objects=[])
    st.divider()
    st.write(f"**{len(filtered)} घरं सापडली**")
    for h in filtered[:20]:
        with st.container(border=True):
            c1, c2 = st.columns([3,1])
            with c1: st.markdown(f"**🏠 {h['name']}** | No: {h['house_no']} | {h['family_count']} लोक | 📍 {h['landmark']}")
            with c2: st.link_button("🧭 रस्ता", f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}", use_container_width=True)

if is_admin:
    with t2:
        st.subheader("➕ Real घर जोडा")
        name = st.text_input("नाव *"); house_no = st.text_input("घर नं *"); landmark = st.text_input("खूण")
        c1,c2,c3 = st.columns(3)
        with c1: family_count = st.number_input("सदस्य",1,20,4)
        with c2: mobile = st.text_input("मोबाईल")
        with c3: water = st.selectbox("पाणी", ["Yes","No"])
        lat = st.number_input("Latitude", value=17.72303, format="%.6f")
        lon = st.number_input("Longitude", value=75.77398, format="%.6f")
        if st.button("✅ सेव्ह करा", type="primary", use_container_width=True):
            if name and house_no:
                houses.append({"name":name,"house_no":house_no,"landmark":landmark,"family_count":family_count,"mobile":mobile,"water":water,"lat":lat,"lon":lon})
                save_data(houses); st.success("Saved!"); st.balloons()
            else: st.error("नाव + घर नं हवे")
    with t3:
        st.subheader("📊 Dashboard")
        total_p = sum([h.get('family_count',0) for h in houses])
        c1,c2 = st.columns(2)
        c1.metric("घरे", len(houses)); c2.metric("लोकसंख्या", total_p)
        st.dataframe(pd.DataFrame(houses), use_container_width=True)
        if st.button("🗑️ Dummy Delete करा"):
            os.remove(DB_FILE); st.rerun()
    with t4:
        st.subheader("🔳 QR Generator")
        typ = st.radio("QR प्रकार", ["🏠 एका घराचा QR", "🏛️ गावाचा मोठा QR (Entry Gate)"])
        if typ == "🏠 एका घराचा QR":
            sel = st.selectbox("घर निवडा", [f"{h['house_no']} - {h['name']}" for h in houses])
            idx = [f"{h['house_no']} - {h['name']}" for h in houses].index(sel)
            h = houses[idx]
            link = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
            qr = make_qr(link)
            st.image(qr, width=250); st.download_button("📥 Download QR", qr, file_name=f"QR_{h['house_no']}.png")
        else:
            link = st.text_input("तुमची Live App Link Paste करा", placeholder="https://pakani-smart-village-final-...streamlit.app")
            if link:
                qr = make_qr(link)
                st.image(qr, width=300); st.download_button("📥 Entry Gate QR Download", qr, file_name="Pakani_Entry_QR.png")
else:
    with t4_info:
        st.info("**कसं काम करतं?** 1. गेटवर QR स्कॅन करा 2. App उघडेल 3. नाव शोधा 4. रस्ता पहा - Google Maps वर जा")
        st.write("**Admin Password:** pakani123")
