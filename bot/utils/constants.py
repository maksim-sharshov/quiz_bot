"""
Общие константы квиза «Крис».
"""

# --- Ограничения категорий и вопросов ---

# Максимальная длина названия категории
MAX_CATEGORY_TITLE_LEN = 100
# Минимальная длина названия категории
MIN_CATEGORY_TITLE_LEN = 1

# Максимальная длина текста вопроса
MAX_QUESTION_TEXT_LEN = 300
# Минимальное и максимальное число вариантов ответа
MIN_OPTIONS = 2
MAX_OPTIONS = 8
# Максимальная длина текста варианта / кнопки (лимит Telegram)
MAX_OPTION_TEXT_LEN = 64
# Максимальный размер загружаемого JSON-файла (в байтах)
MAX_JSON_FILE_SIZE = 512 * 1024

# --- Пагинация списков администратора ---

# Сколько вопросов показывать на одной странице
QUESTIONS_PAGE_SIZE = 8
# Сколько категорий показывать на одной странице
CATEGORIES_PAGE_SIZE = 10
# Обрезка текста вопроса в кнопке списка
QUESTION_BUTTON_PREVIEW_LEN = 50


# --- Комната ---

# Допустимые варианты таймера на вопрос (в секундах)
TIMER_CHOICES = (3, 5, 10, 15)

# Статусы комнаты
ROOM_OPEN = "open"
ROOM_IN_PROGRESS = "in_progress"
ROOM_FINISHED = "finished"
ROOM_INTERRUPTED = "interrupted"
# Активные статусы (в них категорию удалять нельзя)
ACTIVE_ROOM_STATUSES = (ROOM_OPEN, ROOM_IN_PROGRESS)

# Длина случайного кода комнаты
ROOM_CODE_LENGTH = 10


# --- Ход квиза ---

# Пауза перед следующим вопросом (секунды)
RESULT_PAUSE_SECONDS = 5
# Задержка между отправками при рассылке (соблюдение лимитов Telegram)
BROADCAST_DELAY_SECONDS = 0.05
# Размер пачки при рассылке
BROADCAST_BATCH_SIZE = 20

# Тайминги таймера вопроса
TIMER_TICK_SECONDS = 1
TIMER_BAR_FILLED = "🟩"
TIMER_BAR_EMPTY = "⬜"

# Значки мест в таблице лидеров
LEADERBOARD_TROPHY = "🏆"
