from app.services.football_api import FootballAPIClient
import json

client = FootballAPIClient()

data = client.get("/competitions")

print(json.dumps(data, indent=4))