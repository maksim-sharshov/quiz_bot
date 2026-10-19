from html import escape

from bot.utils.constants import (
    MAX_OPTION_TEXT_LEN,
    MAX_OPTIONS,
    MIN_OPTIONS,
)

no_categories_msg = "📭 Категорий пока нет. Сначала создайте категорию."

choose_category_msg = "📂 Выберите категорию, в которую добавить вопросы:"


def ask_file_msg(category_title: str) -> str:
    return (
        f"📎 Пришлите <b>.json</b>-файл с вопросами для категории "
        f"«{escape(category_title)}». Новые вопросы добавятся к уже существующим."
    )


file_hint_msg = (
    "📄 Формат файла — массив вопросов:\n\n"
    "[\n"
    '  {\n'
    '    "text": "Текст вопроса",\n'
    '    "options": [\n'
    '      { "text": "Вариант", "is_correct": true },\n'
    '      { "text": "Вариант", "is_correct": false }\n'
    "    ]\n"
    "  }\n"
    "]\n\n"
    f"• вариантов в вопросе: от {MIN_OPTIONS} до {MAX_OPTIONS};\n"
    f"• текст варианта — не длиннее {MAX_OPTION_TEXT_LEN} символов;\n"
    "• правильных вариантов может быть один или несколько."
)

_ERRORS = {
    "too_large": "❌ Файл слишком большой.",
    "encoding": "❌ Файл должен быть в кодировке UTF-8.",
    "invalid_json": "❌ Не удалось прочитать JSON. Проверьте синтаксис.",
    "root_not_list": "❌ Корень файла должен быть списком вопросов.",
    "empty_root": "❌ Список вопросов пуст.",
    "question_not_object": "❌ Вопрос №{n}: должен быть объектом.",
    "question_text": "❌ Вопрос №{n}: отсутствует или пустой текст вопроса.",
    "question_text_long": "❌ Вопрос №{n}: слишком длинный текст вопроса.",
    "options_not_list": "❌ Вопрос №{n}: поле options должно быть списком.",
    "options_min": f"❌ Вопрос №{{n}}: нужно минимум {MIN_OPTIONS} варианта.",
    "options_max": f"❌ Вопрос №{{n}}: максимум {MAX_OPTIONS} вариантов.",
    "option_not_object": "❌ Вопрос №{n}: каждый вариант должен быть объектом.",
    "option_text": "❌ Вопрос №{n}: у варианта пустой текст.",
    "option_text_long": (
        f"❌ Вопрос №{{n}}: текст варианта длиннее {MAX_OPTION_TEXT_LEN} символов."
    ),
    "option_is_correct": "❌ Вопрос №{n}: поле is_correct должно быть true или false.",
    "option_duplicate": "❌ Вопрос №{n}: варианты ответа повторяются.",
    "no_correct": "❌ Вопрос №{n}: нет ни одного правильного варианта.",
}


wrong_ext_msg = "❌ Нужен файл с расширением .json. Пришлите файл ещё раз."


def error_msg(code: str, index: int = 0) -> str:
    """Текст ошибки валидатора по коду и номеру вопроса."""
    template = _ERRORS.get(code, "❌ Некорректный файл.")
    return template.format(n=index)


def questions_preview(questions: list[dict]) -> list[str]:
    """
    Собрать предпросмотр вопросов. Возвращает список сообщений,
    разбитых по лимиту Telegram.
    """
    header = f"✅ Файл корректен. Проверьте вопросы ({len(questions)} шт.):"

    blocks: list[str] = []
    for number, question in enumerate(questions, start=1):
        lines = [f"{number}. {escape(question['text'])}"]
        for option in question["options"]:
            mark = "✅ " if option["is_correct"] else "• "
            lines.append(f"{mark}{escape(option['text'])}")
        blocks.append("\n".join(lines))

    chunks: list[str] = []
    current = header
    for block in blocks:
        candidate = f"{current}\n\n{block}"
        if len(candidate) > 3500:
            chunks.append(current)
            current = block
        else:
            current = candidate
    chunks.append(current)
    return chunks


def added_msg(count: int, total: int) -> str:
    return f"✅ Добавлено вопросов: {count}. Теперь в категории: {total}."


cancelled_msg = "❌ Добавление вопросов отменено."
