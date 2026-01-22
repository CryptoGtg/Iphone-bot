import os
import requests
import json
import time
from bs4 import BeautifulSoup
from pathlib import Path

# ================= CONFIG =================

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]
ALLEGRO_TOKEN = os.environ["ALLEGRO_TOKEN"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

ALLEGRO_HEADERS = {
    "Authorization": f"Bearer {ALLEGRO_TOKEN}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

DATA_FILE = Path("data.json")

# ================= HELPERS =================

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "text": msg, "disable_web_page_preview": True},
        timeout=20
    )

def price_int(txt):
    return int("".join(c for c in txt if c.isdigit())) if txt else 0

def is_warszawa_olx(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=30).text.lower()
        return "warszawa" in html
    except:
        return False

# ================= LOAD SEEN =================

try:
    seen = set(json.loads(DATA_FILE.read_text()).get("seen", []))
except:
    seen = set()

# ================= OLX =================

OLX_URLS = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/"
]

for url in OLX_URLS:
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=40).text,
        "html.parser"
    )

    for a in soup.select("a[href*='/d/oferta/']"):
        try:
            title = a.get_text(" ", strip=True).lower()

            if "mini" in title:
                continue
            if "iphone 11" not in title:
                continue
            if any(x in title for x in ["case", "etui", "szkło", "glass"]):
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

            if not is_warszawa_olx(link):
                continue

            send(
                f"🔵 OLX\n"
                f"📱 {a.get_text(strip=True)}\n"
                f"💰 {price} zł\n"
                f"📍 Warszawa\n"
                f"🔗 {link}"
            )

            seen.add(link)
            time.sleep(1)

        except:
            continue

# ================= ALLEGRO =================

ALLEGRO_QUERIES = [
    "iphone 11",
    "iphone 12 pro",
    "iphone 13",
    "iphone 14",
    "iphone 15"
]

for q in ALLEGRO_QUERIES:
    params = {
        "phrase": q,
        "limit": 20,
        "sort": "-startTime"
    }

    r = requests.get(
        "https://api.allegro.pl/offers/listing",
        headers=ALLEGRO_HEADERS,
        params=params,
        timeout=30
    )

    if r.status_code != 200:
        continue

    items = r.json().get("items", {}).get("regular", [])

    for it in items:
        try:
            title = it["name"].lower()

            if "mini" in title:
                continue
            if any(x in title for x in ["case", "etui", "szkło", "glass"]):
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

        except:
            continue

# ================= SAVE =================

DATA_FILE.write_text(json.dumps({"seen": list(seen)}, ensure_ascii=False))
