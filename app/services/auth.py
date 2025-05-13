from secrets import token_hex
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key() -> tuple:
    """Генерация безопасного API-ключа."""
    raw_key = token_hex(32)  # 64 символа
    hashed_key = pwd_context.hash(raw_key)
    return raw_key, hashed_key  # Возвращает исходный ключ и его хэш

def hash_api_key(raw_key: str) -> str:
    return pwd_context.hash(raw_key)

def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    return pwd_context.verify(raw_key, hashed_key)