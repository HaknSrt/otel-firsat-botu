import os
import calendar
from datetime import date, timedelta
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEARCH_MONTH = os.environ.get("SEARCH_MONTH", "2026-09")
CHILD_AGE = os.environ.get("CHILD_AGE", "8")
NIGHTS = 5
BUDGET_TRY = 60000

HOTELS = [
    {"name": "AQI Pegasos World", "key": "g297967-d1144460"},
    {"name": "Miracle Resort Hotel", "key": "g15300585-d507978"},
    {"name": "Delphin Imperial", "key": "g20116893-d2680290"},
    {"name": "Rixos Premium Belek", "key": "g312725-d507974"},
    {"name": "Maxx Royal Belek Golf Resort", "key": "g312725-d2135900"},
    {"name": "Voyage Belek Golf & Spa", "key": "g312725-d647824"},
    {"name": "Swandor Topkapi Palace", "key": "g17951017-d307373"},
    {"name": "Lara Barut Collection", "key": "g15300585-d557049"},
    {"name": "Aska Lara Resort & Spa", "key": "g20116893-d5982512"},
    {"name": "Liberty Hotels Lara", "key": "g20116893-d568401"},
    {"name": "Kremlin Palace", "key": "g17951017-d507359"},
    {"name": "Megasaray Westbeach Antalya", "key": "g297962-d1804746"},
    {"name": "Hotel Su & Aqualand", "key": "g297962-d301300"},
    {"name": "Concorde De Luxe Resort", "key": "g20116893-d572784"},
    {"name": "Akra Antalya", "key": "g15300585-d295121"},
    {"name": "Wind of Lara", "key": "g20116893-d9731377"},
    {"name": "Ramada Plaza by Wyndham Antalya", "key": "g15300585-d1563900"},
    {"name": "Porto Bello Hotel Resort & Spa", "key": "g297962-d559596"},
    {"name": "Mardan Palace", "key": "g17951017-d15268740"},
    {"name": "Crowne Plaza Antalya by IHG", "key": "g297962-d1465019"},
    {"name": "Limak Lara Deluxe Hotel & Resort", "key": "g20116893-d599140"},
    {"name": "Sherwood Exclusive Lara", "key": "g20116893-d575894"},
    {"name": "Rixos Downtown Antalya", "key": "g297962-d295124"},
    {"name": "Baia Lara Hotel", "key": "g20116893-d1487312"},
    {"name": "Trendy Perge Resort & Suites", "key": "g17951017-d33456616"},
    {"name": "Delphin Diva Hotel", "key": "g20116893-d1073374"},
    {"name": "Crystal Centro", "key": "g20116893-d628986"},
    {"name": "Royal Seginus", "key": "g20116893-d10768152"},
    {"name": "Adalya Elite Lara", "key": "g20116893-d9453482"},
    {"name": "Delphin Palace", "key": "g20116893-d616817"},
    {"name": "Royal Holiday Palace", "key": "g20116893-d2083787"},
    {"name": "SeaLife Family Resort Hotel", "key": "g23456196-d295927"},
    {"name": "DoubleTree by Hilton Antalya City Centre", "key": "g15300585-d17346285"},
    {"name": "Voyage Kundu", "key": "g17951017-d33456834"},
]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_usd_to_try():
    r = requests.get("https://api.frankfurter.dev/v1/latest", params={"base": "USD", "symbols": "TRY"})
    return r.json()["rates"]["TRY"]

def get_rate(hotel_key, chk_in, chk_out):
    params = {"hotel_key": hotel_key, "chk_in": chk_in, "chk_out": chk_out, "adults": 2, "age_of_children": CHILD_AGE}
    r = requests.get("https://data.xotelo.com/api/rates", params=params)
    data = r.json()
    result = data.get("result")
    if not result:
        print("HATA:", hotel_key, chk_in, data.get("error"))
        return None
    rates = result.get("rates") or []
    if not rates:
        print("FIYAT YOK:", hotel_key, chk_in)
        return None
    return min(rate["rate"] for rate in rates)

def candidate_checkins(year_month):
    year, month = map(int, year_month.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]
    out = []
    for day in range(1, days_in_month - NIGHTS + 1):
        out.append(date(year, month, day))
    return out

def main():
    usd_try = get_usd_to_try()
    checkins = candidate_checkins(SEARCH_MONTH)
    found = 0

    for hotel in HOTELS:
        for chk_in in checkins:
            chk_out = chk_in + timedelta(days=NIGHTS)
            rate = get_rate(hotel["key"], chk_in.isoformat(), chk_out.isoformat())
            if rate is None:
                continue
            total_try = rate * NIGHTS * usd_try
            print(f"{hotel['name']} {chk_in} -> {total_try:.0f} TL")
            if total_try <= BUDGET_TRY:
                found += 1
                send_telegram(
                    f"🚨 BÜTÇE ALTI FIRSAT!\n{hotel['name']}\n"
                    f"{chk_in.strftime('%d.%m.%Y')} - {chk_out.strftime('%d.%m.%Y')} (5 gece)\n"
                    f"Toplam: {total_try:,.0f} TL"
                )

    if found == 0:
        print("Bu çalışmada bütçe altı fırsat bulunamadı.")

if __name__ == "__main__":
    main()
