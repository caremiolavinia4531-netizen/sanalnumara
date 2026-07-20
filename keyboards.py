from telegram import ReplyKeyboardMarkup


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        ["🛒 Ürünler", "📦 Siparişlerim"],
        ["📜 Kullanım Kuralları", "💬 Destek"],
        ["ℹ️ Hakkımızda"]
    ]
    if is_admin:
        keyboard.append(["👑 Admin Paneli"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def country_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🇮🇩 Endonezya", "🇮🇳 Hindistan"],
        ["🇲🇾 Malezya", "🇧🇷 Brezilya"],
        ["🇻🇳 Vietnam", "🇵🇭 Filipinler"],
        ["🇹🇭 Tayland", "🇲🇽 Meksika"],
        ["🇿🇦 Güney Afrika", "🇹🇷 Türkiye"],
        ["🏠 Ana Menü"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def product_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🛒 Satın Al"],
        ["🔙 Ülkeler", "🏠 Ana Menü"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["➕ Ürün Ekle", "➖ Ürün Sil"],
        ["📢 Duyuru Gönder"],
        ["🏠 Ana Menü"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
