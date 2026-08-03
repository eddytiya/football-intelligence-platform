from app.core.config import settings

print("=" * 50)
print("APPLICATION CONFIGURATION")
print("=" * 50)

print(f"Database Host      : {settings.DB_HOST}")
print(f"Database Port      : {settings.DB_PORT}")
print(f"Database Name      : {settings.DB_NAME}")

print()

print(f"Football API URL   : {settings.FOOTBALL_API_BASE_URL}")
print(f"Request Timeout    : {settings.REQUEST_TIMEOUT}")
print(f"Max Retries        : {settings.MAX_RETRIES}")
print(f"Retry Delay        : {settings.RETRY_DELAY}")

print()

print(f"Environment        : {settings.ENVIRONMENT}")
print(f"Debug Mode         : {settings.DEBUG}")