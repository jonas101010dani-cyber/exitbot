import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    PollAnswerHandler, 
    filters, 
    ContextTypes
)

# ==================== CONFIGURATIONS (የአንተ መረጃዎች) ====================
BOT_TOKEN = "8761795577:AAHg925GVjfxoAaM2jQVuBJMXFNijI87pH4"
ADMIN_ID = 8204054122

TELEBIRR_NUMBER = "0987793313"
TELEBIRR_NAME = "yonas daniel"
AMOUNT = "100"
# =======================================================================

def init_db():
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    
    # 1. የተማሪዎች ሰንጠረዥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_paid INTEGER DEFAULT 0,
            current_question INTEGER DEFAULT 1
        )
    ''')
    
    # 2. የጥያቄዎች ሰንጠረዥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT,
            question_text TEXT,
            option_A TEXT,
            option_B TEXT,
            option_C TEXT,
            option_D TEXT,
            correct_option TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ጥያቄን ለተማሪው የሚልክ ፈንክሽን
async def send_next_question(user_id, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_question FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    current_q = row[0] if row else 1
    
    cursor.execute("SELECT id, question_text, option_A, option_B, option_C, option_D, correct_option FROM questions WHERE id = ?", (current_q,))
    question = cursor.fetchone()
    conn.close()
    
    if question:
        q_id, text, a, b, c, d, correct = question
        correct_id = {"A": 0, "B": 1, "C": 2, "D": 3}.get(correct, 0)
        
        clean_text = text[:300]
        clean_options = [str(a)[:100], str(b)[:100], str(c)[:100], str(d)[:100]]
        
        await context.bot.send_poll(
            chat_id=user_id,
            question=clean_text,
            options=clean_options,
            type="quiz",
            correct_option_id=correct_id,
            is_anonymous=False
        )
    else:
        await context.bot.send_message(chat_id=user_id, text="🎉 ማደሻ! ሁሉንም የፈተና ጥያቄዎች ጨርሰዋል። በጣም ጎበዝ! 📚")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No_Username"
    
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_paid FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        cursor.execute("INSERT INTO users (user_id, username, is_paid, current_question) VALUES (?, ?, 0, 1)", (user_id, username))
        conn.commit()
        is_paid = 0
    else:
        is_paid = user[0]
    conn.close()
    
    if is_paid == 1:
        await update.message.reply_text("👋 እንኳን ደህና መጡ! ፈተናውን ለመጀመር /exam ይበሉ።")
    else:
        text = f"👋 ሰላም! የኤግዚት ኤግዛም ጥያቄዎችን ለማግኘት መጀመሪያ ክፍያ መፈጸም አለብዎት።\n\n💵 የክፍያ መጠን: {AMOUNT} ብር\n📱 የቴሌብር ቁጥር: <code>{TELEBIRR_NUMBER}</code>\n👤 ስም: {TELEBIRR_NAME}\n\n⚠️ <b>ማሳሰቢያ:</b> ክፍያውን ፈጽመው ሲያበቁ የደረሰኝ ስክሪንሹት (Screenshot) እዚህ ቦት ላይ ይላኩ።"
        await update.message.reply_text(text, parse_mode="HTML")

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No_Username"
    photo_file_id = update.message.photo[-1].file_id
    
    # ጽሑፉ እንዳይቆራረጥ በአንድ መስመር ላይ ተደርጓል
    admin_text = f"📩 <b>አዲስ የክፍያ ማረጋገጫ ደርሷል!</b>\n\n👤 ተማሪ: @{username}\n🆔 ID: {user_id}"
    
    keyboard = [[InlineKeyboardButton("✅ አጽድቅ (Approve)", callback_data=f"approve_{user_id}"),
                 InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{user_id}")]]
    
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID, 
            photo=photo_file_id, 
            caption=admin_text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="HTML"
        )
        print(f"✅ ስክሪንሹቱ ለአድሚን ({ADMIN_ID}) በተሳካ ሁኔታ ተልኳል!")
        await update.message.reply_text("⏳ ደረሰኝዎ ለአስተዳዳሪ ተልኳል! ክፍያዎ ተረጋግጦ በቅርቡ ይከፈትልዎታል።")
    except Exception as e:
        print(f"❌ ፎቶውን ለአድሚን ለመላክ ሲሞከር ስህተት ተፈጠረ: {e}")
        await update.message.reply_text("⚠️ በሲስተሙ ላይ የኔትወርክ መዘግየት አጋጥሟል። እባክዎ ጥቂት ቆይተው በድጋሚ ይሞክሩ።")

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, target_user_id = query.data.split("_")
    target_user_id = int(target_user_id)
    
    if action == "approve":
        conn = sqlite3.connect('manual_exam.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_paid = 1 WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ <b>ይህ ክፍያ ጸድቋል!</b>", parse_mode="HTML")
        try:
            await context.bot.send_message(chat_id=target_user_id, text="🎉 ክፍያዎ ተረጋግጧል! ለመጀመር /exam ይበሉ።")
        except Exception: pass
    elif action == "reject":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ <b>ይህ ክፍያ ውድቅ ተደርጓል!</b>", parse_mode="HTML")
        try:
            await context.bot.send_message(chat_id=target_user_id, text="❌ የላኩት የክፍያ ማረጋገጫ ውድቅ ተደርጓል። እባክዎ ትክክለኛውን ደረሰኝ በድጋሚ ይላኩ።")
        except Exception: pass

async def start_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_paid FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None or user[0] == 0:
        await update.message.reply_text("⚠️ ይቅርታ! ፈተናውን ለመጀመር መጀመሪያ ክፍያ መፈጸም አለብዎት።")
        return
        
    await send_next_question(user_id, context)

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    
    conn = sqlite3.connect('manual_exam.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET current_question = current_question + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    await send_next_question(user_id, context)

if __name__ == "__main__":
    init_db()
    
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("exam", start_exam))
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(PollAnswerHandler(handle_poll_answer))
    
    print("🚀 ቦቱ በአስተማማኝ ሁኔታ እና በታደሰ አወቃቀር ሥራ ጀምሯል...")
    app.run_polling()