import datetime
from aiogram import Bot
from core.config import settings
from core.logger import logger
from services.system_monitor import get_top_processes
from utils.formatters import format_processes

CPU_THRESHOLD = 90.0
CPU_DURATION_CHECKS = 3
TEMP_THRESHOLD = 85.0
COOLDOWN_MINUTES = 5

GPU_THRESHOLD = 90.0
GPU_TEMP_THRESHOLD = 85.0

class AlertManager:
    def __init__(self):
        self.cpu_high_count = 0
        self.last_cpu_alert_time = None
        self.last_temp_alert_time = None
        
        self.gpu_high_count = 0
        self.last_gpu_alert_time = None
        self.last_gpu_temp_alert_time = None

    async def check_and_notify(self, status: dict, bot: Bot):
        now = datetime.datetime.now()
        cpu_percent = status.get("cpu_percent", 0.0)
        temp = status.get("temperature")

        # Проверка нагрузки на CPU
        if cpu_percent > CPU_THRESHOLD:
            self.cpu_high_count += 1
            if self.cpu_high_count >= CPU_DURATION_CHECKS:
                if not self.last_cpu_alert_time or (now - self.last_cpu_alert_time).total_seconds() > COOLDOWN_MINUTES * 60:
                    try:
                        procs = get_top_processes(5)
                        text = (
                            f"⚠️ <b>ВНИМАНИЕ: Высокая нагрузка на CPU ({cpu_percent}%)</b>\n\n"
                            f"В течение последних 30 секунд загрузка процессора превышает {CPU_THRESHOLD}%.\n\n"
                            f"{format_processes(procs)}"
                        )
                        await bot.send_message(settings.TELEGRAM_ADMIN_ID, text, parse_mode="HTML")
                        self.last_cpu_alert_time = now
                        logger.warning(f"Sent CPU alert: {cpu_percent}%")
                    except Exception as e:
                        logger.error(f"Failed to send CPU alert: {e}")
        else:
            self.cpu_high_count = 0

        # Проверка температуры
        if temp is not None and temp > TEMP_THRESHOLD:
            if not self.last_temp_alert_time or (now - self.last_temp_alert_time).total_seconds() > COOLDOWN_MINUTES * 60:
                try:
                    text = f"🔥 <b>ВНИМАНИЕ: Перегрев процессора ({temp}°C)</b>\n\nТемпература CPU превысила порог в {TEMP_THRESHOLD}°C!"
                    await bot.send_message(settings.TELEGRAM_ADMIN_ID, text, parse_mode="HTML")
                    self.last_temp_alert_time = now
                    logger.warning(f"Sent Temp alert: {temp}°C")
                except Exception as e:
                    logger.error(f"Failed to send Temp alert: {e}")

        # Проверка нагрузки на GPU
        gpu_percent = status.get("gpu_percent")
        if gpu_percent is not None:
            if gpu_percent > GPU_THRESHOLD:
                self.gpu_high_count += 1
                if self.gpu_high_count >= CPU_DURATION_CHECKS:
                    if not self.last_gpu_alert_time or (now - self.last_gpu_alert_time).total_seconds() > COOLDOWN_MINUTES * 60:
                        try:
                            text = (
                                f"⚠️ <b>ВНИМАНИЕ: Высокая нагрузка на GPU ({gpu_percent}%)</b>\n\n"
                                f"В течение последних 30 секунд загрузка видеокарты превышает {GPU_THRESHOLD}%."
                            )
                            await bot.send_message(settings.TELEGRAM_ADMIN_ID, text, parse_mode="HTML")
                            self.last_gpu_alert_time = now
                            logger.warning(f"Sent GPU alert: {gpu_percent}%")
                        except Exception as e:
                            logger.error(f"Failed to send GPU alert: {e}")
            else:
                self.gpu_high_count = 0

        # Проверка температуры GPU
        gpu_temp = status.get("gpu_temp")
        if gpu_temp is not None and gpu_temp > GPU_TEMP_THRESHOLD:
            if not self.last_gpu_temp_alert_time or (now - self.last_gpu_temp_alert_time).total_seconds() > COOLDOWN_MINUTES * 60:
                try:
                    text = f"🔥 <b>ВНИМАНИЕ: Перегрев GPU ({gpu_temp}°C)</b>\n\nТемпература видеокарты превысила порог в {GPU_TEMP_THRESHOLD}°C!"
                    await bot.send_message(settings.TELEGRAM_ADMIN_ID, text, parse_mode="HTML")
                    self.last_gpu_temp_alert_time = now
                    logger.warning(f"Sent GPU Temp alert: {gpu_temp}°C")
                except Exception as e:
                    logger.error(f"Failed to send GPU Temp alert: {e}")
