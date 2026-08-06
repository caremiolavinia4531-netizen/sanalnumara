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
    update_order_status,
    get_user_balance,
    add_user_balance,
    deduct_user_balance,
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
• Aynı mesajı manyak gibi bir çok kişiye göndermek ban sebebidir.

🫡 İyi kullanımlar.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    try:
        add_user(user_id, update.effective_user.username, update.effective_user.first_name)
    except Exception as e:
        logging.error(f"Kullanıcı ekleme hatası: {e}")
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

    elif text == "👤 Hesabım":
        balance = get_user_balance(user_id)
        await update.message.reply_text(
            f"👤 *Profil Bilgileriniz*\n\n"
            f"🆔 *Telegram ID:* `{user_id}`\n"
            f"💰 *Bakiyeniz:* `{balance} TL`",
            parse_mode="Markdown"
        )
        return

    elif text == "💳 Bakiye Yükle":
        shopier_link = "https://www.shopier.com/49138128"
        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Shopier ile Öde", url=shopier_link)],
            [InlineKeyboardButton("✅ Ödemeyi Yaptım", callback_data=f"bakiye_bildir_{user_id}")]
        ])
        await update.message.reply_text(
            "💳 *Bakiye Yükleme*\n\n"
            "1️⃣ Aşağıdaki **Shopier ile Öde** butonuna basarak ödemenizi yapın.\n"
            "2️⃣ Ödemeyi tamamladıktan sonra **Ödemeyi Yaptım** butonuna basın.\n"
            "3️⃣ Ödemeniz kontrol edilip bakiyeniz hesabınıza aktarılacaktır.",
            parse_mode="Markdown",
            reply_markup=inline_kb
        )
        return

    elif text == "📦 Siparişlerim":
        db_user_id = get_user_db_id(user_id)
        if not db_user_id:
            await update.message.reply_text("📦 Henüz siparişiniz bulunmuyor.")
            return
        
        orders = get_orders(db_user_id)
        if not orders:
            await update.message.reply_text("📦 Henüz siparişiniz bulunmuyor.")
        else:
            text_orders = "📦 *Geçmiş Siparişleriniz*\n\n"
            for order_id, prod_name, quantity, status, created_at in orders:
                text_orders += f"🆔 Sipariş No: #{order_id}\n📱 Ürün: {prod_name}\n Adet: {quantity}\n Durum: {status}\n Tarih: {created_at}\n-------------------\n"
            await update.message.reply_text(text_orders, parse_mode="Markdown")
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

    # --- ÜRÜN SORGULAMA ---
    if text in COUNTRIES:
        clean_country_name = text.split(" ", 1)[1].strip() if " " in text else text.strip()
        
        try:
            conn = connect()
            cursor = conn.cursor()
            clean_search = clean_country_name.lower().strip()
            cursor.execute(
                "SELECT price, stock, description FROM products WHERE LOWER(name) LIKE %s ORDER BY id DESC LIMIT 1", 
                (f"%{clean_search}%",)
            )
            product = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            logging.error(f"Ürün çekme hatası: {e}")
            product = None

        if product:
            price, stock, description = product[0], product[1], product[2]
            context.user_data["last_viewed_country_key"] = text
            context.user_data["last_viewed_country"] = COUNTRIES[text]
            context.user_data["last_viewed_price"] = price
            
            if stock > 0:
                await update.message.reply_text(
                    f"📱 {clean_country_name} WhatsApp\n\n💰 Fiyat: {price} TL\n📦 Stok: {stock}\n\n📝 Açıklama:\n{description}",
                    reply_markup=product_menu()
                )
            else:
                await update.message.reply_text(
                    f"📱 {clean_country_name} WhatsApp\n\n💰 Fiyat: {price} TL\n📦 Stok: 0\n\n❌ Bu ürün şu anda stokta bulunmuyor.",
                    reply_markup=country_menu()
                )
        else:
            context.user_data["last_viewed_country_key"] = text
            context.user_data["last_viewed_country"] = COUNTRIES[text]
            context.user_data["last_viewed_price"] = 250
            await update.message.reply_text(
                f"📱 {clean_country_name} WhatsApp\n\n💰 Fiyat: 250 TL\n📦 Stok: 0\n\n❌ Bu ürün şu anda stokta bulunmuyor.",
                reply_markup=country_menu()
            )
        return

    # --- SATIN ALMA İŞLEMİ ---
    if text == "🛒 Satın Al":
        country_key = context.user_data.get("last_viewed_country_key", "🇮🇩 Endonezya")
        price = float(context.user_data.get("last_viewed_price", 250))
        clean_country_name = country_key.split(" ", 1)[1] if " " in country_key else country_key
        
        user_bal = get_user_balance(user_id)

        if user_bal < price:
            await update.message.reply_text(
                f"❌ *Yetersiz Bakiye!*\n\n"
                f"📱 Ürün Fiyatı: *{price} TL*\n"
                f"💰 Bakiyeniz: *{user_bal} TL*\n\n"
                f"Lütfen ana menüden **💳 Bakiye Yükle** butonuna basarak bakiye yükleyiniz.",
                parse_mode="Markdown"
            )
            return

        if deduct_user_balance(user_id, price):
            db_user_id = get_user_db_id(user_id)
            conn = connect()
            cursor = conn.cursor()
            clean_search = clean_country_name.lower().strip()
            cursor.execute("SELECT id FROM products WHERE LOWER(name) LIKE %s ORDER BY id DESC LIMIT 1", (f"%{clean_search}%",))
            prod = cursor.fetchone()
            
            order_id = "Bilinmiyor"
            if prod and db_user_id:
                product_id = prod[0]
                cursor.execute(
                    "INSERT INTO orders (user_id, product_id, quantity, status, created_at) VALUES (%s, %s, 1, 'Beklemede', NOW()) RETURNING id", 
                    (db_user_id, product_id)
                )
                order_id = cursor.fetchone()[0]
                conn.commit()
                update_stock(product_id, 1)
            cursor.close()
            conn.close()

            new_balance = get_user_balance(user_id)

            await update.message.reply_text(
                f"✅ *Siparişiniz Başarıyla Oluşturuldu!*\n\n"
                f"🆔 *Sipariş No:* #{order_id}\n"
                f"📱 *Ürün:* {clean_country_name} WhatsApp\n"
                f"💰 *Çekilen Tutar:* {price} TL\n"
                f"💵 *Kalan Bakiyeniz:* {new_balance} TL\n\n"
                f"⏳ Numaranız teslim edilmek üzere admine iletildi.",
                parse_mode="Markdown"
            )

            admin_kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Teslim Edildi", callback_data=f"order_approve_{order_id}"),
                    InlineKeyboardButton("❌ İptal Et & İade Yap", callback_data=f"order_refund_{order_id}_{user_id}_{price}")
                ]
            ])

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 *YENİ BAKİYELİ SİPARİŞ!*\n\n"
                     f"🆔 *Sipariş No:* #{order_id}\n"
                     f"👤 *Müşteri:* {update.effective_user.first_name} (@{update.effective_user.username})\n"
                     f"🆔 *ID:* `{user_id}`\n"
                     f"📦 *Ülke:* {clean_country_name}\n"
                     f"💰 *Ödenen Tutar:* {price} TL (Bakiyeden Düşüldü)\n\n"
                     f"Numarayı müşteriye iletebilirsin.",
                parse_mode="Markdown",
                reply_markup=admin_kb
            )
        return

    # --- ADMİN İŞLEMLERİ ---
    if is_admin:
        if admin_step == "stok_id_gir":
            try:
                context.user_data["stock_target_id"] = int(text)
                context.user_data["admin_step"] = "stok_adet_gir"
                await update.message.reply_text("📝 Yeni stok adetini girin:")
            except ValueError:
                await update.message.reply_text("❌ Geçersiz ID! Lütfen sayısal bir ID girin.")
            return

        elif admin_step == "stok_adet_gir":
            try:
                new_stock = int(text)
                product_id = context.user_data.get("stock_target_id")
                
                if product_id is None:
                    await update.message.reply_text("❌ Hedef ürün bulunamadı, işlemi baştan başlatın.", reply_markup=admin_menu())
                    context.user_data.clear()
                    return

                conn = connect()
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET stock = %s WHERE id = %s;", (new_stock, int(product_id)))
                conn.commit()
                cursor.close()
                conn.close()

                context.user_data.clear()
                await update.message.reply_text("✅ Stok başarıyla güncellendi!", reply_markup=admin_menu())
            except Exception as e:
                logging.error(f"Stok güncelleme hatası: {e}")
                await update.message.reply_text(f"❌ Hata oluştu: {e}", reply_markup=admin_menu())
                context.user_data.clear()
            return

        elif admin_step == "urun_adi":
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
                cursor.execute(
                    "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)", 
                    (context.user_data["urun_adi"], context.user_data["urun_aciklama"], context.user_data["urun_fiyat"], stok)
                )
                conn.commit()
                cursor.close()
                conn.close()
                context.user_data.clear()
                await update.message.reply_text("✅ Ürün başarıyla eklendi.", reply_markup=admin_menu())
            except Exception as e:
                logging.error(f"Ürün ekleme hatası: {e}")
                await update.message.reply_text("❌ Ürün eklenirken bir hata oluştu.", reply_markup=admin_menu())
                context.user_data.clear()
            return

        elif admin_step == "urun_sil":
            try:
                pid = int(text)
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
                conn.commit()
                cursor.close()
                conn.close()
                context.user_data.clear()
                await update.message.reply_text("✅ Ürün silindi.", reply_markup=admin_menu())
            except Exception as e:
                logging.error(f"Ürün silme hatası: {e}")
                await update.message.reply_text("❌ Ürün silinirken hata oluştu.")
            return

        elif admin_step == "duyuru":
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("SELECT telegram_id FROM users")
                users = cursor.fetchall()
                cursor.close()
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

        if text == "➕ Ürün Ekle":
            context.user_data["admin_step"] = "urun_adi"
            await update.message.reply_text("📝 Eklenecek ürünün adını gönderiniz.")
            return

        elif text == "📦 Stok Güncelle":
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, stock FROM products ORDER BY id ASC")
                products = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                logging.error(f"Stok listeleme hatası: {e}")
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
                cursor.execute("SELECT id, name FROM products ORDER BY id ASC")
                products = cursor.fetchall()
                cursor.close()
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

    await update.message.reply_text("❓ Lütfen menüden bir seçenek seçiniz.", reply_markup=main_menu(is_admin=is_admin))

