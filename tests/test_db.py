from sqlalchemy import create_engine, text
from app.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print("Подключение успешно! Версия PostgreSQL:", result.scalar())