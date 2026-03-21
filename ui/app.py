import streamlit as st
import requests
import uuid
import markdown
import os


api_url = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="גלי – עוזרת AI גינקולוגיה", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap');

/* ── Global — same font everywhere ── */
html, body, [class*="css"], .stApp, .stMarkdown,
section[data-testid="stSidebar"],
input, textarea, button, label, p, h1, h2, h3, h4, span, div, a {
    font-family: 'Assistant', sans-serif !important;
}
html, body, [class*="css"], .stApp, .stMarkdown,
section[data-testid="stSidebar"] {
    direction: rtl !important;
    text-align: right !important;
}
/* Revert Streamlit Material Icons font perfectly */
.material-icons, .material-symbols-rounded, span[class*="material"] {
    font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
}

/* ── Page background — warm ivory / cream ── */
.stApp { background: #FAF5E9 !important; }

/* ── Remove all padding from the main container ── */
.stMainBlockContainer,
[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
}

/* ══════════════════════════════════════════════
   1. HEADER — sticky, forest-green, matte
   ══════════════════════════════════════════════ */
.gali-header {
    background: #476b5f;
    padding: 1.4rem 1rem;
    text-align: center;
    width: 100vw;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
.gali-header h1 {
    color: #fff;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.02em;
}
.gali-header p {
    color: rgba(255,255,255,0.7);
    font-size: 0.82rem;
    font-weight: 300;
    margin-top: 0.2rem;
}
.header-spacer { height: 110px; }

/* ══════════════════════════════════════════════
   2. SIDEBAR — pale mint, NO border, smooth shadow
   ══════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #dfe8e3 !important;
    border: none !important;
    border-left: 1px solid rgba(71, 107, 95, 0.15) !important;
    border-right: none !important;
    border-inline-start: none !important;
    box-shadow: -6px 0 24px rgba(0,0,0,0.12) !important;
    top: 90px !important;
    height: calc(100vh - 90px) !important;
    z-index: 99 !important;
    overflow: hidden !important;
}
/* Ensure the sidebar's inner body never scrolls natively */
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    overflow: hidden !important;
    overflow-y: hidden !important;
}
section[data-testid="stSidebar"]::-webkit-scrollbar,
section[data-testid="stSidebar"] *::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
}
[data-testid="stSidebar"][aria-expanded="true"],
[data-testid="stSidebar"] {
    direction: rtl !important;
    right: 0 !important;
    left: auto !important;
}

/* ── Sidebar info card — forest-green, centered ── */
.sidebar-card-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 160px);
    padding: 1rem;
}
.sidebar-card {
    background: #476b5f;
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    color: #fff;
    width: 100%;
}
.sidebar-card .card-icon {
    font-size: 1.3rem;
    margin-bottom: 0.6rem;
    opacity: 0.9;
}
.sidebar-card .card-title {
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 0.7rem;
    color: #fff;
}
.sidebar-card .card-title strong {
    color: #fff !important;
    font-weight: 700;
}
.sidebar-card .card-divider {
    width: 100%;
    height: 1px;
    background: rgba(255,255,255,0.2);
    margin-bottom: 0.7rem;
}
.sidebar-card .card-disclaimer {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.9);
    line-height: 1.6;
}

/* ══════════════════════════════════════════════
   3. CHAT — Bubbles anchored heavily toward Sidebar 
   ══════════════════════════════════════════════ */
.chat-container {
    max-width: 850px;
    margin-right: 2rem;
    margin-left: auto;
    padding: 4rem 1rem 6rem;
}
.msg-row {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 0.6rem;
}
.msg-bubble {
    max-width: 78%;
    padding: 0.75rem 1.2rem;
    font-size: 0.92rem;
    line-height: 1.75;
    text-align: right;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
}

/* AI (Gali) */
.msg-row.assistant .msg-bubble {
    background: #476b5f;
    color: #fff;
    border-radius: 18px 18px 4px 18px;
}

/* User */
.msg-row.user .msg-bubble {
    background: #dfe8e3;
    color: #3a5f50;
    border-radius: 18px 18px 18px 4px;
}

