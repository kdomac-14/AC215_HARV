import os, base64, requests, streamlit as st
import streamlit.components.v1 as components

API = "http://serve:8000"

# Title and mode toggle
title_col, toggle_col = st.columns([4, 1])
with title_col:
    st.title("HLAB Demo Dashboard")
with toggle_col:
    st.write("")  # spacing
    is_professor = st.toggle("Professor Mode", value=True, help="Toggle between Professor and Student modes")

mode = "Professor" if is_professor else "Student"
st.caption(f"Current Mode: **{mode}**")

st.header("0) Geolocation-first Auth (IP or Client GPS)")

if is_professor:
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
else:
    st.subheader("Student: Verify Location")
    
    # Initialize session state for GPS
    if "gps_data" not in st.session_state:
        st.session_state.gps_data = None
    if "gps_status" not in st.session_state:
        st.session_state.gps_status = None
    
    # Verification method selection
    verify_method = st.radio(
        "Choose verification method:",
        ["📱 GPS (Accurate 5-50m)", "🌐 IP-based (Quick but less accurate)"],
        help="GPS uses your device's location for best accuracy. IP-based uses your internet connection."
    )
    
    if "GPS" in verify_method:
        st.markdown("### 📱 Embedded GPS Collection")
        st.info("Click the button below to use your device's GPS. Your browser will ask for permission.")
        
        # Embedded GPS HTML component
        gps_html = f"""
        <style>
            .gps-container {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
            }}
            .gps-btn {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                margin: 10px 0;
            }}
            .gps-btn:hover {{
                background: #45a049;
            }}
            .gps-btn:disabled {{
                background: #ccc;
                cursor: not-allowed;
            }}
            .gps-status {{
                padding: 12px;
                border-radius: 6px;
                margin: 10px 0;
                display: none;
            }}
            .gps-status.show {{
                display: block;
            }}
            .gps-status.success {{
                background: #d4edda;
                color: #155724;
            }}
            .gps-status.error {{
                background: #f8d7da;
                color: #721c24;
            }}
            .gps-status.info {{
                background: #d1ecf1;
                color: #0c5460;
            }}
            .gps-info {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                font-family: monospace;
                font-size: 13px;
                display: none;
            }}
            .gps-info.show {{
                display: block;
            }}
        </style>
        
        <div class="gps-container">
            <button class="gps-btn" id="gpsBtn" onclick="getGPS()">
                🛰️ Get My GPS Location
            </button>
            <div id="gpsStatus" class="gps-status"></div>
            <div id="gpsInfo" class="gps-info"></div>
        </div>
        
        <script>
            const API_URL = "{API}";
            
            function showStatus(msg, type) {{
                const status = document.getElementById('gpsStatus');
                status.className = 'gps-status show ' + type;
                status.innerHTML = msg;
            }}
            
            function showInfo(info) {{
                const infoDiv = document.getElementById('gpsInfo');
                infoDiv.className = 'gps-info show';
                infoDiv.innerHTML = info;
            }}
            
            async function getGPS() {{
                const btn = document.getElementById('gpsBtn');
                btn.disabled = true;
                btn.textContent = '📡 Requesting GPS...';
                
                showStatus('📡 Requesting GPS permission...', 'info');
                
                if (!navigator.geolocation) {{
                    showStatus('❌ GPS not supported on this browser', 'error');
                    btn.disabled = false;
                    btn.textContent = '🛰️ Get My GPS Location';
                    return;
                }}
                
                navigator.geolocation.getCurrentPosition(
                    async (position) => {{
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const acc = position.coords.accuracy;
                        
                        showStatus('✓ GPS acquired! Verifying...', 'info');
                        showInfo(
                            'Latitude: ' + lat.toFixed(6) + '<br>' +
                            'Longitude: ' + lon.toFixed(6) + '<br>' +
                            'Accuracy: ±' + Math.round(acc) + 'm'
                        );
                        
                        btn.textContent = '📤 Verifying...';
                        
                        try {{
                            const response = await fetch(API_URL + '/geo/verify', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{
                                    client_gps_lat: lat,
                                    client_gps_lon: lon,
                                    client_gps_accuracy_m: acc
                                }})
                            }});
                            
                            const result = await response.json();
                            
                            if (result.ok) {{
                                showStatus(
                                    '✅ <strong>Location Verified!</strong><br>' +
                                    'Distance: ' + Math.round(result.distance_m) + 'm<br>' +
                                    'Allowed: ' + Math.round(result.epsilon_m) + 'm',
                                    'success'
                                );
                            }} else {{
                                const reason = result.reason || 'unknown';
                                if (reason === 'not_calibrated') {{
                                    showStatus('❌ Classroom not calibrated yet', 'error');
                                }} else {{
                                    showStatus(
                                        '❌ <strong>Too far from classroom</strong><br>' +
                                        'Distance: ' + Math.round(result.distance_m) + 'm<br>' +
                                        'Allowed: ' + Math.round(result.epsilon_m) + 'm',
                                        'error'
                                    );
                                }}
                            }}
                        }} catch (error) {{
                            showStatus('❌ Connection error: ' + error.message, 'error');
                        }}
                        
                        btn.disabled = false;
                        btn.textContent = '🔄 Try Again';
                    }},
                    (error) => {{
                        let msg = '';
                        switch(error.code) {{
                            case error.PERMISSION_DENIED:
                                msg = '❌ Permission denied. Please allow location access in your browser settings.';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                msg = '❌ GPS unavailable. Try moving outside or near a window.';
                                break;
                            case error.TIMEOUT:
                                msg = '❌ GPS timeout. Please try again.';
                                break;
                            default:
                                msg = '❌ GPS error: ' + error.message;
                        }}
                        showStatus(msg, 'error');
                        btn.disabled = false;
                        btn.textContent = '🛰️ Get My GPS Location';
                    }},
                    {{
                        enableHighAccuracy: true,
                        timeout: 15000,
                        maximumAge: 0
                    }}
                );
            }}
        </script>
        """
        
        # Embed the HTML component with sufficient height
        components.html(gps_html, height=350)
        
        st.divider()
        
        # Alternative: Manual input (collapsed by default)
        with st.expander("📝 Or enter GPS coordinates manually"):
            st.caption("**Get your coordinates:**")
            st.markdown("""
- **iPhone:** Open Maps → tap blue dot → swipe up → see coordinates
- **Android:** Open Google Maps → long-press your location → see coordinates at top
- **Browser:** Visit https://www.latlong.net/
""")
            
            man_lat = st.number_input("Latitude", value=42.3770, format="%.6f", key="man_lat")
            man_lon = st.number_input("Longitude", value=-71.1167, format="%.6f", key="man_lon")
            man_acc = st.number_input("Accuracy (m)", value=20.0, key="man_acc", 
                                       help="GPS: 5-20m, WiFi: 50-100m")
            
            if st.button("✓ Verify with Manual Coordinates"):
                try:
                    r = requests.post(f"{API}/geo/verify", json={
                        "client_gps_lat": man_lat,
                        "client_gps_lon": man_lon,
                        "client_gps_accuracy_m": man_acc
                    }, timeout=20)
                    result = r.json()
                    
                    if result.get("ok"):
                        st.success(f"✅ **Location Verified!**\n\n"
                                  f"**Method:** `{result.get('source')}`  \n"
                                  f"**Distance:** {result['distance_m']:.1f}m (within {result['epsilon_m']:.0f}m allowed)")
                        st.balloons()
                    else:
                        reason = result.get('reason', 'unknown')
                        if reason == 'not_calibrated':
                            st.error("❌ Classroom not calibrated yet. Ask professor to calibrate first.")
                        else:
                            dist = result.get('distance_m')
                            eps = result.get('epsilon_m')
                            st.error(f"❌ **Too far from classroom**\n\n"
                                    f"**Distance:** {dist:.1f}m  \n"
                                    f"**Allowed:** {eps:.0f}m  \n"
                                    f"**You need to be {dist - eps:.1f}m closer**")
                    
                    with st.expander("📊 Technical details"):
                        st.json(result)
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Failed to connect to server: {e}")
    
    else:  # IP-based verification
        # Show current geo provider status
        try:
            health = requests.get(f"{API}/healthz", timeout=5).json()
            provider = health.get("geo_provider", "Unknown")
            if provider == "GoogleGeo":
                st.info("🌐 Using **Google Geolocation API** (WiFi/cell tower-based, ~1-5km accuracy)")
            elif provider == "IpApi":
                st.warning("⚠️ Using **IP-based geolocation** (city-level accuracy only). Set GOOGLE_API_KEY for better accuracy.")
            elif provider == "MockGeo":
                st.info("🧪 Using **Mock provider** (returns Harvard Yard coordinates)")
        except:
            pass
        
        # Simple verify button - backend will auto-detect location
        if st.button("✓ Verify My Location (IP)", type="primary"):
            try:
                r = requests.post(f"{API}/geo/verify", json={}, timeout=20)
                result = r.json()
                
                if result.get("ok"):
                    st.success(f"✅ **Location verified!**\n\n"
                              f"**Method:** `{result.get('source')}`  \n"
                              f"**Distance:** {result['distance_m']:.1f}m (within {result['epsilon_m']:.0f}m allowed)")
                    st.balloons()
                else:
                    reason = result.get('reason', 'unknown')
                    if reason == 'not_calibrated':
                        st.error("❌ Classroom not calibrated yet. Ask professor to calibrate first.")
                    else:
                        dist = result.get('distance_m')
                        eps = result.get('epsilon_m')
                        st.error(f"❌ **Too far from classroom**\n\n"
                                f"**Distance:** {dist:.1f}m  \n"
                                f"**Allowed:** {eps:.0f}m  \n"
                                f"**You need to be {dist - eps:.1f}m closer**")
                
                with st.expander("📊 Technical details"):
                    st.json(result)
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to connect to server: {e}")
    
    st.caption("💡 **Note:** For production use, deploy a mobile app that sends GPS/WiFi data to the backend.")

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
