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
