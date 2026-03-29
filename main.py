import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher

from core.config import settings
from core.logger import logger
from bot.handlers import router as bot_router
from services.system_monitor import get_system_status

# Aiogram
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(bot_router)


async def metrics_collector():
    """Фоновый сбор метрик каждые 10 сек для накопления истории графика."""
    while True:
        try:
            get_system_status()
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
    await dp.stop_polling()
    await bot.session.close()
    logger.info("👋 Cyber-Pocket stopped.")


app = FastAPI(title="Cyber-Pocket", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
