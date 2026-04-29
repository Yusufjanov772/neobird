import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import sqlite3
import time
import os

# O'zgaruvchilarni kiriting
TOKEN = "8745338371:AAGmXeoxqdfx9aPGFU7LvWRwvCfg07gBvX0"
ADMIN_ID = 7675742198

bot = telebot.TeleBot(TOKEN)

# Global o'zgaruvchi: Texnik ishlar rejimi
MAINTENANCE_MODE = False

# ==========================================
# MA'LUMOTLAR BAZASINI YARATISH (SQLite)
# ==========================================
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        best_score INTEGER
    )
''')
conn.commit()

# ==========================================
# START BUYRUG'I
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global MAINTENANCE_MODE
    
    # Agar texnik ishlar ketyotgan bo'lsa
    if MAINTENANCE_MODE and message.from_user.id != int(ADMIN_ID):
        bot.send_message(message.chat.id, "🛠 <b>Texnik ishlar olib borilmoqda!</b>\n\nTez orada o'yin yana ishga tushadi. Iltimos, birozdan so'ng urinib ko'ring.", parse_mode="HTML")
        return

    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    try:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, first_name, username) VALUES (?, ?, ?)', 
                       (user_id, first_name, username))
        conn.commit()
    except Exception as e:
        pass

    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo("https://neobird.netlify.app/") 
    btn = InlineKeyboardButton(text="🎮 O'yinni Boshlash", web_app=web_app)
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        "👋 <b>NeoBird</b> o'yiniga xush kelibsiz!\n\nPastdagi tugmani bosing va o'z rekordingizni o'rnating. 🚀", 
        parse_mode="HTML", 
        reply_markup=markup
    )

# ==========================================
# SUPER ADMIN PANEL (/admin)
# ==========================================
@bot.message_handler(commands=['admin'])
def super_admin_panel(message):
    if message.from_user.id != int(ADMIN_ID):
        bot.reply_to(message, "🚫 Sizda admin panelga kirish huquqi yo'q.")
        return
    show_admin_menu(message.chat.id)

def show_admin_menu(chat_id, message_id=None):
    global MAINTENANCE_MODE
    
    markup = InlineKeyboardMarkup(row_width=2)
    btn_stats = InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    btn_top = InlineKeyboardButton("🏆 Top O'yinchilar", callback_data="admin_top")
    btn_broadcast = InlineKeyboardButton("📢 Xabar tarqatish", callback_data="admin_broadcast")
    btn_export = InlineKeyboardButton("📂 Bazani yuklab olish", callback_data="admin_export")
    
    # Texnik rejim holati
    m_text = "🟢 O'yinni yopish (Texnik rejim)" if not MAINTENANCE_MODE else "🔴 O'yinni ochish (Texnik rejim)"
    btn_maintenance = InlineKeyboardButton(m_text, callback_data="admin_maintenance")
    
    btn_wipe = InlineKeyboardButton("🧹 Rekordlarni tozalash", callback_data="admin_wipe")
    btn_close = InlineKeyboardButton("❌ Yopish", callback_data="admin_close")
    
    markup.add(btn_stats, btn_top)
    markup.add(btn_broadcast, btn_export)
    markup.add(btn_maintenance)
    markup.add(btn_wipe)
    markup.add(btn_close)

    text = "👑 <b>SUPER ADMIN PANEL</b>\n\nAsosiy boshqaruv bo'limi. Kerakli harakatni tanlang:"
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# ==========================================
# INLINE TUGMALAR UCHUN HANDLER
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callbacks(call):
    global MAINTENANCE_MODE
    
    if call.from_user.id != int(ADMIN_ID):
        bot.answer_callback_query(call.id, "Bu tugma faqat adminlar uchun!", show_alert=True)
        return

    action = call.data.split('_')[1]

    # --- ORQAGA QAYTISH ---
    if action == "back":
        show_admin_menu(call.message.chat.id, call.message.message_id)

    # --- STATISTIKA ---
    elif action == "stats":
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM players')
        total_players = cursor.fetchone()[0]
        
        text = f"📊 <b>BOT STATISTIKASI:</b>\n\n👥 Umumiy obunachilar: <b>{total_users} ta</b>\n🎮 Rekordi bor o'yinchilar: <b>{total_players} ta</b>\n⚙️ Texnik rejim: <b>{'Yoniq' if MAINTENANCE_MODE else 'O\'chiq'}</b>"
        
        back_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=back_btn)
        
    # --- TOP O'YINCHILAR ---
    elif action == "top":
        cursor.execute('SELECT first_name, username, best_score FROM players ORDER BY best_score DESC LIMIT 15')
        top_players = cursor.fetchall()
        
        if not top_players:
            text = "📭 Hozircha reyting bo'sh."
        else:
            text = "🏆 <b>TOP 15 O'YINCHILAR:</b>\n\n"
            for idx, player in enumerate(top_players, start=1):
                name, uname, score = player
                tag = f"(@{uname})" if uname else ""
                text += f"<b>{idx}.</b> {name} {tag} — <b>{score} ball</b>\n"
                
        back_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=back_btn)

    # --- BAZANI YUKLAB OLISH ---
    elif action == "export":
        bot.answer_callback_query(call.id, "Baza yuklanmoqda...")
        if os.path.exists('bot_data.db'):
            with open('bot_data.db', 'rb') as doc:
                bot.send_document(call.message.chat.id, doc, caption="📂 Barcha ma'lumotlar bazasi (SQLite).")
        else:
            bot.send_message(call.message.chat.id, "Baza fayli topilmadi.")

    # --- TEXNIK REJIMNI O'ZGARTIRISH ---
    elif action == "maintenance":
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        status = "YONIQ 🔴 (Foydalanuvchilar o'ynay olmaydi)" if MAINTENANCE_MODE else "O'CHIQ 🟢 (Hamma o'ynay oladi)"
        bot.answer_callback_query(call.id, f"Texnik rejim: {status}", show_alert=True)
        show_admin_menu(call.message.chat.id, call.message.message_id)

    # --- REKORDLARNI TOZALASH ---
    elif action == "wipe":
        msg = bot.edit_message_text("⚠️ <b>DIQQAT!</b>\n\nBu amal bazadagi barcha rekordlarni o'chirib yuboradi. Yangi mavsum boshlash uchun ishlatiladi.\n\nAgar ishonchingiz komil bo'lsa, chatga to'liq harflar bilan <b>TOZALASH</b> deb yozing.\n<i>Bekor qilish uchun /cancel bosing.</i>", 
                              call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_wipe)

    # --- XABAR TARQATISH ---
    elif action == "broadcast":
        msg = bot.edit_message_text("📢 Xabarni (rasm/video/matn) yuboring:\n<i>Bekor qilish: /cancel</i>", 
                                    call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_broadcast)

    # --- YOPISH ---
    elif action == "close":
        bot.delete_message(call.message.chat.id, call.message.message_id)

# ==========================================
# REKORDLARNI TOZALASH (Tasdiqlash)
# ==========================================
def process_wipe(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Bekor qilindi.")
        show_admin_menu(message.chat.id)
        return
        
    if message.text == 'TOZALASH':
        cursor.execute('DELETE FROM players')
        conn.commit()
        bot.send_message(message.chat.id, "✅ <b>Barcha rekordlar muvaffaqiyatli tozalandi!</b> Yangi mavsum boshlandi.", parse_mode="HTML")
        show_admin_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Noto'g'ri so'z kiritildi. Tozalash bekor qilindi.")
        show_admin_menu(message.chat.id)

# ==========================================
# XABAR TARQATISH (Broadcast)
# ==========================================
def process_broadcast(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Bekor qilindi.")
        show_admin_menu(message.chat.id)
        return
        
    bot.send_message(message.chat.id, "⏳ Tarqatish boshlandi...")
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    
    success, failed = 0, 0
    for user in users:
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
            
    bot.send_message(message.chat.id, f"✅ <b>Yakunlandi!</b>\n📨 Yuborildi: <b>{success}</b> | 🚫 Xato: <b>{failed}</b>", parse_mode="HTML")
    show_admin_menu(message.chat.id)

# Botni ishga tushirish
print("🚀 Super Admin Bot ishga tushdi...")
bot.polling(none_stop=True)