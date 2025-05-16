import requests
import pandas as pd

session = requests.Session()    
#steamid = "76561198102151621"
steamid = "76561198413249231"

url = f"https://www.skinpock.com/es/inventory/{steamid}"
url_inventory = f"https://www.skinpock.com/api/inventory"

# response = session.post(url)

# try:
#     if response.status_code == 200:
#         print("Request was successful")
#         print(response.json())
# except requests.exceptions.RequestException as e:
#     print("Error:", e)

params = {
    "steam_id": steamid,
    "sort":      "price_max",
    "game":      "cs2",
    "language":  "english"
}
headers = {
    "Accept":          "application/json, text/plain, */*",
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                       "AppleWebKit/537.36 (KHTML, like Gecko) " \
                       "Chrome/135.0.0.0 Safari/537.36",
    "Referer":         f"https://www.skinpock.com/es/inventory/{steamid}",
    "Accept-Language": "es-ES,es;q=0.9",
    "Apikeys":         '["0a465e43-8320-400d-ba8a-58a5918a71df","bfbaa291-76c7-4c5c-8f2a-5ecf55294e33"]'
}

# r = requests.get(url_inventory, params=params, headers=headers)
# print("Status code:", r.status_code)
# print("Final URL :", r.url)
# print("Content-Type:", r.headers.get("Content-Type"))
# print("Is JSON?   ", r.headers.get("Content-Type","").startswith("application/json"))
# print("Body snippet:\n", r.text[:300])

r = requests.get(url_inventory, params=params, headers=headers)
r.raise_for_status()          # lanza excepción si status != 200
data = r.json()               # ahora debe parsear bien

df = pd.DataFrame(data)

print(df)

df.to_excel("skinspock.xlsx", index=False)