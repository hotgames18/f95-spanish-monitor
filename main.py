import requests
import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MEMORY_FILE = "memoria.json"
MAX_MEMORY = 500  # Guardaremos solo los últimos 500 juegos para no hacer el archivo gigante

# --- FUNCIONES DE MEMORIA ---
def load_seen():
    """Carga los IDs ya enviados desde el archivo memoria.json"""
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return set(data)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si el archivo no existe o está vacío, empezamos con set vacío
        return set()

def save_seen(seen_set):
    """Guarda los IDs en el archivo memoria.json"""
    # Convertimos el set a lista y nos quedamos solo con los últimos MAX_MEMORY elementos
    seen_list = list(seen_set)[-MAX_MEMORY:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(seen_list, f)

# Cargamos la memoria al arrancar
seen_posts = load_seen()

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(thread_url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        text_lower = soup.get_text().lower()
        
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        has_android = ("android" in text_lower) or (".apk" in text_lower)
        
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
            
            if has_spanish and has_android:
                print(f"🎯 ¡ESPAÑOL + ANDROID DETECTADO!: {title}")
                msg = f"<b>📱 Nuevo/Actualizado en Español (Android)</b>\n\n"
                msg += f"<b>{title}</b>\n"
                msg += f"📌 Versión: {version}\n\n"
                msg += f"🔗 <a href='{link}'>Abrir en F95Zone</a>"
                send_message(msg)
                seen_posts.add(post_id)
                count += 1
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos nuevos.")
        # Al terminar, guardamos la memoria actualizada
        save_seen(seen_posts)
        print(f"💾 Memoria guardada ({len(seen_posts)} IDs guardados).")
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    print("🚀 Monitor F95 Español + Android - Versión con Memoria")
    check_updates()
