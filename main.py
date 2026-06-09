import requests
import os
from datetime import datetime
from telegram import Bot
import asyncio
import xml.etree.ElementTree as ET

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Revisando F95Zone...")
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=50",
            timeout=20,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        root = ET.fromstring(r.text)
        
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            
            if title_elem is None or link_elem is None:
                continue
                
            title = (title_elem.text or "").strip()
            link = (link_elem.text or "").strip()
            
            if not title or not link:
                continue
                
            post_id = link.split('.')[-1] if '.' in link else ""
            
            if any(k in title.lower() for k in ["español", "spanish", "traduc", "traducción", "parche"]):
                print(f"✅ Detectado en Español: {title[:70]}")
                msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n\n🔗 <a href='{link}'>Abrir en F95</a>"
                asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML'))
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_updates()
