import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl
import json, os, io
import pandas as pd

st.set_page_config(page_title="Pakani Smart Map", layout="wide", page_icon="📍")

PAKANI_LAT, PAKANI_LON = 17.6205, 75.8820
APPROVED_FILE = "pakani_houses.json"
PENDING_FILE = "pakani_pending.json"
PASSWORD = "pakani123"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if 'auto_lat' not in st.session_state: st.session_state.auto_lat = ""
if 'auto_lon' not in st.session_state: st.session_state.auto_lon = ""
if 'admin_lat' not in st.session_state: st.session_state.admin_lat = ""
if 'admin_lon' not in st.session_state: st.session_state.admin_lon = ""
if 'search_query' not in st.session_state: st.session_state.search_query = ""

houses = load_json(APPROVED_FILE)
pending = load_json(PENDING_FILE)

st.markdown("<h2 style='text-align:center;'>📍 पाकणी स्मार्ट व्हिलेज</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Gaon ka Apna Google Maps - Admin Full Control</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗺️ MAP + Search", "🏠 Add My House", "🔐 Admin - King"])

# ================= TAB 1 MAP - PRIVACY LOGIC =================
with tab1:
    col1, col2 = st.columns([5,1])
    with col1:
        search_input = st.text_input("Search", value=st.session_state.search_query, placeholder="Naam likho ya 🎙️ bolo...", label_visibility="collapsed")
    with col2:
        try:
            from streamlit_mic_recorder import mic_recorder
            audio = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key="mic")
            if audio:
                import speech_recognition as sr
                r = sr.Recognizer()
                with io.BytesIO(audio['bytes']) as wav_file:
                    with sr.AudioFile(wav_file) as source:
                        audio_data = r.record(source)
                        try:
                            text = r.recognize_google(audio_data, language="mr-IN")
                            st.session_state.search_query = text
                            st.rerun()
                        except:
                            try:
                                text = r.recognize_google(audio_data, language="en-IN")
                                st.session_state.search_query = text
                                st.rerun()
                            except:
                                st.error("Phir bolo")
        except:
            st.write("")

    final_search = st.session_state.search_query if st.session_state.search_query else search_input

    # PRIVACY LOGIC
    def is_visible(house, search_text):
        privacy = house.get('privacy', 'Private')
        if privacy == 'Public':
            return True
        if privacy == 'Hidden':
            return False # Public Map pe kabhi nahi
        if privacy == 'Private':
            if not search_text:
                return False # Search nahi toh Private nahi dikhega - bheed kam
            else:
                return search_text.lower() in house['name'].lower() or search_text.lower() in house.get('family','').lower()
        return True

    filtered = [h for h in houses if is_visible(h, final_search)]

    if final_search:
        st.success(f"Search: {final_search} | Found: {len(filtered)}")
    else:
        st.info(f"Public Houses: {len(filtered)} | Search karo toh Private ghar bhi milenge")

    m = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=17)
    LocateControl(auto_start=True).add_to(m)
    folium.Marker([PAKANI_LAT, PAKANI_LON], tooltip="Gram Panchayat", icon=folium.Icon(color="green", icon="star")).add_to(m)

    for h in filtered:
        folium.Marker([h['lat'], h['lon']],
                      popup=f"<b>{h['name']}</b><br>House:{h.get('house_no','')}<br>Ward:{h.get('ward','')}<br>Family:{h.get('family','')}<br>Privacy:{h.get('privacy','Private')}<br><a href='https://www.google.com/maps/dir/?api=1&destination={h['lat']},{h['lon']}' target='_blank'>🧭 Rasta Dekho</a>",
                      tooltip=f"🏠 {h['name']} ({h.get('privacy','Private')})",
                      icon=folium.Icon(color="red", icon="home")).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width=1200, height=550, key="main_map")

# ================= TAB 2 VILLAGER - SIRF FORM =================
with tab2:
    st.subheader("🏠 माझे घर जोडा - Sirf Form Bharo")
    st.warning("Note: Aapka ghar default Private rahega - Sirf naam search pe milega - Public karna Admin ka kaam hai")

    m2 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19)
    LocateControl(auto_start=True, flyTo=True).add_to(m2)
    data2 = st_folium(m2, width=1200, height=350, returned_objects=["last_clicked"], key="map2")

    if data2.get("last_clicked"):
        st.session_state.auto_lat = str(data2["last_clicked"]["lat"])
        st.session_state.auto_lon = str(data2["last_clicked"]["lng"])

    if st.session_state.auto_lat:
        st.success(f"✅ Location Locked: {st.session_state.auto_lat}, {st.session_state.auto_lon}")
    else:
        st.info("📍 Map pe apne ghar pe CLICK karo")

    with st.form("villager_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *")
            house_no = st.text_input("House No")
            mobile = st.text_input("Mobile")
        with c2:
            ward = st.text_input("Ward / Galli")
            family = st.text_area("Family Members")

        if st.form_submit_button("📤 Admin ko Bhejo", use_container_width=True):
            if not name or not st.session_state.auto_lat:
                st.error("Pehle Map pe click karo!")
            else:
                pending.append({"name": name, "house_no": house_no, "ward": ward, "mobile": mobile, "family": family, "lat": float(st.session_state.auto_lat), "lon": float(st.session_state.auto_lon), "privacy": "Private"})
                save_json(PENDING_FILE, pending)
                st.success(f"✅ {name} - Admin approve karega - Privacy Admin set karega")
                st.balloons()
                st.session_state.auto_lat = ""
                st.session_state.auto_lon = ""

