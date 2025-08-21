from models.ml_model import MLModel
from models.theme import Theme
from models.task_log import TaskResult


class GrammarModel(MLModel):
    def __init__(self):
        super().__init__(name="GrammarModel", cost=1.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        explanation = f"Грамматическое упражнение по теме: {theme.name} | Уровень: {theme.level}"
        vocab = ["el verbo", "la conjugación", "el tiempo"]

        return TaskResult(
            difficulty="medium",
            vocabulary=vocab,
            explanation=explanation,
            is_correct=True
        )
