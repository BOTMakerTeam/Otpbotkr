# FILE: otpbot_v4.7_country_fix.py (COUNTRY DETECTION & DIAGNOSTIC FIX)

import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import signal
import sqlite3
import os
import threading
import hashlib
import queue
import random
from datetime import datetime, timedelta

# --- Configuration ---
BOT_NAME = "OTP Bot"
USERNAME = "Stream"
PASSWORD = "Stream@#"
DB_FILE = "sms_database_np.db" 

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = "7959848592:AAHzlnHoVxD4302s9yLjwgYJBBUNGx39uBc"
DEFAULT_GROUP_CHAT_ID = "-1002516783528" 
DM_CHAT_ID = "7701278483" 

# --- New Configuration ---
DEVELOPER_NAME = "𓆩💔̲͟𝄠𝐋𝐨𝐧𝐞𝐥𝐲𖠌𝐇𝐞𝐚𝐫𝐭̲͟𓂀𝐌𝐢𝐬𝐬𝐢𝐧𝐠͟𝐌𝐞𓆪𝄠♥"
DEVELOPER_TG_ID = "7701278483" 

# --- API Endpoints ---
BASE_URL = "http://51.89.99.105/NumberPanel"
DOMAIN_URL = "http://51.89.99.105"
LOGIN_PAGE_URL = f"{BASE_URL}/"
SMS_HTML_PAGE_URL = f"{BASE_URL}/client/SMSCDRStats" 

POTENTIAL_API_URLS = [
    f"{BASE_URL}/client/res/data_smscdr.php",
    f"{DOMAIN_URL}/res/data_smscdr.php",
    f"{BASE_URL}/res/data_smscdr.php"
]
working_api_url = None 

# --- Global variables ---
db_connection = None
stop_event = threading.Event()
reported_sms_hashes_cache = set()

# --- Data for Formatting ---

