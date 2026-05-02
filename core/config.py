import os
import platform
from dotenv import load_dotenv

load_dotenv()


def _detect_os() -> str:
    """Автоопределение ОС. Можно переопределить через OS_TYPE в .env."""
    override = os.getenv("OS_TYPE", "").strip().lower()
    if override in ("windows", "linux"):
        return override
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    return "linux"


class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_ID: str = os.getenv("TELEGRAM_ADMIN_ID", "")
    LOG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    LOG_FILE: str = "cyber_pocket.log"
    TEMP_THRESHOLD: float = 85.0
    OS_TYPE: str = _detect_os()

    @property
    def IS_WINDOWS(self) -> bool:
        return self.OS_TYPE == "windows"


settings = Settings()
