from html import escape

from bot.templates.common import participants_text


def room_panel_msg(category_title: str, timer_sec: int, names: list[str], link: str) -> str:
    """Панель управления комнатой у администратора."""
    return (
        f"🏁 Комната квиза\n\n"
        f"📂 Категория: <b>{escape(category_title)}</b>\n"
        f"⏱ Таймер на вопрос: {timer_sec} сек\n"
        f"{participants_text(names)}\n\n"
        f"🔗 Ссылка-приглашение:\n{link}"
    )


def quiz_started_msg(category_title: str) -> str:
    return f"🚀 Квиз по категории «{escape(category_title)}» запущен!"


def quiz_finished_msg(category_title: str) -> str:
    return f"🏁 Квиз по категории «{escape(category_title)}» завершён."


need_players_msg = "⚠️ Нельзя начать квиз без участников."

already_running_msg = "⚠️ Квиз уже запущен."

room_gone_msg = "⚠️ Комната уже удалена."


def interrupted_msg(category_title: str) -> str:
    return (
        f"⚠️ Квиз по категории «{escape(category_title)}» был прерван "
        f"из-за перезапуска бота."
    )
