"""
Генерация кодов комнат.
"""

import secrets
import string

from bot.utils.constants import ROOM_CODE_LENGTH

# Алфавит без похожих символов (0/O, 1/l/I)
_ALPHABET = "".join(
    c for c in string.ascii_uppercase + string.digits if c not in "O0I1L"
)


def generate_room_code() -> str:
    """
    Сгенерировать трудно угадываемый код комнаты.
    """
    return "".join(secrets.choice(_ALPHABET) for _ in range(ROOM_CODE_LENGTH))
