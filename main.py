import requests
import time
import schedule
import json
import os
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import re
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN = "8696663106:AAGQxUIswl8sSJUcXHjaRDpduRoh6bhlx-s"
CHAT_ID = "-1003804664180"

CHECK_INTERVAL = 15

LATEST_RSS = "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=40"

KEYWORDS = ["español", "spanish", "traduc", "traducción", "parche"]

seen_posts = set()
DATA_FILE = "f95_seen.json"

bot = Bot(token=TELEGRAM_TOKEN)

def get_session():
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    return s

session = get_session()

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        seen_posts = set(json.load(f))

async def send_telegram(title, link):
    msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Abrir en F95</a>"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.HTML)
        print(f"✅ Enviado: {title[:60]}")
    except:
        pass

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M')}] Revisando F95...")
        r = session.get(LATEST_RSS, timeout=20)
        root = ET.fromstring(r.text)
        
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            
            if title_elem is None or link_elem is None:
                continue
                
            title = title_elem.text.strip() if title_elem.text else ""
            link = link_elem.text if link_elem.text else ""
            
            if not link or post_id in seen_posts or not title:
                continue
                
            post_id = link.split('.')[-1] if '.' in link else ""
            
            if not any(k in title.lower() for k in KEYWORDS):
                continue
                
            print(f"✅ Detectado en Español: {title[:60]}")
            asyncio.run(send_telegram(title, link))
            seen_posts.add(post_id)
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    schedule.every(CHECK_INTERVAL).minutes.do(check_updates)
    print("🚀 Monitor F95 Español iniciado en Railway")
    check_updates()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
