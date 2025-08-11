from database.config import get_settings
from database.database import init_db, get_database_engine
from sqlmodel import Session

from models.theme import Theme
from models.user import User
from services.crud.user import create_user, get_all_users
from services.crud.theme import create_theme, get_all_themes
from services.crud.wallet import create_wallet_for_user
from services.admin import top_up_user, get_transaction_history_for_user
from services.generation.task_request import TaskRequest
from services.generation.grammar import GrammarModel


if __name__ == "__main__":
    # 1. Настройки
    settings = get_settings()
    print(f"{settings.APP_NAME} (v{settings.API_VERSION})")
    print(f"Debug: {settings.DEBUG}")
    print(f"DB: {settings.DB_USER}@{settings.DB_HOST}/{settings.DB_NAME}")

    # 2. Инициализируем БД
    init_db(drop_all=True)
    print("✅ БД инициализирована")

    # 3. Подключаемся
    engine = get_database_engine()
    with Session(engine) as session:
        # 4. Создаём пользователей
        user = create_user("student@correo.es", "superclave123", session)
        create_wallet_for_user(user.id, session)
        admin = create_user("admin@correo.es", "adminadmin", session)
        admin.is_admin = True
        create_wallet_for_user(admin.id, session)
        session.commit()
        print(f"👤 Создан пользователь: {user.email}")
        print(f"👑 Админ: {admin.email}")

        # 5. Пополняем баланс
        top_up_user(user, amount=5.0, session=session)
        print(f"💰 Баланс пользователя после пополнения: {user.wallet.balance}")

        # 6. Создаём темы
        theme1 = Theme(name="глагол ser", level="A1", base_comic="comic_ser_base.jpg", bonus_comics=["comic_ser_bonus1.jpg"])
        theme2 = Theme(name="прилагательные", level="A1", base_comic="comic_adj_base.jpg")
        create_theme(theme1, session)
        create_theme(theme2, session)

        themes = get_all_themes(session)
        print("📚 Темы:")
        for t in themes:
            print(f" - {t.name} ({t.level})")

        # 7. Генерация задания
        model = GrammarModel()
        recommended = model.recommend_theme(user, themes, session)

        print(f"\n🧠 Рекомендуемая тема: {recommended.name}")

        task = TaskRequest(
            user=user,
            model=model,
            theme=recommended,
            session=session,
            is_bonus_comic=False
        )
        log = task.execute()

        print(f"\n✅ Выполнено задание: {log.task_description}")
        print(f"🧾 Объяснение: {log.result.explanation}")
        print(f"💵 Остаток баланса: {user.wallet.balance}")

        # 7.1 Предложение бонусного комикса и списание баллов
        if recommended.bonus_comics:
            print("\n🎁 Предлагается бонусный комикс!")

            try:
                from services.crud.wallet import deduct_from_wallet
                deduct_from_wallet(user.id, amount=2.0, session=session)
                session.refresh(user.wallet)
                print(f"💸 Баланс после списания за бонус: {user.wallet.balance}")
            except ValueError as e:
                print(f"❌ Не удалось списать за бонус: {e}")
        else:
            print("\n⚠️ Для этой темы бонусные комиксы отсутствуют.")

        # 8. Печатаем историю транзакций
        print("\n📜 История транзакций:")
        history = get_transaction_history_for_user(user.id, session)
        for tx in history:
            print(f"{tx.timestamp}: {tx.operation} {tx.amount} — {tx.reason}")
