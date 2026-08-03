from etl.config.settings import settings

print("Database Host :", settings.DB_HOST)
print("Database Name :", settings.DB_NAME)
print("Environment   :", settings.ENVIRONMENT)
print("Debug Mode    :", settings.DEBUG)
print("API Key Loaded:", settings.FOOTBALL_API_KEY[:6] + "...")