/* Sources badge */
.msg-source {
    display: inline-block;
    margin-top: 0.45rem;
    font-size: 0.75rem;
    color: #fff;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 6px;
    padding: 0.1rem 0.45rem;
}

/* Links */
.msg-row.assistant .msg-bubble a {
    color: #d4e5e0 !important;
    font-weight: 600;
    text-decoration: underline;
}
.msg-row.assistant .msg-bubble a:hover { color: #fff !important; }
.msg-row.user .msg-bubble a {
    color: #3a5f50 !important;
    font-weight: 600;
    text-decoration: underline;
}

/* Typing dots */
.typing-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #fff;
    margin: 0 2px;
    animation: tp 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes tp {
    0%,60%,100% { opacity: 0.3; }
    30% { opacity: 1; }
}

/* ══════════════════════════════════════════════
   4. INPUT — pill shape, transparent internal fix,
      with low z-index so shadow falls cleanly
   ══════════════════════════════════════════════ */
[data-testid="stBottom"],
[data-testid="stBottom"] > *,
[data-testid="stBottom"] > * > *,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > *,
[data-testid="stBottomBlockContainer"] > * > * {
    background: #FAF5E9 !important;
    background-color: #FAF5E9 !important;
    position: relative;
    z-index: 10 !important;
}

/* Inner elements — transparent so white parent shows through cleanly */
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
    background: transparent !important;
    background-color: transparent !important;
}

.stChatInput > div,
[data-testid="stChatInput"] > div {
    background: rgba(223, 232, 227, 0.85) !important;
    background-color: rgba(223, 232, 227, 0.85) !important;
    border: 1.5px solid #476b5f !important;
    border-radius: 9999px !important;
    box-shadow: none !important;
    overflow: hidden !important;
}

.stChatInput > div:focus-within,
[data-testid="stChatInput"] > div:focus-within {
    border-color: #3a5f50 !important;
    box-shadow: none !important;
}

.stChatInput textarea,
[data-testid="stChatInput"] textarea {
    direction: rtl !important;
    text-align: right !important;
    font-size: 0.92rem !important;
    color: #3e3540 !important;
    background: transparent !important;
    background-color: transparent !important;
}
.stChatInput textarea::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #8a9e94 !important;
}

.stChatInput button,
[data-testid="stChatInput"] button {
    background: #476b5f !important;
    background-color: #476b5f !important;
    border-radius: 50% !important;
    color: #fff !important;
    border: none !important;
}
.stChatInput button:hover,
[data-testid="stChatInput"] button:hover {
    background: #3a5f50 !important;
    background-color: #3a5f50 !important;
}
.stChatInput button svg,
[data-testid="stChatInput"] button svg {
    fill: #fff !important;
    stroke: #fff !important;
}

