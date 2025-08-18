from sqlmodel import SQLModel
from sqlalchemy import create_engine, text

from database.config import get_settings

def check_database_connection():
    """Проверка подключения к БД"""
    settings = get_settings()

    url = settings.DATABASE_URL,
    print(f"🔗 Пробую подключиться: {url}")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            print(f"✅ Подключение успешно! PostgreSQL версия: {version}")
            return url, engine
    except Exception as e:
        print(f"❌ Ошибка: {e}")            
        return None, None

def test_create_tables():
    """Создание таблиц"""
    _, engine = check_database_connection()
    if not engine:
        return False
    try:
        from models import theme, user, wallet, transaction_log, task_log, prediction_log
        print("\n🛠️  Создание таблиц...")
        SQLModel.metadata.create_all(engine)
        print("✅ Таблицы успешно созданы!")
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
