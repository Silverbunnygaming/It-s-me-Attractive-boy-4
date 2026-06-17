import telebot
import config
from instagram_bot import send_ig_message, cl

bot = telebot.TeleBot(config.TG_TOKEN)

# Sirf Admin access check karne ke liye decorator helper
def is_admin(message):
    return str(message.from_user.id) == str(config.TG_ADMIN_ID)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_admin(message):
        bot.reply_to(message, f"⛔ Access denied. Aapka ID ({message.from_user.id}) authorized nahi hai.")
        return
    bot.reply_to(message, "Welcome Boss! Main aapka IG Management Bot hoon.\n\nCommands:\n/status - Bot status dekhne ke liye\n/listgc - Apne saare IG Group Chats aur unki IDs dekhne ke liye\n/send <thread_id> <text> - IG GC me message bhejne ke liye")

@bot.message_handler(commands=['listgc'])
def list_group_chats(message):
    if not is_admin(message): return
    bot.reply_to(message, "⏳ Instagram se GC list fetch kar raha hoon...")
    try:
        threads = cl.direct_threads(amount=20)
        if not threads:
            bot.reply_to(message, "❌ Koi bhi Group Chat nahi mila. Pehle Instagram bot ko GC mein add karo.")
            return
        gc_list = "📋 *Aapke Instagram Group Chats:*\n\n"
        found = 0
        for t in threads:
            if t.is_group:
                title = t.thread_title if t.thread_title else "Naam nahi"
                gc_list += f"*{title}*\n`{t.id}`\n\n"
                found += 1
        if found == 0:
            gc_list = "❌ Koi Group Chat nahi mila last 20 threads mein.\n\nBot ko GC mein add karke wapas try karo."
        else:
            gc_list += "👆 Jo ID copy karni ho woh `TARGET_GC_ID` mein daalo."
        bot.reply_to(message, gc_list, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['status'])
def check_status(message):
    if not is_admin(message): return
    status_text = f"🤖 **Bot Status Control** 🤖\n\n📷 IG Main: {config.STATUS['instagram_main']}\n🛡️ IG Emergency: {config.STATUS['instagram_emergency']}\n✈️ Telegram: {config.STATUS['telegram']}"
    bot.reply_to(message, status_text, parse_mode="Markdown")

@bot.message_handler(commands=['send'])
def send_to_ig(message):
    if not is_admin(message): return
    try:
        # Command format: /send 123456789 Hello World
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Format galat hai! Use karein: `/send <thread_id> <message>`", parse_mode="Markdown")
            return
        
        thread_id = parts[1]
        text_to_send = parts[2]
        
        success = send_ig_message(thread_id, text_to_send)
        if success:
            bot.reply_to(message, f"✅ Instagram GC (ID: {thread_id}) me message bhej diya gaya hai!")
        else:
            bot.reply_to(message, "❌ Message nahi bheja ja saka. Check logs.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def run_telegram_bot():
    config.STATUS["telegram"] = "Online 🟢"
    print("[TG] Telegram Bot is Online!")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"[TG] Polling error: {e}, retrying in 5s...")
            import time
            time.sleep(5)
    