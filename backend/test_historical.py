from etl.extract.football_data import FootballDataExtractor

extractor = FootballDataExtractor()

response = extractor.get_matches(
    "PL",
    season=2016,
)

matches = response.get("matches", [])

print(f"Matches returned: {len(matches)}")

if matches:
    print(matches[0]["utcDate"])
    print(matches[-1]["utcDate"])

extractor.close()