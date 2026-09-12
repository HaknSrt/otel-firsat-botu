import os
import calendar
from datetime import date, timedelta
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEARCH_MONTH = os.environ.get("SEARCH_MONTH", "2026-09")
CHILD_AGE = os.environ.get("CHILD_AGE", "8")
LOCATION_QUERY = "Antalya"
NIGHTS = 5
BUDGET_TRY = 50000
MIN_RATING = 4.0

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_usd_to_try():
    r = requests.get("https://api.frankfurter.dev/v1/latest", params={"base": "USD", "symbols": "TRY"})
    return r.json()["rates"]["TRY"]

def get_location_key(query):
    r = requests.get("https://data.xotelo.com/api/search", params={"query": query, "location_type": "geo"})
    results = r.json().get("result", {}).get("list", [])
    return results[0]["location_key"] if results else None

def get_hotel_list(location_key, offset=0, limit=100):
    r = requests.get("https://data.xotelo.com/api/list", params={
        "location_key": location_key, "offset": offset, "limit": limit, "sort": "best_value"
    })
    return r.json().get("result", {}).get("list", [])

def get_rate(hotel_key, chk_in, chk_out):
    params = {"hotel_key": hotel_key, "chk_in": chk_in, "chk_out": chk_out, "adults": 2, "age_of_children": CHILD_AGE}
    r = requests.get("https://data.xotelo.com/api/rates", params=params)
    data = r.json()
    rates = data.get("result", {}).get("rates") or []
    if not rates:
        return None
    return min(rate["rate"] for rate in rates)

def candidate_checkins(year_month):
    year, month = map(int, year_month.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    out = []
    for day in range(1, days_in_month - NIGHTS + 1):
        d = date(year, month, day)
        if d.weekday() in (4, 5):
            out.append(d)
    return out

def main():
    usd_try = get_usd_to_try()
    location_key = get_location_key(LOCATION_QUERY)
    if not location_key:
        send_telegram("⚠️ Antalya için konum bulunamadı.")
        return

    hotels, offset = [], 0
    while offset < 300:
        batch = get_hotel_list(location_key, offset=offset)
        if not batch:
            break
        hotels.extend(batch)
        offset += 100

    checkins = candidate_checkins(SEARCH_MONTH)
    found = 0

    for hotel in hotels:
        rating = (hotel.get("review_summary") or {}).get("rating", 0) or 0
        if rating < MIN_RATING:
            continue
        for chk_in in checkins:
            chk_out = chk_in + timedelta(days=NIGHTS)
            rate = get_rate(hotel["key"], chk_in.isoformat(), chk_out.isoformat())
            if rate is None:
                continue
            total_try = rate * NIGHTS * usd_try
            if total_try <= BUDGET_TRY:
                found += 1
                send_telegram(
                    f"🚨 BÜTÇE ALTI FIRSAT!\n{hotel['name']}\n"
                    f"{chk_in.strftime('%d.%m.%Y')} - {chk_out.strftime('%d.%m.%Y')} (5 gece)\n"
                    f"Toplam: {total_try:,.0f} TL\n{hotel.get('url','')}"
                )

    if found == 0:
        print("Bu çalışmada bütçe altı fırsat bulunamadı.")

if __name__ == "__main__":
    main()
