import os
import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path
import time

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

URLS = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-12-pro/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-13/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-14/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-15/",
]

MAX_PRICE = {
    # 11 — вся Польща
    "iphone 11 pro max": 300,
    "iphone 11 pro": 300,
    "iphone 11": 300,

    # інші — тільки Варшава
    "iphone 12 pro max": 950,
    "iphone 12 pro": 950,

    "iphone 13 pro max": 950,
    "iphone 13 pro": 950,
    "iphone 13": 950,

    "iphone 14 pro max": 950,
    "iphone 14 pro": 950,
    "iphone 14 plus": 950,
    "iphone 14": 950,

    "iphone 15 pro max": 950,
    "iphone 15 pro": 950,
    "iphone 15 plus": 950,
    "iphone 15": 950,
}

BLOCKED_WORDS = [
    "case", "cover", "szkło", "szklo", "etui",
    "futerał", "futeral", "glass", "hartowane",
    "pokrowiec", "obudowa", "ładowarka",
    "kabel", "charger", "cable"
]

DATA_FILE = Path("data.json")

def send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True},
        timeout=20
    )

def price_to_int(text):
    digits = "".join(c for c in text if c.isdigit())
    return int(digits) if digits else 0

def get_city_from_ad(url):
    """Беремо РЕАЛЬНЕ місто зсередини оголошення"""
    try:
        html = requests.get(url, headers=headers, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        for span in soup.select("span"):
            txt = span.get_text(strip=True).lower()
            if "warszawa" in txt:
                return "warszawa"
        return ""
    except:
        return ""

# ---------- load seen ----------
try:
    seen = set(json.loads(DATA_FILE.read_text(encoding="utf-8")).get("seen", []))
except:
    seen = set()

headers = {"User-Agent": "Mozilla/5.0"}

for url in URLS:
    soup = BeautifulSoup(
        requests.get(url, headers=headers, timeout=25).text,
        "html.parser"
    )

    for item in soup.select("a[href*='/d/oferta/']"):
        title = item.get_text(" ", strip=True)
        title_l = title.lower()

        # ❌ mini та базовий 12
        if "mini" in title_l:
            continue
        if "iphone 12" in title_l and "pro" not in title_l:
            continue

        # ❌ аксесуари
        if any(w in title_l for w in BLOCKED_WORDS):
            continue

        link = item.get("href")
        if not link:
            continue
        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        if link in seen:
            continue

        price_tag = item.find_next("p")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price_val = price_to_int(price_text)

        matched = None
        for key in sorted(MAX_PRICE.keys(), key=len, reverse=True):
            if key in title_l:
                matched = key
                break

        if not matched:
            continue
        if price_val <= 0 or price_val > MAX_PRICE[matched]:
            continue

        # 📍 ПЕРЕВІРКА МІСТА ВСЕРЕДИНІ ОГОЛОШЕННЯ
        if not matched.startswith("iphone 11"):
            city = get_city_from_ad(link)
            time.sleep(1)  # щоб OLX не злився
            if city != "warszawa":
                continue

        send(
            f"📱 {title}\n"
            f"💰 {price_text}\n"
            f"📍 Warszawa\n"
            f"🔗 {link}"
        )

        seen.add(link)

# ---------- save ----------
DATA_FILE.write_text(
    json.dumps({"seen": list(seen)}, ensure_ascii=False),
    encoding="utf-8"
)
