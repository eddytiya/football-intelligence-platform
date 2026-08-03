from datetime import datetime


def parse_datetime(value):
    """
    Convert different datetime formats returned by the Football API
    into a Python datetime object.

    Supported formats:
    ------------------
    YYYY-MM-DDTHH:MM:SSZ
    YYYY-MM-DDTHH:MM:SS.sssZ
    YYYY-MM-DD HH:MM:SS
    YYYY-MM-DD
    YYYY-MM
    YYYY

    Returns:
        datetime.datetime | None
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    if value == "":
        return None

    if value.lower() in {"none", "null", "n/a", "na", "unknown"}:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(value, fmt)

            # Handle partial dates
            if fmt == "%Y-%m":
                return datetime(parsed.year, parsed.month, 1)

            if fmt == "%Y":
                return datetime(parsed.year, 1, 1)

            return parsed

        except ValueError:
            continue

    print(f"Warning: Unable to parse datetime '{value}'")

    return None