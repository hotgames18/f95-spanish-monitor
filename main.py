import requests
import os
from datetime import datetime
from telegram import Bot
import xml.etree.ElementTree as ET
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
seen_posts = set()

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando F95Zone...")
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=50",
            timeout=20,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        root = ET.fromstring(r.text)
        
        for item in root.findall(".//item"):
            title = (item.find("title").text or "").strip()
            link = (item.find("link").text or "").strip()
            
            if not title or not link:
                continue
                
            post_id = link.split('.')[-1] if '.' in link else ""
            if post_id in seen_posts:
                continue

            lower_title = title.lower()
            if any(kw in lower_title for kw in ["español", "spanish", "traduc", "traducción", "parche"]):
                msg = f"<b>🎮 Nuevo en Español</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Abrir en F95</a>"
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
                print(f"✅ Enviado: {title[:60]}")
                seen_posts.add(post_id)
                time.sleep(3)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - NUEVO BOT Y CANAL")
    bot.send_message(chat_id=CHAT_ID, text="🧪 TEST - Nuevo sistema iniciado correctamente.\nSi ves este mensaje, todo funciona.")
    check_updates()
