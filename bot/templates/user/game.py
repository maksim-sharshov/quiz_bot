from html import escape

from bot.utils.constants import TIMER_BAR_EMPTY, TIMER_BAR_FILLED


def timer_bar(left: int, total: int) -> str:
    """Полоска таймера вида 🟩⬜."""
    left = max(0, min(left, total))
    return TIMER_BAR_FILLED * left + TIMER_BAR_EMPTY * (total - left)


def question_msg(bar: str, seconds_left: int, index: int, total: int, text: str) -> str:
    """Текст сообщения с вопросом и таймером."""
    return (
        f"❓ Вопрос {index}/{total}\n\n"
        f"{escape(text)}\n\n"
        f"⏳ Шкала времени: {bar}\n"
        f"Осталось секунд: {seconds_left}"
    )


def timeout_msg(selected: set, options: list[dict]) -> str:
    """Итог игрока, когда время вышло."""
    if selected:
        chosen = ", ".join(
            options[i]["text"] for i in sorted(selected) if 0 <= i < len(options)
        )
    else:
        chosen = "ничего не выбрано"
    return f"⏰ Время вышло!\nВаш выбор: {escape(chosen)}"


stale_answer_msg = "⏰ Время на этот вопрос уже вышло."

choice_saved_msg = "Выбор сохранён!"

choice_cancelled_msg = "Выбор отменён"


def scorers_text(scorers: list[tuple[str, int]]) -> str:
    """Кто угадал и сколько баллов получил."""
    if not scorers:
        return "— никто не угадал"
    return "\n".join(f"• {escape(name)} — +{points}" for name, points in scorers)


def leaderboard_text(board: list[dict]) -> str:
    """Таблица лидеров с 🏆 у первых трёх мест."""
    lines: list[str] = []
    for row in board:
        prefix = "🏆" if row["place"] <= 3 else ""
        name = row["username"] or f"Игрок {row['tg_id']}"
        lines.append(f"{prefix} {row['place']}. {escape(str(name))} — {row['score']}".strip())
    return "\n".join(lines)


def results_msg(
    correct_options: list[str],
    scorers: list[tuple[str, int]],
    board: list[dict],
) -> str:
    """Итог одного вопроса: правильные ответы, угадавшие и таблица лидеров."""
    correct = ", ".join(correct_options) if correct_options else "—"
    return (
        f"✅ Правильные ответы: {escape(correct)}\n\n"
        f"🎯 Угадали:\n{scorers_text(scorers)}\n\n"
        f"🏁 Таблица лидеров:\n{leaderboard_text(board)}"
    )


def final_msg(board: list[dict]) -> str:
    """Финальная таблица после последнего вопроса."""
    return f"🏁 Квиз завершён!\n\nИтоговая таблица:\n{leaderboard_text(board)}"


interrupted_msg = "⚠️ Квиз был прерван из-за перезапуска бота."
