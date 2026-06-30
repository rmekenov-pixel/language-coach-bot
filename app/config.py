from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Все секреты и настройки приходят из переменных окружения (.env локально,
    или Variables в Railway). Никогда не хардкодим токены в коде.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- WhatsApp Cloud API (Meta) ---
    whatsapp_token: str  # временный или постоянный токен доступа Graph API
    whatsapp_phone_number_id: str  # ID тестового/боевого номера в Meta for Developers
    whatsapp_verify_token: str  # строка, которую ты сам придумываешь для верификации вебхука

    # --- Graph API base URL (редко меняется, но пусть будет настраиваемым) ---
    whatsapp_api_version: str = "v21.0"


settings = Settings()
