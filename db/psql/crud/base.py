import logging
from sqlalchemy import text

from core.psql import async_db_session, engine
from db.psql.models.models import Base


# Лёгкие миграции для уже созданных таблиц (create_all не добавляет колонки).
_MIGRATIONS = (
    "ALTER TABLE quiz_room_players ADD COLUMN IF NOT EXISTS first_name VARCHAR(255)",
    "ALTER TABLE quiz_room_players ADD COLUMN IF NOT EXISTS last_name VARCHAR(255)",
)


async def init_postgres() -> bool:
    """
    Создать все таблицы в ядре
    :return: True or False
    """
    async with async_db_session() as s:
        try:

            await s.run_sync(
                lambda s_value: Base.metadata.create_all(
                    bind=s_value.bind
                )
            )
            for statement in _MIGRATIONS:
                await s.execute(text(statement))
            await s.commit()

            return True

        except Exception as e:
            logging.exception(e)
            return False