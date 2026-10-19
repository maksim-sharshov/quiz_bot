from html import escape

no_categories_msg = "📭 Категорий пока нет. Сначала создайте категорию."

choose_category_msg = "🎯 Выберите категорию для квиза:"


def no_questions_msg(category_title: str) -> str:
    return f"📭 В категории «{escape(category_title)}» нет вопросов."


def choose_timer_msg(category_title: str) -> str:
    return f"⏱ Выберите таймер на вопрос для категории «{escape(category_title)}»:"


def room_created_msg(
    category_title: str,
    timer_sec: int,
    link: str,
    players: int,
) -> str:
    return (
        f"🏁 Квиз создан!\n\n"
        f"📂 Категория: <b>{escape(category_title)}</b>\n"
        f"⏱ Таймер на вопрос: {timer_sec} сек\n"
        f"👥 Участников: {players}\n\n"
        f"🔗 Ссылка-приглашение:\n{link}\n\n"
        f"Отправьте ссылку игрокам и нажмите «Начать квиз»."
    )
