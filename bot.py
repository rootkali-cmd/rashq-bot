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

async def create_account_task(app):
    driver = None
    try:
        response = requests.get("https://api.tempmail.lol/generate", timeout=15)
        if response.status_code != 200:
            await app.bot.send_message(ADMIN_ID, "فشل في جلب الإيميل")
            return False
        data = response.json()
        email = data['address']
        token = data['token']
        password = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=14))
        
        driver = get_driver()
        driver.get("https://www.tiktok.com/signup/phone-or-email/email")
        time.sleep(8)
        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)

        code = None
        for _ in range(20):
            msgs = requests.get(f"https://api.tempmail.lol/auth/{token}", timeout=10).json()
            for msg in msgs.get('emails', []):
                if "verification code" in msg.get('subject', '').lower():
                    code = re.search(r'\d{6}', msg.get('body', '')).group()
                    break
            if code: break
            await asyncio.sleep(6)

        if not code:
            await app.bot.send_message(ADMIN_ID, f"فشل الكود: {email}")
            return False

        for i, digit in enumerate(code):
            inputs = driver.find_elements(By.XPATH, "//input[@maxlength='1']")
            if i < len(inputs):
                inputs[i].send_keys(digit)
                time.sleep(0.5)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(12)

        if "foryou" in driver.current_url:
            c.execute("INSERT INTO accounts (email, pass, status, created_at) VALUES (?, ?, 'active', ?)",
                      (email, password, int(time.time())))
            conn.commit()
            await app.bot.send_message(ADMIN_ID, f"تم إنشاء: {email}")
            return True
    except Exception as e:
        logging.error(f"خطأ: {e}")
    finally:
        if driver: driver.quit()
    return False

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

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

async def rashq_core(service, target, amount):
    c.execute("SELECT email, pass FROM accounts WHERE status = 'active' LIMIT 30")
    accounts = c.fetchall()
    sent = 0
    for email, password in random.sample(accounts, min(len(accounts), amount)):
        driver = get_driver()
        if login(driver, email, password):
            try:
                if service == 'followers':
                    driver.get(f"https://www.tiktok.com/@{target.lstrip('@')}")
                    time.sleep(5)
                    btn = driver.find_elements(By.XPATH, "//button[contains(., 'Follow') and not(contains(., 'Following'))]")
                    if btn: btn[0].click(); sent += 1
                elif service == 'views':
                    driver.get(target); time.sleep(10); sent += 1
                elif service == 'likes':
                    driver.get(target); time.sleep(10); 
                    btn = driver.find_elements(By.XPATH, "//button[@data-e2e='like-button']")
                    if btn: btn[0].click(); sent += 1
            except: pass
        driver.quit()
    c.execute("INSERT INTO logs (service, target, amount, time) VALUES (?, ?, ?, ?)", (service, target, sent, int(time.time())))
    conn.commit()
    return sent

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton(v['name'], callback_data=k)] for k, v in SERVICES.items()]
    keyboard.append([InlineKeyboardButton("إحصائيات", callback_data='stats')])
    await update.message.reply_text("اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID: return
    service = query.data
    context.user_data['service'] = service
    context.user_data['step'] = 'target'
    msg = "أرسل اسم المستخدم:" if SERVICES[service]['type'] == 'username' else "أرسل رابط الفيديو:"
    await query.edit_message_text(msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = update.message.text.strip()
    step = context.user_data.get('step')
    service = context.user_data.get('service')
    if step == 'target':
        context.user_data['target'] = text
        context.user_data['step'] = 'amount'
        await update.message.reply_text("أرسل العدد:")
    elif step == 'amount':
        if not text.isdigit(): 
            await update.message.reply_text("أرسل رقم!")
            return
        amount = int(text)
        target = context.user_data['target']
        await update.message.reply_text(f"جاري رشق {amount}...")
        sent = await rashq_core(service, target, amount)
        await update.message.reply_text(f"تم: {sent}")
        context.user_data.clear()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'"); active = c.fetchone()[0]
    c.execute("SELECT SUM(amount) FROM logs"); total = c.fetchone()[0] or 0
    text = f"حسابات نشيطة: {active}\nإجمالي الرشق: {total}"
    keyboard = [[InlineKeyboardButton("تحديث", callback_data='stats')]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def auto_create(app):
    while True:
        c.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
        if c.fetchone()[0] < 10:
            await app.bot.send_message(ADMIN_ID, "إنشاء 3 حسابات...")
            for _ in range(3):
                await create_account_task(app)
                await asyncio.sleep(30)
        await asyncio.sleep(1800)

def main():
    print("Bot شغال!")
    app = Application.builder().token(TOKEN).concurrent_updates(True).job_queue(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern='^(followers|views|likes)$'))
    app.add_handler(CallbackQueryHandler(lambda u, c: stats(u, c), pattern='^stats$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.job_queue.run_repeating(lambda _: asyncio.create_task(auto_create(app)), interval=1800, first=10)
    app.run_polling()

if __name__ == "__main__":
    main()
