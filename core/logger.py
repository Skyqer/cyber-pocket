import os
import logging
from logging.handlers import RotatingFileHandler
from core.config import settings

os.makedirs(settings.LOG_DIR, exist_ok=True)

_log_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE)

# Ротация: макс 5 МБ на файл, хранить 3 бэкапа
_handler = RotatingFileHandler(
    _log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
)

logger = logging.getLogger("cyber_pocket")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)

# Также выводим в консоль для отладки
_console = logging.StreamHandler()
_console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
logger.addHandler(_console)


def get_last_logs(n: int = 20) -> str:
    """Возвращает последние n строк из лог-файла."""
    if not os.path.exists(_log_path):
        return "Лог-файл пуст."
    with open(_log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    tail = lines[-n:] if len(lines) >= n else lines
    return "".join(tail) if tail else "Лог-файл пуст."
