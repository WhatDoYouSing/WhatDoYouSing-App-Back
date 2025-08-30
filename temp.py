import requests
from pprint import pprint

client_id = "f4121cf9734a42d2ab07ee2e2c655fd9"
client_secret = "149bf25ffba549c69f7fbfb7f42d0bb9"
code = "AQC5d-iY8Mz9jwV1UsLKm6UqncskkvGanyEZV1VeW0dIwuFYtuVZ_yBtYz4FET93hmpXqEMbvENGXFa8Qpej_riDPpjIDyBEhbvJwKcPIl1jNM59MhN2y7I3eJaFM2W9986m6qYcrKhNLdYfx7-4UY1oyIUCyFPeaId_aO3BqrUUushRimsYBMtW2Kgo_LIsC-hZlvM33lA2CT05wauZ9IyLwqK27XFAyOUuPA"
redirect_uri = "https://api.whatdoyousing.com/uploads/spotify/callback/"

token_url = "https://accounts.spotify.com/api/token"

data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": redirect_uri,
    "client_id": client_id,
    "client_secret": client_secret,
}

response = requests.post(token_url, data=data)
pprint(response.json())