async def inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or "Yok"
    first_name = query.from_user.first_name

    if data.startswith("bakiye_bildir_"):
        target_user_id = data.split("_")[2]
        await query.answer()
        await query.message.reply_text("⏳ Bakiye yükleme talebiniz admine iletildi.")

        admin_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ 50 TL", callback_data=f"addbal_{target_user_id}_50"),
                InlineKeyboardButton("➕ 100 TL", callback_data=f"addbal_{target_user_id}_100"),
                InlineKeyboardButton("➕ 250 TL", callback_data=f"addbal_{target_user_id}_250"),
            ]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💳 *YENİ BAKİYE YÜKLEME TALEBİ!*\n\n"
                 f"👤 *Müşteri:* {first_name} (@{username})\n"
                 f"🆔 *ID:* `{target_user_id}`\n\n"
                 f"Shopier'i kontrol edip bakiyesini onaylayabilirsiniz:",
            parse_mode="Markdown",
            reply_markup=admin_kb
        )

    elif data.startswith("addbal_"):
        if user_id != ADMIN_ID:
            await query.answer("Yetkiniz yok!", show_alert=True)
            return
        
        _, target_user_id, amount = data.split("_")
        amount = float(amount)
        
        add_user_balance(int(target_user_id), amount)
        current_bal = get_user_balance(int(target_user_id))
        
        await query.answer(f"{amount} TL Bakiye Eklendi!")
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"🎉 *Bakiyeniz Yüklendi!*\n\nHesabınıza *{amount} TL* bakiye eklenmiştir.\n💵 Güncel Bakiyeniz: *{current_bal} TL*",
                parse_mode="Markdown"
            )
        except Exception:
            pass

        await query.edit_message_text(text=f"{query.message.text}\n\n✅ *{amount} TL Bakiye Eklendi.*")

    elif data.startswith("order_approve_"):
        if user_id != ADMIN_ID:
            await query.answer("Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        await query.answer("Sipariş teslim edildi olarak işaretlendi!")
        order_id = data.split("_")[2]
        update_order_status(order_id, "Tamamlandı")
        
        new_text = f"{query.message.text}\n\n✅ *Durum:* Sipariş Tamamlandı."
        await query.edit_message_text(text=new_text, parse_mode="Markdown")

elif data.startswith("order_refund_"):
        if user_id != ADMIN_ID:
            await query.answer("Yetkiniz yok!", show_alert=True)
            return
        
        _, order_id, target_user_id, price = data.split("_")
        price = float(price)
        
        add_user_balance(int(target_user_id), price)
        update_order_status(order_id, "İptal/İade Edildi")
        
        await query.answer("Sipariş iptal edildi ve bakiye iade edildi!")
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"❌ *Siparişiniz İptal Edildi*\n\n#{order_id} numaralı siparişiniz iptal edildi ve *{price} TL* tutarındaki bakiye hesabınıza iade edildi.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

        await query.edit_message_text(text=f"{query.message.text}\n\n❌ *İptal Edildi ve {price} TL İade Yapıldı.*")
