from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.admin.start import AdminMenuCB
from bot.utils.constants import (
    CATEGORIES_PAGE_SIZE,
    QUESTION_BUTTON_PREVIEW_LEN,
    QUESTIONS_PAGE_SIZE,
)


class CategoryOpenCB(CallbackData, prefix="a_cat_open"):
    category_id: int


class CategoryPageCB(CallbackData, prefix="a_cat_page"):
    page: int


class QuestionPageCB(CallbackData, prefix="a_q_page"):
    category_id: int
    page: int


class QuestionOpenCB(CallbackData, prefix="a_q_open"):
    category_id: int
    question_id: int


class QuestionDeleteCB(CallbackData, prefix="a_q_del"):
    category_id: int
    question_id: int


class CategoryDeleteCB(CallbackData, prefix="a_cat_del"):
    action: str
    category_id: int


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def categories_keyb(categories: list, page: int) -> InlineKeyboardMarkup:
    """Список категорий с постраничной навигацией."""
    start = page * CATEGORIES_PAGE_SIZE
    end = start + CATEGORIES_PAGE_SIZE
    page_items = categories[start:end]

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=_shorten(category.title, 60),
                callback_data=CategoryOpenCB(category_id=category.id).pack(),
            )
        ]
        for category in page_items
    ]

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(text="◀️", callback_data=CategoryPageCB(page=page - 1).pack())
        )
    if end < len(categories):
        nav.append(
            InlineKeyboardButton(text="▶️", callback_data=CategoryPageCB(page=page + 1).pack())
        )
    if nav:
        rows.append(nav)

    rows.append(
        [InlineKeyboardButton(text="Назад в меню", callback_data=AdminMenuCB(action="menu").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def no_categories_keyb() -> InlineKeyboardMarkup:
    """Заглушка, когда категорий нет."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Создать категорию",
                    callback_data=AdminMenuCB(action="create_category").pack(),
                    style=ButtonStyle.SUCCESS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню", callback_data=AdminMenuCB(action="menu").pack()
                )
            ],
        ]
    )


def questions_page_keyb(category_id: int, questions: list, page: int) -> InlineKeyboardMarkup:
    """Список вопросов категории с пагинацией и удалением категории."""
    start = page * QUESTIONS_PAGE_SIZE
    end = start + QUESTIONS_PAGE_SIZE
    page_items = questions[start:end]

    rows: list[list[InlineKeyboardButton]] = []
    for number, question in enumerate(page_items, start=start + 1):
        preview = _shorten(question.text, QUESTION_BUTTON_PREVIEW_LEN)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{number}. {preview}",
                    callback_data=QuestionOpenCB(
                        category_id=category_id, question_id=question.id
                    ).pack(),
                )
            ]
        )

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=QuestionPageCB(category_id=category_id, page=page - 1).pack(),
            )
        )
    if end < len(questions):
        nav.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=QuestionPageCB(category_id=category_id, page=page + 1).pack(),
            )
        )
    if nav:
        rows.append(nav)

    rows.append(
        [
            InlineKeyboardButton(
                text="Удалить категорию",
                callback_data=CategoryDeleteCB(action="ask", category_id=category_id).pack(),
                style=ButtonStyle.DANGER,
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data=AdminMenuCB(action="view_categories").pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_detail_keyb(category_id: int, question_id: int) -> InlineKeyboardMarkup:
    """Просмотр одного вопроса: удалить / назад к списку."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить вопрос",
                    callback_data=QuestionDeleteCB(
                        category_id=category_id, question_id=question_id
                    ).pack(),
                    style=ButtonStyle.DANGER,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=QuestionPageCB(category_id=category_id, page=0).pack(),
                )
            ],
        ]
    )


def category_delete_confirm_keyb(category_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления категории."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=CategoryDeleteCB(action="confirm", category_id=category_id).pack(),
                    style=ButtonStyle.DANGER,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=CategoryDeleteCB(action="cancel", category_id=category_id).pack(),
                )
            ],
        ]
    )
