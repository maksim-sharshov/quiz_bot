from datetime import datetime
from typing import TypeVar, Generic, Sequence

from sqlalchemy.exc import NoResultFound
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.future import select as sqlalchemy_select
from sqlalchemy.orm import Mapped, selectinload, load_only
from sqlalchemy.sql import select, update as sqlalchemy_update
from sqlalchemy import ForeignKey, Integer, Boolean, Text, UniqueConstraint

from db.psql.models.mapped_columns import *
from core.psql import async_db_session, Base


T = TypeVar("T")


class ModelAdmin(Generic[T]):
    
    class DoesNotExists(Exception):
        pass

    @classmethod
    async def create(cls, **kwargs) -> T:
        """
        # Создает новый объект и возвращает его.
        :param kwargs: Поля и значения для объекта.
        :return: Созданный объект.
        """

        async with async_db_session() as session:
            obj = cls(**kwargs)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    @classmethod
    async def add(cls, **kwargs) -> None:
        """
        # Создает новый объект.
        :param kwargs: Поля и значения для объекта.
        """

        async with async_db_session() as session:
            session.add(cls(**kwargs))
            await session.commit()

    async def update(self, **kwargs) -> T:
        """
        Обновляет текущий объект в базе и возвращает его заново (с актуальными данными).

        :param kwargs: Поля и значения, которые надо обновить.
        :return: Обновлённый объект
        """
        async with async_db_session() as session:
            stmt = sqlalchemy_update(self.__class__).where(
                self.__class__.id == self.id
            ).values(**kwargs)

            await session.execute(stmt)
            await session.commit()

            # Заново получаем объект из базы
            result = await session.execute(
                sqlalchemy_select(self.__class__).where(self.__class__.id == self.id)
            )
            updated_obj = result.scalar_one_or_none()

            return updated_obj

    async def delete(self) -> None:
        """
        # Удаляет объект.
        """
        async with async_db_session() as session:
            await session.delete(self)
            await session.commit()

    @classmethod
    async def check(cls, **kwargs) -> int | None:
        """
            Проверить наличие записи в таблице не тяжелым запросом и вернуть только его id
        :param kwargs: Id of obj
        """
        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls.id).where(*params)

        try:
            async with async_db_session() as session:
                results = await session.execute(query)
                (result,) = results.one()
                return result
        except NoResultFound:
            return None

    @classmethod
    async def get(cls, select_in_load: str | None = None, **kwargs) -> T:
        """
        # Возвращает одну запись, которая удовлетворяет введенным параметрам.

        :param select_in_load: Загрузить сразу связанную модель.
        :param kwargs: Поля и значения.
        :return: Объект или вызовет исключение DoesNotExists.
        """

        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        try:
            async with async_db_session() as session:
                results = await session.execute(query)
                (result,) = results.one()
                return result
        except NoResultFound:
            return None

    @classmethod
    async def get_first(cls, select_in_load: str | None = None, **kwargs) -> T | None:
        """
        Возвращает первую запись, удовлетворяющую условиям. 
        Безопасный аналог get(): не выбрасывает исключений при множественных результатах или их отсутствии.

        :param select_in_load: Имя связанной модели для подгрузки (если нужно).
        :param kwargs: Параметры фильтрации по полям модели.
        :return: Первая подходящая запись или None.
        """
        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query = query.options(selectinload(getattr(cls, select_in_load)))

        async with async_db_session() as session:
            results = await session.execute(query)
            row = results.first()
            if row:
                return row[0]
            return None

    @classmethod
    async def filter(cls, select_in_load: str | None = None, **kwargs) -> Sequence[T]:
        """
        # Возвращает все записи, которые удовлетворяют фильтру.

        :param select_in_load: Загрузить сразу связанную модель.
        :param kwargs: Поля и значения.
        :return: Перечень записей.
        """

        params = [getattr(cls, key) == val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        try:
            async with async_db_session() as session:
                results = await session.execute(query)
                return results.scalars().all()
        except NoResultFound:
            return ()

    @classmethod
    async def all(
            cls, select_in_load: str = None, values: list[str] = None
    ) -> Sequence[T]:
        """
        # Получает все записи.

        :param select_in_load: Загрузить сразу связанную модель.
        :param values: Список полей, которые надо вернуть, если нет, то все (default None).
        """

        if values and isinstance(values, list):
            # Определенные поля
            values = [getattr(cls, val) for val in values if isinstance(val, str)]
            query = select(cls).options(load_only(*values))
        else:
            # Все поля
            query = select(cls)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        async with async_db_session() as session:
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def exclude(cls, select_in_load: str | None = None, **kwargs) -> Sequence[T]:
        """
        # Возвращает все записи, которые не удовлетворяют фильтру (то есть, исключает значения).
        :param select_in_load: Загрузить сразу связанную модель.
        :param kwargs: Поля и значения для исключения.
        :return: Перечень записей.
        """
        # Строим условия для исключения (не равно)
        params = [getattr(cls, key) != val for key, val in kwargs.items()]
        query = select(cls).where(*params)

        if select_in_load:
            query.options(selectinload(getattr(cls, select_in_load)))

        async with async_db_session() as session:
            result = await session.execute(query)
            return result.scalars().all()


# Хранение всех пользователей
class Users(Base, ModelAdmin):
    
    __tablename__ = 'users'

    id: Mapped[intpk]
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None]
    role: Mapped[str] = mapped_column(
        default='user',
        comment='Роль пользователя'
    )
    date_registration: Mapped[datetime] = mapped_column(default=now_moscow)


