import os
import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# ================== ENV ==================

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT = os.environ.get("TG_CHAT")

ALLEGRO_CLIENT_ID = os.environ.get("ALLEGRO_CLIENT_ID")
ALLEGRO_CLIENT_SECRET = os.environ.get("ALLEGRO_CLIENT_SECRET")
ALLEGRO_REFRESH_TOKEN = os.environ.get("ALLEGRO_REFRESH_TOKEN")

DATA_FILE = Path("data.json")
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================== HELPERS ==================

def send(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "text": msg, "disable_web_page_preview": True},
        timeout=20
    )

def load_seen():
    if DATA_FILE.exists():
        return set(json.loads(DATA_FILE.read_text()).get("seen", []))
    return set()

def save_seen(seen):
    DATA_FILE.write_text(json.dumps({"seen": list(seen)}, ensure_ascii=False))

def price_int(text):
    return int("".join(c for c in text if c.isdigit())) if text else 0

# ================== ALLEGRO TOKEN ==================

def allegro_access_token():
    r = requests.post(
        "https://allegro.pl/auth/oauth/token",
        auth=(ALLEGRO_CLIENT_ID, ALLEGRO_CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": ALLEGRO_REFRESH_TOKEN
        },
        timeout=20
    )
    r.raise_for_status()
    return r.json()["access_token"]

# ================== OLX ==================

def run_olx(seen):
    url = "https://www.olx.pl/elektronika/telefony/q-iphone-11/"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=30).text, "html.parser")

    for a in soup.select("a[href*='/d/oferta/']"):
        title = a.get_text(" ", strip=True).lower()
        if "iphone 11" not in title:
            continue
        if any(x in title for x in ["etui", "case", "szkło", "glass"]):
            continue

        link = a.get("href")
        if not link:
            continue
        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        if link in seen:
            continue

        price_tag = a.find_next("p")
        price = price_int(price_tag.get_text() if price_tag else "")
        if price == 0 or price > 300:
            continue

        # перевірка Варшави
        if "warszawa" not in requests.get(link, headers=HEADERS, timeout=20).text.lower():
            continue

        send(
            f"🔵 OLX\n"
            f"📱 iPhone 11\n"
            f"💰 {price} zł\n"
            f"📍 Warszawa\n"
            f"🔗 {link}"
        )
        seen.add(link)
        time.sleep(1)

# ================== ALLEGRO ==================

def run_allegro(seen):
    token = allegro_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }

    models = [
        "iphone 11",
        "iphone 12 pro",
        "iphone 12 pro max",
        "iphone 13",
        "iphone 14",
        "iphone 15"
    ]

    for q in models:
        r = requests.get(
            "https://api.allegro.pl/offers/listing",
            headers=headers,
            params={"phrase": q, "limit": 20, "sort": "-startTime"},
            timeout=30
        )
        if r.status_code != 200:
            continue

        for it in r.json().get("items", {}).get("regular", []):
            title = it["name"].lower()
            if any(x in title for x in ["etui", "case", "szkło", "glass", "mini"]):
                continue

            price = float(it["sellingMode"]["price"]["amount"])
            if "iphone 11" in title:
                if price > 300:
                    continue
            else:
                if price > 950:
                    continue

            city = it.get("location", {}).get("city", "").lower()
            if city != "warszawa":
                continue

            link = f"https://allegro.pl/oferta/{it['id']}"
            if link in seen:
                continue

            send(
                f"🟠 ALLEGRO\n"
                f"📱 {it['name']}\n"
                f"💰 {price} zł\n"
                f"📍 Warszawa\n"
                f"🔗 {link}"
            )
            seen.add(link)

# ================== MAIN ==================

def main():
    seen = load_seen()
    run_olx(seen)
    run_allegro(seen)
    save_seen(seen)

if __name__ == "__main__":
    main()
