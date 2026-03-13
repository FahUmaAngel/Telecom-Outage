import requests

url = "https://nominatim.openstreetmap.org/reverse"
params = {'lat': 59.3360861, 'lon': 18.0718987, 'format': 'json', 'zoom': 10, 'addressdetails': 1}
headers = {'User-Agent': 'TelecomOutageMonitor/1.0'}

r = requests.get(url, params=params, headers=headers, timeout=10)
print(r.json().get('address', {}))
