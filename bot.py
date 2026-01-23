import os
import json
import requests
from bs4 import BeautifulSoup

# ===== TELEGRAM =====
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT = os.environ["TG_CHAT"]

# ===== ALLEGRO =====
ALLEGRO_CLIENT_ID = os.environ["ALLEGRO_CLIENT_ID"]
ALLEGRO_CLIENT_SECRET = os.environ["ALLEGRO_CLIENT_SECRET"]
ALLEGRO_REFRESH_TOKEN = os.environ["ALLEGRO_REFRESH_TOKEN"]

# ===== FILE =====
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"seen": []}, f)

with open(DATA_FILE, "r") as f:
    seen = set(json.load(f)["seen"])


def save_seen():
    with open(DATA_FILE, "w") as f:
        json.dump({"seen": list(seen)}, f)


def send(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT, "text": msg})


# ==========================
# OLX
# ==========================
def run_olx():
    url = "https://www.olx.pl/elektronika/telefony/q-iphone-11/?search%5Bfilter_float_price%3Ato%5D=300&search%5Bdistrict_id%5D=1"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    for offer in soup.select("div[data-cy=l-card]"):
        a = offer.find("a", href=True)
        price = offer.find("p", {"data-testid": "ad-price"})
        if not a or not price:
            continue

        link = "https://www.olx.pl" + a["href"]
        if link in seen:
            continue

        seen.add(link)
        send(f"📱 OLX iPhone 11\n{price.text.strip()}\n{link}")


# ==========================
# ALLEGRO TOKEN
# ==========================
def allegro_token():
    r = requests.post(
        "https://allegro.pl/auth/oauth/token",
        auth=(ALLEGRO_CLIENT_ID, ALLEGRO_CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": ALLEGRO_REFRESH_TOKEN,
        },
    )
    r.raise_for_status()
    return r.json()["access_token"]


# ==========================
# ALLEGRO SEARCH
# ==========================
def run_allegro():
    token = allegro_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.allegro.public.v1+json",
    }

    params = {
        "phrase": "iphone 11",
        "price.to": 300,
        "city": "Warszawa",
        "limit": 20,
    }

    r = requests.get(
        "https://api.allegro.pl/offers/listing",
        headers=headers,
        params=params,
    )

    for item in r.json().get("items", {}).get("regular", []):
        link = item["id"]
        if link in seen:
            continue

        seen.add(link)
        send(
            f"📱 Allegro iPhone 11\n"
            f"{item['sellingMode']['price']['amount']} zł\n"
            f"https://allegro.pl/oferta/{item['id']}"
        )


def main():
    run_olx()
    run_allegro()
    save_seen()


if __name__ == "__main__":
    main()
