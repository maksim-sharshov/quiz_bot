from html import escape

from bot.templates.common import participants_text


def room_lobby_msg(category_title: str, timer_sec: int, names: list[str]) -> str:
    """Лобби игрока внутри комнаты."""
    return (
        f"🎉 Вы попали в комнату: <b>{escape(category_title)}</b>\n"
        f"⏱ Таймер на вопрос: {timer_sec} сек\n"
        f"{participants_text(names)}\n\n"
        f"Ожидайте старта квиза..."
    )


you_left_msg = "🚪 Вы вышли из комнаты."
