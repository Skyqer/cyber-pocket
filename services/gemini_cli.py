import asyncio
import shutil
from core.logger import logger

# Чёрный список опасных команд/подстрок
_DANGEROUS = [
    # Удаление файлов / директорий
    "rm -rf", "rm -r /", "rm -f", "rmdir", "unlink ",
    "shred ", "trash ",
    # Форматирование / диски
    "mkfs", "dd if=", "wipefs", "fdisk", "parted",
    # Перезагрузка / выключение
    "reboot", "shutdown", "poweroff", "halt", "init 0", "init 6",
    # Опасные системные действия
    "chmod 777", ":(){ :|:& };:", "fork bomb",
    "> /dev/sd", "systemctl stop", "systemctl disable", "kill -9 1",
]

# Запрещённые действия в промпте (чтобы не просили gemini запускать программы)
_BLOCKED_PROMPTS = [
    "sudo ", "apt ", "pacman ", "yay ",
    "удали", "delete ", "remove ",
]


def _is_safe(text: str) -> bool:
    """Проверяет, нет ли в тексте опасных команд."""
    lower = text.lower()
    return not any(d in lower for d in _DANGEROUS)


def _is_prompt_safe(prompt: str) -> bool:
    """Проверяет, не просит ли пользователь выполнить что-то опасное."""
    lower = prompt.lower().strip()
    return not any(b in lower for b in _BLOCKED_PROMPTS)


async def ask_gemini(prompt: str, timeout: int = 120) -> str:
    """
    Отправляет запрос в Gemini CLI и возвращает ответ.
    Безопасно: auto_edit mode, без shell=True, с таймаутом, с фильтрацией.
    Может создавать/редактировать файлы, но НЕ удалять.
    """
    # Проверяем промпт на опасность
    if not _is_prompt_safe(prompt):
        logger.warning(f"Blocked dangerous prompt: {prompt[:100]}")
        return (
            "🚫 Я не могу выполнять команды на ПК.\n"
            "Я только анализирую, объясняю и даю подсказки.\n\n"
            "Попробуйте спросить что-нибудь вроде:\n"
            "• /ask Что такое load average?\n"
            "• /ask Почему CPU на 100%?\n"
            "• /ask Как обновить Arch Linux безопасно?"
        )

    # Проверяем, установлен ли gemini
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        return "⚠️ Gemini CLI не найден. Установите: npm install -g @google/gemini-cli"

    # Добавляем контекст к промпту
    safe_prompt = (
        f"Ты — ИТ-помощник. Отвечай на русском языке. "
        f"ВЫВОДИ ответ исключительно как ПРОСТОЙ ТЕКСТ. НЕ используй Markdown-разметку (никаких бэктиков, звездочек). "
        f"НИКОГДА НЕ СОЗДАВАЙ файлы. "
        f"НИКОГДА НЕ удаляй файлы и директории. "
        f"НЕ используй команды rm, rmdir, unlink, shred. "
        f"НЕ выполняй sudo и НЕ устанавливай пакеты.\n\n"
        f"Вопрос: {prompt}"
    )

    logger.info(f"Gemini запрос: {prompt[:100]}...")

    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            gemini_path,
            "-p", safe_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )

        output = stdout.decode("utf-8", errors="replace").strip()
        errors = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            logger.error(f"Gemini error (code {process.returncode}): {errors}")
            return f"⚠️ Gemini вернул ошибку:\n<code>{errors[:500]}</code>"

        if not output:
            return "Gemini вернул пустой ответ."

        # Проверяем ответ на опасные команды
        if not _is_safe(output):
            logger.warning(f"Gemini предложил потенциально опасное: {output[:200]}")
            return (
                "⚠️ Gemini предложил потенциально опасную команду.\n"
                "Ответ заблокирован из соображений безопасности.\n"
                "Попробуйте переформулировать вопрос."
            )

        logger.info(f"Gemini ответ: {output[:100]}...")
        return output

    except asyncio.TimeoutError:
        # Убиваем зависший процесс
        if process is not None:
            try:
                process.kill()
            except Exception:
                pass
        logger.warning("Gemini timeout")
        return "⏳ Gemini не ответил за 2 минуты. Попробуйте позже или упростите вопрос."
    except Exception as e:
        logger.error(f"Gemini exception: {e}")
        return f"⚠️ Ошибка при вызове Gemini: {e}"
