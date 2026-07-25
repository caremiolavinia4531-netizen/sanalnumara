import os
import threading
from flask import Flask
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TOKEN
from handlers import start, buttons, inline_buttons
from database import create_tables

# --- Render'ın Port Beklentisini Karşılayan Flask Sunucusu ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# Flask'ı arka planda ayrı bir thread'de başlatıyoruz
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
# -----------------------------------------------------------


def main():
    # Veritabanını oluştur
    create_tables()

    # Botu başlat
    app = Application.builder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))

    # Satır içi (Inline) Buton Tıklamaları
    app.add_handler(CallbackQueryHandler(inline_buttons))

    # Butonlar ve mesajlar
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, buttons)
    )

    print("✅ Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()