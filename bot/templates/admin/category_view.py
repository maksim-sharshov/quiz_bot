from html import escape


no_categories_msg = "📭 Категорий пока нет."

categories_msg = "📚 Выберите категорию:"


def no_questions_msg(category_title: str) -> str:
    return f"📭 В категории «{escape(category_title)}» пока нет вопросов."


def questions_msg(category_title: str) -> str:
    return (
        f"📂 Категория «{escape(category_title)}»\n\n"
        f"Нажмите на вопрос, чтобы посмотреть его полностью."
    )


def question_detail_msg(number: int, text: str, options: list[dict]) -> str:
    """Полный текст вопроса с пометкой правильных вариантов."""
    lines = [f"❓ Вопрос {number}", "", escape(text), ""]
    for index, option in enumerate(options, start=1):
        mark = "✅ " if option.get("is_correct") else "• "
        lines.append(f"{mark}{index}) {escape(option['text'])}")
    return "\n".join(lines)


def category_delete_confirm_msg(title: str, count: int) -> str:
    return (
        f"🗑 Удалить категорию «{escape(title)}» и все её вопросы "
        f"({count} шт.)? Это действие необратимо."
    )


def category_deleted_msg(title: str) -> str:
    return f"✅ Категория «{escape(title)}» удалена."


question_deleted_msg = "✅ Вопрос удалён."

category_in_room_msg = (
    "🚫 Нельзя удалить категорию: она используется в активной комнате."
)

element_deleted_msg = "⚠️ Элемент уже удалён."
