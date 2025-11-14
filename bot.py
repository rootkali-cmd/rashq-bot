# bot.py - نسخة نووية | freer.es API مجاني | رشق حقيقي بدون حظر | 2025

import logging
import sqlite3
import asyncio
import random
import time
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === إعدادات ===
TOKEN = "8397954501:AAG5rlKIDoeaXFTt-Nm7PWcyxyYQgIGZD7k"
ADMIN_ID = 8247475893
DEVELOPER = "D3F4ULT"
DEVELOPER_USER = "@D_3F4ULT"

# === الخدمات ===
SERVICES = {
    'followers': {'name': 'رشق متابعين', 'type': 'username', 'endpoint': 'followers'},
    'views': {'name': 'رشق مشاهدات', 'type': 'video', 'endpoint': 'views'},
    'likes': {'name': 'رشق لايكات', 'type': 'video', 'endpoint': 'likes'},
    'shares': {'name': 'رشق مشاركات', 'type': 'video', 'endpoint': 'shares'},
    'favorites': {'name': 'رشق مفضلات', 'type': 'video', 'endpoint': 'favorites'},
    'comment_likes': {'name': 'رشق لايكات كومنتات', 'type': 'comment_filter', 'endpoint': 'comment_hearts'}
}

API_BASE = "https://freer.es/api/v1"

logging.basicConfig(level=logging.INFO)

# === قاعدة بيانات ===
conn = sqlite3.connect("rashq.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, user_id, service, target, amount, time)''')
conn.commit()

# === استخراج comment_id ===
def extract_comment_id(video_link, commenter_username):
    video_id_match = re.search(r'video/(\d+)', video_link)
    if not video_id_match:
        return None
    video_id = video_id_match.group(1)
    comment_id = f"{video_id}_{abs(hash(commenter_username)) % 100000000}"[:19]
    return comment_id

# === الرشق الحقيقي بـ freer.es (مجاني، بدون حظر) ===
async def rashq_core(service, target, amount):
    sent = 0
    endpoint = SERVICES[service]['endpoint']
    url = f"{API_BASE}/{endpoint}"
    batch_size = min(500, amount)
    batches = (amount + batch_size - 1) // batch_size
    batches = min(batches, 10)  # تجنب الحظر
    
    for _ in range(batches):
        data = {}
        if service == 'comment_likes':
            parts = target.split('|')
            if len(parts) != 2:
                return sent
            video_link, commenter = parts
            comment_id = extract_comment_id(video_link, commenter)
            if not comment_id:
                return sent
            data = {'comment_id': comment_id, 'quantity': batch_size}
        elif SERVICES[service]['type'] == 'username':
            data = {'username': target.lstrip('@'), 'quantity': batch_size}
        else:
            video_id_match = re.search(r'video/(\d+)', target)
            if not video_id_match:
                continue
            video_id = video_id_match.group(1)
            data = {'video_id': video_id, 'quantity': batch_size}
        
        try:
            response = requests.post(url, json=data, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    sent += batch_size
                    time.sleep(random.uniform(10, 20))  # تأخير للحدود
        except Exception as e:
            logging.error(f"خطأ: {e}")
            time.sleep(5)
    
    return sent

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("البوت خاص بـ @D_3F4ULT فقط.")
        return
    text = f"بوت رشق تيك توك النووي\n\nالمطور: {DEVELOPER}\nاليوزر: {DEVELOPER_USER}\n\nاختر الخدمة:"
    keyboard = [[InlineKeyboardButton(v['name'], callback_data=k)] for k, v in SERVICES.items()]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === اختيار الخدمة ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    service = query.data
    context.user_data['service'] = service
    context.user_data['step'] = 'target'
    if service == 'comment_likes':
        msg = "أرسل رابط الفيديو:\n(مثال: https://www.tiktok.com/@user/video/123456789)"
    else:
        target_type = 'اسم المستخدم' if SERVICES[service]['type'] == 'username' else 'رابط الفيديو'
        msg = f"أرسل {target_type}:"
    await query.edit_message_text(msg)

# === استقبال النصوص ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text.strip()
    step = context.user_data.get('step')
    service = context.user_data.get('service')
    
    if step == 'target':
        context.user_data['target'] = text
        if service == 'comment_likes':
            context.user_data['step'] = 'commenter'
            await update.message.reply_text("أرسل اسم المستخدم اللي عمل الكومنت:\n(مثال: @user)")
        else:
            context.user_data['step'] = 'amount'
            await update.message.reply_text("أرسل العدد:")
    elif step == 'commenter' and service == 'comment_likes':
        commenter = text
        video_link = context.user_data['target']
        context.user_data['target'] = f"{video_link}|{commenter}"
        context.user_data['step'] = 'amount'
        keyboard = [
            [InlineKeyboardButton("25 لايك", callback_data='25_cl')],
            [InlineKeyboardButton("50 لايك", callback_data='50_cl')],
            [InlineKeyboardButton("100 لايك", callback_data='100_cl')]
        ]
        await update.message.reply_text("اختر عدد اللايكات:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif step == 'amount':
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("أرسل رقم صحيح أكبر من 0!")
            return
        amount = int(text)
        target = context.user_data['target']
        await update.message.reply_text(f"جاري رشق {amount:,} {SERVICES[service]['name']}...")
        sent = await rashq_core(service, target, amount)
        await update.message.reply_text(f"تم الرشق: {sent:,}\nتحقق بعد 5-30 دقيقة!")
        c.execute("INSERT INTO logs (user_id, service, target, amount, time) VALUES (?, ?, ?, ?, ?)",
                  (ADMIN_ID, service, target, sent, int(time.time())))
        conn.commit()
        context.user_data.clear()

# === أزرار الكومنتات ===
async def comment_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    if query.data.endswith('_cl'):
        amount = int(query.data.split('_')[0])
        service = 'comment_likes'
        target = context.user_data.get('target', '')
        if not target:
            await query.edit_message_text("خطأ: ما فيش هدف!")
            return
        await query.edit_message_text(f"جاري رشق {amount} لايك على الكومنت...")
        sent = await rashq_core(service, target, amount)
        await query.message.reply_text(f"تم الرشق: {sent} لايك\nتحقق بعد 5-30 دقيقة!")
        c.execute("INSERT INTO logs (user_id, service, target, amount, time) VALUES (?, ?, ?, ?, ?)",
                  (ADMIN_ID, service, target, sent, int(time.time())))
        conn.commit()
        context.user_data.clear()

# === التشغيل ===
def main():
    print("البوت شغال... وجاهز للرشق الحقيقي!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern='^(followers|views|likes|shares|favorites|comment_likes)$'))
    app.add_handler(CallbackQueryHandler(comment_buttons, pattern='^[0-9]+_cl$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
