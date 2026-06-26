import re


def normalize_phone(raw: str) -> str:
    """Normalize to E.164. Accepts 10-digit US numbers or 11-digit starting with 1."""
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10:
        return f'+1{digits}'
    if len(digits) == 11 and digits.startswith('1'):
        return f'+{digits}'
    raise ValueError(f"Invalid phone number: {raw!r}")