# ================= TAB 3 ADMIN - KING =================
with tab3:
    pwd = st.text_input("Admin Password", type="password")
    if pwd == PASSWORD:
        st.success(f"ADMIN POWER ON | Total: {len(houses)} | Pending: {len(pending)} | Hidden bhi yaha dikhenge")
        t1, t2, t3_admin, t4 = st.tabs(["✅ Pending", "➕ Direct Add", "🔒 Privacy Control - KING", "🗑️ Edit/Delete"])

        with t1:
            if not pending:
                st.info("No pending")
            for i, h in enumerate(pending):
                with st.container(border=True):
                    st.write(f"**{h['name']}** | H:{h.get('house_no','')} | W:{h.get('ward','')} | F:{h.get('family','')} | M:{h.get('mobile','')}")
                    st.caption(f"{h['lat']}, {h['lon']} | Default: {h.get('privacy','Private')}")
                    c1, c2, c3 = st.columns(3)
                    # Admin yahi pe privacy set kar sakta hai
                    p_choice = c1.selectbox("Set Privacy", ["Private","Public","Hidden"], key=f"p_pending_{i}")
                    if c2.button("✅ Approve", key=f"a{i}"):
                        h['privacy'] = p_choice
                        houses.append(h)
                        pending.pop(i)
                        save_json(APPROVED_FILE, houses)
                        save_json(PENDING_FILE, pending)
                        st.rerun()
                    if c3.button("❌ Reject", key=f"r{i}"):
                        pending.pop(i)
                        save_json(PENDING_FILE, pending)
                        st.rerun()

        with t2:
            st.subheader("Admin Direct Add - Full Power")
            m3 = folium.Map(location=[PAKANI_LAT, PAKANI_LON], zoom_start=19)
            LocateControl(auto_start=True, flyTo=True).add_to(m3)
            data3 = st_folium(m3, width=1200, height=300, returned_objects=["last_clicked"], key="m3")
            if data3.get("last_clicked"):
                st.session_state.admin_lat = str(data3["last_clicked"]["lat"])
                st.session_state.admin_lon = str(data3["last_clicked"]["lng"])
            if st.session_state.admin_lat:
                st.success(f"✅ {st.session_state.admin_lat}, {st.session_state.admin_lon}")

            with st.form("admin_direct"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    aname = st.text_input("Name *")
                    ahouse = st.text_input("House No")
                with c2:
                    award = st.text_input("Ward")
                    amob = st.text_input("Mobile")
                with c3:
                    afam = st.text_area("Family")
                    aprivacy = st.selectbox("Privacy - KING POWER", ["Private","Public","Hidden"])
                if st.form_submit_button("🏠 Add Direct", use_container_width=True):
                    if not aname or not st.session_state.admin_lat:
                        st.error("Map pe click karo")
                    else:
                        houses.append({"name": aname, "house_no": ahouse, "ward": award, "mobile": amob, "family": afam, "lat": float(st.session_state.admin_lat), "lon": float(st.session_state.admin_lon), "privacy": aprivacy})
                        save_json(APPROVED_FILE, houses)
                        st.success(f"✅ {aname} Added as {aprivacy}")
                        st.balloons()

        with t3_admin:
            st.subheader("🔒 Privacy Control - Sirf Admin Kar Sakta Hai")
            st.info("Yaha se kisi bhi ghar ko Public/Private/Hidden kar sakte ho - Villager nahi kar sakta")
            if houses:
                df = pd.DataFrame(houses)
                st.dataframe(df, use_container_width=True)
                st.divider()
                for idx, h in enumerate(houses):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3,2,1])
                        with col1:
                            st.write(f"**{h['name']}** - {h.get('ward','')} | Now: **{h.get('privacy','Private')}**")
                        with col2:
                            new_p = st.selectbox("Change to", ["Public","Private","Hidden"], index=["Public","Private","Hidden"].index(h.get('privacy','Private')), key=f"change_{idx}")
                        with col3:
                            if st.button("💾 Save", key=f"save_p_{idx}"):
                                houses[idx]['privacy'] = new_p
                                save_json(APPROVED_FILE, houses)
                                st.success(f"{h['name']} -> {new_p}")
                                st.rerun()

        with t4:
            if houses:
                st.dataframe(pd.DataFrame(houses), use_container_width=True)
                idx = st.number_input("Row to Delete/Edit", 0, len(houses)-1, 0)
                if st.button("🗑️ Delete House"):
                    houses.pop(idx)
                    save_json(APPROVED_FILE, houses)
                    st.rerun()
    elif pwd:
        st.error("Wrong Password")