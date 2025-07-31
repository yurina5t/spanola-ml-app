from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Theme:
    """
    Тематический модуль.
    Включает название темы, уровень сложности (A1, A2 и т.д.), базовый и бонусные комиксы.
    Используется при генерации заданий.
    """
    name: str
    level: str
    base_comic: str
    bonus_comics: List[str] = field(default_factory=list)

    def get_bonus_comic(self) -> Optional[str]:
        """Возвращает первый доступный бонусный комикс или None."""
        return self.bonus_comics[0] if self.bonus_comics else None