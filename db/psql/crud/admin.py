"""
Модуль расширенной работы с БД для квиза «Крис».

Собран в том же стиле, что и `db/psql/models/models.py` (асинхронные сессии,
выражения SQLAlchemy), но добавляет удобные функции под сценарии квиза:
категории, вопросы, комнаты, игроки и история ответов.
"""

from sqlalchemy import select, delete as sqlalchemy_delete, func, update as sqlalchemy_update

from core.psql import async_db_session
from db.psql.models.mapped_columns import now_moscow
from db.psql.models.models import (
    QuizCategories,
    QuizQuestions,
    QuizRooms,
    QuizRoomPlayers,
    QuizRoomAnswers,
)

from bot.utils.constants import ACTIVE_ROOM_STATUSES, ROOM_INTERRUPTED


# --- Категории ---

async def get_categories() -> list[QuizCategories]:
    """Все категории по алфавиту."""
    async with async_db_session() as session:
        result = await session.execute(select(QuizCategories).order_by(QuizCategories.title))
        return list(result.scalars().all())


async def get_category(category_id: int) -> QuizCategories | None:
    """Категория по id."""
    async with async_db_session() as session:
        return await session.get(QuizCategories, category_id)


async def get_category_by_title(title: str) -> QuizCategories | None:
    """Категория по точному названию (для проверки дубликатов)."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizCategories.id).where(QuizCategories.title == title)
        )
        return result.scalar_one_or_none()


async def create_category(title: str) -> QuizCategories:
    """Создать категорию."""
    async with async_db_session() as session:
        category = QuizCategories(title=title)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


async def delete_category_with_questions(category_id: int) -> int:
    """
    Удалить категорию вместе со всеми её вопросами.
    Возвращает количество удалённых вопросов.
    """
    async with async_db_session() as session:
        questions = await session.execute(
            select(func.count(QuizQuestions.id)).where(QuizQuestions.category_id == category_id)
        )
        count = questions.scalar_one()

        await session.execute(
            sqlalchemy_delete(QuizQuestions).where(QuizQuestions.category_id == category_id)
        )
        await session.execute(
            sqlalchemy_delete(QuizCategories).where(QuizCategories.id == category_id)
        )
        await session.commit()
        return int(count)


# --- Вопросы ---

async def get_questions(category_id: int) -> list[QuizQuestions]:
    """Все вопросы категории в порядке добавления."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizQuestions)
            .where(QuizQuestions.category_id == category_id)
            .order_by(QuizQuestions.id)
        )
        return list(result.scalars().all())


async def get_question(question_id: int) -> QuizQuestions | None:
    """Вопрос по id."""
    async with async_db_session() as session:
        return await session.get(QuizQuestions, question_id)


async def count_questions(category_id: int) -> int:
    """Сколько вопросов в категории."""
    async with async_db_session() as session:
        result = await session.execute(
            select(func.count(QuizQuestions.id)).where(QuizQuestions.category_id == category_id)
        )
        return int(result.scalar_one())


async def add_questions(category_id: int, questions: list[dict]) -> int:
    """
    Добавить вопросы к категории (старые остаются на месте).
    `questions` — список вида [{"text": str, "options": [...]}, ...].
    Возвращает количество добавленных вопросов.
    """
    async with async_db_session() as session:
        session.add_all(
            [
                QuizQuestions(
                    category_id=category_id,
                    text=item["text"],
                    options=item["options"],
                )
                for item in questions
            ]
        )
        await session.commit()
        return len(questions)


async def delete_question(question_id: int) -> bool:
    """Удалить один вопрос. True — если что-то удалили."""
    async with async_db_session() as session:
        result = await session.execute(
            sqlalchemy_delete(QuizQuestions).where(QuizQuestions.id == question_id)
        )
        await session.commit()
        return bool(result.rowcount)


# --- Комнаты ---

async def create_room(
    code: str,
    category_id: int,
    timer_sec: int,
    admin_tg_id: int,
    admin_chat_id: int,
) -> QuizRooms:
    """Создать комнату квиза."""
    async with async_db_session() as session:
        room = QuizRooms(
            code=code,
            category_id=category_id,
            timer_sec=timer_sec,
            admin_tg_id=admin_tg_id,
            admin_chat_id=admin_chat_id,
            status="open",
        )
        session.add(room)
        await session.commit()
        await session.refresh(room)
        return room


async def get_room(room_id: int) -> QuizRooms | None:
    """Комната по id."""
    async with async_db_session() as session:
        return await session.get(QuizRooms, room_id)


async def get_room_by_code(code: str) -> QuizRooms | None:
    """Комната по коду приглашения."""
    async with async_db_session() as session:
        result = await session.execute(select(QuizRooms).where(QuizRooms.code == code))
        return result.scalar_one_or_none()


async def get_active_rooms() -> list[QuizRooms]:
    """Комнаты в статусах «открыта» / «идёт квиз»."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizRooms).where(QuizRooms.status.in_(ACTIVE_ROOM_STATUSES))
        )
        return list(result.scalars().all())


async def category_in_active_room(category_id: int) -> bool:
    """Используется ли категория в активной комнате."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizRooms.id).where(
                QuizRooms.category_id == category_id,
                QuizRooms.status.in_(ACTIVE_ROOM_STATUSES),
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None


async def set_room_status(room_id: int, status: str, finish: bool = False) -> None:
    """Сменить статус комнаты (опционально проставить время завершения)."""
    values: dict = {"status": status}
    if finish:
        values["finished_at"] = now_moscow()
    async with async_db_session() as session:
        await session.execute(
            sqlalchemy_update(QuizRooms).where(QuizRooms.id == room_id).values(**values)
        )
        await session.commit()