/* ── Spinner ── */
.stSpinner > div { color: #8a9e94 !important; }

/* ── Hide Streamlit chrome completely ── */
#MainMenu, footer, header { visibility: hidden; }

/* Eliminate weird native chat borders */
[data-testid="stChatMessage"] {
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    min-height: 0 !important;
}

/* ══════════════════════════════════════════════
   MOBILE / NARROW WINDOWS — cleanly compacted scaling
   ══════════════════════════════════════════════ */
@media (max-width: 768px) {
    /* Hide the sidebar completely on mobile/tablet */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Shrink the sidebar inner content beautifully */
    .sidebar-card-wrapper { padding: 0.6rem; min-height: auto; margin-top: 0.5rem; }
    .sidebar-card { padding: 0.8rem 0.6rem; border-radius: 10px; }
    .sidebar-card .card-icon { font-size: 1rem; margin-bottom: 0.3rem; }
    .sidebar-card .card-title { font-size: 0.72rem; line-height: 1.45; margin-bottom: 0.4rem; }
    .sidebar-card .card-disclaimer { font-size: 0.62rem; line-height: 1.3; }
    
    /* Header compactness */
    .gali-header { padding: 0.85rem 0.5rem; }
    .gali-header h1 { font-size: 1.35rem; }
    .gali-header p { font-size: 0.65rem; margin-top: 0.1rem; }
    .header-spacer { height: 75px; }
    
    /* Main Chat proportionality */
    .chat-container {
        padding: 1.5rem 0.5rem 4.5rem;
        margin-right: 0;
        max-width: 100%;
    }
    .msg-bubble {
        max-width: 95%;
        padding: 0.55rem 0.8rem;
        font-size: 0.82rem;
        line-height: 1.5;
        border-radius: 14px 14px 4px 14px;
    }
    .msg-row.user .msg-bubble { border-radius: 14px 14px 14px 4px; }
    .msg-source { font-size: 0.65rem; padding: 0.1rem 0.35rem; margin-top: 0.25rem; }
    
    .stMainBlockContainer,
    [data-testid="stMainBlockContainer"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Bottom text input scaling */
    [data-testid="stBottom"] { padding: 0 0.4rem !important; }
    .stChatInput > div { border-width: 1px !important; }
    .stChatInput textarea,
    [data-testid="stChatInput"] textarea { font-size: 0.82rem !important; padding: 0.5rem !important; }
}

/* ── Extra small (under 450px) — Ultimate shrink ── */
@media (max-width: 450px) {
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    .gali-header h1 { font-size: 1.2rem; }
    .gali-header p { font-size: 0.6rem; }
    .header-spacer { height: 70px; }
    .msg-bubble { font-size: 0.78rem; padding: 0.5rem 0.65rem; }
    .chat-container { padding: 1rem 0.3rem 4rem; }
}
</style>
""", unsafe_allow_html=True)

# Header — fixed, above everything
st.markdown("""
<div class="gali-header">
    <h1>גלי</h1>
    <p>עוזרת AI למחלקת גינקולוגיה · מרכז רפואי וולפסון</p>
</div>
<div class="header-spacer"></div>
""", unsafe_allow_html=True)

# Session state
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

# Sidebar — vertically centered green card
with st.sidebar:
    st.markdown("""
    <div class="sidebar-card-wrapper">
        <div class="sidebar-card">
            <div class="card-icon">ⓘ</div>
            <div class="card-title">
                <strong>גלי</strong> עונה על שאלות מתוך פרוטוקולים,
                הנחיות ומסמכים רפואיים של המחלקה.
            </div>
            <div class="card-divider"></div>
            <div class="card-disclaimer">
                גלי היא עוזרת AI ואינה מחליפה ייעוץ רפואי מקצועי. יש להתייעץ תמיד עם רופא/ה.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Chat rendering — all right-aligned (RTL: flex-start = right)
def render_chat():
    parts = ['<div class="chat-container">']
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant" and "\n\nמקורות:" in content:
            text_part, src = content.split("\n\nמקורות:", 1)
            html = markdown.markdown(text_part) + f'<span class="msg-source">{src.strip()}</span>'
        else:
            html = markdown.markdown(content)
        parts.append(f'<div class="msg-row {role}"><div class="msg-bubble">{html}</div></div>')
    parts.append('</div>')
    return "\n".join(parts)

chat_area = st.empty()
chat_area.markdown(render_chat(), unsafe_allow_html=True)

if user_input := st.chat_input("כתבי כאן את השאלה..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    typing = render_chat().rstrip('</div>') + (
        '<div class="msg-row assistant"><div class="msg-bubble" style="background:#476b5f;color:#fff;'
        'border-radius:18px 18px 4px 18px;">'
        '<span class="typing-dot"></span><span class="typing-dot"></span>'
        '<span class="typing-dot"></span></div></div></div>'
    )
    chat_area.markdown(typing, unsafe_allow_html=True)
    try:
        resp = requests.post(f"{api_url}/chat", json={"query": user_input, "session_id": st.session_state.session_id}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        answer = data["answer"]
        sources = data.get("sources", [])
        if sources:
            answer += f"\n\nמקורות: {', '.join(sources)}"
    except Exception as e:
        answer = f"שגיאה בחיבור לשרת: {e}"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    chat_area.markdown(render_chat(), unsafe_allow_html=True)