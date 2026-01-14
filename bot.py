import os
import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

URLS = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-12-pro/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-13/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-14/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-15/",
]

# Макс ціни: ти просив "по тим же цінам" — залишаю 11=300, 13=950.
# Для 12 Pro/Pro Max ставлю як було в попередньому варіанті (600) — можеш змінити.
MAX_PRICE = {
    # 11 — вся Польща
    "iphone 11 pro max": 300,
    "iphone 11 pro": 300,
    "iphone 11": 300,

    # 12 — тільки Pro та Pro Max (і тільки Варшава)
    "iphone 12 pro max": 600,
    "iphone 12 pro": 600,

    # 13 — тільки Варшава (без mini)
    "iphone 13 pro max": 950,
    "iphone 13 pro": 950,
    "iphone 13": 950,

    # 14/15 — тільки Варшава (ціни залишив “заглушками”, підкоригуєш якщо треба)
    "iphone 14 pro max": 1200,
    "iphone 14 pro": 1200,
    "iphone 14 plus": 1200,
    "iphone 14": 1200,

    "iphone 15 pro max": 1500,
    "iphone 15 pro": 1500,
    "iphone 15 plus": 1500,
    "iphone 15": 1500,
}

# ❌ аксесуари
BLOCKED_WORDS = [
    "case", "cover", "szkło", "szklo", "etui",
    "futerał", "futeral", "glass",
    "hartowane", "pokrowiec", "obudowa",
    "ładowarka", "kabel", "charger", "cable"
]

DATA_FILE = Path("data.json")

def send(text: str):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True},
        timeout=20
    )

def normalize_price(text: str) -> int:
    digits = "".join(c for c in text if c.isdigit())
    return int(digits) if digits else 0

# ---------- load seen ----------
try:
    seen_list = json.loads(DATA_FILE.read_text(encoding="utf-8")).get("seen", [])
except Exception:
    seen_list = []
seen = set(seen_list)

headers = {"User-Agent": "Mozilla/5.0"}

for url in URLS:
    html = requests.get(url, headers=headers, timeout=25).text
    soup = BeautifulSoup(html, "html.parser")

    for item in soup.select("a[href*='/d/oferta/']"):
        title = item.get_text(" ", strip=True)
        title_l = title.lower()

        # ❌ не треба mini і не треба звичайні 12
        if "mini" in title_l:
            continue
        if "iphone 12" in title_l and ("pro" not in title_l):
            continue

        # ❌ аксесуари
        if any(w in title_l for w in BLOCKED_WORDS):
            continue

        link = item.get("href") or ""
        if not link:
            continue
        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        if link in seen:
            continue

        # ціна
        price_tag = item.find_next("p")
        price_text = price_tag.get_text(strip=True) if price_tag else ""
        price_val = normalize_price(price_text)

        # місто (для Варшави)
        city_tag = item.find_next("span")
        city = city_tag.get_text(strip=True) if city_tag else ""
        city_l = city.lower()

        # визначаємо модель (беремо найдовший збіг першим)
        matched = None
        for key in sorted(MAX_PRICE.keys(), key=len, reverse=True):
            if key in title_l:
                matched = key
                break
        if not matched:
            continue

        # фільтр по ціні
        if price_val <= 0 or price_val > MAX_PRICE[matched]:
            continue

        # 📍 Варшава для 12 Pro/Pro Max і для всіх 13+
        if (
            matched.startswith("iphone 12 pro")
            or matched.startswith("iphone 13")
            or matched.startswith("iphone 14")
            or matched.startswith("iphone 15")
        ):
            if "warszawa" not in city_l:
                continue

        # якщо дійшли сюди — надсилаємо
        send(
            f"📱 {title}\n"
            f"💰 {price_text}\n"
            f"📍 {city}\n"
            f"🔗 {link}"
        )

        seen.add(link)

# ---------- save seen ----------
DATA_FILE.write_text(json.dumps({"seen": list(seen)}, ensure_ascii=False), encoding="utf-8")
