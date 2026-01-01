import os
import requests
import json
from bs4 import BeautifulSoup

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

def send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": text})

urls = [
    "https://www.olx.pl/elektronika/telefony/q-iphone-11/",
    "https://www.olx.pl/elektronika/telefony/q-iphone-13/"
]

with open("data.json", "r") as f:
    seen = json.load(f)["seen"]

new_seen = seen.copy()

for url in urls:
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select("a[href*='/d/oferta/']")

    for item in items:
        title = item.get_text(strip=True)
        link = item["href"]
        if not link.startswith("http"):
            link = "https://www.olx.pl" + link

        price = item.find_next("p")
        price_text = price.get_text(strip=True) if price else ""
        digits = "".join(filter(str.isdigit, price_text))
        price_value = int(digits) if digits else 0

        ok = (
            ("11" in title and price_value <= 3000) or
            ("13" in title and price_value <= 9500)
        )

        if ok and link not in seen:
            send(f"📱 {title}\n💰 {price_text}\n🔗 {link}")
            new_seen.append(link)

with open("data.json", "w") as f:
    json.dump({"seen": new_seen}, f)
