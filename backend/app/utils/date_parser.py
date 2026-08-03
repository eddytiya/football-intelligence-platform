from datetime import datetime, date


def parse_date(value):
    """
    Convert different date formats returned by the Football API
    into a Python date object.

    Supported formats:
    ------------------
    YYYY-MM-DD
    YYYY-MM
    YYYY
    YYYY-MM-DDTHH:MM:SSZ

    Returns:
        datetime.date | None
    """

    if value is None:
        return None

    if isinstance(value, date):
        return value

    value = str(value).strip()

    if value == "":
        return None

    if value.lower() in {"none", "null", "n/a", "na", "unknown"}:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(value, fmt)

            # Handle partial dates
            if fmt == "%Y-%m":
                return date(parsed.year, parsed.month, 1)

            if fmt == "%Y":
                return date(parsed.year, 1, 1)

            return parsed.date()

        except ValueError:
            continue

    print(f"Warning: Unable to parse date '{value}'")

    return None