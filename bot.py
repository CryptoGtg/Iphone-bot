import os
import requests
import json
from bs4 import BeautifulSoup

# ================== НАЛАШТУВАННЯ ==================

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

URLS = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-13/",
]

MAX_PRICE_IPHONE_11 = 300   # ТЕСТОВО (потім поставиш 300)
MAX_PRICE_IPHONE_13 = 950   # ТЕСТОВО (потім поставиш 950)

# ==================================================


def send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": TG_CHAT,
            "text": text,
            "disable_web_page_preview": True
        }
    )



# ---------- ЗАВАНТАЖЕНІ ОГОЛОШЕННЯ ----------
try:
    with open("data.json", "r") as f:
        seen = json.load(f)["seen"]
except:
    seen = []

new_seen = seen.copy()

headers = {
    "User-Agent": "Mozilla/5.0"
}

# ---------- ОСНОВНИЙ ЦИКЛ ----------
for url in URLS:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select("a[href*='/d/oferta/']")

    for item in items:
        title = item.get_text(strip=True)
        link = item.get("href")

        if not link:
            continue

        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        # пробуємо витягти ціну
        price_tag = item.find_next("p")
        price_text = price_tag.get_text(strip=True) if price_tag else ""

        digits = "".join(ch for ch in price_text if ch.isdigit())
        price_value = int(digits) if digits else 0

        title_lower = title.lower()

        is_iphone_11 = "iphone 11" in title_lower
        is_iphone_13 = "iphone 13" in title_lower

        ok = (
            (is_iphone_11 and price_value <= MAX_PRICE_IPHONE_11) or
            (is_iphone_13 and price_value <= MAX_PRICE_IPHONE_13)
        )

        if ok and link not in seen:
            message = (
                f"📱 {title}\n"
                f"💰 {price_text}\n"
                f"🌍 OLX Polska\n"
                f"🔗 {link}"
            )
            send(message)
            new_seen.append(link)

# ---------- ЗАПИСУЄМО ПОБАЧЕНЕ ----------
with open("data.json", "w") as f:
    json.dump({"seen": new_seen}, f)
