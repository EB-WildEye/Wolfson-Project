import os
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient
import lancedb

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
EMBED_MODEL = os.getenv("EMBED_MODEL")


def embed_text(text: str) -> list[float]:
    """Turn a string into a 768-dim vector using Gemini embeddings."""
    result = gemini_client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


def ask_gemini(query: str, context: str, history: list[dict] = None) -> str:
    """Send query + context + conversation history to Gemini."""
    # Build conversation history string
    history_text = ""
    if history:
        history_lines = []
        for msg in history[-10:]:  # last 10 messages
            role_label = "Patient" if msg["role"] == "user" else "Gali"
            history_lines.append(f"{role_label}: {msg['content']}")
        history_text = "\n".join(history_lines)

    prompt = (
        "You are Gali (גלי), the supportive, professional medical assistant at Wolfson Medical Center's Women's Department. "
        "Your mission is to provide accurate information based ONLY on the provided context.\n\n"

        "### 1. LANGUAGE & TONE:\n"
        "- Default language: Hebrew (עברית). If the user writes in another language, respond in THAT language.\n"
        "- Write in first-person feminine: 'אני כאן', 'אשמח לעזור'.\n"
        "- Speak warmly and professionally, as if face-to-face with the patient.\n"
        "- BANNED words: Never use 'יקרה', 'אהובה', 'מתוקה', 'נשמה', 'אמפתיה'.\n\n"

        "### 2. REASONING & NAME MEMORY (CRITICAL):\n"
        "- Scan the conversation history below for the patient's name.\n"
        "- If a name was given, use it approximately once every 4-5 messages to keep the interaction warm and human.\n"
        "- NEVER use the patient's name more than once in a single response.\n"
        "- If the user refuses to give their name or says they prefer not to, respect this completely. "
        "Continue helpfully without ever asking again.\n"
        "- If this is the first message and it looks like a name, greet them warmly and ask how you can help.\n\n"

        "### 3. SAFETY & RED FLAGS (CRITICAL):\n"
        "- SCAN context for 'Red Flags' (severe bleeding, fever, extreme pain).\n"
        "- If an emergency is detected, provide ONLY the ER link: [מיון נשים - חיוג 24/7: 03-5028318](tel:035028318)\n"
        "- For medical decisions, ALWAYS recommend consulting a physician.\n\n"

        "### 4. DATA INTEGRITY:\n"
        "- Answer based ONLY on the context below. If the answer is not in the context, say so honestly.\n"
        "- Staff Anonymity: Never mention names. Refer only to 'השירות הסוציאלי של המחלקה'.\n\n"

        "### 5. OUTPUT FORMAT & LINKS:\n"
        "- Plain text only. NO plain text phone numbers.\n"
        "- MANDATORY Markdown links for all contact info:\n"
        "  - Phone: [03-5028490](tel:035028490)\n"
        "  - WhatsApp: [לחצי כאן לשליחת הודעה](https://wa.me/97235028111)\n"
        "  - Emergency ER: [מיון נשים - חיוג 24/7: 03-5028318](tel:035028318)\n\n"

        "### 6. MANDATORY DISCLAIMER (DSC-GEN-01):\n"
        "You MUST end every single response with this exact text:\n"
        "'שימי לב כי המידע המוצג כאן הינו אינפורמטיבי בלבד ואינו מהווה תחליף לייעוץ רפואי מקצועי. השיחה נמחקת לאחר 24 שעות ואינה נשמרת בתיק הרפואי.'\n\n"
    )

    # Add conversation history if available
    if history_text:
        prompt += f"### Conversation History:\n{history_text}\n\n"

    prompt += f"Context:\n{context}\n\nQuestion: {query}"

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text



LANCEDB_PATH = os.getenv("LANCEDB_PATH", "./lancedb_data")
lance_db = lancedb.connect(LANCEDB_PATH)


def search_docs(query: str, top_k: int = 4) -> list[dict]:
    """Embed the query and search LanceDB for similar chunks."""
    table = lance_db.open_table("documents")
    query_vec = embed_text(query)
    results = table.search(query_vec).limit(top_k).to_list()
    return results




MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    mongo_client.admin.command("ping")  # test connection
    chat_db = mongo_client["gali"]
    history_col = chat_db["chat_history"]
    MONGO_AVAILABLE = True
    print("✅ MongoDB connected")
except Exception:
    MONGO_AVAILABLE = False
    print("⚠️  MongoDB not available – chat history disabled")


def save_message(session_id: str, role: str, content: str):
    """Save a single chat message to MongoDB (skips if Mongo is down)."""
    if not MONGO_AVAILABLE:
        return
    history_col.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
    })


def get_history(session_id: str, limit: int = 10) -> list[dict]:
    """Get the last N messages for a session."""
    if not MONGO_AVAILABLE:
        return []
    cursor = history_col.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1},
    ).sort("_id", -1).limit(limit)
    messages = list(cursor)
    messages.reverse()  # oldest first
    return messages

