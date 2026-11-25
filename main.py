import requests
import os
import json
import sys
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MEMORY_FILE = "memoria.json"
MAX_MEMORY = 500

# Headers más robustos para evitar bloqueos básicos de Cloudflare
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/html',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache'
}

def load_seen():
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return set(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen_set):
    seen_list = list(seen_set)[-MAX_MEMORY:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(seen_list, f)

seen_posts = load_seen()

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Enviado")
            time.sleep(2.5)
            return True
        else:
            print(f"❌ Error Telegram: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Excepción enviando mensaje: {e}")
        return False

def get_thread_details(thread_url):
    try:
        r = requests.get(thread_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"⚠️ No se pudo acceder al hilo (HTTP {r.status_code})")
            return False, False, "Desconocida"
            
        soup = BeautifulSoup(r.text, 'html.parser')
        text_lower = soup.get_text().lower()
        
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        has_android = ("android" in text_lower) or (".apk" in text_lower)
        
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        version = version_match.group(0) if version_match else "Desconocida"
        
        return has_spanish, has_android, version
    except Exception as e:
        print(f"❌ Error obteniendo detalles del hilo: {e}")
        return False, False, "Desconocida"

def check_updates():
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando F95Zone...")
        r = requests.get(
            "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games&rows=60",
            timeout=25,
            headers=HEADERS
        )
        
        # BLINDAJE 1: Verificar que la respuesta sea exitosa antes de parsear
        if r.status_code != 200:
            print(f"❌ CRÍTICO: F95Zone devolvió HTTP {r.status_code}. Posible bloqueo de Cloudflare.")
            print(f"Respuesta: {r.text[:200]}...")
            sys.exit(1) # Esto hace que GitHub Actions falle en ROJO
            
        # BLINDAJE 2: Capturar errores de parseo XML por separado
        try:
            root = ET.fromstring(r.text)
        except ET.ParseError as xml_err:
            print(f"❌ CRÍTICO: Error al parsear XML. F95Zone probablemente devolvió HTML en lugar de RSS.")
            print(f"Detalle: {xml_err}")
            print(f"Contenido recibido: {r.text[:300]}...")
            sys.exit(1) # Fallar en ROJO
            
        count = 0
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            
            if title_elem is None or link_elem is None or not title_elem.text or not link_elem.text:
                continue
                
            title = title_elem.text.strip()
            link = link_elem.text.strip()
            
            post_id = link.split('.')[-1] if '.' in link else ""
            if post_id in seen_posts:
                continue
            
            print(f"🔍 Analizando: {title[:60]}...")
            has_spanish, has_android, version = get_thread_details(link)
            
            if has_spanish and has_android:
                print(f"🎯 ¡ESPAÑOL + ANDROID DETECTADO!: {title}")
                msg = f"<b>📱 Nuevo/Actualizado en Español (Android)</b>\n\n"
                msg += f"<b>{title}</b>\n"
                msg += f"📌 Versión: {version}\n\n"
                msg += f"🔗 <a href='{link}'>Abrir en F95Zone</a>"
                
                if send_message(msg):
                    seen_posts.add(post_id)
                    count += 1
                
        print(f"✅ Revisión terminada. Encontrados {count} juegos nuevos.")
        save_seen(seen_posts)
        print(f"💾 Memoria guardada ({len(seen_posts)} IDs).")
        
    except Exception as e:
        # Cualquier otro error no previsto también debe fallar el workflow
        print(f"❌ Error general no manejado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Monitor F95 Español + Android - Versión Blindada")
    if not TOKEN or not CHAT_ID:
        print("❌ Faltan variables de entorno TELEGRAM_TOKEN o CHAT_ID")
        sys.exit(1)
    check_updates()
