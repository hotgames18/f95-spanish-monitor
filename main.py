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
F95_COOKIE = os.getenv("F95_COOKIE")
MEMORY_FILE = "memoria.json"
MAX_MEMORY = 500

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache'
}

WN_URL = "https://f95zone.to/whats-new/posts/?type=post"

def load_seen():
    try:
        with open(MEMORY_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen(seen_set):
    with open(MEMORY_FILE, "w") as f:
        json.dump(list(seen_set)[-MAX_MEMORY:], f)

seen_posts = load_seen()

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Enviado a Telegram")
            time.sleep(2.5)
            return True
        print(f"❌ Error Telegram: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Excepción enviando mensaje: {e}")
        return False

def get_thread_details(session, thread_url):
    try:
        r = session.get(thread_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return False, False, "Desconocida"
        soup = BeautifulSoup(r.text, 'html.parser')
        text_lower = soup.get_text().lower()
        has_spanish = any(kw in text_lower for kw in ["spanish", "español", "castellano", "traducido al español", "parche español"])
        has_android = ("android" in text_lower) or (".apk" in text_lower)
        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', text_lower)
        return has_spanish, has_android, (version_match.group(0) if version_match else "Desconocida")
    except Exception:
        return False, False, "Desconocida"

def extract_threads(soup):
    found = {}
    for a in soup.find_all('a', href=True):
        m = re.search(r'/threads/[^/]+\.(\d+)', a['href'])
        if not m:
            continue
        pid = m.group(1)
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        if pid not in found:
            link = a['href']
            if link.startswith('/'):
                link = "https://f95zone.to" + link
            found[pid] = (title, link)
    return found

def check_updates():
    if not F95_COOKIE:
        print("❌ CRÍTICO: Falta F95_COOKIE en GitHub Secrets.")
        sys.exit(1)

    session = requests.Session()
    session.cookies.set('xf_user', F95_COOKIE)
    session.cookies.set('xf_nojs', '0')

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Revisando F95Zone (What's New - Posts)...")
        r = session.get(WN_URL, headers=HEADERS, timeout=25)

        if r.status_code != 200:
            print(f"❌ CRÍTICO: F95Zone devolvió HTTP {r.status_code}.")
            sys.exit(1)

        if "login" in r.url.lower():
            print("❌ CRÍTICO: F95Zone redirigió al login. La cookie expiró.")
            sys.exit(1)

        soup = BeautifulSoup(r.text, 'html.parser')
        threads = extract_threads(soup)
        print(f"🔍 Encontrados {len(threads)} hilos recientes en la página.")

        if len(threads) == 0:
            print("⚠️ DEBUG: 0 hilos. Primeros 400 chars del HTML:")
            print(r.text[:400].replace('\n', ' '))

        count = 0
        for pid, (title, link) in threads.items():
            if pid in seen_posts:
                continue
            print(f"🔍 Analizando: {title[:60]}...")
            has_spanish, has_android, version = get_thread_details(session, link)
            if has_spanish and has_android:
                print(f"🎯 ¡ESPAÑOL + ANDROID DETECTADO!: {title}")
                msg = (f"<b>📱 Nuevo/Actualizado en Español (Android)</b>\n\n"
                       f"<b>{title}</b>\n📌 Versión: {version}\n\n"
                       f"🔗 <a href='{link}'>Abrir en F95Zone</a>")
                if send_message(msg):
                    seen_posts.add(pid)
                    count += 1

        print(f"✅ Revisión terminada. Encontrados {count} juegos nuevos.")
        save_seen(seen_posts)
        print(f"💾 Memoria guardada ({len(seen_posts)} IDs).")

    except Exception as e:
        print(f"❌ Error general no manejado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Monitor F95 Español + Android - Versión Robusta (URL verificada + patron de enlace)")
    if not TOKEN or not CHAT_ID:
        print("❌ Faltan TELEGRAM_TOKEN o CHAT_ID")
        sys.exit(1)
    check_updates()
