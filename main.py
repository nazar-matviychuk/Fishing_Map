# backend/main.py
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3, os, uuid

app = FastAPI()
os.makedirs("images", exist_ok=True)

# створення БД
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        lat REAL,
        lon REAL,
        description TEXT,
        image_path TEXT,
        likes INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        report_id TEXT,
        text TEXT
    )
''')
conn.commit()

@app.post("/add_report")
async def add_report(lat: float = Form(), lon: float = Form(),
                     description: str = Form(), image: UploadFile = Form()):
    image_id = str(uuid.uuid4()) + ".jpg"
    image_path = os.path.join("images", image_id)
    with open(image_path, "wb") as f:
        f.write(await image.read())
    report_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?)",
                   (report_id, lat, lon, description, image_id, 0))
    conn.commit()
    return {"status": "ok"}

@app.get("/reports")
def get_reports():
    cursor.execute("SELECT id, lat, lon, description, image_path, likes FROM reports")
    return cursor.fetchall()

@app.get("/image/{filename}")
def get_image(filename: str):
    return FileResponse(f"images/{filename}")

@app.post("/like/{report_id}")
def like(report_id: str):
    cursor.execute("UPDATE reports SET likes = likes + 1 WHERE id = ?", (report_id,))
    conn.commit()
    return {"status": "liked"}

@app.post("/comment/{report_id}")
def comment(report_id: str, text: str = Form()):
    comment_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO comments VALUES (?, ?, ?)", (comment_id, report_id, text))
    conn.commit()
    return {"status": "comment_added"}

@app.get("/comments/{report_id}")
def get_comments(report_id: str):
    cursor.execute("SELECT text FROM comments WHERE report_id = ?", (report_id,))
    return [row[0] for row in cursor.fetchall()]
