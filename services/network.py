import asyncio
import speedtest
from core.logger import logger

async def run_speedtest() -> dict:
    """Измеряет скорость интернета и возвращает результаты."""
    def _test():
        st = speedtest.Speedtest()
        st.get_best_server()
        st.download()
        st.upload()
        return st.results.dict()

    try:
        # Библиотека speedtest блокирующая, поэтому выполняем её в отдельном потоке
        logger.info("Starting speedtest...")
        results = await asyncio.to_thread(_test)
        logger.info("Speedtest completed.")
        return results
    except Exception as e:
        logger.error(f"Error during speedtest: {e}")
        raise e
