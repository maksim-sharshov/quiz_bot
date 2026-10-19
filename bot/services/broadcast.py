"""
Безопасная рассылка и редактирование сообщений с учётом лимитов Telegram.
"""

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from bot.utils.constants import BROADCAST_BATCH_SIZE, BROADCAST_DELAY_SECONDS

logger = logging.getLogger(__name__)


class PlayerUnreachable(Exception):
    """Игрок заблокировал бота или недоступен для сообщений."""

    def __init__(self, tg_id: int):
        self.tg_id = tg_id
        super().__init__(f"Игрок {tg_id} недоступен")


async def safe_send(bot: Bot, tg_id: int, text: str, reply_markup=None):
    """
    Отправить сообщение. При блокировке бота — PlayerUnreachable.
    Прочие ошибки логируются и возвращают None.
    """
    try:
        return await bot.send_message(chat_id=tg_id, text=text, reply_markup=reply_markup)
    except TelegramForbiddenError as exc:
        raise PlayerUnreachable(tg_id) from exc
    except TelegramRetryAfter as exc:
        await asyncio.sleep(exc.retry_after + 1)
        try:
            return await bot.send_message(chat_id=tg_id, text=text, reply_markup=reply_markup)
        except Exception as retry_exc:  # noqa: BLE001
            logger.warning("Повторная отправка игроку %s не удалась: %s", tg_id, retry_exc)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось отправить сообщение игроку %s: %s", tg_id, exc)
        return None


async def safe_edit_text(bot: Bot, chat_id: int, message_id: int, text: str, reply_markup=None) -> bool:
    """
    Отредактировать текст сообщения. Гасит ошибку «message is not modified».
    Возвращает True при успехе.
    """
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return True
        logger.warning("Не удалось изменить сообщение %s: %s", message_id, exc)
        return False
    except TelegramForbiddenError:
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось изменить сообщение %s: %s", message_id, exc)
        return False


async def safe_edit_markup(bot: Bot, chat_id: int, message_id: int, reply_markup) -> None:
    """Отредактировать только клавиатуру сообщения, гася «message is not modified»."""
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        logger.warning("Не удалось изменить клавиатуру сообщения %s: %s", message_id, exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось изменить клавиатуру сообщения %s: %s", message_id, exc)


async def broadcast(bot: Bot, tg_ids: list[int], text: str, reply_markup=None) -> list[int]:
    """
    Разослать текст списку игроков с паузами между пачками.
    Возвращает список недоступных игроков.
    """
    unreachable: list[int] = []
    for index, tg_id in enumerate(tg_ids, start=1):
        try:
            await safe_send(bot, tg_id, text, reply_markup)
        except PlayerUnreachable:
            unreachable.append(tg_id)
        if index % BROADCAST_BATCH_SIZE == 0:
            await asyncio.sleep(BROADCAST_DELAY_SECONDS)
    return unreachable
