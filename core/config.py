import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_ID: str = os.getenv("TELEGRAM_ADMIN_ID", "")
    LOG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    LOG_FILE: str = "cyber_pocket.log"
    TEMP_THRESHOLD: float = 85.0


settings = Settings()
