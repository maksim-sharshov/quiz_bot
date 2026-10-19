"""
Движок квиза: выдача вопросов, отдельный таймер на каждого игрока,
подсчёт очков, таблица лидеров и финализация.
"""

import asyncio
import logging
import random

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

import bot.keyboards.user.game as k_user_game
import bot.services.broadcast as b
import bot.services.room as room_service
import bot.services.scoring as scoring
import bot.templates.user.game as t_user_game
import bot.utils as u
import db.psql.crud.admin as db_admin

logger = logging.getLogger(__name__)

# Запущенные задачи квизов: room_id -> asyncio.Task
_running: dict[int, asyncio.Task] = {}


def is_running(room_id: int) -> bool:
    task = _running.get(room_id)
    return bool(task and not task.done())


async def start_quiz(bot: Bot, storage, room) -> bool:
    """Запустить квиз. False — если он уже идёт."""
    if is_running(room.id):
        return False

    await db_admin.reset_scores(room.id)
    await db_admin.set_room_status(room.id, u.ROOM_IN_PROGRESS)
    room.status = u.ROOM_IN_PROGRESS

    _running[room.id] = asyncio.create_task(_run_quiz(bot, storage, room))
    logger.info("Квиз комнаты %s запущен", room.id)
    return True


async def finish_early(bot: Bot, storage, room) -> None:
    """Досрочно завершить квиз по кнопке администратора."""
    task = _running.get(room.id)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await _finish(bot, storage, room)
    logger.info("Квиз комнаты %s завершён досрочно", room.id)


async def _run_quiz(bot: Bot, storage, room) -> None:
    try:
        questions = list(await db_admin.get_questions(room.category_id))
        random.shuffle(questions)
        total = len(questions)

        for index, question in enumerate(questions, start=1):
            players = await db_admin.get_room_players(room.id)
            if not players:
                logger.info("В комнате %s не осталось игроков — квиз остановлен", room.id)
                break

            options = list(question.options)
            random.shuffle(options)

            await _run_question(bot, storage, room, question, options, index, total)
            await asyncio.sleep(u.RESULT_PAUSE_SECONDS)

        await _finish(bot, storage, room)

    except asyncio.CancelledError:
        logger.info("Задача квиза комнаты %s отменена", room.id)
        raise
    except Exception:  # noqa: BLE001
        logger.exception("Ошибка хода квиза комнаты %s", room.id)
    finally:
        _running.pop(room.id, None)


