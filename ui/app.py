"""
ui/app.py – Gali chat UI (clean minimal, purple-sage, RTL).

Run:  uv run streamlit run ui/app.py
"""

import streamlit as st
import requests
import uuid
import markdown

API_URL = "http://localhost:8001/api/v1"

st.set_page_config(page_title="גלי – עוזרת AI גינקולוגיה", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"], .stApp, .stMarkdown,
section[data-testid="stSidebar"] {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Assistant', sans-serif !important;
}

/* ── Page background ── */
.stApp { background: #faf8f6 !important; }

/* ── Kill ALL default padding on main container ── */
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

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #f0ecf4 !important;
    border-left: 1px solid #e2dce8 !important;
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

/* ── Header (full-width) ── */
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

/* ── Chat ── */
.chat-container {
    max-width: 660px;
    margin: 0 auto;
    padding: 1.5rem 1rem 6rem;
}
.msg-row { display: flex; margin-bottom: 0.6rem; }
.msg-row.assistant { justify-content: flex-start; }
.msg-row.user { justify-content: flex-end; }
.msg-bubble {
    max-width: 80%;
    padding: 0.75rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.75;
    border-radius: 18px;
    color: #3e3540;
}
.msg-row.assistant .msg-bubble {
    background: #fff;
    border: 1px solid #e6e1ea;
}
.msg-row.user .msg-bubble {
    background: #eae4ef;
    border: 1px solid #ddd6e4;
}
.msg-source {
    display: inline-block;
    margin-top: 0.45rem;
    font-size: 0.75rem;
    color: #5b7e72;
    background: rgba(91,126,114,0.07);
    border: 1px solid rgba(91,126,114,0.18);
    border-radius: 6px;
    padding: 0.1rem 0.45rem;
}

/* ── Links inside chat bubbles ── */
.msg-row.assistant .msg-bubble a {
    color: #5b7e72 !important;
    font-weight: 600;
    text-decoration: underline;
}
.msg-row.assistant .msg-bubble a:hover {
    color: #476b5f !important;
}
.msg-row.user .msg-bubble a {
    color: #3e0254 !important;
    font-weight: 600;
    text-decoration: underline;
}
.msg-row.user .msg-bubble a:hover {
    color: #2a013a !important;
}

/* ── Typing dots ── */
.typing-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #99ada7;
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
   INPUT BAR – nuclear override for dark bg
   ══════════════════════════════════════════════ */

/* The entire bottom dock */
[data-testid="stBottom"],
[data-testid="stBottom"] > *,
[data-testid="stBottom"] > * > *,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > *,
[data-testid="stBottomBlockContainer"] > * > * {
    background: #faf8f6 !important;
    background-color: #faf8f6 !important;
}

/* The chat input wrapper and all children */
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

/* The actual visible input container */
.stChatInput > div,
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #ddd6e4 !important;
    border-radius: 18px !important;
    box-shadow: none !important;
}

/* Focus state */
.stChatInput > div:focus-within,
[data-testid="stChatInput"] > div:focus-within {
    border-color: #a48db8 !important;
    box-shadow: none !important;
}

/* Textarea itself */
.stChatInput textarea,
[data-testid="stChatInput"] textarea {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Assistant', sans-serif !important;
    font-size: 0.92rem !important;
    color: #3e3540 !important;
    background: transparent !important;
    background-color: transparent !important;
}
.stChatInput textarea::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #c0b5ca !important;
}

/* Send button */
.stChatInput button,
[data-testid="stChatInput"] button {
    background: #a48db8 !important;
    background-color: #a48db8 !important;
    border-radius: 50% !important;
    color: #fff !important;
    border: none !important;
}
.stChatInput button:hover,
[data-testid="stChatInput"] button:hover {
    background: #957da9 !important;
    background-color: #957da9 !important;
}
.stChatInput button svg,
[data-testid="stChatInput"] button svg {
    fill: #fff !important;
    stroke: #fff !important;
}

/* ── Spinner ── */
.stSpinner > div { color: #99ada7 !important; }

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

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stChatMessage"] {
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    min-height: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────

st.markdown("""
<div class="gali-header">
    <h1>גלי</h1>
    <p>עוזרת AI למחלקת גינקולוגיה · מרכז רפואי וולפסון</p>
</div>
""", unsafe_allow_html=True)

# ── Session State (persistent via URL query param) ────────────

query_params = st.query_params
param_session = query_params.get("session", None)

if "session_id" not in st.session_state:
    if param_session:
        st.session_state.session_id = param_session
    else:
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.query_params["session"] = st.session_state.session_id

if "messages" not in st.session_state:
    # Try to load existing history from MongoDB
    loaded = []
    try:
        resp = requests.get(
            f"{API_URL}/history/{st.session_state.session_id}", timeout=5
        )
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

# ── Sidebar ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### אודות")
    st.markdown("**גלי** עונה על שאלות מתוך פרוטוקולים, הנחיות ומסמכים רפואיים של המחלקה.")
    st.markdown("---")
    st.markdown('<div class="disclaimer">גלי היא עוזרת AI ואינה מחליפה ייעוץ רפואי מקצועי. יש להתייעץ תמיד עם רופא/ה.</div>', unsafe_allow_html=True)

# ── Render Chat ───────────────────────────────────────────────

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

# ── Chat Input ────────────────────────────────────────────────

if user_input := st.chat_input("כתבי כאן את השאלה..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    typing = render_chat().rstrip('</div>') + (
        '<div class="msg-row assistant"><div class="msg-bubble">'
        '<span class="typing-dot"></span><span class="typing-dot"></span>'
        '<span class="typing-dot"></span></div></div></div>'
    )
    chat_area.markdown(typing, unsafe_allow_html=True)
    try:
        resp = requests.post(f"{API_URL}/chat", json={"query": user_input, "session_id": st.session_state.session_id}, timeout=60)
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