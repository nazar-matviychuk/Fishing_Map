from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os, requests

# Стан користувачів: photo, description, location
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_states[chat_id] = {"step": "photo"}
    await update.message.reply_text("Привіт! Надішли фото з риболовлі 📸")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_states.get(chat_id, {})
    
    if state.get("step") != "photo":
        await update.message.reply_text("Я зараз чекаю інший етап. Якщо щось не так — напиши /start.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    os.makedirs("temp", exist_ok=True)
    path = f"temp/{chat_id}.jpg"
    await file.download_to_drive(path)

    user_states[chat_id] = {
        "step": "description",
        "photo_path": path
    }

    await update.message.reply_text("Фото збережено ✅. Тепер надішли короткий опис 🎣.")

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_states.get(chat_id, {})

    if state.get("step") != "description":
        await update.message.reply_text("Зараз я чекаю інший етап. Напиши /start, щоб почати заново.")
        return

    user_states[chat_id]["description"] = update.message.text
    user_states[chat_id]["step"] = "location"

    await update.message.reply_text(
        "Дякую! ✅ Тепер надішли геолокацію 📍 цього місця риболовлі.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Надіслати геолокацію", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = user_states.get(chat_id, {})

    if state.get("step") != "location":
        await update.message.reply_text("Я зараз чекаю інший етап. Напиши /start, щоб почати заново.")
        return

    lat = update.message.location.latitude
    lon = update.message.location.longitude
    description = state.get("description")
    photo_path = state.get("photo_path")

    # Надіслати на сервер
    with open(photo_path, "rb") as img:
        response = requests.post("http://localhost:8000/add_report",
                                 files={"image": img},
                                 data={
                                     "lat": lat,
                                     "lon": lon,
                                     "description": description
                                 })

    # Очистити тимчасові дані
    os.remove(photo_path)
    user_states.pop(chat_id, None)

    if response.status_code == 200:
        await update.message.reply_text("✅ Звіт додано! Дякую за участь.")
    else:
        await update.message.reply_text("❌ Сталася помилка при відправці звіту.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не розумію цю команду. Почни з /start.")

def main():
    app = Application.builder().token("8391256868:AAGzJD1VMqNDZfvSnTavBdHSQko13Tl1ENE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_description))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("🤖 Бот запущено")
    app.run_polling()

if __name__ == "__main__":
    main()
