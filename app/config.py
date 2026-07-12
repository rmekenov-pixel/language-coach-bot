from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # WhatsApp Cloud API
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str
    whatsapp_api_version: str = "v21.0"

    # Groq API
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"

    # PostgreSQL
    database_url: str


settings = Settings()
