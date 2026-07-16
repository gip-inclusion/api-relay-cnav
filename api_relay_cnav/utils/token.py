import hashlib


def token_hexdigest(token: str) -> str:
    return hashlib.sha512(token.encode()).hexdigest()
