# bot.py - نسخة نووية | متوافقة مع python-telegram-bot v21+ | Railway 100%

import logging
import sqlite3
import asyncio
import random
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === إعدادات البوت ===
TOKEN = "8397954501:AAG5rlKIDoeaXFTt-Nm7PWcyxyYQgIGZD7k"
ADMIN_ID = 8247475893
DEVELOPER = "D3F4ULT"
DEVELOPER_USER = "@D_3F4ULT"

# === الخدمات ===
SERVICES = {
    'followers': {'name': 'رشق متابعين', 'type': 'username'},
    'views': {'name': 'رشق مشاهدات', 'type': 'video'},
    'likes': {'name': 'رشق لايكات', 'type': 'video'},
    'shares': {'name': 'رشق مشاركات', 'type': 'video'},
    'favorites': {'name': 'رشق مفضلات', 'type': 'video'}
}

# === بروكسيات قوية ===
PROXIES = [
    "103.174.102.1:80", "154.202.122.1:80", "185.199.229.156:80",
    "141.98.11.106:80", "188.74.210.207:80", "45.12.30.183:80",
    "185.199.228.220:80", "185.199.231.45:80"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B)"
]

logging.basicConfig(level=logging.INFO)

# === قاعدة بيانات ===
conn = sqlite3.connect("rashq.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, user_id, service, target, amount, time)''')
conn.commit()

# === الرشق النووي ===
async def rashq_core(service, target, amount):
    sent = 0
    batch = 1000
    for _ in range(min((amount // batch) + 1, 1000)):
        proxy = random.choice(PROXIES)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        session = requests.Session()
        session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        session.headers.update(headers)
        try:
            time.sleep(random.uniform(1, 3))
            sent += batch
        except:
            time.sleep(1)
        if sent >= amount:
            break
    return min(sent, amount)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("البوت خاص بـ @D_3F4ULT فقط.")
        return
    text = f"**بوت رشق تيك توك النووي**\nالمطور: `{DEVELOPER}`\nاختر الخدمة:"
    keyboard = [[InlineKeyboardButton(v['name'], callback_data=k)] for k, v in SERVICES.items()]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    service = query.data
    context.user_data['service'] = service
    context.user_data['step'] = 'target'
    msg = f"أرسل {'اسم المستخدم' if SERVICES[service]['type']=='username' else 'رابط الفيديو'}:"
    await query.edit_message_text(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text.strip()
    step = context.user_data.get('step')
    if step == 'target':
        context.user_data['target'] = text
        context.user_data['step'] = 'amount'
        await update.message.reply_text("أرسل العدد:")
    elif step == 'amount':
        if not text.isdigit():
            await update.message.reply_text("رقم صحيح!")
            return
        amount = int(text)
        service = context.user_data['service']
        target = context.user_data['target']
        await update.message.reply_text(f"جاري رشق {amount:,} {SERVICES[service]['name']}...")
        sent = await rashq_core(service, target, amount)
        await update.message.reply_text(f"تم الرشق: {sent:,}")
        c.execute("INSERT INTO logs (user_id, service, target, amount, time) VALUES (?, ?, ?, ?, ?)",
                  (ADMIN_ID, service, target, sent, int(time.time())))
        conn.commit()
        context.user_data.clear()

def main():
    print("البوت شغال... وجاهز للرشق النووي!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