# <<< рж╕ржорж╛ржзрж╛ржи: ржХрж╛ржирзНржЯрзНрж░рж┐ ржХрзЛржбрзЗрж░ рж╕ржорзНржкрзВрж░рзНржг рждрж╛рж▓рж┐ржХрж╛ ржЖржмрж╛рж░ ржпрзЛржЧ ржХрж░рж╛ рж╣рж▓рзЛ >>>
COUNTRY_CODES = {
    '1': ('USA/Canada', 'ЁЯЗ║ЁЯЗ╕'), '7': ('Russia', 'ЁЯЗ╖ЁЯЗ║'), '20': ('Egypt', 'ЁЯЗкЁЯЗм'), '27': ('South Africa', 'ЁЯЗ┐ЁЯЗж'),
    '30': ('Greece', 'ЁЯЗмЁЯЗ╖'), '31': ('Netherlands', 'ЁЯЗ│ЁЯЗ▒'), '32': ('Belgium', 'ЁЯЗзЁЯЗк'), '33': ('France', 'ЁЯЗлЁЯЗ╖'),
    '34': ('Spain', 'ЁЯЗкЁЯЗ╕'), '36': ('Hungary', 'ЁЯЗнЁЯЗ║'), '39': ('Italy', 'ЁЯЗоЁЯЗ╣'), '40': ('Romania', 'ЁЯЗ╖ЁЯЗ┤'),
    '41': ('Switzerland', 'ЁЯЗиЁЯЗн'), '43': ('Austria', 'ЁЯЗжЁЯЗ╣'), '44': ('United Kingdom', 'ЁЯЗмЁЯЗз'), '45': ('Denmark', 'ЁЯЗйЁЯЗ░'),
    '46': ('Sweden', 'ЁЯЗ╕ЁЯЗк'), '47': ('Norway', 'ЁЯЗ│ЁЯЗ┤'), '48': ('Poland', 'ЁЯЗ╡ЁЯЗ▒'), '49': ('Germany', 'ЁЯЗйЁЯЗк'),
    '51': ('Peru', 'ЁЯЗ╡ЁЯЗк'), '52': ('Mexico', 'ЁЯЗ▓ЁЯЗ╜'), '53': ('Cuba', 'ЁЯЗиЁЯЗ║'), '54': ('Argentina', 'ЁЯЗжЁЯЗ╖'),
    '55': ('Brazil', 'ЁЯЗзЁЯЗ╖'), '56': ('Chile', 'ЁЯЗиЁЯЗ▒'), '57': ('Colombia', 'ЁЯЗиЁЯЗ┤'), '58': ('Venezuela', 'ЁЯЗ╗ЁЯЗк'),
    '60': ('Malaysia', 'ЁЯЗ▓ЁЯЗ╛'), '61': ('Australia', 'ЁЯЗжЁЯЗ║'), '62': ('Indonesia', 'ЁЯЗоЁЯЗй'), '63': ('Philippines', 'ЁЯЗ╡ЁЯЗн'),
    '64': ('New Zealand', 'ЁЯЗ│ЁЯЗ┐'), '65': ('Singapore', 'ЁЯЗ╕ЁЯЗм'), '66': ('Thailand', 'ЁЯЗ╣ЁЯЗн'), '81': ('Japan', 'ЁЯЗпЁЯЗ╡'),
    '82': ('South Korea', 'ЁЯЗ░ЁЯЗ╖'), '84': ('Vietnam', 'ЁЯЗ╗ЁЯЗ│'), '86': ('China', 'ЁЯЗиЁЯЗ│'), '90': ('Turkey', 'ЁЯЗ╣ЁЯЗ╖'),
    '91': ('India', 'ЁЯЗоЁЯЗ│'), '92': ('Pakistan', 'ЁЯЗ╡ЁЯЗ░'), '93': ('Afghanistan', 'ЁЯЗжЁЯЗл'), '94': ('Sri Lanka', 'ЁЯЗ▒ЁЯЗ░'),
    '95': ('Myanmar', 'ЁЯЗ▓ЁЯЗ▓'), '98': ('Iran', 'ЁЯЗоЁЯЗ╖'), '212': ('Morocco', 'ЁЯЗ▓ЁЯЗж'), '213': ('Algeria', 'ЁЯЗйЁЯЗ┐'),
    '216': ('Tunisia', 'ЁЯЗ╣ЁЯЗ│'), '218': ('Libya', 'ЁЯЗ▒ЁЯЗ╛'), '221': ('Senegal', 'ЁЯЗ╕ЁЯЗ│'), '223': ('Mali', 'ЁЯЗ▓ЁЯЗ▒'),
    '224': ('Guinea', 'ЁЯЗмЁЯЗ│'), '225': ("C├┤te d'Ivoire", 'ЁЯЗиЁЯЗо'), '226': ('Burkina Faso', 'ЁЯЗзЁЯЗл'), '227': ('Niger', 'ЁЯЗ│ЁЯЗк'),
    '228': ('Togo', 'ЁЯЗ╣ЁЯЗм'), '229': ('Benin', 'ЁЯЗзЁЯЗп'), '230': ('Mauritius', 'ЁЯЗ▓ЁЯЗ║'), '233': ('Ghana', 'ЁЯЗмЁЯЗн'),
    '234': ('Nigeria', 'ЁЯЗ│ЁЯЗм'), '237': ('Cameroon', 'ЁЯЗиЁЯЗ▓'), '245': ('Guinea-Bissau', 'ЁЯЗмЁЯЗ╝'), '251': ('Ethiopia', 'ЁЯЗкЁЯЗ╣'),
    '254': ('Kenya', 'ЁЯЗ░ЁЯЗк'), '255': ('Tanzania', 'ЁЯЗ╣ЁЯЗ┐'), '256': ('Uganda', 'ЁЯЗ║ЁЯЗм'), '258': ('Mozambique', 'ЁЯЗ▓ЁЯЗ┐'),
    '260': ('Zambia', 'ЁЯЗ┐ЁЯЗ▓'), '263': ('Zimbabwe', 'ЁЯЗ┐ЁЯЗ╝'), '351': ('Portugal', 'ЁЯЗ╡ЁЯЗ╣'), '353': ('Ireland', 'ЁЯЗоЁЯЗк'),
    '354': ('Iceland', 'ЁЯЗоЁЯЗ╕'), '358': ('Finland', 'ЁЯЗлЁЯЗо'), '375': ('Belarus', 'ЁЯЗзЁЯЗ╛'), '380': ('Ukraine', 'ЁЯЗ║ЁЯЗж'),
    '420': ('Czech Republic', 'ЁЯЗиЁЯЗ┐'), '855': ('Cambodia', 'ЁЯЗ░ЁЯЗн'), '856': ('Laos', 'ЁЯЗ▒ЁЯЗж'),
    '880': ('Bangladesh', 'ЁЯЗзЁЯЗй'), '886': ('Taiwan', 'ЁЯЗ╣ЁЯЗ╝'), '961': ('Lebanon', 'ЁЯЗ▒ЁЯЗз'), '962': ('Jordan', 'ЁЯЗпЁЯЗ┤'),
    '963': ('Syria', 'ЁЯЗ╕ЁЯЗ╛'), '964': ('Iraq', 'ЁЯЗоЁЯЗ╢'), '965': ('Kuwait', 'ЁЯЗ░ЁЯЗ╝'), '966': ('Saudi Arabia', 'ЁЯЗ╕ЁЯЗж'),
    '967': ('Yemen', 'ЁЯЗ╛ЁЯЗк'), '968': ('Oman', 'ЁЯЗ┤ЁЯЗ▓'), '971': ('United Arab Emirates', 'ЁЯЗжЁЯЗк'), '973': ('Bahrain', 'ЁЯЗзЁЯЗн'),
    '974': ('Qatar', 'ЁЯЗ╢ЁЯЗж'), '976': ('Mongolia', 'ЁЯЗ▓ЁЯЗ│'), '977': ('Nepal', 'ЁЯЗ│ЁЯЗ╡'), '998': ('Uzbekistan', 'ЁЯЗ║ЁЯЗ┐'),
}

