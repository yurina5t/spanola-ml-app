# app/seed_data.py
from sqlmodel import Session
from database.database import init_db, get_database_engine
from services.crud.user import get_user_by_email, create_user
from services.crud.wallet import create_wallet_for_user, top_up_wallet
from services.crud.theme import get_theme_by_name, create_theme
from services.crud.prediction_log import log_prediction
from services.crud.task_log import log_task
from models.theme import Theme

def seed():
    # 1) Создаём таблицы, если их ещё нет
    init_db()
    engine = get_database_engine()

    with Session(engine) as session:
        # ---------- Пользователи ----------
        def ensure_user(email: str, password: str, *, is_admin=False, topup: float = 0.0):
            u = get_user_by_email(email, session)
            if not u:
                u = create_user(email=email, raw_password=password, session=session)
                print(f"👤 Создан пользователь: {email} (id={u.id})")
            else:
                print(f"👤 Пользователь уже существует: {email} (id={u.id})")

            # кошелёк
            if not u.wallet:
                create_wallet_for_user(u.id, session)
                print(f"💼 Кошелёк создан для {email}")
            # пополнение
            if topup > 0:
                top_up_wallet(u.id, topup, session)
                session.refresh(u.wallet)
                print(f"💰 Баланс пополнен на {topup} — теперь {u.wallet.balance}")

            # права
            if is_admin and not u.is_admin:
                u.is_admin = True
                session.add(u)
                session.commit()
                session.refresh(u)
                print(f"👑 {email} помечен как админ")
            return u

        student = ensure_user("student@correo.es", "superclave123", topup=10.0)
        admin   = ensure_user("admin@correo.es",   "adminadmin",   is_admin=True, topup=0.0)

        # ---------- Темы ----------
        def ensure_theme(name: str, level: str, base_comic: str, bonus=None, description: str | None = None):
            t = get_theme_by_name(name, session)
            if t:
                print(f"📚 Тема уже существует: {t.name} (id={t.id})")
                return t
            t = Theme(
                name=name,
                level=level,
                base_comic=base_comic,
                bonus_comics=bonus or [],
                description=description
            )
            t = create_theme(t, session)
            print(f"📚 Создана тема: {t.name} (id={t.id})")
            return t

        t1 = ensure_theme(
            name="глагол ser",
            level="A1",
            base_comic="comic_ser_base.jpg",
            bonus=["comic_ser_bonus1.jpg"],
            description="Испанский глагол ser в настоящем времени"
        )
        t2 = ensure_theme(
            name="прилагательные",
            level="A1",
            base_comic="comic_adj_base.jpg",
            bonus=[],
            description="Испанские прилагательные"
        )

        # ---------- Логи предсказаний ----------
        try:
            rec = log_prediction(
                user_id=student.id,
                model_name="GrammarModel",
                theme_name=t1.name,
                difficulty="medium",
                session=session
            )
            print(f"🧠 PredictionLog создан: id={rec.id} (user_id={student.id}, theme={t1.name})")
        except Exception as e:
            print(f"⚠️ Не удалось создать PredictionLog: {e}")

        # ---------- Логи заданий ----------
        try:
            task_log = log_task(
                user_id=student.id,
                task_description=f"Упражнение по теме '{t1.name}'",
                model_name="GrammarModel",
                credits_spent=1.0,
                difficulty="medium",
                vocabulary=["ser", "soy", "es", "somos"],
                explanation="Заполните пропуски формами 'ser'.",
                is_correct=True,
                session=session
            )
            print(f"✅ TaskLog создан: id={task_log.id} (user_id={student.id})")
        except Exception as e:
            print(f"⚠️ Не удалось создать TaskLog: {e}")

if __name__ == "__main__":
    seed()
    print("🎉 Сидинг завершён")
