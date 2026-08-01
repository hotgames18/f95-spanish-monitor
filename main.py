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

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_page": True
        }
        requests.post(url, json=payload, timeout=10)
        print("✅ Enviado")
        time.sleep(2.5)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(4)
        return False

def get_thread_details(thread_url):
    try:
        # Un User-Agent un poco más completo para evitar bloqueos básicos
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        text_lower = soup.get_text().lower()
        
        # 1. Detección de Español
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        
        # 2. Detección de Android
        # Buscamos la palabra "android" o la extensión ".apk" en el texto de la página
        has_android = ("android" in text_lower) or (".apk" in text_lower)
        
        # 3. Detección de Versión
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, has_android, version
    except Exception as e:
        print(f"❌ Error obteniendo detalles: {e}")
        return False, False, "Desconocida"

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
            
            print(f"🔍 Analizando: {title[:80]}...")
            has_spanish, has_android, version = get_thread_details(link)
            
            # Condición: Debe tener español Y estar disponible para Android
            if has_spanish and has_android:
                print(f"🎯 ¡ESPAÑOL + ANDROID DETECTADO!: {title}")
                msg = f"<b>📱 Nuevo/Actualizado en Español (Android)</b>\n\n"
                msg += f"<b>{title}</b>\n"
                msg += f"📌 Versión: {version}\n\n"
                msg += f"🔗 <a href='{link}'>Abrir en F95Zone</a>"
                send_message(msg)
                seen_posts.add(post_id)
                count += 1
            else:
                # Opcional: para debug, ver por qué no pasó el filtro
                # if has_spanish and not has_android:
                #     print(f"   ⏭️ Descartado (No es Android): {title[:60]}")
                pass
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos en español para Android.")
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español + Android - Versión Simple y Estable")
    send_message("🧪 Monitor reiniciado correctamente (Buscando Español + Android)")
    check_updates()
