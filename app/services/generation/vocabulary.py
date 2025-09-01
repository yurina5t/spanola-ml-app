from models.ml_model import MLModel
from models.theme import Theme
from models.task_log import TaskResult


class VocabularyModel(MLModel):
    def __init__(self):
        super().__init__(name="VocabularyModel", cost=0.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        explanation = f"Упражнение на лексику по теме: {theme.name} | Уровень: {theme.level}"
        vocab = ["casa", "comida", "ropa"]
        return TaskResult(
            difficulty="medium",
            vocabulary=vocab,
            explanation=explanation,
            is_correct=False
        )
