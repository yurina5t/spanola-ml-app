from workers.worker_base import start_worker
from services.generation.vocabulary import VocabularyModel
from sqlmodel import Session

def handle_job(job, session: Session):
    theme = session.get(Theme, job.theme_id)
    if not theme:
        raise ValueError("Тема не найдена")
    model = VocabularyModel()
    task_result = model.generate_task(theme, is_bonus=False)
    return {
        "model_name": model.name,
        "theme_name": theme.name,
        "difficulty": task_result.difficulty,
        "explanation": task_result.explanation,
        "vocabulary": task_result.vocabulary,
    }

if __name__ == "__main__":
    start_worker("queue.vocab", handle_job)
