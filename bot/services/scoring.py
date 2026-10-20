"""
Подсчёт очков и построение таблицы лидеров.
"""

from bot.utils import display_name


def compute_points(selected: set[int], options: list[dict]) -> int:
    """
    Правила начисления:
    - если выбран хотя бы один неверный вариант, за вопрос начисляется 0 баллов;
    - иначе +1 балл за каждый правильно выбранный вариант (неполный набор верных
      вариантов допускается и приносит баллы за отмеченные правильные);
    - пустой выбор даёт 0 баллов.
    """
    if not selected:
        return 0
    points = 0
    for index in selected:
        if not 0 <= index < len(options):
            return 0
        if not options[index].get("is_correct"):
            return 0
        points += 1
    return points


def correct_texts(options: list[dict]) -> list[str]:
    """Тексты правильных вариантов вопроса."""
    return [option["text"] for option in options if option.get("is_correct")]


def build_leaderboard(players: list) -> list[dict]:
    """
    Таблица лидеров: от первого места до последнего.
    Возвращает список словарей place / tg_id / name / score.
    """
    ordered = sorted(players, key=lambda player: (-player.score, player.date_joined))
    return [
        {
            "place": place,
            "tg_id": player.tg_id,
            "name": display_name(player),
            "score": player.score,
        }
        for place, player in enumerate(ordered, start=1)
    ]
