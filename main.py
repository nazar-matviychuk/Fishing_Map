from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3, os, uuid
import asyncio

from bot import start_bot  # 🚀 функція запуску Telegram-бота

app = FastAPI()

# ▶️ Запускаємо бота при старті
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())

# 🗂️ Папки
os.makedirs("images", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 🧠 База даних
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

# 🌐 Головна сторінка (HTML)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 📤 Додати звіт
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

# 📥 Отримати звіти
@app.get("/reports")
def get_reports():
    cursor.execute("SELECT id, lat, lon, description, image_path, likes FROM reports")
    return cursor.fetchall()

# 🖼️ Показати зображення
@app.get("/image/{filename}")
def get_image(filename: str):
    return FileResponse(f"images/{filename}")

# 👍 Лайк
@app.post("/like/{report_id}")
def like(report_id: str):
    cursor.execute("UPDATE reports SET likes = likes + 1 WHERE id = ?", (report_id,))
    conn.commit()
    return {"status": "liked"}

# 💬 Додати коментар
@app.post("/comment/{report_id}")
def comment(report_id: str, text: str = Form()):
    comment_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO comments VALUES (?, ?, ?)", (comment_id, report_id, text))
    conn.commit()
    return {"status": "comment_added"}

# 📄 Отримати коментарі
@app.get("/comments/{report_id}")
def get_comments(report_id: str):
    cursor.execute("SELECT text FROM comments WHERE report_id = ?", (report_id,))
    return [row[0] for row in cursor.fetchall()]
