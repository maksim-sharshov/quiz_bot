from html import escape


def room_lobby_msg(category_title: str, timer_sec: int, players: int) -> str:
    """Лобби игрока внутри комнаты."""
    return (
        f"🎉 Вы попали в комнату: <b>{escape(category_title)}</b>\n"
        f"⏱ Таймер на вопрос: {timer_sec} сек\n"
        f"👥 Участников: {players}\n\n"
        f"Ожидайте старта квиза..."
    )


you_left_msg = "🚪 Вы вышли из комнаты."
