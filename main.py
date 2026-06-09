import requests
import os
from datetime import datetime
from telegram import Bot
import asyncio
import xml.etree.ElementTree as ET
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
seen_posts = set()

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Revisando actualizaciones en F95Zone...")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=50",
            timeout=25,
            headers=headers
        )
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code}")
            return

        root = ET.fromstring(r.text)
        found_count = 0

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
            
            if post_id in seen_posts:
                continue

            # Detección mejorada
            lower_title = title.lower()
            if any(kw in lower_title for kw in ["español", "spanish", "traduc", "traducción", "parche español", "castellano"]):
                print(f"🎯 DETECTADO EN ESPAÑOL: {title[:80]}")
                
                msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n"
                msg += f"<b>{title}</b>\n\n"
                msg += f"🔗 <a href='{link}'>Abrir en F95Zone</a>"
                
                asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML'))
                seen_posts.add(post_id)
                found_count += 1

        print(f"✅ Revisión completada. Encontrados: {found_count} nuevos en español.")

    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español v2.0 - GitHub Actions")
    check_updates()
