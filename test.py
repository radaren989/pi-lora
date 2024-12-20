import requests as req

url = "https://api.thingspeak.com/update?api_key=LLO71U52SD2B8685"
res = req.get(url, params={
              "field1": 42,
              "field2": 69,
              "field3": 51})
res.raise_for_status()
print(res.status_code)
