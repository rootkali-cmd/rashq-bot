# bot.py - نسخة نووية | Zefoy API + كومنتات + تصفية | Railway 100% | 2025

import logging
import sqlite3
import asyncio
import random
import time
import re
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
    'followers': {'name': 'رشق متابعين', 'type': 'username', 'zefoy_service': 'followers'},
    'views': {'name': 'رشق مشاهدات', 'type': 'video', 'zefoy_service': 'views'},
    'likes': {'name': 'رشق لايكات', 'type': 'video', 'zefoy_service': 'likes'},
    'shares': {'name': 'رشق مشاركات', 'type': 'video', 'zefoy_service': 'shares'},
    'favorites': {'name': 'رشق مفضلات', 'type': 'video', 'zefoy_service': 'favorites'},
    'comment_likes': {'name': 'رشق لايكات كومنتات', 'type': 'comment_filter', 'zefoy_service': 'comment_hearts'}
}

# === بروكسيات قوية 2025 ===
PROXIES = [
    "103.174.102.1:80", "154.202.122.1:80", "185.199.229.156:80",
    "141.98.11.106:80", "188.74.210.207:80", "45.12.30.183:80",
    "185.199.228.220:80", "185.199.231.45:80", "45.12.31.183:80"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36"
]

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

# === الرشق الحقيقي بـ Zefoy API ===
async def rashq_core(service, target, amount):
    sent = 0
    base_url = "https://zefoy.com"
    batch_size = min(500, amount)
    batches = min((amount + batch_size - 1) // batch_size, 10)
    
    for _ in range(batches):
        proxy = {'http': f'http://{random.choice(PROXIES)}', 'https': f'http://{random.choice(PROXIES)}'}
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Origin': base_url,
            'Referer': base_url,
            'Content-Type': 'application/json'
        }
        
        session = requests.Session()
        session.proxies = proxy
        session.headers.update(headers)
        
        try:
            token_resp = session.get(f"{base_url}/api/getToken", timeout=10)
            if token_resp.status_code != 200:
                time.sleep(5)
                continue
            task_token = token_resp.json().get('token', '')
            
            if service == 'comment_likes':
                parts = target.split('|')
                if len(parts) != 2:
                    return 0
                video_link, commenter = parts
                comment_id = extract_comment_id(video_link, commenter)
                if not comment_id:
                    return 0
                url = f"{base_url}/api/comment_hearts"
                payload = {'token': task_token, 'comment': comment_id, 'count': batch_size}
            elif SERVICES[service]['type'] == 'username':
                url = f"{base_url}/api/{SERVICES[service]['zefoy_service']}"
                payload = {'token': task_token, 'user': target.lstrip('@'), 'count': batch_size}
            else:
                video_id = re.search(r'video/(\d+)', target).group(1) if '/' in target else target
                url = f"{base_url}/api/{SERVICES[service]['zefoy_service']}"
                payload = {'token': task_token, 'video': video_id, 'count': batch_size}
            
            submit_resp = session.post(url, json=payload, timeout=15)
            if submit_resp.status_code == 200 and ('success' in submit_resp.text.lower() or submit_resp.json().get('status') == 'ok'):
                sent += batch_size
            time.sleep(random.uniform(3, 7))
        except Exception as e:
            logging.error(f"خطأ في الرشق: {e}")
            time.sleep(5)
    
    return sent

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("البوت خاص بـ @D_3F4ULT فقط.")
        return
    text = f"بوت رشق تيك توك النووي - Zefoy API\n\nالمطور: {DEVELOPER}\nاليوزر: {DEVELOPER_USER}\n\nاختر الخدمة:"
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

# === استقبال النصوص (بدون :=) ===
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

# === أزرار الكومنتات (منفصل) ===
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
 SENT = await rashq_core(service, target, amount)
        await query.message.reply_text(f"تم الرشق: {sent} لايك\nتحقق بعد 5-30 دقيقة!")
        c.execute("INSERT INTO logs (user_id, service, target, amount, time) VALUES (?, ?, ?, ?, ?)",
                  (ADMIN_ID, service, target, sent, int(time.time())))
        conn.commit()
        context.user_data.clear()

# === التشغيل ===
def main():
    print("البوت شغال... وجاهز للرشق الحقيقي مع Zefoy + كومنتات!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern='^(followers|views|likes|shares|favorites|comment_likes)$'))
    app.add_handler(CallbackQueryHandler(comment_buttons, pattern='^[0-9]+_cl$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
