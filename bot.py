# bot.py - Ahmed Mahmoud Farm Bot | خارق | تلقائي | إحصائيات | مجاني 100%

import logging
import sqlite3
import asyncio
import random
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === إعدادات ===
TOKEN = "8397954501:AAG5rlKIDoeaXFTt-Nm7PWcyxyYQgIGZD7k"
ADMIN_ID = 8247475893
DEVELOPER = "Ahmed Mahmoud"
DEVELOPER_USER = "@D_3F4ULT"

SERVICES = {
    'followers': {'name': 'رشق متابعين', 'type': 'username'},
    'views': {'name': 'رشق مشاهدات', 'type': 'video'},
    'likes': {'name': 'رشق لايكات', 'type': 'video'},
    'shares': {'name': 'رشق مشاركات', 'type': 'video'},
    'favorites': {'name': 'رشق مفضلات', 'type': 'video'},
    'comment_likes': {'name': 'رشق لايكات كومنتات', 'type': 'comment_filter'}
}

logging.basicConfig(level=logging.INFO)

# === قاعدة بيانات ===
conn = sqlite3.connect("rashq.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    email TEXT,
    pass TEXT,
    status TEXT DEFAULT 'creating',
    created_at INTEGER
)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY,
    service TEXT,
    target TEXT,
    amount INTEGER,
    time INTEGER
)''')
conn.commit()

# === إنشاء حساب تلقائي (tempmail.lol - مجاني + SMS) ===
async def create_account_task(app):
    driver = None
    try:
        # جلب إيميل + token من tempmail.lol
        response = requests.get("https://api.tempmail.lol/generate", timeout=15)
        if response.status_code != 200:
            await app.bot.send_message(ADMIN_ID, "فشل في جلب الإيميل من tempmail.lol")
            return False
        data = response.json()
        email = data['address']
        token = data['token']

        password = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=14))
        
        driver = get_driver()
        driver.get("https://www.tiktok.com/signup/phone-or-email/email")
        time.sleep(8)

        # ملء الإيميل والباسورد
        email_input = driver.find_element(By.NAME, "email")
        email_input.clear()
        email_input.send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)

        # انتظار الكود في الإيميل
        code = None
        for _ in range(20):
            try:
                msgs = requests.get(f"https://api.tempmail.lol/auth/{token}", timeout=10).json()
                for msg in msgs.get('emails', []):
                    body = msg.get('body', '') or ''
                    subject = msg.get('subject', '') or ''
                    if "verification code" in subject.lower() or "كود" in subject or "verify" in subject.lower():
                        code_match = re.search(r'(\d{6})', body)
                        if code_match:
                            code = code_match.group(1)
                            break
                if code:
                    break
            except:
                pass
            await asyncio.sleep(6)

        if not code:
            await app.bot.send_message(ADMIN_ID, f"فشل في استقبال الكود لـ {email}")
            c.execute("INSERT INTO accounts (email, pass, status, created_at) VALUES (?, ?, 'error', ?)",
                      (email, password, int(time.time())))
            conn.commit()
            return False

        # إدخال الكود
        inputs = driver.find_elements(By.XPATH, "//input[@maxlength='1']")
        for i, digit in enumerate(code):
            if i < len(inputs):
                inputs[i].clear()
                inputs[i].send_keys(digit)
                time.sleep(0.5)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(12)

        # التحقق من النجاح
        if "foryou" in driver.current_url or "following" in driver.current_url:
            c.execute("INSERT INTO accounts (email, pass, status, created_at) VALUES (?, ?, 'active', ?)",
                      (email, password, int(time.time())))
            conn.commit()
            await app.bot.send_message(ADMIN_ID, f"تم إنشاء حساب بنجاح: {email}")
            return True
        else:
            await app.bot.send_message(ADMIN_ID, f"فشل في تسجيل الدخول بعد الكود: {email}")
            return False

    except Exception as e:
        logging.error(f"خطأ في إنشاء حساب: {e}")
        await app.bot.send_message(ADMIN_ID, f"خطأ: {str(e)[:150]}")
        return False
    finally:
        if driver:
            driver.quit()

# === get_driver ===
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={user_agent}')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

# === login ===
def login(driver, email, password):
    try:
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)
        return "foryou" in driver.current_url or "following" in driver.current_url
    except:
        return False

# === رشق من حسابات نشيطة ===
async def rashq_core(service, target, amount):
    c.execute("SELECT email, pass FROM accounts WHERE status = 'active' LIMIT 30")
    accounts = c.fetchall()
    if not accounts:
        return 0
    sent = 0
    random.shuffle(accounts)
    for email, password in accounts:
        if sent >= amount:
            break
        driver = get_driver()
        if login(driver, email, password):
            try:
                if service == 'followers':
                    driver.get(f"https://www.tiktok.com/@{target.lstrip('@')}")
                    time.sleep(6)
                    btn = driver.find_elements(By.XPATH, "//button[contains(., 'Follow') and not(contains(., 'Following'))]")
                    if btn and btn[0].is_enabled():
                        btn[0].click()
                        sent += 1
                elif service in ['views', 'likes', 'shares', 'favorites']:
                    driver.get(target)
                    time.sleep(10)
                    if service == 'views':
                        sent += 1
                    elif service == 'likes':
                        btn = driver.find_elements(By.XPATH, "//button[@data-e2e='like-button']")
                        if btn: btn[0].click(); sent += 1
                    elif service == 'shares':
                        btn = driver.find_elements(By.XPATH, "//button[@data-e2e='share-button']")
                        if btn: btn[0].click(); time.sleep(1); sent += 1
                    elif service == 'favorites':
                        btn = driver.find_elements(By.XPATH, "//button[@data-e2e='save-button']")
                        if btn: btn[0].click(); sent += 1
                elif service == 'comment_likes':
                    parts = target.split('|')
                    if len(parts) != 2: continue
                    video_link, commenter = parts
                    driver.get(video_link)
                    time.sleep(7)
                    comments = driver.find_elements(By.XPATH, "//div[@data-e2e='comment-level-1']")
                    for comment in comments:
                        if commenter.lstrip('@') in comment.text:
                            try:
                                btn = comment.find_element(By.XPATH, ".//button[@data-e2e='comment-like-button']")
                                if btn.is_enabled():
                                    btn.click()
                                    sent += 1
                                    break
                            except: pass
                time.sleep(random.uniform(5, 10))
            except: pass
        driver.quit()
    c.execute("INSERT INTO logs (service, target, amount, time) VALUES (?, ?, ?, ?)",
              (service, target, sent, int(time.time())))
    conn.commit()
    return sent

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("البوت خاص بـ @D_3F4ULT فقط.")
        return
    text = f"بوت رشق Ahmed Mahmoud\n\nالمطور: {DEVELOPER}\nاليوزر: {DEVELOPER_USER}\n\nاختر الخدمة:"
    keyboard = [[InlineKeyboardButton(v['name'], callback_data=k)] for k, v in SERVICES.items()]
    keyboard.append([InlineKeyboardButton("إحصائيات المزرعة", callback_data='stats')])
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
        await update.message.reply_text(f"تم الرشق: {sent:,}\nتحقق بعد 5-15 دقيقة!")
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
        await query.message.reply_text(f"تم الرشق: {sent} لايك\nتحقق بعد 5-15 دقيقة!")
        context.user_data.clear()

# === /stats ===
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'creating'"); creating = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'banned'"); banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'error'"); error = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM logs"); total_rashq = c.fetchone()[0] or 0

    text = f"""
المزرعة شغالة 24/7

حسابات نشيطة: {active}
تحت الإنشاء: {creating}
محظورة: {banned}
فشلت: {error}
إجمالي الرشق: {total_rashq:,}

آخر تحديث: {time.strftime('%H:%M:%S')}
"""
    keyboard = [[InlineKeyboardButton("تحديث الإحصائيات", callback_data='refresh_stats')]]
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# === refresh stats ===
async def refresh_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stats(update, context)

# === خلفية تلقائية ===
async def auto_create_accounts(app):
    while True:
        try:
            c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
            active = c.fetchone()[0]
            if active < 15:
                await app.bot.send_message(ADMIN_ID, "إنشاء 3 حسابات جديدة تلقائيًا...")
                for _ in range(3):
                    await create_account_task(app)
                    await asyncio.sleep(40)
        except Exception as e:
            logging.error(f"خطأ في الخلفية: {e}")
        await asyncio.sleep(1800)

# === التشغيل ===
def main():
    print("Ahmed Mahmoud Farm Bot شغال... خارق!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).job_queue=True).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button, pattern='^(followers|views|likes|shares|favorites|comment_likes)$'))
    app.add_handler(CallbackQueryHandler(comment_buttons, pattern='^[0-9]+_cl$'))
    app.add_handler(CallbackQueryHandler(refresh_stats, pattern='^refresh_stats$'))
    app.add_handler(CallbackQueryHandler(lambda u, c: stats(u, c), pattern='^stats$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.job_queue.run_repeating(lambda c: asyncio.create_task(auto_create_accounts(app)), interval=1800, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