QURANIC_VERSES = [
    ("ржПржмржВ рж╕рж╛рж╣рж╛ржпрзНржп ржкрзНрж░рж╛рж░рзНржержирж╛ ржХрж░ ржзрзИрж░рзНржпрзНржп ржУ ржирж╛ржорж╛ржпрзЗрж░ ржорж╛ржзрзНржпржорзЗред ржирж┐рж╢рзНржЪрзЯ рждрж╛ ржХржарж┐ржи, ржХрж┐ржирзНрждрзБ ржмрж┐ржирзАрждржжрзЗрж░ ржЬржирзНржпрзЗ ржирзЯред", "рж╕рзВрж░рж╛ ржЖрж▓-ржмрж╛ржХрж╛рж░рж╛, ржЖрзЯрж╛ржд рзкрзл"),
    ("ржЖрж▓рзНрж▓рж╛рж╣ ржХрзЛржи ржмрзНржпржХрзНрждрж┐рж░ ржЙржкрж░ рждрж╛рж░ рж╕рж╛ржзрзНржпрж╛рждрзАржд ржХрзЗрж╛ржи ржХрж╛ржЬрзЗрж░ ржжрж╛рзЯрж┐рждрзНржм ржЪрж╛ржкрж┐рзЯрзЗ ржжрзЗржи ржирж╛ред", "рж╕рзВрж░рж╛ ржЖрж▓-ржмрж╛ржХрж╛рж░рж╛, ржЖрзЯрж╛ржд рзирзорзм"),
    ("ржПржмржВ рждрзЗрж╛ржорж░рж╛ ржирж┐рж░рж╛рж╢ рж╣рзЯрзЗрж╛ ржирж╛ ржПржмржВ ржжрзБржГржЦ ржХрж░рзЗрж╛ ржирж╛ред ржпржжрж┐ рждрзЗрж╛ржорж░рж╛ ржорзБржорж┐ржи рж╣ржУ, рждржмрзЗ рждрзЗрж╛ржорж░рж╛ржЗ ржЬрзЯрзА рж╣ржмрзЗред", "рж╕рзВрж░рж╛ ржЖрж▓-ржЗржорж░рж╛ржи, ржЖрзЯрж╛ржд █▒█│█╣"),
    ("ржпрж╛рж░рж╛ ржЖрж▓рзНрж▓рж╛рж╣ ржУ рж╢рзЗрж╖ ржжрж┐ржмрж╕рзЗрж░ ржЖрж╢рж╛ рж░рж╛ржЦрзЗ ржПржмржВ ржЖрж▓рзНрж▓рж╛рж╣ржХрзЗ ржЕржзрж┐ржХ рж╕рзНржорж░ржг ржХрж░рзЗ, рждрж╛ржжрзЗрж░ ржЬржирзНржпрзЗ рж░рж╕рзВрж▓рзБрж▓рзНрж▓рж╛рж╣рж░ ржоржзрзНржпрзЗ ржЙрждрзНрждржо ржиржорзБржирж╛ рж░рзЯрзЗржЫрзЗред", "рж╕рзВрж░рж╛ ржЖрж▓-ржЖрж╣ржпрж╛ржм, ржЖрзЯрж╛ржд рзирзз"),
    ("ржмрж▓рзБржи, рж╣рзЗ ржЖржорж╛рж░ ржмрж╛ржирзНржжрж╛ржЧржг! ржпрж╛рж░рж╛ ржирж┐ржЬрзЗржжрзЗрж░ ржЙржкрж░ ржпрзБрж▓рзБржо ржХрж░рзЗржЫ рждрзЗрж╛ржорж░рж╛ ржЖрж▓рзНрж▓рж╛рж╣рж░ рж░рж╣ржоржд ржерзЗржХрзЗ ржирж┐рж░рж╛рж╢ рж╣рзЯрзЗрж╛ ржирж╛ред", "рж╕рзВрж░рж╛ ржЖржп-ржпрзБржорж╛рж░, ржЖрзЯрж╛ржд рзлрзй"),
    ("ржирж┐рж╢рзНржЪрзЯ ржХрж╖рзНржЯрзЗрж░ рж╕рж╛ржерзЗ рж╕рзНржмрж╕рзНрждрж┐ рж░рзЯрзЗржЫрзЗред", "рж╕рзВрж░рж╛ ржЖрж▓-ржЗржирж╢рж┐рж░рж╛рж╣, ржЖрзЯрж╛ржд рзм"),
    ("ржкрзЬрзБржи ржЖржкржирж╛рж░ ржкрж╛рж▓ржиржХрж░рзНрждрж╛рж░ ржирж╛ржорзЗ ржпрж┐ржирж┐ рж╕рзГрж╖рзНржЯрж┐ ржХрж░рзЗржЫрзЗржиред", "рж╕рзВрж░рж╛ ржЖрж▓-ржЖрж▓рж╛ржХ, ржЖрзЯрж╛ржд рзз"),
]

