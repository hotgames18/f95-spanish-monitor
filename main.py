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

def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
        print(f"✅ Mensaje enviado a Telegram")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Error real enviando a Telegram: {e}")
        time.sleep(5)
        return False

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando F95Zone...")
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=60",
            timeout=25,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        root = ET.fromstring(r.text)
        count = 0
        
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
                msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Abrir en F95</a>"
                
                if send_message(msg):
                    seen_posts.add(post_id)
                    count += 1
                    
        print(f"✅ Revisión terminada. Encontrados {count} juegos en español.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - VERSIÓN FINAL LIMPIA")
    send_message("🧪 TEST FINAL - Si ves este mensaje en el canal, el sistema funciona.")
    check_updates()
