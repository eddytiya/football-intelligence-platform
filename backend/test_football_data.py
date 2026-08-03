from etl.extract.football_data import FootballDataExtractor

extractor = FootballDataExtractor()

competitions = extractor.get_competitions()

print("=" * 50)
print(f"Found {len(competitions['competitions'])} competitions")
print("=" * 50)

for competition in competitions["competitions"][:10]:
    print(f"{competition['code']:<8} {competition['name']}")

extractor.close()