import streamlit as st
import requests
import uuid
import os

api_url = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="גלי – עוזרת AI גינקולוגיה", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap');

/* ── Global RTL & Fonts ── */
html, body, [class*="css"], .stApp, .stMarkdown,
[data-testid="stSidebar"], [data-testid="stChatMessageContent"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Assistant', sans-serif !important;
}

.stApp { background: #faf8f6 !important; }

/* ── Remove Default Main Padding ── */
.stMainBlockContainer,
[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    max-width: 900px !important;
    margin: 0 auto !important;
    padding-bottom: 6rem !important;
}
[data-testid="stAppViewBlockContainer"] { padding-top: 0 !important; }

/* ── Sidebar (Force Native to Right) ── */
section[data-testid="stSidebar"] {
    background: #f0ecf4 !important;
    border-left: none !important;
    border-right: none !important;
    border-inline-start: 1px solid #e2dce8 !important;
}
[data-testid="stSidebar"][aria-expanded="true"],
[data-testid="stSidebar"] {
    direction: rtl !important;
    right: 0 !important;
    left: auto !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown strong,
section[data-testid="stSidebar"] label {
    color: #7a6d83 !important;
    font-size: 0.88rem !important;
    line-height: 1.8 !important;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #5c4f66 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] hr { border-color: #e2dce8 !important; }

/* ── Header (Full-width) ── */
.gali-header {
    background: #5b7e72;
    padding: 1.3rem 1rem;
    text-align: center;
    width: 100vw;
    position: relative;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    margin-bottom: 2rem;
}
.gali-header h1 {
    color: #fff;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    font-family: 'Assistant', sans-serif;
}
.gali-header p {
    color: rgba(255,255,255,0.7);
    font-size: 0.82rem;
    font-weight: 300;
    margin-top: 0.15rem;
}

/* ── Streamlit Chat Message Native RTL Alignments ── */
[data-testid="stChatMessage"] {
    direction: rtl !important;
    display: flex !important;
    flex-direction: row !important;
    gap: 1rem !important;
}

/* ── Custom Sources Badge ── */
.native-source {
    display: inline-block;
    margin-top: 0.8rem;
    font-size: 0.75rem;
    color: #5b7e72;
    background: rgba(91,126,114,0.07);
    border: 1px solid rgba(91,126,114,0.18);
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
}

/* ── Input Bar ── */
[data-testid="stBottom"],
[data-testid="stBottom"] > *,
[data-testid="stBottom"] > * > *,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > *,
[data-testid="stBottomBlockContainer"] > * > * {
    background: #faf8f6 !important;
    background-color: #faf8f6 !important;
}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > *,
[data-testid="stChatInput"] > * > *,
.stChatInput,
.stChatInput > *,
.stChatInput > * > *,
.stChatInput div,
.stChatInput form,
.stChatInput [data-baseweb],
.stChatInput [data-baseweb] > * {
    background: #ffffff !important;
    background-color: #ffffff !important;
}

.stChatInput > div,
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 1px solid #ddd6e4 !important;
    border-radius: 18px !important;
    box-shadow: none !important;
}
.stChatInput > div:focus-within,
[data-testid="stChatInput"] > div:focus-within {
    border-color: #a48db8 !important;
}
.stChatInput textarea,
[data-testid="stChatInput"] textarea {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Assistant', sans-serif !important;
    font-size: 0.92rem !important;
    color: #3e3540 !important;
}

/* ── Disclaimer ── */
.disclaimer {
    background: rgba(153,173,167,0.1);
    border: 1px solid rgba(153,173,167,0.25);
    border-radius: 12px;
    padding: 0.9rem 1rem;
    font-size: 0.82rem;
    color: #7a6d83;
    line-height: 1.7;
    text-align: center;
    margin-top: 1rem;
}

/* Hide chrome */
#MainMenu, header { visibility: hidden; }

/* ══════════════════════════════════════════════
   MOBILE RESPONSIVE
   ══════════════════════════════════════════════ */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        min-width: 0 !important;
        width: 260px !important;
        transform: translateX(100%) !important;
        transition: transform 0.3s ease !important;
    }
    section[data-testid="stSidebar"][aria-expanded="true"] {
        transform: translateX(0) !important;
    }
    .gali-header { padding: 1rem 0.75rem; }
    .gali-header h1 { font-size: 1.4rem; }
}
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="gali-header">
    <h1>גלי</h1>
    <p>עוזרת AI למחלקת גינקולוגיה · מרכז רפואי וולפסון</p>
</div>
""", unsafe_allow_html=True)

# State init
query_params = st.query_params
param_session = query_params.get("session", None)

if "session_id" not in st.session_state:
    if param_session:
        st.session_state.session_id = param_session
    else:
        st.session_state.session_id = str(uuid.uuid4())
        st.query_params["session"] = st.session_state.session_id

if "messages" not in st.session_state:
    loaded = []
    try:
        resp = requests.get(f"{api_url}/history/{st.session_state.session_id}", timeout=10)
        if resp.ok:
            loaded = resp.json()
    except Exception:
        pass

    if loaded:
        st.session_state.messages = loaded
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "היי, אני גלי, העוזרת הדיגיטלית של מחלקת נשים בוולפסון. לפני שנתחיל, מה שמך?"}
        ]

# Sidebar
with st.sidebar:
    st.markdown("### אודות")
    st.markdown("**גלי** עונה על שאלות מתוך פרוטוקולים, הנחיות ומסמכים רפואיים של המחלקה.")
    st.markdown("---")
    st.markdown('<div class="disclaimer">גלי היא עוזרת AI ואינה מחליפה ייעוץ רפואי מקצועי. יש להתייעץ תמיד עם רופא/ה.</div>', unsafe_allow_html=True)

# Render Chat Output natively
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        if msg["role"] == "assistant" and "\n\nמקורות:" in content:
            text_part, src = content.split("\n\nמקורות:", 1)
            st.markdown(text_part)
            st.markdown(f'<span class="native-source">{src.strip()}</span>', unsafe_allow_html=True)
        else:
            st.markdown(content)

# Handle user input via native chat_input
if user_input := st.chat_input("כתבי כאן את השאלה..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("גלי מקלידה..."):
            try:
                resp = requests.post(
                    f"{api_url}/chat", 
                    json={"query": user_input, "session_id": st.session_state.session_id}, 
                    timeout=60
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])
                
                st.markdown(answer)
                if sources:
                    sources_str = ', '.join(sources)
                    st.markdown(f'<span class="native-source">{sources_str}</span>', unsafe_allow_html=True)
                    answer += f"\n\nמקורות: {sources_str}"
            except Exception as e:
                answer = f"שגיאה בחיבור לשרת: {e}"
                st.error(answer)
                
    st.session_state.messages.append({"role": "assistant", "content": answer})