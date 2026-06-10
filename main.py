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

def send_telegram_message(text):
    """Envía mensaje usando API oficial de Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram")
            return True
        else:
            print(f"❌ Error Telegram API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def get_thread_details(thread_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        text_lower = soup.get_text().lower()
        
        keywords = ["spanish", "español", "castellano", "traducido al español", "parche español"]
        has_spanish = any(kw in text_lower for kw in keywords)
        
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, version
    except:
        return False, "Desconocida"

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

            print(f"🔍 Analizando: {title[:80]}...")
            has_spanish, version = get_thread_details(link)
            
            if has_spanish:
                print(f"🎯 ¡ESPAÑOL DETECTADO!: {title}")
                msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n📌 Versión: {version}\n\n🔗 <a href='{link}'>Abrir en F95</a>"
                send_telegram_message(msg)
                seen_posts.add(post_id)
                count += 1
                time.sleep(3)
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos en español.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - API Oficial de Telegram")
    send_telegram_message("🧪 TEST - Sistema usando API Oficial de Telegram iniciado.")
    check_updates()
