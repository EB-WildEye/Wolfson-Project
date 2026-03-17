"""Extract chat history from MongoDB — grouped by session, ordered by time.

Writes output to logs/chat_history_YYYY-MM-DD.txt

Usage:
    uv run python scripts/chat_history.py
"""

from pathlib import Path
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
col = client["gali"]["chat_history"]

# Output file
out_dir = Path("logs")
out_dir.mkdir(exist_ok=True)
out_path = out_dir / f"chat_history_{datetime.now().strftime('%Y-%m-%d')}.txt"
out = open(out_path, "w", encoding="utf-8")

# Get all sessions ordered by their first message time
pipeline = [
    {"$group": {
        "_id": "$session_id",
        "first_msg": {"$min": "$_id"},
        "count": {"$sum": 1},
    }},
    {"$sort": {"first_msg": 1}},
]

sessions = list(col.aggregate(pipeline))

if not sessions:
    out.write("No chat history found.\n")
    out.close()
    print(f"Report saved: {out_path}")
    exit()

def w(text=""):
    out.write(text + "\n")

w()
w("=" * 72)
w(f"  GALI — Chat History Report  |  {len(sessions)} session(s)")
w("=" * 72)

for i, session in enumerate(sessions, 1):
    sid = session["_id"]
    count = session["count"]

    messages = list(
        col.find({"session_id": sid}, {"_id": 0})
        .sort("_id", 1)
    )

    first_time = messages[0].get("created_at", "N/A") if messages else "N/A"
    if isinstance(first_time, datetime):
        first_time = first_time.strftime("%Y-%m-%d %H:%M:%S")

    w()
    w(f"  SESSION #{i}  |  Messages: {count}  |  Started: {first_time}")
    w(f"  ID: {sid}")
    w("-" * 72)

    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        label = "PATIENT  " if role == "USER" else "ASSISTANT"

        lines = content.split("\n")
        w(f"  [{label}]  {lines[0]}")
        for line in lines[1:]:
            w(f"              {line}")
        w()

    w("-" * 72)

total = sum(s["count"] for s in sessions)
w()
w(f"  Total: {total} messages across {len(sessions)} session(s)")
w("=" * 72)

out.close()
print(f"Report saved: {out_path}")

