import os
import json
import requests
from bs4 import BeautifulSoup

TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

ALLEGRO_CLIENT_ID = os.environ["ALLEGRO_CLIENT_ID"]
ALLEGRO_CLIENT_SECRET = os.environ["ALLEGRO_CLIENT_SECRET"]
ALLEGRO_REFRESH_TOKEN = os.environ["ALLEGRO_REFRESH_TOKEN"]

HEADERS = {"User-Agent": "Mozilla/5.0"}
DATA_FILE = "data.json"

BAD_WORDS = [
    "etui", "case", "szkło", "glass", "ekran", "wyswietlacz",
    "plecki", "obudowa", "części", "czesci", "bateria",
    "zamiennik", "lcd", "oled", "folia"
]

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"seen": []}, f)

with open(DATA_FILE) as f:
    seen = set(json.load(f)["seen"])


def save_seen():
    with open(DATA_FILE, "w") as f:
        json.dump({"seen": list(seen)}, f)


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={
            "chat_id": TG_CHAT,
            "text": msg,
            "disable_web_page_preview": True
        }
    )


def is_phone(title: str):
    title = title.lower()
    if "iphone 11" not in title:
        return False
    for w in BAD_WORDS:
        if w in title:
            return False
    return True


# ================= OLX =================
def run_olx():
    url = (
        "https://www.olx.pl/elektronika/telefony/"
        "q-iphone-11/?search[filter_float_price:to]=300"
        "&search[city_id]=26131"
    )
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS).text,
        "html.parser"
    )

    for offer in soup.select("div[data-cy=l-card]"):
        a = offer.find("a", href=True)
        price_el = offer.find("p", {"data-testid": "ad-price"})
        title_el = offer.find("h6")

        if not a or not price_el or not title_el:
            continue

        title = title_el.text.strip()
        if not is_phone(title):
            continue

        link = "https://www.olx.pl" + a["href"]
        if link in seen:
            continue

        price = price_el.text.strip()
        seen.add(link)

        send(
            f"📱 {title}\n"
            f"💰 {price}\n"
            f"📍 Warszawa\n"
            f"🔗 {link}"
        )


# ================= ALLEGRO =================
def allegro_token():
    r = requests.post(
        "https://allegro.pl/auth/oauth/token",
        auth=(ALLEGRO_CLIENT_ID, ALLEGRO_CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": ALLEGRO_REFRESH_TOKEN
        },
        timeout=30
    )
    r.raise_for_status()
    return r.json()["access_token"]


def run_allegro():
    token = allegro_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }

    r = requests.get(
        "https://api.allegro.pl/offers/listing",
        headers=headers,
        params={
            "phrase": "iphone 11",
            "price.to": 300,
            "limit": 20,
            "sellingMode.format": "BUY_NOW"
        },
        timeout=30
    )

    for item in r.json().get("items", {}).get("regular", []):
        title = item["name"]
        if not is_phone(title):
            continue

        link = f"https://allegro.pl/oferta/{item['id']}"
        if link in seen:
            continue

        price = item["sellingMode"]["price"]["amount"]
        seen.add(link)

        send(
            f"🟠 {title}\n"
            f"💰 {price} zł\n"
            f"🔗 {link}"
        )


def main():
    run_olx()
    run_allegro()
    save_seen()


if __name__ == "__main__":
    main()
