import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# ----------------------------------
# ASETUKSET
# ----------------------------------

SEARCH_URL = "https://www.nettiauto.com/volvo/v60"

MAX_PRICE = 20000
MAX_KM = 200000
MIN_YEAR = 2017

TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=TELEGRAM_TOKEN)

# ----------------------------------
# TIETOKANTA
# ----------------------------------

db = sqlite3.connect("cars.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS seen_ads(
    ad_id TEXT PRIMARY KEY
)
""")

db.commit()

# ----------------------------------
# APUTOIMINNOT
# ----------------------------------

def ad_seen(ad_id):
    cur.execute(
        "SELECT ad_id FROM seen_ads WHERE ad_id=?",
        (ad_id,)
    )
    return cur.fetchone() is not None


def mark_seen(ad_id):
    cur.execute(
        "INSERT OR IGNORE INTO seen_ads VALUES(?)",
        (ad_id,)
    )
    db.commit()


def send_telegram(message):

    bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

# ----------------------------------
# PISTEYTYS
# ----------------------------------

def score_car(title,
              year,
              km,
              price):

    score = 50

    if year >= 2020:
        score += 15

    elif year >= 2018:
        score += 10

    if km < 150000:
        score += 10

    if price < 18000:
        score += 10

    text = title.lower()

    if "automaatti" in text:
        score += 10

    if "huoltokirja" in text:
        score += 5

    return min(score, 100)

# ----------------------------------
# HAKU
# ----------------------------------

def fetch_ads():

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    response = requests.get(
        SEARCH_URL,
        headers=headers,
        timeout=30
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    ads = []

    for link in soup.select("a"):

        href = link.get("href")

        if not href:
            continue

        if "/auto/" not in href:
            continue

        title = link.get_text(
            strip=True
        )

        ads.append({
            "id": href,
            "title": title,
            "url":
            f"https://www.nettiauto.com{href}"
        })

    return ads

# ----------------------------------
# ILMOITUKSEN KÄSITTELY
# ----------------------------------

def process_ad(ad):

    ad_id = ad["id"]

    if ad_seen(ad_id):
        return

    # Oletuksena.
    # Todellisessa versiossa
    # ilmoitussivu luetaan
    # erikseen.

    year = 2019
    mileage = 160000
    price = 19000

    if price > MAX_PRICE:
        return

    if mileage > MAX_KM:
        return

    if year < MIN_YEAR:
        return

    score = score_car(
        ad["title"],
        year,
        mileage,
        price
    )

    msg = f"""
🚗 Uusi osuma

{ad["title"]}

Vuosimalli: {year}
Kilometrit: {mileage}
Hinta: {price} €

Pisteet: {score}/100

{ad["url"]}
"""

    send_telegram(msg)

    mark_seen(ad_id)

# ----------------------------------
# PÄÄOHJELMA
# ----------------------------------

def main():

    ads = fetch_ads()

    print(
        f"Löydetty "
        f"{len(ads)} ilmoitusta"
    )

    for ad in ads:

        try:
            process_ad(ad)

        except Exception as e:

            print(
                f"Virhe: {e}"
            )


if __name__ == "__main__":
    main()
