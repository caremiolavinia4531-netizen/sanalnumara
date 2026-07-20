import asyncio
import sys
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import (
    connect,
    add_user,
    get_product,
    add_order,
    get_orders,
    update_stock,
    get_user_db_id,
)
from messages import (
    START_MESSAGE,
    HELP_MESSAGE,
    ADMIN_MESSAGE,
)
from keyboards import (
    main_menu,
    country_menu,
    product_menu,
    admin_menu,
)

ADMIN_ID = 6851426041

COUNTRIES = {
    "🇮🇩 Endonezya": "indonesia",
    "🇮🇳 Hindistan": "india",
    "🇲🇾 Malezya": "malaysia",
    "🇧🇷 Brezilya": "brazil",
    "🇻🇳 Vietnam": "vietnam",
    "🇵🇭 Filipinler": "philippines",
    "🇹🇭 Tayland": "thailand",
    "🇲🇽 Meksika": "mexico",
    "🇿🇦 Güney Afrika": "southafrica",
    "🇹🇷 Türkiye": "turkey",
}

RULES = """
📌 Önemli Kullanım Kuralları

1️⃣ Endonezya (+62) → Endonezya IP (Jakarta)
2️⃣ Hindistan (+91) → Hindistan IP (Mumbai / Delhi)
3️⃣ Malezya (+60) → Malezya IP (Kuala Lumpur)
4️⃣ Brezilya (+55) → Brezilya IP (São Paulo)
5️⃣ Vietnam (+84) → Vietnam IP (Hanoi / Ho Chi Minh)
6️⃣ Filipinler (+63) → Filipinler IP (Manila)
7️⃣ Tayland (+66) → Tayland IP (Bangkok)
8️⃣ Meksika (+52) → Meksika IP (Mexico City)
9️⃣ Güney Afrika (+27) → Johannesburg
🔟 Türkiye (+90) → İstanbul

• Hesabı açtıktan sonra 30-60 dakika mesaj göndermeyin.
• Profil fotoğrafı ve isim ekleyin.
• İlk gün çok fazla mesaj göndermeyin.
• Aynı mesajı manyak gibi birçok kişiye göndermek ban sebebidir.

🫡 İyi kullanımlar.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    try:
        add_user(user_id, update.effective_user.username, update.effective_user.first_name)
    except Exception:
        pass
    await update.message.reply_text(START_MESSAGE, reply_markup=main_menu(is_admin=is_admin))

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    admin_step = context.user_data.get("admin_step")

    if text == "🏠 Ana Menü":
        context.user_data.clear()
        await update.message.reply_text("🏠 Ana menüye döndünüz.", reply_markup=main_menu(is_admin=is_admin))
        return

    if text in ["⬅️ Geri", "🔙 Ülkeler"]:
        await update.message.reply_text("🌍 Satın almak istediğiniz ülkeyi seçiniz.", reply_markup=country_menu())
        return

    if text == "🛒 Ürünler":
        await update.message.reply_text("🌍 Satın almak istediğiniz ülkeyi seçiniz.", reply_markup=country_menu())
        return

    elif text == "📦 Siparişlerim":
        await update.message.reply_text("📦 Henüz siparişiniz bulunmuyor.")
        return

    elif text == "📜 Kullanım Kuralları":
        await update.message.reply_text(RULES)
        return

    elif text == "💬 Destek":
        await update.message.reply_text("💬 Destek: @kullanici_000")
        return

    elif text == "ℹ️ Hakkımızda":
        await update.message.reply_text(HELP_MESSAGE)
        return

    elif text == "👑 Admin Paneli":
        if is_admin:
            await update.message.reply_text(ADMIN_MESSAGE, reply_markup=admin_menu())
        else:
            await update.message.reply_text("❌ Bu menüye erişim yetkiniz yok.")
        return

    if text in COUNTRIES:
        display_name = text.split(" ")[1]
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("SELECT price, stock, description FROM products WHERE name=?", (display_name,))
            product = cursor.fetchone()
            conn.close()
        except Exception:
            product = None

        if product:
            price, stock, description = product[0], product[1], product[2]
            context.user_data["last_viewed_country_key"] = text
            context.user_data["last_viewed_country"] = COUNTRIES[text]
            context.user_data["last_viewed_price"] = price
            await update.message.reply_text(
                f"📱 {display_name} WhatsApp\n\n💰 Fiyat: {price} TL\n📦 Stok: {stock}\n\n📝 Açıklama:\n{description}",
                reply_markup=product_menu()
            )
        else:
            context.user_data["last_viewed_country_key"] = text
            context.user_data["last_viewed_country"] = COUNTRIES[text]
            context.user_data["last_viewed_price"] = "250"
            await update.message.reply_text(
                f"📱 {display_name} WhatsApp\n\n💰 Fiyat: 250 TL\n📦 Stok: 0\n\n❌ Bu ürün şu anda stokta bulunmuyor.",
                reply_markup=country_menu()
            )
        return

    elif text == "🛒 Satın Al":
        country_key = context.user_data.get("last_viewed_country_key", "🇮🇩 Endonezya")
        country_code = COUNTRIES[country_key]
        price = context.user_data.get("last_viewed_price", "250")
        
        # --- SHOPIER DOĞRUDAN KARTLA ÖDEME LİNKLERİ ---
        shopier_linkleri = {
            "indonesia": "https://www.shopier.com/s/payment/Sanalnnumara/595789260",
            # İleride ekleyeceğin diğer ülkelerin linklerini buraya ekleyebilirsin
        }
        
        shopier_link = shopier_linkleri.get(country_code, "https://www.shopier.com/s/payment/Sanalnnumara/595789260")

        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Kredi/Banka Kartı İle Öde", url=shopier_link)],
            [InlineKeyboardButton("✅ Ödemeyi Tamamladım", callback_data=f"pay_confirm_{country_code}_{price}")]
        ])
        
        await update.message.reply_text(
            f"🛒 *Siparişiniz Oluşturuldu ({country_key.split(' ')[1]} WhatsApp)*\n\n"
            f"💰 *Tutar:* {price} TL\n\n"
            f"⚠️ Güvenli ödeme sayfasına geçmek için lütfen aşağıdaki **Kredi/Banka Kartı İle Öde** butonuna tıklayın.\n\n"
            f"Kartla ödemenizi tamamladıktan sonra bota geri dönüp **Ödemeyi Tamamladım** butonuna basınız. "
            f"Bildiriminiz anlık olarak admine iletilecektir.",
            parse_mode="Markdown",
            reply_markup=inline_kb
        )
        return

    if text in ["➕ Ürün Ekle", "➖ Ürün Sil", "📢 Duyuru Gönder", "📦 Stok Güncelle"] or admin_step:
        if not is_admin:
            await update.message.reply_text("❌ Yetkisiz işlem.")
            return

        if text == "➕ Ürün Ekle":
            context.user_data["admin_step"] = "urun_adi"
            await update.message.reply_text("📝 Eklenecek ürünün adını gönderiniz.")
            return

        elif text == "📦 Stok Güncelle":
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, stock FROM products")
                products = cursor.fetchall()
                conn.close()
            except Exception:
                products = []
            if not products:
                await update.message.reply_text("❌ Ürün bulunmuyor.")
            else:
                text_list = "📦 *Stok Güncelleme*\n\n"
                for pid, name, stock in products:
                    text_list += f"🆔 ID: {pid} - {name} ({stock})\n"
                context.user_data["admin_step"] = "stok_id_gir"
                await update.message.reply_text(text_list, parse_mode="Markdown")
            return

        elif text == "➖ Ürün Sil":
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM products")
                products = cursor.fetchall()
                conn.close()
            except Exception:
                products = []
            if not products:
                await update.message.reply_text("❌ Ürün bulunmuyor.")
            else:
                text_list = "🗑 Silinecek Ürünler\n\n"
                for pid, name in products:
                    text_list += f"{pid} - {name}\n"
                context.user_data["admin_step"] = "urun_sil"
                await update.message.reply_text(text_list)
            return

        elif text == "📢 Duyuru Gönder":
            context.user_data["admin_step"] = "duyuru"
            await update.message.reply_text("📢 Duyuru metnini yazınız.")
            return

        if admin_step == "stok_id_gir":
            try:
                context.user_data["stock_target_id"] = int(text)
                context.user_data["admin_step"] = "stok_adet_gir"
                await update.message.reply_text("📝 Yeni stok adetini girin:")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz ID.")
            return

        elif admin_step == "stok_adet_gir":
            try:
                new_stock = int(text)
                product_id = context.user_data.get("stock_target_id")
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
                conn.commit()
                conn.close()
                context.user_data.clear()
                await update.message.reply_text("✅ Stok güncellendi.", reply_markup=admin_menu())
            except Exception:
                await update.message.reply_text("❌ Hata oluştu.", reply_markup=admin_menu())
                context.user_data.clear()
            return

        if admin_step == "urun_adi":
            context.user_data["urun_adi"] = text
            context.user_data["admin_step"] = "urun_aciklama"
            await update.message.reply_text("📝 Açıklama gönderiniz.")
            return

        elif admin_step == "urun_aciklama":
            context.user_data["urun_aciklama"] = text
            context.user_data["admin_step"] = "urun_fiyat"
            await update.message.reply_text("💰 Fiyat giriniz.")
            return

        elif admin_step == "urun_fiyat":
            try:
                context.user_data["urun_fiyat"] = float(text)
                context.user_data["admin_step"] = "urun_stok"
                await update.message.reply_text("📦 Stok giriniz.")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz fiyat.")
            return

        elif admin_step == "urun_stok":
            try:
                stok = int(text)
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", (context.user_data["urun_adi"], context.user_data["urun_aciklama"], context.user_data["urun_fiyat"], stok))
                conn.commit()
                conn.close()
                context.user_data.clear()
                await update.message.reply_text("✅ Ürün eklendi.", reply_markup=admin_menu())
            except Exception:
                await update.message.reply_text("❌ Hata oluştu.", reply_markup=admin_menu())
                context.user_data.clear()
            return

        elif admin_step == "urun_sil":
            try:
                pid = int(text)
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=?", (pid,))
                conn.commit()
                conn.close()
                context.user_data.clear()
                await update.message.reply_text("✅ Ürün silindi.", reply_markup=admin_menu())
            except Exception:
                await update.message.reply_text("❌ Hata.")
            return

        elif admin_step == "duyuru":
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("SELECT telegram_id FROM users")
                users = cursor.fetchall()
                conn.close()
            except Exception:
                users = []
            sent = 0
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u[0], text=f"📢 DUYURU\n\n{text}")
                    sent += 1
                except Exception:
                    pass
            context.user_data.clear()
            await update.message.reply_text(f"✅ Duyuru {sent} kişiye iletildi.", reply_markup=admin_menu())
            return

    await update.message.reply_text("❓ Lütfen menüden bir seçenek seçiniz.", reply_markup=main_menu(is_admin=is_admin))

async def inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or "Yok"
    first_name = query.from_user.first_name

    if data.startswith("pay_confirm_"):
        parts = data.split("_")
        country_code = parts[2]
        price = parts[3]

        await query.message.reply_text("⏳ Ödeme bildiriminiz admine iletildi. Kontrol edildikten sonra manuel onaylanacaktır.")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 *YENİ BİRİ SATIN ALMAYA BASTI!*\n\n👤 *Müşteri:* {first_name} (@{username})\n🆔 *ID:* `{user_id}`\n📦 *Ülke:* {country_code}\n💰 *Tutar:* {price} TL\n\nManuel teslimat yapabilirsin.",
            parse_mode="Markdown"
        )
