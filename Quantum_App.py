import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

# ==========================================
# 1. CORE SYSTEM & DATABASE HANDSHAKE
# ==========================================
st.set_page_config(layout="wide", page_title="Quantum X Global", page_icon="💹")

# Force black/dark theme styling
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #e7e9ea; }
    .pfp-circle { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; margin-right: 12px; }
    .logo-square { width: 48px; height: 48px; border-radius: 8px; object-fit: contain; background: #16181c; margin-right: 12px; }
    .content-card { border: 1px solid #2f3336; padding: 20px; border-radius: 16px; margin-bottom: 15px; background: #000000; }
    .verified-badge { color: #FFD700; margin-left: 5px; font-weight: bold; }
    .handle-text { color: #71767b; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# Connection to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_profiles = conn.read(worksheet="Profiles", ttl=0)
    df_posts = conn.read(worksheet="Posts", ttl=0)
    # Ensure columns exist if sheet is empty
    if df_profiles.empty:
        df_profiles = pd.DataFrame(columns=["username", "name", "type", "verified", "style", "pfp", "bio"])
    if df_posts.empty:
        df_posts = pd.DataFrame(columns=["author", "text", "likes", "dislikes"])
except Exception as e:
    st.error("⚠️ Connection Error: Check your Streamlit Secrets and Google Sheet sharing permissions.")
    st.stop()

# ==========================================
# 2. IDENTITY MANAGEMENT (SIDEBAR)
# ==========================================
if "auth" not in st.session_state: st.session_state.auth = False

with st.sidebar:
    st.markdown("<h1 style='color:#1d9bf0;'>💹 Quantum X</h1>", unsafe_allow_html=True)
    
    if not st.session_state.auth:
        st.subheader("Login / Register")
        u_in = st.text_input("Choose Username", placeholder="e.g. quantum_ceo")
        u_type = st.radio("Account Type", ["Individual", "Company"])
        
        if st.button("Enter Network", use_container_width=True):
            if u_in:
                # Login if exists, otherwise Register
                if u_in in df_profiles['username'].values:
                    st.session_state.user = u_in
                    st.session_state.auth = True
                    st.rerun()
                else:
                    new_user = pd.DataFrame([{
                        "username": u_in, "name": u_in, "type": u_type,
                        "verified": "False", "style": "Circle", "bio": "",
                        "pfp": "https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png"
                    }])
                    updated_p = pd.concat([df_profiles, new_user], ignore_index=True)
                    conn.update(worksheet="Profiles", data=updated_p)
                    st.success("Identity Created! Click Enter again.")
    else:
        # Fetch logged-in user details
        user_row = df_profiles[df_profiles['username'] == st.session_state.user].iloc[0]
        st.write(f"Logged in: **@{st.session_state.user}**")
        
        with st.expander("👤 Edit Profile"):
            edit_pfp = st.text_input("Avatar URL", value=user_row['pfp'])
            edit_style = st.radio("Shape", ["Circle", "Square"], index=0 if user_row['style'] == "Circle" else 1)
            if st.button("Update Identity"):
                df_profiles.loc[df_profiles['username'] == st.session_state.user, ['pfp', 'style']] = [edit_pfp, edit_style]
                conn.update(worksheet="Profiles", data=df_profiles)
                st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

# ==========================================
# 3. GLOBAL PULSE (MAIN FEED)
# ==========================================
st.title("Global Pulse")

if st.session_state.auth:
    with st.container(border=True):
        post_txt = st.text_area("What's happening?", placeholder="Broadcast to the network...", label_visibility="collapsed")
        if st.button("Post", type="primary"):
            if post_txt:
                new_post = pd.DataFrame([{"author": st.session_state.user, "text": post_txt, "likes": 0, "dislikes": 0}])
                updated_posts = pd.concat([df_posts, new_post], ignore_index=True)
                conn.update(worksheet="Posts", data=updated_posts)
                st.rerun()

# Display logic for the feed
for _, row in df_posts.iloc[::-1].iterrows():
    # Find the author's profile info for the UI
    p_info = df_profiles[df_profiles['username'] == row['author']]
    if not p_info.empty:
        p = p_info.iloc[0]
        img_class = "pfp-circle" if p['style'] == "Circle" else "logo-square"
        badge = "<span class='verified-badge'>✔</span>" if str(p['verified']) == "True" else ""
        
        st.markdown(f"""
        <div class="content-card">
            <div style="display: flex; align-items: flex-start;">
                <img src="{p['pfp']}" class="{img_class}">
                <div>
                    <b>{p['name']}</b>{badge} <span class="handle-text">@{row['author']}</span><br>
                    <div style="margin-top:8px;">{row['text']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. MARKET WATCH
# ==========================================
with st.sidebar:
    st.divider()
    st.subheader("📊 Market Pulse")
    ticker = st.text_input("Symbol", "BTC-USD")
    try:
        price = yf.Ticker(ticker).fast_info.last_price
        st.metric(ticker, f"${price:,.2f}")
    except:
        st.caption("Enter a valid ticker (e.g. AAPL, ETH-USD)")
