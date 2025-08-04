from models.ml_model import MLModel
from models.theme import Theme
from models.task_log import TaskResult


class SpanishComicModel(MLModel):
    """
    Модель генерации заданий в формате комиксов.
    """
    def __init__(self):
        super().__init__(name="SpanishComicModel", cost=0.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        comic_file = theme.base_comic if not is_bonus else theme.get_bonus_comic()
        if not comic_file:
            raise ValueError("Нет бонусных комиксов для этой темы")

        explanation = f"[easy]. Комикс: {comic_file} | Тема: {theme.name} | Уровень: {theme.level}"
        vocab = ["ser", "soy", "eres", "es"] if theme.name == "глагол ser" else ["palabra", "nueva"]

        return TaskResult(
            difficulty="easy",
            vocabulary=vocab,
            explanation=explanation,
            is_correct=True
        )
