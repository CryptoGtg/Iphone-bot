import os
import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

URLS = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-13/"
]

MAX_PRICE_11 = 300
MAX_PRICE_13 = 950

BLOCKED_WORDS = [
    "case", "cover", "szkło", "szklo", "etui", "futerał", "futeral",
    "glass", "hartowane", "pokrowiec", "obudowa"
]

DATA_FILE = Path("data.json")

def send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": text})

# ---------- load seen ----------
if DATA_FILE.exists():
    seen = json.loads(DATA_FILE.read_text()).get("seen", [])
else:
    seen = []

new_seen = set(seen)

headers = {"User-Agent": "Mozilla/5.0"}

for url in URLS:
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    items = soup.select("a[href*='/d/oferta/']")

    for item in items:
        title = item.get_text(" ", strip=True)
        title_l = title.lower()

        # ❌ аксесуари
        if any(word in title_l for word in BLOCKED_WORDS):
            continue

        link = item.get("href")
        if not link:
            continue
        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        if link in new_seen:
            continue

        # ціна
        price_tag = item.find_next("p")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        digits = "".join(c for c in price_text if c.isdigit())
        price = int(digits) if digits else 0

        # місто (для iPhone 13)
        city_tag = item.find_next("span")
        city = city_tag.get_text(strip=True) if city_tag else ""
        city_l = city.lower()

        is_11 = "iphone 11" in title_l
        is_13 = "iphone 13" in title_l

        if is_11 and price > MAX_PRICE_11:
            continue

        if is_13:
            if price > MAX_PRICE_13:
                continue
            if "warszawa" not in city_l:
                continue

        if not (is_11 or is_13):
            continue

        send(
            f"📱 {title}\n"
            f"💰 {price_text}\n"
            f"📍 {city}\n"
            f"🔗 {link}"
        )

        new_seen.add(link)

# ---------- save + commit ----------
DATA_FILE.write_text(json.dumps({"seen": list(new_seen)}, ensure_ascii=False))
