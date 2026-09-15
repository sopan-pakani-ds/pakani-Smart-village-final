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
    f_names = ["तुकाराम","शिवाजी","बाळू","दत्तात्रय","हनुमंत","संजय","अमोल","विकास","सुनील","रमेश","पांडुरंग","महादेव","गणेश","अमित","सुरेश"]
    l_names = ["पाटील","शिंदे","जाधव","काळे","माने","देशमुख","गायकवाड","कदम","भोसले","मोरे","पवार"]
    landmarks = ["हनुमान मंदिराजवळ","शाळेजवळ","पाण्याच्या टाकीजवळ","बस स्टॉप जवळ","ग्रामपंचायत जवळ","मुख्य रस्ता","स्टेशन रोड"]
    data = []
    for i in range(60):
        data.append({
            "name": f"{random.choice(f_names)} {random.choice(l_names)}",
            "house_no": f"{100+i}",
            "landmark": random.choice(landmarks),
            "family_count": random.randint(2,8),
            "mobile": f"9{random.randint(100000000,999999999)}",
            "water": random.choice(["Yes","No"]),
            "lat": round(base_lat + random.uniform(-0.006,0.006),6),
            "lon": round(base_lon + random.uniform(-0.006,0.006),6)
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
role = st.sidebar.radio("तुम्ही कोण?", ["👤 पाहुणे (Guest)", "🔑 Admin"])
is_admin = False
if role == "🔑 Admin":
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd == ADMIN_PASS:
        is_admin = True
        st.sidebar.success("Admin OK")

if is_admin:
    t1, t2, t3, t4 = st.tabs(["🔍 शोधा", "➕ जोडा", "📊 Dashboard", "🔳 QR"])
else:
    t1, _ = st.tabs(["🔍 घर शोधा", "ℹ️ माहिती"])

with t1:
    st.subheader("📍 घर शोधा - Google सारखं")

    # --- FIXED SEARCH BOX WITH VOICE ---
    if 'search_q' not in st.session_state:
        st.session_state.search_q = ""

    # Voice Search - This will auto-fill the search box
    st.components.v1.html(f"""
    <div style="text-align:center; margin-bottom:15px;">
        <button onclick=\"startVoice()\" style=\"padding:14px 25px; background:#FF5722; color:white; border:none; border-radius:25px; font-size:18px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);\">🎙️ बोला - पाटील, शिंदे, जाधव</button>
        <p id=\"vr\" style=\"color:#2E7D32; font-weight:bold; margin-top:10px; font-size:16px;\"></p>
    </div>
    <script>
    function startVoice(){{
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            document.getElementById('vr').innerText = \"Voice not supported in this browser. Use Chrome.\";
            return;
        }}
        var r = new SpeechRecognition();
        r.lang = 'mr-IN';
        r.interimResults = false;
        r.maxAlternatives = 1;
        document.getElementById('vr').innerText = \"🎧 ऐकतोय... बोला...\";
        r.start();
        r.onresult = function(e){{
            var t = e.results[0][0].transcript;
            document.getElementById('vr').innerText = \"तुम्ही बोललात: \" + t + \" - खाली शोधत आहे...\";
            // Try to set Streamlit input
            var inputs = window.parent.document.querySelectorAll('input[type=\"text\"]');
            if(inputs.length > 0){{
                inputs[0].value = t;
                inputs[0].dispatchEvent(new Event('input', {{bubbles:true}}));
                inputs[0].dispatchEvent(new KeyboardEvent('keydown', {{key:'Enter', bubbles:true}}));
            }}
            // Also copy to clipboard for manual paste
            navigator.clipboard.writeText(t);
        }};
        r.onerror = function(e){{
            document.getElementById('vr').innerText = \"Error: \" + e.error + \". पुन्हा प्रयत्न करा.\";
        }};
    }}
    </script>
    """, height=120)

    search = st.text_input("🔍 नाव / आडनाव / घर नं टाका (जसं Google वर टाकता)", value=st.session_state.search_q, placeholder="उदा: पाटील, शिंदे, 142, मंदिराजवळ...", key="main_search")

    # --- GOOGLE LIKE SEARCH LOGIC ---
    def google_search(houses, query):
        if not query:
            return houses
        query = query.lower().strip()
        # Split query into words like Google
        q_words = query.split()
        results = []
        for h in houses:
            # Make one big searchable string for each house
            searchable = f"{h['name']} {h['house_no']} {h['landmark']}".lower()
            # Check if ALL words are present (Google AND logic)
            # OR if any word is present (OR logic - more results)
            score = 0
            for w in q_words:
                if w in searchable:
                    score += 1
            if score > 0:
                results.append((h, score))
        # Sort by score - best match first like Google
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]

    filtered = google_search(houses, search)

    st.write(f"**{len(filtered)} रिझल्ट सापडले** for '{search}'" if search else f"**{len(filtered)} घरं आहेत गावात**")

    # Map
    m = folium.Map(location=[17.72303, 75.77398], zoom_start=16)
    for h in filtered[:50]:
        popup = f"<b>{h['name']}</b><br>घर नं: {h['house_no']}<br>{h['landmark']}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 दिशा पहा</a>"
        folium.Marker([h['lat'], h['lon']], popup=folium.Popup(popup, max_width=250), tooltip=h['name'], icon=folium.Icon(color="red", icon="home")).add_to(m)
    st_folium(m, width=700, height=400, returned_objects=[])

    st.divider()
    # Results like Google
    for h in filtered[:30]:
        with st.container(border=True):
            c1, c2 = st.columns([3,1])
            with c1:
                # Highlight matching text
                st.markdown(f"**🏠 {h['name']}** | घर नं: `{h['house_no']}` | 👨‍👩‍👧‍👦 {h['family_count']} लोक")
                st.caption(f"📍 {h['landmark']} | Lat: {h['lat']}, Lon: {h['lon']}")
            with c2:
                st.link_button("🧭 रस्ता पहा", f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}", use_container_width=True, type="primary")

# --- Admin Tabs (same as before) ---
if is_admin:
    with t2:
        st.subheader("➕ Real घर जोडा")
        name = st.text_input("नाव *"); house_no = st.text_input("घर नं *"); landmark = st.text_input("खूण")
        c1,c2,c3 = st.columns(3)
        with c1: family_count = st.number_input("सदस्य",1,20,4)
        with c2: mobile = st.text_input("मोबाईल")
        with c3: water = st.selectbox("पाणी", ["Yes","No"])
        lat = st.number_input("Lat", value=17.72303, format="%.6f"); lon = st.number_input("Lon", value=75.77398, format="%.6f")
        if st.button("✅ सेव्ह करा", type="primary", use_container_width=True):
            if name and house_no:
                houses.append({"name":name,"house_no":house_no,"landmark":landmark,"family_count":family_count,"mobile":mobile,"water":water,"lat":lat,"lon":lon})
                save_data(houses); st.success("Saved!"); st.balloons()
    with t3:
        st.subheader("📊 Dashboard")
        total_p = sum([h.get('family_count',0) for h in houses])
        c1,c2 = st.columns(2); c1.metric("घरे", len(houses)); c2.metric("लोकसंख्या", total_p)
        st.dataframe(pd.DataFrame(houses), use_container_width=True)
        if st.button("🗑️ Dummy Delete"): os.remove(DB_FILE); st.rerun()
    with t4:
        st.subheader("🔳 QR Generator")
        typ = st.radio("QR प्रकार", ["🏠 एका घराचा QR", "🏛️ गावाचा मोठा QR"])
        if typ == "🏠 एका घराचा QR":
            sel = st.selectbox("घर निवडा", [f"{h['house_no']} - {h['name']}" for h in houses])
            idx = [f"{h['house_no']} - {h['name']}" for h in houses].index(sel)
            h = houses[idx]
            link = f"https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}"
            qr = make_qr(link)
            st.image(qr, width=250); st.download_button("📥 Download QR", qr, file_name=f"QR_{h['house_no']}.png")
        else:
            link = st.text_input("Live App Link", value="https://pakani-smart-village-final-i7wl8jzd9ftr5mdskvwwm6.streamlit.app/")
            if link:
                qr = make_qr(link)
                st.image(qr, width=300); st.download_button("📥 Entry QR Download", qr, file_name="Pakani_Entry_QR.png")