# Ahmed Mahmoud Farm Bot | خارق | تلقائي | إحصائيات | مجاني 100%

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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, JobQueue
)

# إعدادات
TOKEN = "8397954501:AAG5rlKIDoeaXFTt-Nm7PWcyxyYQgIGZD7k"
ADMIN_ID = 8247475893
PASSWORD = "K112KK21@"
MIN_USERNAME = 111000
MAX_USERNAME = 999999

SERVICES = {
    'followers': {'name': 'رشق متابعين', 'type': 'username'},
    'views': {'name': 'رشق مشاهدات', 'type': 'video'},
    'likes': {'name': 'رشق لايكات', 'type': 'video'},
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# قاعدة بيانات
conn = sqlite3.connect("rashq.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    username TEXT,
    status TEXT DEFAULT 'creating',
    created_at INTEGER
)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT,
    target TEXT,
    amount INTEGER,
    sent INTEGER,
    timestamp INTEGER
)''')
conn.commit()

# إنشاء حساب تلقائي
async def create_account_task(app):
    driver = None
    try:
        resp = requests.get("https://api.tempmail.lol/generate", timeout=15)
        if resp.status_code != 200:
            await app.bot.send_message(ADMIN_ID, "فشل جلب الإيميل")
            return False
        data = resp.json()
        email = data['address']
        token = data['token']
        username = f"user111_{random.randint(MIN_USERNAME, MAX_USERNAME)}"

        driver = get_driver()
        driver.get("https://www.tiktok.com/signup/phone-or-email/email")
        await asyncio.sleep(8)

        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        await asyncio.sleep(10)

        code = None
        for _ in range(20):
            try:
                msgs = requests.get(f"https://api.tempmail.lol/auth/{token}").json()
                for msg in msgs.get('emails', []):
                    if "verification code" in msg.get('subject', '').lower():
                        code = re.search(r'\d{6}', msg.get('body', '')).group()
                        break
                if code: break
            except: pass
            await asyncio.sleep(6)

        if not code:
            await app.bot.send_message(ADMIN_ID, f"فشل الكود: {email}")
            c.execute("INSERT OR IGNORE INTO accounts (email, password, username, status, created_at) VALUES (?, ?, ?, 'error', ?)",
                      (email, PASSWORD, username, int(time.time())))
            conn.commit()
            return False

        inputs = driver.find_elements(By.XPATH, "//input[@maxlength='1']")
        for i, digit in enumerate(code):
            if i < len(inputs):
                inputs[i].send_keys(digit)
                await asyncio.sleep(0.5)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        await asyncio.sleep(12)

        if "foryou" in driver.current_url or "following" in driver.current_url:
            c.execute("INSERT OR IGNORE INTO accounts (email, password, username, status, created_at) VALUES (?, ?, ?, 'active', ?)",
                      (email, PASSWORD, username, int(time.time())))
            conn.commit()
            await app.bot.send_message(ADMIN_ID, f"تم إنشاء حساب:\nيوزر: @{username}\nإيميل: {email}")
            return True
        else:
            await app.bot.send_message(ADMIN_ID, f"فشل تسجيل الدخول: {email}")
            return False

    except Exception as e:
        logging.error(f"خطأ إنشاء حساب: {e}")
        await app.bot.send_message(ADMIN_ID, f"خطأ: {str(e)[:100]}")
        return False
    finally:
        if driver:
            driver.quit()

# تشغيل المتصفح
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.binary_location = '/usr/bin/google-chrome'
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

# تسجيل الدخول
def login(driver, email, password):
    try:
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "username").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)
        return "foryou" in driver.current_url
    except:
        return False

# رشق
async def rashq_core(service, target, amount):
    c.execute("SELECT email, password FROM accounts WHERE status = 'active' LIMIT 30")
    accounts = c.fetchall()
    if not accounts:
        return 0
    sent = 0
    for email, password in random.sample(accounts, min(len(accounts), amount)):
        driver = get_driver()
        if login(driver, email, password):
            try:
                if service == 'followers':
                    driver.get(f"https://www.tiktok.com/@{target.lstrip('@')}")
                    time.sleep(6)
                    btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Follow') and not(contains(text(), 'Following'))]")
                    if btn: btn[0].click(); sent += 1
                elif service == 'views':
                    driver.get(target); time.sleep(12); sent += 1
                elif service == 'likes':
                    driver.get(target); time.sleep(10)
                    btn = driver.find_elements(By.XPATH, "//button[@data-e2e='like-button']")
                    if btn: btn[0].click(); sent += 1
                time.sleep(random.uniform(5, 10))
            except: pass
        driver.quit()
    c.execute("INSERT INTO logs (service, target, amount, sent, timestamp) VALUES (?, ?, ?, ?, ?)",
              (service, target, amount, sent, int(time.time())))
    conn.commit()
    return sent

# زر رجوع
def back_button():
    return [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("البوت خاص بـ @D_3F4ULT")
        return
    keyboard = [
        [InlineKeyboardButton("رشق متابعين", callback_data="followers")],
        [InlineKeyboardButton("رشق مشاهدات", callback_data="views")],
        [InlineKeyboardButton("رشق لايكات", callback_data="likes")],
        [InlineKeyboardButton("إحصائيات المزرعة", callback_data="stats")]
    ]
    await update.message.reply_text("اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return

    data = query.data
    if data == "back":
        context.user_data.clear()
        await start(query, context)
        return
    if data in SERVICES:
        context.user_data['service'] = data
        context.user_data['step'] = 'target'
        msg = "أرسل اسم المستخدم:" if SERVICES[data]['type'] == 'username' else "أرسل رابط الفيديو:"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(back_button()))
    elif data == 'stats':
        await show_stats(query)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = update.message.text.strip()
    step = context.user_data.get('step')
    service = context.user_data.get('service')

    if step == 'target':
        context.user_data['target'] = text
        context.user_data['step'] = 'amount'
        await update.message.reply_text("أرسل العدد (100 - 50000):", reply_markup=InlineKeyboardMarkup(back_button()))
    elif step == 'amount':
        if not text.isdigit() or not (100 <= int(text) <= 50000):
            await update.message.reply_text("العدد يجب أن يكون بين 100 و 50000!")
            return
        amount = int(text)
        target = context.user_data['target']
        await update.message.reply_text(f"جاري رشق {amount:,} {SERVICES[service]['name']}...")
        sent = await rashq_core(service, target, amount)
        await update.message.reply_text(f"تم الرشق: {sent:,} تم الإرسال\nتحقق بعد 5-15 دقيقة", reply_markup=InlineKeyboardMarkup(back_button()))
        context.user_data.clear()

async def show_stats(query):
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'creating'"); creating = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM accounts"); total = c.fetchone()[0]
    c.execute("SELECT SUM(sent) FROM logs"); rashq = c.fetchone()[0] or 0
    text = f"""
المزرعة شغالة 24/7

الحسابات النشطة: {active}
تحت الإنشاء: {creating}
الإجمالي: {total}
إجمالي الرشق: {rashq:,}

آخر تحديث: {time.strftime('%H:%M:%S')}
"""
    keyboard = [[InlineKeyboardButton("تحديث الإحصائيات", callback_data="stats")], [InlineKeyboardButton("رجوع", callback_data="back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# خلفية تلقائية
async def auto_create(app):
    while True:
        try:
            c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
            active = c.fetchone()[0]
            if active < 10:
                await app.bot.send_message(ADMIN_ID, "إنشاء 3 حسابات جديدة تلقائيًا...")
                success = 0
                for _ in range(3):
                    if await create_account_task(app):
                        success += 1
                    await asyncio.sleep(40)
                await app.bot.send_message(ADMIN_ID, f"تم إنشاء {success}/3 حسابات بنجاح")
        except Exception as e:
            logging.error(f"خطأ في الخلفية: {e}")
        await asyncio.sleep(1800)

# التشغيل
def main():
    print("Ahmed Mahmoud Farm Bot شغال... خارق!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).job_queue(JobQueue()).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.job_queue.run_repeating(
        callback=lambda ctx: asyncio.create_task(auto_create(app)),
        interval=1800,
        first=10
    )

    app.run_polling()

if __name__ == "__main__":
    main()