# Актуальный список фьючерсов для анализа
class Futures(Base, ModelAdmin):
    
    __tablename__ = 'futures'

    id: Mapped[int] = mapped_column(primary_key=True)
    futures: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


# Для хранения данных по VA фьючерсам.
class VAFuturesData(Base, ModelAdmin):

    __tablename__ = "va_futures_data"

    id: Mapped[intpk]
    date: Mapped[datetime] = mapped_column(default=now_moscow)
    futures: Mapped[str]
    timeframe: Mapped[str]
    price: Mapped[float]
    percent: Mapped[float] = mapped_column(comment="Сколько осталось до ближ. уровня в %")
    info: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Структурированные данные по VA (пример: {'4h': {'vah':123, 'poc':2342, 'val':23432}, '1h': {...}})"
    )


# --- Квиз «Крис» ---

# Категории вопросов
class QuizCategories(Base, ModelAdmin):

    __tablename__ = "quiz_categories"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(240), unique=True, comment="Название категории")
    date_registration: Mapped[datetime] = mapped_column(default=now_moscow)


# Вопросы категорий
class QuizQuestions(Base, ModelAdmin):

    __tablename__ = "quiz_questions"

    id: Mapped[intpk]
    category_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_categories.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, comment="Формулировка вопроса")
    # [{"text": str, "is_correct": bool}, ...]
    options: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    date_registration: Mapped[datetime] = mapped_column(default=now_moscow)


# Комнаты квиза
class QuizRooms(Base, ModelAdmin):

    __tablename__ = "quiz_rooms"

    id: Mapped[intpk]
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="Код приглашения")
    category_id: Mapped[int] = mapped_column(ForeignKey("quiz_categories.id", ondelete="CASCADE"))
    timer_sec: Mapped[int] = mapped_column(Integer, default=10, comment="Секунд на вопрос")
    status: Mapped[str] = mapped_column(
        String(32), default="open", index=True,
        comment="open / in_progress / finished / interrupted"
    )
    admin_tg_id: Mapped[int] = mapped_column(BigInteger)
    admin_chat_id: Mapped[int] = mapped_column(BigInteger)
    admin_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    date_created: Mapped[datetime] = mapped_column(default=now_moscow)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)


# Игроки комнаты
class QuizRoomPlayers(Base, ModelAdmin):

    __tablename__ = "quiz_room_players"

    id: Mapped[intpk]
    room_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_rooms.id", ondelete="CASCADE"), index=True
    )
    tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    username: Mapped[str | None]
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    score: Mapped[int] = mapped_column(Integer, default=0)
    lobby_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(default=now_moscow)

    __table_args__ = (UniqueConstraint("room_id", "tg_id", name="uq_room_player"),)


# История ответов игроков
class QuizRoomAnswers(Base, ModelAdmin):

    __tablename__ = "quiz_room_answers"

    id: Mapped[intpk]
    room_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_rooms.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    selected: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    points: Mapped[int] = mapped_column(Integer, default=0)
    date_answer: Mapped[datetime] = mapped_column(default=now_moscow)