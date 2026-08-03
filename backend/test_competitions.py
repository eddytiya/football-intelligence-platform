from etl.extract.football_data import FootballDataExtractor
import json

extractor = FootballDataExtractor()

competitions = extractor.get_competitions()

print(json.dumps(competitions["competitions"][0], indent=4))

extractor.close()