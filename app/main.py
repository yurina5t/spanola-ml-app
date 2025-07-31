from fastapi import FastAPI
from models.user import User
from models.theme import Theme
from models.models import GrammarModel
from models.request import TaskRequest
from models.logs import TransactionHistory, PredictionHistory

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    try:
        user = User(id=1, email="nuevo@correo.es", _password="superclave123")
        predictions = PredictionHistory()
        transactions = TransactionHistory()

        print(f"✅ Зарегистрирован: {user.email}, баланс: {user.wallet.balance} баллов")

        themes = [
            Theme(name="глагол ser", level="A1", base_comic="comic_ser_base.jpg", bonus_comics=["comic_ser_bonus1.jpg"]),
            Theme(name="прилагательные", level="A1", base_comic="comic_adj_base.jpg")
        ]

        model = GrammarModel()
        recommended = model.recommend_theme(user, themes, predictions)

        base_task = TaskRequest(
            user=user,
            model=model,
            theme=recommended,
            wallet=user.wallet,
            transactions=transactions,
            is_bonus_comic=False
        )
        base_task.execute()

        bonus_cost = 2.0
        print(f"\n🎁 Доступен бонусный комикс на эту тему! Стоимость: {bonus_cost} балла")
        bonus_task = TaskRequest(
            user=user,
            model=model,
            theme=recommended,
            wallet=user.wallet,
            transactions=transactions,
            is_bonus_comic=True,
            bonus_cost=bonus_cost
        )
        bonus_task.execute()

        print(f"💎 Остаток баланса: {user.wallet.balance} баллов")

        print("\n🧠 История рекомендаций:")
        for rec in predictions.get_user_history(user.id):
            print(f"  → {rec.model_name} рекомендовал: {rec.theme_name} ({rec.difficulty}) в {rec.recommended_at}")

        print("\n💰 История транзакций:")
        for t in transactions.get_user_history(user.id):
            print(f"  → {t.operation} {t.amount} | Причина: {t.reason} | Время: {t.timestamp}")

    except ValueError as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
