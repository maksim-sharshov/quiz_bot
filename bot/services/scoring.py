"""
Подсчёт очков и построение таблицы лидеров.
"""


def compute_points(selected: set[int], options: list[dict]) -> int:
    """
    Правила начисления: +1 балл за каждый правильно выбранный вариант.
    Неверный вариант ничего не отнимает, итог не опускается ниже нуля.
    """
    points = 0
    for index in selected:
        if 0 <= index < len(options) and options[index].get("is_correct"):
            points += 1
    return max(0, points)


def correct_texts(options: list[dict]) -> list[str]:
    """Тексты правильных вариантов вопроса."""
    return [option["text"] for option in options if option.get("is_correct")]


def build_leaderboard(players: list) -> list[dict]:
    """
    Таблица лидеров: от первого места до последнего.
    Возвращает список словарей place / tg_id / username / score.
    """
    ordered = sorted(players, key=lambda player: (-player.score, player.date_joined))
    return [
        {
            "place": place,
            "tg_id": player.tg_id,
            "username": player.username,
            "score": player.score,
        }
        for place, player in enumerate(ordered, start=1)
    ]
