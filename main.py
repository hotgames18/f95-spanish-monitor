import requests
import os
from datetime import datetime
from telegram import Bot, InputMediaPhoto
import asyncio
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
seen_posts = set()

def get_thread_details(thread_url):
    """Extrae información detallada del hilo"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(thread_url, headers=headers, timeout=25)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Imagen de portada
        img_tag = soup.find('img', class_='bbImage') or soup.find('meta', property='og:image')
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else img_tag['content'] if img_tag else None
        
        text = soup.get_text().lower()
        
        # Languages
        has_spanish = any(word in text for word in ["spanish", "español", "castellano"])
        
        # Versión
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, version, image_url
        
    except:
        return False, "Desconocida", None

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Revisando F95Zone...")
        
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=50",
            timeout=25,
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
            
            if post_id in seen_posts:
                continue

            # Primera pasada rápida
            lower_title = title.lower()
            if not any(kw in lower_title for kw in ["español", "spanish", "traduc", "traducción"]):
                continue

            # Segunda pasada profunda
            print(f"🔍 Analizando hilo: {title[:70]}...")
            has_spanish, version, image_url = get_thread_details(link)
            
            if has_spanish:
                print(f"🎯 ¡ESPAÑOL DETECTADO!: {title}")
                
                msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n"
                msg += f"<b>{title}</b>\n"
                msg += f"📌 Versión: {version}\n"
                msg += f"🔗 <a href='{link}'>Abrir Hilo en F95</a>"
                
                try:
                    if image_url:
                        asyncio.run(bot.send_photo(chat_id=CHAT_ID, photo=image_url, caption=msg, parse_mode='HTML'))
                    else:
                        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML'))
                except:
                    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML'))
                
                seen_posts.add(post_id)
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español vAvanzada - GitHub Actions")
    check_updates()
