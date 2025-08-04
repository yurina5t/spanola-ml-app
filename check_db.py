import os
from sqlmodel import SQLModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from app.database.config import get_settings

def check_database_connection():
    """Проверка подключения к БД"""
    load_dotenv()
    settings = get_settings()

    urls_to_try = [
        settings.DATABASE_URL_psycopg,
        "postgresql://postgres:postgres@localhost:5432/spanola",
        "postgresql://postgres:postgres@database:5432/spanola"
    ]

    for i, url in enumerate(urls_to_try, 1):
        print(f"🔄 Попытка {i}: {url}")
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
                print(f"✅ Подключение успешно! PostgreSQL версия: {version}")
                return url, engine
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            continue

    print("💀 Не удалось подключиться ни к одной БД")
    return None, None

def test_create_tables():
    """Создание таблиц"""
    _, engine = check_database_connection()
    if not engine:
        return False

    try:
        from app.models import theme, user, wallet, transaction_log, task_log, prediction_log  # важно для регистрации моделей
        print("\n🛠️  Создание таблиц...")
        SQLModel.metadata.create_all(engine)

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]

        print(f"📦 Найдены таблицы: {tables}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка базы данных\n" + "=" * 50)
    if test_create_tables():
        print("\n🎉 База данных готова к работе!")
    else:
        print("\n💡 Убедитесь, что БД запущена и переменные окружения указаны верно.")
