"""
FSM-состояния бота-квиза «Крис».
"""

from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    """Все состояния квиза (админ и игрок)."""

    # Админ вводит название новой категории
    waiting_category_name = State()
    # Админ присылает JSON-файл с вопросами
    waiting_questions_file = State()
    # Админ выбирает таймер для новой комнаты
    waiting_timer = State()
    # Игрок отвечает на текущий вопрос
    answering = State()