async def set_admin_message(room_id: int, message_id: int) -> None:
    """Запомнить id сообщения-панели администратора."""
    async with async_db_session() as session:
        await session.execute(
            sqlalchemy_update(QuizRooms).where(QuizRooms.id == room_id).values(
                admin_message_id=message_id
            )
        )
        await session.commit()


async def mark_active_rooms_interrupted() -> list[QuizRooms]:
    """
    Пометить активные комнаты прерванными (вызывается при старте бота).
    Возвращает список затронутых комнат.
    """
    rooms = await get_active_rooms()
    async with async_db_session() as session:
        for room in rooms:
            await session.execute(
                sqlalchemy_update(QuizRooms)
                .where(QuizRooms.id == room.id)
                .values(status=ROOM_INTERRUPTED, finished_at=now_moscow())
            )
        await session.commit()
    return rooms


# --- Игроки ---

async def get_player(room_id: int, tg_id: int) -> QuizRoomPlayers | None:
    """Игрок в конкретной комнате."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizRoomPlayers).where(
                QuizRoomPlayers.room_id == room_id,
                QuizRoomPlayers.tg_id == tg_id,
            )
        )
        return result.scalar_one_or_none()


async def get_player_any_room(tg_id: int) -> QuizRoomPlayers | None:
    """Активное участие игрока в любой комнате (для запрета двух комнат)."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizRoomPlayers)
            .join(QuizRooms, QuizRooms.id == QuizRoomPlayers.room_id)
            .where(
                QuizRoomPlayers.tg_id == tg_id,
                QuizRoomPlayers.is_active.is_(True),
                QuizRooms.status.in_(ACTIVE_ROOM_STATUSES),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()


async def add_player(room_id: int, tg_id: int, username: str | None) -> QuizRoomPlayers:
    """Добавить игрока в комнату (или вернуть существующего и реактивировать)."""
    async with async_db_session() as session:
        result = await session.execute(
            select(QuizRoomPlayers).where(
                QuizRoomPlayers.room_id == room_id,
                QuizRoomPlayers.tg_id == tg_id,
            )
        )
        player = result.scalar_one_or_none()

        if player:
            player.is_active = True
            player.username = username
            await session.commit()
            await session.refresh(player)
            return player

        player = QuizRoomPlayers(room_id=room_id, tg_id=tg_id, username=username, is_active=True)
        session.add(player)
        await session.commit()
        await session.refresh(player)
        return player


async def get_room_players(room_id: int, active_only: bool = True) -> list[QuizRoomPlayers]:
    """Игроки комнаты."""
    async with async_db_session() as session:
        query = select(QuizRoomPlayers).where(QuizRoomPlayers.room_id == room_id)
        if active_only:
            query = query.where(QuizRoomPlayers.is_active.is_(True))
        query = query.order_by(QuizRoomPlayers.score.desc(), QuizRoomPlayers.date_joined)
        result = await session.execute(query)
        return list(result.scalars().all())


async def count_active_players(room_id: int) -> int:
    """Количество активных игроков в комнате."""
    async with async_db_session() as session:
        result = await session.execute(
            select(func.count(QuizRoomPlayers.id)).where(
                QuizRoomPlayers.room_id == room_id,
                QuizRoomPlayers.is_active.is_(True),
            )
        )
        return int(result.scalar_one())


async def remove_player(room_id: int, tg_id: int) -> bool:
    """Пометить игрока неактивным (выход из комнаты)."""
    async with async_db_session() as session:
        result = await session.execute(
            sqlalchemy_update(QuizRoomPlayers)
            .where(QuizRoomPlayers.room_id == room_id, QuizRoomPlayers.tg_id == tg_id)
            .values(is_active=False)
        )
        await session.commit()
        return bool(result.rowcount)


async def set_lobby_message(room_id: int, tg_id: int, message_id: int) -> None:
    """Запомнить id лобби-сообщения игрока."""
    async with async_db_session() as session:
        await session.execute(
            sqlalchemy_update(QuizRoomPlayers)
            .where(QuizRoomPlayers.room_id == room_id, QuizRoomPlayers.tg_id == tg_id)
            .values(lobby_message_id=message_id)
        )
        await session.commit()


async def add_score(room_id: int, tg_id: int, points: int) -> None:
    """Начислить игроку баллы."""
    if points <= 0:
        return
    async with async_db_session() as session:
        await session.execute(
            sqlalchemy_update(QuizRoomPlayers)
            .where(QuizRoomPlayers.room_id == room_id, QuizRoomPlayers.tg_id == tg_id)
            .values(score=QuizRoomPlayers.score + points)
        )
        await session.commit()


async def reset_scores(room_id: int) -> None:
    """Обнулить баллы всех игроков комнаты (перед новым квизом)."""
    async with async_db_session() as session:
        await session.execute(
            sqlalchemy_update(QuizRoomPlayers)
            .where(QuizRoomPlayers.room_id == room_id)
            .values(score=0)
        )
        await session.commit()


async def save_answer(
    room_id: int, question_id: int, tg_id: int, selected: list, points: int
) -> None:
    """Сохранить ответ игрока на вопрос (история)."""
    async with async_db_session() as session:
        session.add(
            QuizRoomAnswers(
                room_id=room_id,
                question_id=question_id,
                tg_id=tg_id,
                selected=list(selected),
                points=points,
            )
        )
        await session.commit()
