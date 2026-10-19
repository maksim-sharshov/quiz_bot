from html import escape

from bot.utils.constants import MAX_CATEGORY_TITLE_LEN

ask_name_msg = "✏️ Пришлите название новой категории текстом."

title_empty_msg = "❌ Название не может быть пустым. Пришлите название ещё раз."

title_long_msg = (
    f"❌ Слишком длинное название. Максимум {MAX_CATEGORY_TITLE_LEN} символов. "
    f"Пришлите другое название."
)


def title_duplicate_msg(title: str) -> str:
    return f"❌ Категория «{escape(title)}» уже существует. Пришлите другое название."


def confirm_msg(title: str) -> str:
    return (
        f"Проверьте название:\n\n<b>{escape(title)}</b>\n\n"
        f"Подтвердить создание категории?"
    )


def saved_msg(title: str) -> str:
    return f"✅ Категория «{escape(title)}» сохранена."


cancelled_msg = "❌ Черновик категории удалён."
