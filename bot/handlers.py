from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton

from core.logger import logger, get_last_logs
from services.system_monitor import get_system_status, get_top_processes, generate_graph
from services.gemini_cli import ask_gemini
from utils.formatters import format_status, format_processes

router = Router()

# Клавиатура навигации
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статус"), KeyboardButton(text="📝 Логи")],
        [KeyboardButton(text="❓ Помощь")],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} — /start")
    await message.answer(
        "👋 <b>Cyber-Pocket</b> — твой локальный помощник.\n\n"
        "📋 <b>Команды:</b>\n"
        "/status — Состояние системы + график\n"
        "/logs — Последние записи из лога\n"
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
    await message.answer(
        "🛠 <b>Справка Cyber-Pocket</b>\n\n"
        "<b>/status</b>\n"
        "Показывает CPU, RAM, температуру, диск, uptime,\n"
        "load average и топ-5 тяжёлых процессов.\n"
        "Прикладывает график нагрузки, если есть история.\n\n"
        "<b>/logs</b>\n"
        "Показывает последние 20 строк лога приложения.\n\n"
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
