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

def get_thread_details(thread_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        text_lower = soup.get_text().lower()
        
        # Lógica de detección más fuerte
        keywords = [
            "spanish", "español", "castellano", "españa",
            "traducido", "traducción", "parche español",
            "idioma: spanish", "languages.*spanish", "language.*spanish"
        ]
        
        has_spanish = any(kw in text_lower for kw in keywords)
        
        # Buscar en sección Languages
        if not has_spanish:
            lang_match = re.search(r'languages?[:.\s-]*(.+?)(?:\n|$)', text_lower)
            if lang_match:
                lang_text = lang_match.group(1)
                has_spanish = any(word in lang_text for word in ["spanish", "español", "castellano"])
        
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, version
    except:
        return False, "Desconocida"

def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
        print("✅ Mensaje enviado")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Error enviando: {e}")
        time.sleep(5)
        return False

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando Latest Updates...")
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=80",
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
                send_message(msg)
                seen_posts.add(post_id)
                count += 1
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos en español.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español - VERSIÓN FINAL v7")
    send_message("🧪 TEST - Monitor reiniciado correctamente.")
    check_updates()
