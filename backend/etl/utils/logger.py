from pathlib import Path

from loguru import logger


# Create the logs directory if it doesn't exist
LOG_DIR = Path("etl/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Remove the default logger
logger.remove()

# Console logging
logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "{message}",
)

# File logging
logger.add(
    LOG_DIR / "football_platform.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
