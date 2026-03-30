from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton

from core.config import settings
from core.logger import logger, get_last_logs
from services.system_monitor import get_system_status, get_top_processes, generate_graph
from services.gemini_cli import ask_gemini
from utils.formatters import format_status, format_processes

router = Router()


def _is_admin(message: Message) -> bool:
    """Check if the message sender is the bot admin."""
    if not message.from_user:
        return False
    return str(message.from_user.id) == settings.TELEGRAM_ADMIN_ID

# Клавиатура навигации
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статус"), KeyboardButton(text="📝 Логи")],
        [KeyboardButton(text="🌐 Speedtest"), KeyboardButton(text="❓ Помощь")],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /start")
    if not _is_admin(message):
        logger.warning(f"⛔ Unauthorized access attempt from user {user_id}")
        await message.answer("⛔ Access denied. This is a private bot.")
        return
    await message.answer(
        "👋 <b>Cyber-Pocket</b> — твой локальный помощник.\n\n"
        "📋 <b>Команды:</b>\n"
        "/status — Состояние системы + график\n"
        "/logs — Последние записи из лога\n"
        "/speedtest — Измерить скорость сети\n"
        "/ask &lt;вопрос&gt; — Спросить Gemini\n"
        "/help — Справка",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(Command("help"))
@router.message(lambda m: m.text == "❓ Помощь")
async def cmd_help(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /help")
    if not _is_admin(message):
        await message.answer("⛔ Access denied.")
        return
    await message.answer(
        "🛠 <b>Справка Cyber-Pocket</b>\n\n"
        "<b>/status</b>\n"
        "Показывает CPU, RAM, температуру, диск, uptime,\n"
        "load average и топ-5 тяжёлых процессов.\n"
        "Прикладывает график нагрузки, если есть история.\n\n"
        "<b>/logs</b>\n"
        "Показывает последние 20 строк лога приложения.\n\n"
        "<b>/speedtest</b>\n"
        "Замеряет скорость интернет-соединения.\n"
        "Может занять около 30 секунд.\n\n"
        "<b>/ask &lt;вопрос&gt;</b>\n"
        "Отправляет вопрос в Gemini CLI и возвращает ответ.\n"
        "Gemini не выполняет никаких команд на ПК,\n"
        "только даёт подсказки и анализ.\n\n"
        "⚙️ Бот работает только на вашем ПК локально.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.message(Command("status"))
@router.message(lambda m: m.text == "📊 Статус")
async def cmd_status(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /status")
    if not _is_admin(message):
        await message.answer("⛔ Access denied.")
        return
    try:
        status = get_system_status()
        procs = get_top_processes(5)

        text = format_status(status) + "\n" + format_processes(procs)

        graph = generate_graph()
        if graph:
            photo = BufferedInputFile(graph.read(), filename="system_load.png")
            await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")
        else:
            await message.answer(
                text + "\n\n<i>📈 График появится через ~2 мин (идёт сбор данных).</i>",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.error(f"Error in /status: {e}")
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("logs"))
@router.message(lambda m: m.text == "📝 Логи")
async def cmd_logs(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /logs")
    if not _is_admin(message):
        await message.answer("⛔ Access denied.")
        return
    try:
        tail = get_last_logs(20)
        # Telegram ограничение 4096 символов
        if len(tail) > 3900:
            tail = tail[-3900:]
        await message.answer(
            f"📝 <b>Последние логи:</b>\n\n<pre>{tail}</pre>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /logs: {e}")
        await message.answer(f"⚠️ Ошибка: {e}")


@router.message(Command("ask"))
async def cmd_ask(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /ask")
    if not _is_admin(message):
        await message.answer("⛔ Access denied.")
        return

    # Извлекаем текст после команды /ask
    if not message.text:
        await message.answer(
            "❓ Использование: /ask <i>ваш вопрос</i>", parse_mode="HTML"
        )
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "❓ Использование: /ask <i>ваш вопрос</i>", parse_mode="HTML"
        )
        return

    question = parts[1].strip()
    logger.info(f"Gemini question: {question[:100]}")

    wait_msg = await message.answer("🤔 Думаю...")

    answer = await ask_gemini(question)

    # Ограничение длины для Telegram
    if len(answer) > 3900:
        answer = answer[:3900] + "\n\n<i>... (ответ обрезан)</i>"

    await wait_msg.delete()
    await message.answer(f"🤖 <b>Gemini:</b>\n\n{answer}", parse_mode="HTML")

@router.message(Command("speedtest"))
@router.message(lambda m: m.text == "🌐 Speedtest")
async def cmd_speedtest(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /speedtest")
    if not _is_admin(message):
        await message.answer("⛔ Access denied.")
        return

    wait_msg = await message.answer("⏳ <i>Измеряю скорость... Это может занять около 30 секунд.</i>", parse_mode="HTML")
    
    try:
        from services.network import run_speedtest
        from utils.formatters import format_speedtest
        
        results = await run_speedtest()
        text = format_speedtest(results)
        await wait_msg.delete()
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /speedtest: {e}")
        await wait_msg.delete()
        await message.answer(f"⚠️ Ошибка при измерении скорости: {e}")