def get_country_info(phone_number):
    for i in range(4, 0, -1):
        prefix = phone_number[:i]
        if prefix in COUNTRY_CODES: return COUNTRY_CODES[prefix]
    return ('Unknown', 'тЭУ')

def detect_service(sender_name, message_text):
    full_text = (sender_name + " " + message_text).lower()
    services = ['whatsapp', 'facebook', 'google', 'telegram', 'instagram', 'discord', 'twitter', 'snapchat', 'imo', 'tiktok']
    for service in services:
        if service in full_text: return service.capitalize()
    return sender_name if sender_name else "Unknown"

def format_telegram_message(recipient_number, sender_name, message, otp, sms_time):
    country_name, country_flag = get_country_info(recipient_number)
    service_name = detect_service(sender_name, message)
    verse, surah_info = random.choice(QURANIC_VERSES)
    developer_link = f"[{DEVELOPER_NAME}](tg://user?id={DEVELOPER_TG_ID})"
    
    return f"""тЬЕ {country_flag} *{country_name} {service_name} OTP Code Received!*
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
ЁЯУ▒ *Number:* `{recipient_number}`
ЁЯМН *Country:* {country_flag} {country_name}
тЪЩя╕П *Service:* {service_name}
ЁЯФТ *OTP Code:* `{otp}`
тП│ *Time:* `{sms_time}`
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
*Message:*
```{message}```
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
*ЁЯУЦ ржкржмрж┐рждрзНрж░ ржХрзБрж░ржЖржи:*
> _{verse}_
> тАФ _{surah_info}_
тФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ
*Bot Developer:* {developer_link}
---
*Powered By Stream Vault Method*"""

