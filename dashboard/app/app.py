import os, base64, requests, streamlit as st

API = "http://serve:8000"
st.title("HLAB Demo Dashboard")

st.header("0) Geolocation-first Auth (IP or Client GPS)")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Professor: Calibrate Classroom")
    lat = st.number_input("Latitude", value=42.3770, format="%.6f")
    lon = st.number_input("Longitude", value=-71.1167, format="%.6f")
    eps = st.number_input("Epsilon (meters)", value=float(os.getenv("GEO_EPSILON_M","60")), step=10.0)
    if st.button("Save Calibration"):
        try:
            r = requests.post(f"{API}/geo/calibrate", json={"lat":lat,"lon":lon,"epsilon_m":eps}, timeout=20)
            st.success(r.json())
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to calibrate: {e}")

with col2:
    st.subheader("Student: Verify Location")
    use_gps = st.checkbox("Provide my GPS (HTML5) manually (for demo)")
    gps_lat = st.number_input("My GPS Latitude", value=0.0, format="%.6f", disabled=not use_gps)
    gps_lon = st.number_input("My GPS Longitude", value=0.0, format="%.6f", disabled=not use_gps)
    gps_acc = st.number_input("My GPS Accuracy (m)", value=50.0, disabled=not use_gps)

    payload = {}
    if use_gps:
        payload = {"client_gps_lat": gps_lat, "client_gps_lon": gps_lon, "client_gps_accuracy_m": gps_acc}

    if st.button("Verify by IP/GPS"):
        try:
            r = requests.post(f"{API}/geo/verify", json=payload, timeout=20)
            st.json(r.json())
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to verify location: {e}")

st.divider()
st.header("1) Visual Verification (after geo passes)")
st.caption("Demo photo verification with challenge word. In production the frontend would call /geo/verify first.")
challenge = os.getenv("CHALLENGE_WORD","orchid")
img_file = st.file_uploader("Upload an image", type=["jpg","jpeg","png"])
st.write(f"Challenge word: **{challenge}**")
if img_file and st.button("Verify Photo"):
    b64 = base64.b64encode(img_file.read()).decode("utf-8")
    payload = {"image_b64": b64, "challenge_word": challenge}
    try:
        r = requests.post(f"{API}/verify", json=payload, timeout=30)
        st.json(r.json())
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to API: {e}")
