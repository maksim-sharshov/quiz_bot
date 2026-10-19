"""
Валидатор JSON-файла с вопросами.

Возвращаемые ошибки — это структура `(код, номер_вопроса)`, без
пользовательского текста. Текст для этих кодов лежит в шаблонах
(`bot/templates/admin/questions_add.py`), чтобы не дублировать UI-строки.
"""

import json

from bot.utils.constants import (
    MAX_JSON_FILE_SIZE,
    MAX_OPTION_TEXT_LEN,
    MAX_OPTIONS,
    MAX_QUESTION_TEXT_LEN,
    MIN_OPTIONS,
)


def parse_and_validate(raw: bytes) -> tuple[list[dict] | None, tuple | None]:
    """
    Полностью проверить содержимое файла.

    :param raw: байты файла
    :return: (список вопросов, None) при успехе или (None, (код, номер)) при ошибке
    """
    if len(raw) > MAX_JSON_FILE_SIZE:
        return None, ("too_large", 0)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, ("encoding", 0)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, ("invalid_json", 0)

    return validate_questions(data)


def validate_questions(data) -> tuple[list[dict] | None, tuple | None]:
    """
    Проверить структуру вопросов и нормализовать (обрезать пробелы).

    :param data: распарсенный JSON
    :return: (список вопросов, None) или (None, (код, номер))
    """
    if not isinstance(data, list):
        return None, ("root_not_list", 0)
    if not data:
        return None, ("empty_root", 0)

    normalized: list[dict] = []

    for index, question in enumerate(data, start=1):
        if not isinstance(question, dict):
            return None, ("question_not_object", index)

        text = question.get("text")
        if not isinstance(text, str) or not text.strip():
            return None, ("question_text", index)
        if len(text) > MAX_QUESTION_TEXT_LEN:
            return None, ("question_text_long", index)

        options = question.get("options")
        if not isinstance(options, list):
            return None, ("options_not_list", index)
        if len(options) < MIN_OPTIONS:
            return None, ("options_min", index)
        if len(options) > MAX_OPTIONS:
            return None, ("options_max", index)

        seen_texts: set[str] = set()
        has_correct = False
        norm_options: list[dict] = []

        for option in options:
            if not isinstance(option, dict):
                return None, ("option_not_object", index)

            opt_text = option.get("text")
            if not isinstance(opt_text, str) or not opt_text.strip():
                return None, ("option_text", index)
            if len(opt_text) > MAX_OPTION_TEXT_LEN:
                return None, ("option_text_long", index)

            is_correct = option.get("is_correct")
            if not isinstance(is_correct, bool):
                return None, ("option_is_correct", index)

            key = opt_text.strip().lower()
            if key in seen_texts:
                return None, ("option_duplicate", index)
            seen_texts.add(key)

            if is_correct:
                has_correct = True

            norm_options.append({"text": opt_text.strip(), "is_correct": is_correct})

        if not has_correct:
            return None, ("no_correct", index)

        normalized.append({"text": text.strip(), "options": norm_options})

    return normalized, None
