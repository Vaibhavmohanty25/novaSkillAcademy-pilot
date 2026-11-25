
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "SalesPilot AI"
    database_url: str = "sqlite:///./salespilot.db"
    admin_api_key: str
    vapi_public_key: str = ""
    vapi_private_key: str = ""
    vapi_assistant_id: str = ""
    vapi_webhook_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
