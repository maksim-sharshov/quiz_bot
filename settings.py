from aiogram.types import BotCommand
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    NAME: str
    HOST: str
    PORT: int
    PASSWORD: str
    USER: str

    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    class Config:
        env_prefix = 'POSTGRES_'
        env_file = '.env'
        extra = 'ignore'


class BotConfig(BaseSettings):
    TOKEN: str
    ADMINS: list[int] | None = []
    COMMANDS: list[BotCommand] = [
        BotCommand(command='start', description='Запустить бота 🚀')
    ]

    class Config:
        env_prefix = 'BOT_'
        env_file = '.env'
        extra = 'ignore'


class WebhookConfig(BaseSettings):
    # Публичный HTTPS-адрес бота без пути, например https://bot.example.com
    # Если пусто — бот работает через long polling (удобно для локальной разработки).
    BASE_URL: str = ""
    # Путь, на который Telegram будет присылать обновления
    PATH: str = "/webhook"
    # Секрет для проверки заголовка X-Telegram-Bot-Api-Secret-Token
    SECRET: str = ""
    # Адрес и порт локального HTTP-сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    # Удалять накопившиеся обновления при установке webhook
    DROP_PENDING: bool = False

    @property
    def URL(self) -> str:
        return f"{self.BASE_URL.rstrip('/')}/{self.PATH.lstrip('/')}"

    class Config:
        env_prefix = 'WEBHOOK_'
        env_file = '.env'
        extra = 'ignore'


class Settings:
    postgres = PostgresConfig()
    bot = BotConfig()
    webhook = WebhookConfig()


settings = Settings()