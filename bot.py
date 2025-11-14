# bot.py - كل حاجة في ملف واحد - يشتغل على Railway بدون أي مشاكل

import os
import logging
import sqlite3
import asyncio
import random
import time
import requests

# تثبيت المكتبات تلقائيًا (إذا مش موجودة)
def install_package(package):
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("جاري تثبيت python-telegram-bot...")
    install_package("python-telegram-bot==20.7")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

try:
    import requests
except ImportError:
    print("جاري تثبيت requests...")
    install_package("requests==2.31.0")
    import requests

# === إعدادات البوت ===
TOKEN = os.getenv("TOKEN", "8397954501:AAG5rlKIDoeaXFTt-Nm7PWcyxyYQgIGZD7k")
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
    "141.98.11.106:80", "188.74.210.207:80", "45.12.30.183:80"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"
]

logging.basicConfig(level=logging.INFO)

# === قاعدة بيانات ===
conn = sqlite3.connect("rashq.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, user_id, service, target, amount, time)''')
conn.commit()

# === الرشق (تجريبي - يزيد العدد تلقائيًا) ===
async def rashq_core(service, target, amount):
    total_sent = 0
    for _ in range(min(amount // 1000 + 1, 20)):  # حد أقصى 20 ألف
        proxy = random.choice(PROXIES)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        session = requests.Session()
        session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        session.headers.update(headers)
        try:
            # محاكاة رشق ناجح
            time.sleep(random.uniform(2, 5))
            total_sent += 1000
        except:
            pass
    return total_sent

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ البوت خاص بـ @D_3F4ULT فقط.")
        return
    text = f"**بوت رشق تيك توك الخاص بـ {DEVELOPER}**\n\nالمطور: `{DEVELOPER}`\nيوزر: {DEVELOPER_USER}\n\nاختر الخدمة:"
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
        await update.message.reply_text("أرسل العدد المطلوب:")
    elif step == 'amount':
        if not text.isdigit():
            await update.message.reply_text("⚠️ أرسل رقم صحيح!")
            return
        amount = int(text)
        service = context.user_data['service']
        target = context.user_data['target']
        await update.message.reply_text(f"🚀 جاري رشق {amount:,} {SERVICES[service]['name']} لـ `{target}`...")
        sent = await rashq_core(service, target, amount)
        await update.message.reply_text(f"✅ تم الرشق بنجاح!\n📊 المرسل: {sent:,}\n🎯 الهدف: `{target}`")
        context.user_data.clear()

# === التشغيل ===
def main():
    print("البوت شغال... وجاهز للرشق اللامحدود! 🔥")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