class TelegramSender:
    def __init__(self, token, stop_signal):
        self.token, self.queue, self.stop_event = token, queue.Queue(), stop_signal
        self.thread = threading.Thread(target=self._worker, daemon=True)
    def start(self): self.thread.start(); print("[*] Telegram Sender thread started.")
    def _worker(self):
        while not self.stop_event.is_set():
            try:
                chat_id, text, sms_hash = self.queue.get(timeout=1)
                if self._send_message(chat_id, text): add_sms_to_reported_db(sms_hash)
                self.queue.task_done()
            except queue.Empty: continue
    def _send_message(self, chat_id, text):
        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
        try:
            r = requests.post(api_url, json=payload, timeout=20)
            if r.status_code != 200: print(f"[!] Telegram API Error: {r.status_code} - {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"[!] Failed to send message to Telegram: {e}"); return False
    def queue_message(self, chat_id, text, sms_hash): self.queue.put((chat_id, text, sms_hash))

telegram_sender = TelegramSender(TELEGRAM_BOT_TOKEN, stop_event)

def setup_database():
    global db_connection, reported_sms_hashes_cache
    try:
        db_connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = db_connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS reported_sms (hash TEXT PRIMARY KEY)')
        reported_sms_hashes_cache = {row[0] for row in cursor.execute("SELECT hash FROM reported_sms")}
        db_connection.commit(); print(f"[*] Database connected. Loaded {len(reported_sms_hashes_cache)} hashes.")
        return True
    except sqlite3.Error as e: print(f"[!!!] DATABASE ERROR: {e}"); return False

def add_sms_to_reported_db(sms_hash):
    try:
        with db_connection: db_connection.execute("INSERT INTO reported_sms (hash) VALUES (?)", (sms_hash,))
    except sqlite3.Error: pass

def send_operational_message(chat_id, text):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={'chat_id': chat_id, 'text': f"{text}\n\nЁЯдЦ _{BOT_NAME}_", 'parse_mode': 'Markdown'}, timeout=15)
    except Exception: pass

def graceful_shutdown(signum, frame):
    print("\n[!!!] Shutdown signal detected. Stopping.")
    stop_event.set()
    time.sleep(1)
    if db_connection: db_connection.close()
    sys.exit(0)

def solve_math_captcha(captcha_text):
    match = re.search(r'(\d+)\s*([+*])\s*(\d+)', captcha_text)
    if not match: return None
    n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
    result = n1 + n2 if op == '+' else n1 * n2
    print(f"[*] Solved Captcha: {n1} {op} {n2} = {result}")
    return result

