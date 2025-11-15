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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager, ChromeType  # ← الحل النهائي
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

# تشغيل المتصفح (الحل النهائي - webdriver-manager مع ChromeType.GOOGLE)
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
    
    # Chrome من apt
    options.binary_location = '/usr/bin/google-chrome'
    
    # webdriver-manager يحمل الإصدار الصحيح لـ google-chrome-stable
    service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

# باقي الكود (نفس اللي فات)
# ... (login, rashq_core, back_button, start, button, handle_text, show_stats, auto_create, main) ...
