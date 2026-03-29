import psutil
import platform
import datetime
from io import BytesIO
from collections import deque
from core.logger import logger

# Храним историю метрик в памяти (до 900 точек = 30 минут при интервале 2 сек)
_history: deque[dict] = deque(maxlen=900)


def get_system_status() -> dict:
    """Собирает текущие метрики системы."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    ram_used_gb = round(mem.used / (1024 ** 3), 1)
    ram_total_gb = round(mem.total / (1024 ** 3), 1)

    # Температура
    temp = None
    try:
        sensors = psutil.sensors_temperatures()
        if sensors:
            # Ищем первый доступный датчик
            for chip_name in ("k10temp", "coretemp", "cpu_thermal", "acpitz"):
                if chip_name in sensors and sensors[chip_name]:
                    temp = sensors[chip_name][0].current
                    break
            # Если не нашли по имени, берём первый попавшийся
            if temp is None:
                first_chip = list(sensors.values())[0]
                if first_chip:
                    temp = first_chip[0].current
    except Exception:
        pass

    # Load average
    try:
        load_avg = os.getloadavg()
        load_str = f"{load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}"
    except (OSError, AttributeError):
        load_str = "N/A"

    # Диск
    disk = psutil.disk_usage("/")
    disk_used_gb = round(disk.used / (1024 ** 3), 1)
    disk_total_gb = round(disk.total / (1024 ** 3), 1)

    # Uptime
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    status = {
        "cpu_percent": cpu,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "ram_percent": mem.percent,
        "temperature": temp,
        "load_avg": load_str,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "disk_percent": disk.percent,
        "uptime": f"{hours}ч {minutes}мин",
        "os": f"{platform.system()} {platform.release()}",
        "timestamp": datetime.datetime.now(),
    }

    # Сохраняем в историю для графика
    _history.append({"time": status["timestamp"], "cpu": cpu, "ram": mem.percent})

    logger.info(f"Metrics: CPU={cpu}% RAM={mem.percent}% Temp={temp}")
    return status


def get_top_processes(n: int = 5) -> list[dict]:
    """Возвращает топ-N процессов по потреблению CPU."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"][:25],
                "cpu": info["cpu_percent"] or 0.0,
                "mem": round(info["memory_percent"] or 0.0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:n]


def generate_graph() -> BytesIO | None:
    """Строит график CPU/RAM из истории. Возвращает None если данных мало."""
    if len(_history) < 5:
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times = [p["time"] for p in _history]
    cpus = [p["cpu"] for p in _history]
    rams = [p["ram"] for p in _history]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, cpus, label="CPU %", color="#3b82f6", linewidth=1.5)
    ax.plot(times, rams, label="RAM %", color="#22c55e", linewidth=1.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")
    ax.set_title("System Load")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf


import os  # noqa: E402  (нужен для getloadavg)
