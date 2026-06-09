import requests
import time
import schedule
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN = "8696663106:AAGQxUIswl8sSJUcXHjaRDpduRoh6bhlx-s"
CHAT_ID = "-1003804664180"

CHECK_INTERVAL = 20

LATEST_RSS = "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=30"

KEYWORDS = ["español", "spanish", "traduc", "traducción", "parche"]

seen_posts = set()

bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram(title, link):
    msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Abrir en F95</a>"
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode=ParseMode.HTML))
        print(f"✅ Enviado: {title[:60]}")
    except:
        pass

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M')}] Revisando F95...")
        r = requests.get(LATEST_RSS, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        
        if r.status_code != 200:
            print(f"HTTP Error: {r.status_code}")
            return

        root = ET.fromstring(r.text)
        
        for item in root.findall(".//item"):
            title = (item.find("title").text or "").strip()
            link = (item.find("link").text or "").strip()
            
            if not title or not link:
                continue
                
            post_id = link.split('.')[-1] if '.' in link else ""
            
            if post_id in seen_posts:
                continue
                
            if any(k in title.lower() for k in KEYWORDS):
                print(f"✅ Detectado en Español: {title[:70]}")
                send_telegram(title, link)
                seen_posts.add(post_id)
                
    except Exception as e:
        print(f"Error: {e}")

def main():
    schedule.every(CHECK_INTERVAL).minutes.do(check_updates)
    print("🚀 Monitor F95 Español - Railway vFinal")
    print("Manteniendo servicio activo...")
    
    check_updates()  # Primera revisión
    
    # Mantener el proceso vivo
    while True:
        schedule.run_pending()
        time.sleep(30)   # Sleep más corto para Railway

if __name__ == "__main__":
    main()
