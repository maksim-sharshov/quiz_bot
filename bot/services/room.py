"""
Управление комнатами квиза: создание, вход/выход, счётчики, статусы.
"""

import logging

from aiogram import Bot

import bot.services.broadcast as b
import bot.templates.admin.room as t_admin_room
import bot.templates.user.game as t_user_game
import bot.templates.user.room as t_user_room
import bot.keyboards.admin.room as k_admin_room
import bot.keyboards.user.room as k_user_room
import bot.utils as u
import db.psql.crud.admin as db_admin

logger = logging.getLogger(__name__)

_bot_username: str | None = None


async def _get_bot_username(bot: Bot) -> str:
    global _bot_username
    if not _bot_username:
        me = await bot.get_me()
        _bot_username = me.username
    return _bot_username


async def invite_link(bot: Bot, code: str) -> str:
    """Ссылка-приглашение в комнату."""
    username = await _get_bot_username(bot)
    return f"https://t.me/{username}?start=room_{code}"


async def create_room(
    bot: Bot,
    admin_tg_id: int,
    admin_chat_id: int,
    category_id: int,
    timer_sec: int,
    admin_username: str | None = None,
    admin_first_name: str | None = None,
    admin_last_name: str | None = None,
):
    """Создать комнату с уникальным кодом. Администратор сразу становится участником."""
    code = u.generate_room_code()
    while await db_admin.get_room_by_code(code):
        code = u.generate_room_code()

    room = await db_admin.create_room(
        code=code,
        category_id=category_id,
        timer_sec=timer_sec,
        admin_tg_id=admin_tg_id,
        admin_chat_id=admin_chat_id,
    )
    await db_admin.add_player(
        room.id,
        admin_tg_id,
        admin_username,
        first_name=admin_first_name,
        last_name=admin_last_name,
    )
    logger.info("Создана комната %s (код %s) для категории %s", room.id, code, category_id)
    return room


async def try_join(
    bot: Bot,
    room,
    tg_id: int,
    username: str | None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> str:
    """
    Попытка входа игрока в комнату.
    Возвращает: "busy" | "already" | "joined".
    """
    busy = await db_admin.get_player_any_room(tg_id)
    if busy and busy.room_id != room.id:
        return "busy"

    existing = await db_admin.get_player(room.id, tg_id)
    if existing and existing.is_active:
        return "already"

    await db_admin.add_player(
        room.id,
        tg_id,
        username,
        first_name=first_name,
        last_name=last_name,
    )
    return "joined"


async def enter_room(
    bot: Bot,
    chat_id: int,
    tg_id: int,
    username: str | None,
    code: str,
    first_name: str | None = None,
    last_name: str | None = None,
) -> str:
    """
    Полный вход в комнату по коду (для игрока и администратора).
    Отправляет игроку лобби и обновляет панели.
    Возвращает: "not_found" | "finished" | "closed" | "busy" | "already" | "joined" | "unreachable".
    """
    room = await db_admin.get_room_by_code(code)
    if room is None:
        return "not_found"

    if room.status in (u.ROOM_FINISHED, u.ROOM_INTERRUPTED):
        return "finished"
    if room.status != u.ROOM_OPEN:
        return "closed"

    status = await try_join(
        bot,
        room,
        tg_id,
        username,
        first_name=first_name,
        last_name=last_name,
    )
    if status != "joined":
        return status

    category = await db_admin.get_category(room.category_id)
    title = category.title if category else ""
    players = await db_admin.get_room_players(room.id)
    names = [u.display_name(player) for player in players]

    try:
        lobby = await b.safe_send(
            bot,
            chat_id,
            t_user_room.room_lobby_msg(title, room.timer_sec, names),
            k_user_room.room_lobby_keyb(room.id),
        )
    except b.PlayerUnreachable:
        await leave_player(bot, room, tg_id)
        return "unreachable"

    if lobby is not None:
        await db_admin.set_lobby_message(room.id, tg_id, lobby.message_id)
    await refresh_room_messages(bot, room)
    return "joined"


async def leave_player(bot: Bot, room, tg_id: int) -> bool:
    """Выход игрока из комнаты с обновлением счётчиков."""
    removed = await db_admin.remove_player(room.id, tg_id)
    if removed:
        logger.info("Игрок %s вышел из комнаты %s", tg_id, room.id)
        await refresh_room_messages(bot, room)
    return removed


async def refresh_room_messages(bot: Bot, room) -> None:
    """Обновить панель администратора и лобби всех игроков (участники и их имена)."""
    fresh = await db_admin.get_room(room.id) or room
    category = await db_admin.get_category(fresh.category_id)
    title = category.title if category else ""
    players = await db_admin.get_room_players(fresh.id)
    names = [u.display_name(player) for player in players]
    link = await invite_link(bot, fresh.code)

    if fresh.admin_message_id:
        await b.safe_edit_text(
            bot,
            fresh.admin_chat_id,
            fresh.admin_message_id,
            t_admin_room.room_panel_msg(title, fresh.timer_sec, names, link),
            k_admin_room.room_control_keyb(fresh.id, started=fresh.status == u.ROOM_IN_PROGRESS),
        )

    for player in players:
        if player.lobby_message_id:
            await b.safe_edit_text(
                bot,
                player.tg_id,
                player.lobby_message_id,
                t_user_room.room_lobby_msg(title, fresh.timer_sec, names),
                k_user_room.room_lobby_keyb(fresh.id),
            )


async def notify_admin_started(bot: Bot, room) -> None:
    """Сообщить администратору о старте квиза."""
    fresh = await db_admin.get_room(room.id) or room
    category = await db_admin.get_category(fresh.category_id)
    title = category.title if category else ""
    if fresh.admin_message_id:
        await b.safe_edit_text(
            bot,
            fresh.admin_chat_id,
            fresh.admin_message_id,
            t_admin_room.quiz_started_msg(title),
            k_admin_room.room_control_keyb(fresh.id, started=True),
        )


async def notify_admin_finished(bot: Bot, room) -> None:
    """Сообщить администратору о завершении квиза."""
    fresh = await db_admin.get_room(room.id) or room
    category = await db_admin.get_category(fresh.category_id)
    title = category.title if category else ""
    if fresh.admin_message_id:
        await b.safe_edit_text(
            bot,
            fresh.admin_chat_id,
            fresh.admin_message_id,
            t_admin_room.quiz_finished_msg(title),
            k_admin_room.empty_keyb,
        )


async def cleanup_interrupted(bot: Bot) -> list:
    """
    Пометить активные комнаты прерванными при старте бота
    и уведомить администратора и игроков.
    """
    rooms = await db_admin.mark_active_rooms_interrupted()
    for room in rooms:
        category = await db_admin.get_category(room.category_id)
        title = category.title if category else ""

        await b.safe_send(bot, room.admin_chat_id, t_admin_room.interrupted_msg(title))

        players = await db_admin.get_room_players(room.id)
        for player in players:
            await b.safe_send(bot, player.tg_id, t_user_game.interrupted_msg)

        logger.info("Комната %s помечена прерванной", room.id)

    return rooms
