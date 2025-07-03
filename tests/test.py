
import requests
import urllib.parse

def obtener_inventario_steam(steamid64):
    url = f"https://steamcommunity.com/inventory/{steamid64}/730/2?l=english&count=5000"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"No se pudo obtener el inventario, status: {response.status_code}")
    return response.json()

def obtener_instanceid_por_assetid(inventario_json, assetid):
    for asset in inventario_json.get("assets", []):
        if asset.get("assetid") == assetid:
            return asset.get("instanceid")
    return None

def obtener_datos_skin(inspect_link):
    encoded_link = urllib.parse.quote(inspect_link, safe='')
    api_url = f"https://www.skinpock.com/api/float?url={encoded_link}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return {
            "float": data.get("float"),
            "wear": data.get("wear"),
            "paintseed": data.get("paintseed"),
            "stickers": data.get("stickers", []),
            "market_hash_name": data.get("markethashname")
        }
    else:
        raise Exception(f"Error en la request a Skinpock: {response.status_code}")

def main(steamid64, assetids):
    inventario = obtener_inventario_steam(steamid64)
    resultados = []
    for assetid in assetids:
        instanceid = obtener_instanceid_por_assetid(inventario, assetid)
        if instanceid is None:
            print(f"No se encontró instanceid para assetid {assetid}")
            continue

        inspect_link = f"steam://rungame/730/76561202255233023/+csgo_econ_action_preview S{steamid64}A{assetid}D{instanceid}"
        print(f"Consultando skin: {inspect_link}")
        
        try:
            datos = obtener_datos_skin(inspect_link)
            datos["inspect_link"] = inspect_link
            datos["assetid"] = assetid
            resultados.append(datos)
        except Exception as e:
            print(f"Error obteniendo datos para assetid {assetid}: {e}")
    
    return resultados


# ---------------------------
# EJEMPLO DE USO
# ---------------------------

steamid64 = "76561198102151621"  # Reemplaza con el SteamID64 del dueño
assetids = [
    "43668495826",
    "43668539177"
]  # Lista de asset IDs para consultar

if __name__ == "__main__":
    skins_info = main(steamid64, assetids)
    for info in skins_info:
        print("------")
        for k, v in info.items():
            print(f"{k}: {v}")