def start_watching_sms(session, destination_chat_id):
    global working_api_url
    polling_interval = 1
    
    while not stop_event.is_set():
        try:
            print(f"[*] Fetching SMS data... ({time.strftime('%H:%M:%S')})")
            print(f"    - Current session cookies: {session.cookies.get_dict()}")

            if not working_api_url:
                print("[!] Working API URL not set. Trying to find it again...")
                for url_to_test in POTENTIAL_API_URLS:
                    try:
                        test_response = session.get(url_to_test, timeout=20, params={'sEcho': '1'})
                        if test_response.status_code != 404:
                            print(f"[SUCCESS] Found working API URL: {url_to_test}")
                            working_api_url = url_to_test; break
                    except requests.exceptions.RequestException: pass
                if not working_api_url:
                    print("[!!!] CRITICAL: Could not find a working API URL. Bot cannot proceed.")
                    graceful_shutdown(None, None)

            date_to, date_from = datetime.now(), datetime.now() - timedelta(days=1)
            params = {'fdate1': date_from.strftime('%Y-%m-%d %H:%M:%S'), 'fdate2': date_to.strftime('%Y-%m-%d %H:%M:%S')}
            api_headers = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest", "Referer": SMS_HTML_PAGE_URL}
            
            response = session.get(working_api_url, params=params, headers=api_headers, timeout=30)
            
            print(f"    - API Status Code: {response.status_code}")
            print(f"    - API Response (first 150 chars): {response.text[:150]}")

            response.raise_for_status()
            json_data = response.json()
            
            if 'aaData' in json_data and isinstance(json_data['aaData'], list):
                sms_list = json_data['aaData']
                print(f"    - Found {len(sms_list)} SMS entries in the API response.")
                
                for sms_data in reversed(sms_list):
                    if len(sms_data) > 4:
                        dt, rc, sn, msg = str(sms_data[0]), str(sms_data[2]), str(sms_data[3]), str(sms_data[4])
                        
                        if not msg or not rc or rc.strip() == '0' or len(rc.strip()) < 5:
                            print(f"    - Ignoring invalid/empty SMS data: Number='{rc}', Message='{msg}'")
                            continue

                        h = hashlib.md5(f"{dt}-{rc}-{msg}".encode()).hexdigest()
                        
                        print(f"    - Processing SMS for {rc}. Hash: {h}")
                        if h not in reported_sms_hashes_cache:
                            reported_sms_hashes_cache.add(h)
                            print(f"    - [+] New SMS Queued! For: {rc}")
                            otp_match = re.search(r'\b(\d{3}[-\s]\d{3})\b|\b(\d{4,8})\b', msg)
                            otp = otp_match.group(0) if otp_match else "N/A"
                            notification_message = format_telegram_message(rc, sn, msg, otp, dt)
                            telegram_sender.queue_message(destination_chat_id, notification_message, h)
                        else:
                            print(f"    - [-] Duplicate SMS ignored (hash already in cache).")
            else:
                print("[!] API response format is not as expected. 'aaData' key not found or is not a list.")
            
            print("-" * 40)
            time.sleep(polling_interval)
            
        except requests.exceptions.RequestException as e: print(f"[!] Network error: {e}. Retrying..."); time.sleep(30)
        except Exception as e: print(f"[!!!] CRITICAL ERROR in SMS watch loop: {e}"); time.sleep(30)

def main():
    signal.signal(signal.SIGINT, graceful_shutdown)
    print("="*60 + "\n--- NumberPanel OTP Bot (v4.7 Country Fix) ---\n" + "="*60)
    if not setup_database(): return
    
    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'})
            print("\n[*] Step 1: Logging in...")
            r = session.get(LOGIN_PAGE_URL, timeout=20); soup = BeautifulSoup(r.text, 'html.parser')
            form = soup.find('form');
            if not form: raise Exception("Could not find <form> tag.")
            post_url = form.get('action')
            if not post_url.startswith('http'): post_url = f"{BASE_URL}/{post_url.lstrip('/')}"
            
            payload = {}
            for tag in form.find_all('input'):
                n, v, p = tag.get('name'), tag.get('value', ''), tag.get('placeholder', '').lower()
                if not n: continue
                if 'user' in p: payload[n] = USERNAME
                elif 'pass' in p: payload[n] = PASSWORD
                elif 'ans' in p:
                    el = soup.find(string=re.compile(r'What is \d+ \s*[+*]\s* \d+'))
                    if not el: raise Exception("Could not find captcha text.")
                    payload[n] = solve_math_captcha(el)
                else: payload[n] = v
            
            r = session.post(post_url, data=payload, headers={'Referer': LOGIN_PAGE_URL})
            
            if "dashboard" in r.url.lower() or "Logout" in r.text:
                print("[SUCCESS] Authentication complete!")
                print(f"    - Final URL: {r.url}")
                print(f"    - Final Session Cookies: {session.cookies.get_dict()}")
                telegram_sender.start()
                send_operational_message(DM_CHAT_ID, "тЬЕ *Bot Started & Logged In!*\n\nWatching for SMS on NumberPanel.")
                start_watching_sms(session, DEFAULT_GROUP_CHAT_ID)
            else:
                print("\n[!!!] AUTHENTICATION FAILED.")
                e_div = BeautifulSoup(r.text, 'html.parser').find('div', class_='alert-danger')
                print(f"    - Reason: {e_div.get_text(strip=True)}" if e_div else f"    - Status: {r.status_code}, URL: {r.url}. Check credentials.")
                print(f"    - Full response on failure: {r.text[:500]}")
    except Exception as e:
        print(f"\n[!!!] Critical startup error: {e}")

if __name__ == "__main__":
    main()
