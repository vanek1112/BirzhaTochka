"""from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print("Подключение успешно, версия PostgreSQL:", result.scalar())"""