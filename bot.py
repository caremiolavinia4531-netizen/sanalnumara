import os
import threading
import logging
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

# Flask loglarını sessize al (log kirliliğini engeller)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app_flask.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# daemon=True ekleyerek ana uygulama durduğunda flask thread'inin de otomatik kapanmasını sağlıyoruz
flask_thread = threading.Thread(target=run_flask, daemon=True)
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
    
    # drop_pending_updates=True sayesinde Render yeniden başlarken 
    # askıda kalan eski bağlantıları ve çakışmaları otomatik temizler!
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
