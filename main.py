import requests
import os
import json
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
F95_COOKIE = os.getenv("F95_COOKIE") # NUEVO: Tu cookie de sesión
MEMORY_FILE = "memoria.json"
MAX_MEMORY = 500

# Headers que simulan un navegador real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
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
            print("✅ Enviado a Telegram")
            time.sleep(2.5)
            return True
        else:
            print(f"❌ Error Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Excepción enviando mensaje: {e}")
        return False

def get_thread_details(session, thread_url):
    try:
        # Usamos la misma sesión con cookies para evitar bloqueos al entrar al hilo
        r = session.get(thread_url, headers=HEADERS, timeout=20)
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
    if not F95_COOKIE:
        print("❌ CRÍTICO: Falta la variable de entorno F95_COOKIE en GitHub Secrets.")
        sys.exit(1)

    # Creamos una sesión persistente para guardar las cookies
    session = requests.Session()
    # Inyectamos tu cookie real
    session.cookies.set('xf_user', F95_COOKIE)
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando F95Zone (What's New)...")
        
        # URL pública de "What's New" filtrada por hilos (requiere login, por eso usamos la sesión)
        url_wn = "https://f95zone.to/whats-new/posts/?type=post"
        r = session.get(url_wn, headers=HEADERS, timeout=25)
        
        if r.status_code != 200:
            print(f"❌ CRÍTICO: F95Zone devolvió HTTP {r.status_code}. La cookie podría haber expirado.")
            sys.exit(1)
            
        # Verificar que no nos redirigió al login (a veces pasa si la cookie es inválida)
        if "login" in r.url.lower():
            print("❌ CRÍTICO: F95Zone redirigió al login. La cookie F95_COOKIE no es válida o expiró.")
            sys.exit(1)

        soup = BeautifulSoup(r.text, 'html.parser')
        count = 0
        
        # XenForo usa la clase 'structItem-title' para los títulos de los hilos en What's New
        threads = soup.find_all('a', class_='structItem-title')
        print(f"🔍 Encontrados {len(threads)} hilos recientes en la página.")
        
        for thread in threads:
            title = thread.text.strip()
            link = thread.get('href', '')
            
            # Asegurar que la URL sea absoluta
            if link.startswith('/'):
                link = "https://f95zone.to" + link
                
            # Extraer el ID del hilo (ej: /threads/game-name.12345/ -> 12345)
            post_id_match = re.search(r'threads/[^.]+\.(\d+)', link)
            post_id = post_id_match.group(1) if post_id_match else ""
            
            if not post_id or post_id in seen_posts:
                continue
            
            print(f"🔍 Analizando: {title[:60]}...")
            has_spanish, has_android, version = get_thread_details(session, link)
            
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
        print(f"❌ Error general no manejado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Monitor F95 Español + Android - Versión con Cookie de Sesión")
    if not TOKEN or not CHAT_ID:
        print("❌ Faltan variables de entorno TELEGRAM_TOKEN o CHAT_ID")
        sys.exit(1)
    check_updates()
