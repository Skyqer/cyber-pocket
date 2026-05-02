import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher

from core.config import settings
from core.logger import logger
from bot.handlers import router as bot_router
from services.system_monitor import get_system_status
from services.alerts import AlertManager

# Aiogram
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)

alert_manager = AlertManager()


async def metrics_collector():
    """Фоновый сбор метрик каждые 10 сек для накопления истории графика,
    а также проверка на алерты."""
    while True:
        try:
            status = get_system_status()
            await alert_manager.check_and_notify(status, bot)
        except Exception as e:
            logger.error(f"Metrics collector error: {e}")
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Cyber-Pocket starting...")

    # Запуск фонового сбора метрик (для графиков)
    collector_task = asyncio.create_task(metrics_collector())

    # Запуск бота в фоне
    await bot.delete_webhook(drop_pending_updates=True)
    bot_task = asyncio.create_task(dp.start_polling(bot))

    logger.info("✅ Bot polling started.")
    yield

    # Graceful shutdown
    logger.info("Shutting down...")
    collector_task.cancel()
    bot_task.cancel()
    try:
        await collector_task
    except asyncio.CancelledError:
        pass
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    await dp.stop_polling()
    await bot.session.close()
    logger.info("👋 Cyber-Pocket stopped.")


app = FastAPI(title="Cyber-Pocket", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
