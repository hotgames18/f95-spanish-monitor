import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

seen_posts = set()

def send_rich_notification(title, link, version, image_url=None):
    try:
        msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n"
        msg += f"<b>{title}</b>\n"
        msg += f"📌 Versión: <b>{version}</b>\n\n"
        msg += f"🔗 <a href='{link}'>Abrir en F95Zone</a>"
        
        if image_url and image_url.startswith('http'):
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "photo": image_url,
                "caption": msg,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload, timeout=15)
            print(f"✅ Enviado con imagen: {title[:60]}")
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload, timeout=10)
            print(f"✅ Enviado sin imagen: {title[:60]}")
        
        time.sleep(2.5)
        return True
    except Exception as e:
        print(f"❌ Error enviando: {e}")
        return False

def get_thread_details(thread_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extraer imagen (miniatura)
        image_url = None
        img = soup.find('img', {'class': 'bbImage'}) or soup.find('meta', {'property': 'og:image'})
        if img:
            image_url = img.get('src') or img.get('content')
        
        text_lower = soup.get_text().lower()
        
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, version, image_url
    except:
        return False, "Desconocida", None

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando...")
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

            print(f"🔍 Analizando: {title[:75]}...")
            has_spanish, version, image_url = get_thread_details(link)
            
            if has_spanish:
                print(f"🎯 ¡ESPAÑOL DETECTADO!: {title}")
                send_rich_notification(title, link, version, image_url)
                seen_posts.add(post_id)
                count += 1
                time.sleep(3)
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - Versión con Miniaturas")
    send_rich_notification("TEST - Monitor con imágenes", "https://f95zone.to", "v1.0")
    check_updates()