async def _run_question(bot: Bot, storage, room, question, options, index: int, total: int) -> None:
    players = await db_admin.get_room_players(room.id)
    correct_count = sum(1 for option in options if option.get("is_correct"))
    multiple = correct_count > 1
    deadline = asyncio.get_running_loop().time() + room.timer_sec

    tasks = [
        asyncio.create_task(
            _ask_player(
                bot, storage, room, question, options, index, total, player, deadline, multiple
            )
        )
        for player in players
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    selected_map: dict[int, set[int]] = {}
    message_map: dict[int, int] = {}
    for player, result in zip(players, results):
        if isinstance(result, Exception):
            logger.warning("Таймер игрока %s завершился ошибкой: %s", player.tg_id, result)
            continue
        if not result:
            continue
        selected, message_id = result
        selected_map[player.tg_id] = selected
        message_map[player.tg_id] = message_id

    scorers: list[tuple[str, int]] = []
    for player in players:
        selected = selected_map.get(player.tg_id, set())
        points = scoring.compute_points(selected, options)
        await db_admin.add_score(room.id, player.tg_id, points)
        await db_admin.save_answer(room.id, question.id, player.tg_id, sorted(selected), points)
        if points > 0:
            scorers.append((player.username or f"Игрок {player.tg_id}", points))

    all_players = await db_admin.get_room_players(room.id)
    board = scoring.build_leaderboard(all_players)
    text = t_user_game.results_msg(scoring.correct_texts(options), scorers, board)

    # Итог вопроса показываем прямо в сообщении с вопросом у каждого игрока
    for player in all_players:
        message_id = message_map.get(player.tg_id)
        if message_id:
            await b.safe_edit_text(bot, player.tg_id, message_id, text, None)
            continue
        try:
            await b.safe_send(bot, player.tg_id, text)
        except b.PlayerUnreachable:
            await _drop_unreachable(bot, storage, room, player.tg_id)


async def _ask_player(
    bot: Bot,
    storage,
    room,
    question,
    options,
    index: int,
    total: int,
    player,
    deadline: float,
    multiple: bool,
) -> tuple[set[int], int] | None:
    """Отдельная задача таймера одного игрока."""
    key = StorageKey(bot_id=bot.id, chat_id=player.tg_id, user_id=player.tg_id)
    context = FSMContext(storage=storage, key=key)

    await context.set_state(u.QuizState.answering)
    await context.update_data(
        room_id=room.id,
        question_id=question.id,
        selected=[],
        options=options,
        finished=False,
    )

    bar = t_user_game.timer_bar(room.timer_sec, room.timer_sec)
    try:
        message = await b.safe_send(
            bot,
            player.tg_id,
            t_user_game.question_msg(
                bar, room.timer_sec, index, total, question.text, multiple
            ),
            k_user_game.answer_keyb(room.id, question.id, options, set()),
        )
    except b.PlayerUnreachable:
        await _drop_unreachable(bot, storage, room, player.tg_id)
        return None

    if message is None:
        return None

    await context.update_data(message_id=message.message_id)

    loop = asyncio.get_running_loop()
    for _ in range(room.timer_sec):
        await asyncio.sleep(u.TIMER_TICK_SECONDS)
        seconds_left = max(0, int(round(deadline - loop.time())))
        data = await context.get_data()
        selected = set(data.get("selected", []))
        await b.safe_edit_text(
            bot,
            player.tg_id,
            message.message_id,
            t_user_game.question_msg(
                t_user_game.timer_bar(seconds_left, room.timer_sec),
                seconds_left,
                index,
                total,
                question.text,
                multiple,
            ),
            k_user_game.answer_keyb(room.id, question.id, options, selected),
        )

    data = await context.get_data()
    selected = set(data.get("selected", []))

    await context.update_data(finished=True)
    await context.set_state(None)
    # Кнопки гасим, но текст вопроса не трогаем: итог придёт сразу после подсчёта
    await b.safe_edit_markup(bot, player.tg_id, message.message_id, k_user_game.empty_keyb)
    return selected, message.message_id


async def _drop_unreachable(bot: Bot, storage, room, tg_id: int) -> None:
    """Исключить заблокировавшего бота игрока и обновить счётчики."""
    logger.warning("Игрок %s недоступен, исключаю из комнаты %s", tg_id, room.id)
    await db_admin.remove_player(room.id, tg_id)
    await _clear_state(bot, storage, tg_id)
    await room_service.refresh_room_messages(bot, room)


async def _clear_state(bot: Bot, storage, tg_id: int) -> None:
    key = StorageKey(bot_id=bot.id, chat_id=tg_id, user_id=tg_id)
    try:
        await FSMContext(storage=storage, key=key).clear()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось очистить состояние игрока %s: %s", tg_id, exc)


async def _finish(bot: Bot, storage, room) -> None:
    players = await db_admin.get_room_players(room.id)
    board = scoring.build_leaderboard(players)
    unreachable = await b.broadcast(
        bot, [player.tg_id for player in players], t_user_game.final_msg(board)
    )

    for tg_id in unreachable:
        await db_admin.remove_player(room.id, tg_id)

    for player in players:
        await _clear_state(bot, storage, player.tg_id)

    await db_admin.set_room_status(room.id, u.ROOM_FINISHED, finish=True)
    room.status = u.ROOM_FINISHED
    await room_service.notify_admin_finished(bot, room)
