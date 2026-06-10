import requests
import os
from datetime import datetime
from telegram import Bot
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
seen_posts = set()

def send_test_message():
    try:
        bot.send_message(chat_id=CHAT_ID, text="🧪 TEST - El monitor está funcionando correctamente.\nSi ves este mensaje, el bot tiene permisos.", parse_mode='HTML')
        print("✅ Mensaje de prueba enviado")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Error en mensaje de prueba: {e}")

def get_thread_details(thread_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        text_lower = soup.get_text().lower()
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, version
    except:
        return False, "Desconocida"

def send_notification(title, link, version):
    try:
        msg = f"<b>🎮 Nuevo/Actualizado en Español</b>\n\n<b>{title}</b>\n📌 Versión: {version}\n\n🔗 <a href='{link}'>Abrir en F95</a>"
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        print(f"✅ Enviado: {title[:60]}")
        time.sleep(3)   # Delay largo
        return True
    except Exception as e:
        print(f"❌ Error enviando: {e}")
        time.sleep(5)
        return False

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

            has_spanish, version = get_thread_details(link)
            
            if has_spanish:
                print(f"🎯 ¡ESPAÑOL DETECTADO!: {title}")
                if send_notification(title, link, version):
                    seen_posts.add(post_id)
                    count += 1
                    
        print(f"✅ Revisión terminada. Encontrados {count} juegos.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - VERSIÓN FINAL v5")
    send_test_message()   # Mensaje de prueba
    check_updates()
