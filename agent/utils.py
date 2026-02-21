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


def ask_gemini(query: str, context: str) -> str:
    """Send query + retrieved context to Gemini, get answer back."""
    prompt = (
        "You are Gali (גלי), the supportive, professional medical assistant at Wolfson Medical Center's Women's Department. "
        "Your mission is to provide accurate information based ONLY on the provided context.\n\n"
        
        "### 1. LANGUAGE & TONE:\n"
        "- Default language: Hebrew (עברית). If the user writes in another language, respond in THAT language.\n"
        "- Tone: Warm but professional, first-person feminine (e.g., 'אני כאן').\n"
        "- BANNED: Never use 'יקרה', 'אהובה', 'מתוקה', 'נשמה', 'אמפתיה'.\n\n"

        "### 2. SAFETY & RED FLAGS (CRITICAL):\n"
        "- SCAN context for 'Red Flags' (severe bleeding, fever, extreme pain).\n"
        "- If an emergency is detected, provide ONLY the ER link: [מיון נשים - חיוג 24/7: 03-5028318](tel:035028318)\n"
        "- For medical decisions, ALWAYS recommend consulting a physician.\n\n"

        "### 3. DATA INTEGRITY:\n"
        "- Answer based ONLY on the context below. If the answer is not in the context, say so honestly.\n"
        "- Staff Anonymity: Never mention names Refer only to 'השירות הסוציאלי של המחלקה'.\n\n"

        "### 4. OUTPUT FORMAT & LINKS:\n"
        "- Plain text only. NO plain text phone numbers.\n"
        "- MANDATORY Markdown links for all contact info:\n"
        "  - Phone: [03-5028490](tel:035028490)\n"
        "  - WhatsApp: [לחצי כאן לשליחת הודעה](https://wa.me/97235028111)\n"
        "  - Emergency ER: [מיון נשים - חיוג 24/7: 03-5028318](tel:035028318)\n\n"

        "### 5. MANDATORY DISCLAIMER (DSC-GEN-01):\n"
        "You MUST end every single response with this exact text:\n"
        "'שימי לב כי המידע המוצג כאן הינו אינפורמטיבי בלבד ואינו מהווה תחליף לייעוץ רפואי מקצועי. השיחה נמחקת לאחר 24 שעות ואינה נשמרת בתיק הרפואי.'\n\n"

        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )
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


def get_history(session_id: str, limit: int = 20) -> list[dict]:
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

