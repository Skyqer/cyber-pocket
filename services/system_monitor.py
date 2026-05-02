import os
import subprocess
import psutil
import platform
import datetime
import asyncio
from io import BytesIO
from collections import deque
from core.config import settings
from core.logger import logger

# Храним историю метрик в памяти (до 900 точек ≈ 150 мин при интервале 10 сек)
_history: deque[dict] = deque(maxlen=900)


# ─── GPU: Linux (AMD sysfs) ──────────────────────────────────────────────────

def _get_gpu_status_linux() -> dict:
    """Читает GPU метрики из sysfs (AMD/AMDGPU)."""
    gpu_status: dict = {"gpu_percent": None, "gpu_temp": None, "vram_used_gb": None, "vram_total_gb": None}
    try:
        cards_dir = "/sys/class/drm"
        if not os.path.exists(cards_dir):
            return gpu_status

        for card in os.listdir(cards_dir):
            if card.startswith("card") and "-" not in card:
                dev_dir = os.path.join(cards_dir, card, "device")
                busy_path = os.path.join(dev_dir, "gpu_busy_percent")
                if os.path.exists(busy_path):
                    with open(busy_path, "r") as f:
                        gpu_status["gpu_percent"] = float(f.read().strip())

                    vram_used_path = os.path.join(dev_dir, "mem_info_vram_used")
                    if os.path.exists(vram_used_path):
                        with open(vram_used_path, "r") as f:
                            gpu_status["vram_used_gb"] = round(int(f.read().strip()) / (1024**3), 2)

                    vram_total_path = os.path.join(dev_dir, "mem_info_vram_total")
                    if os.path.exists(vram_total_path):
                        with open(vram_total_path, "r") as f:
                            gpu_status["vram_total_gb"] = round(int(f.read().strip()) / (1024**3), 2)

                    hwmon_dir = os.path.join(dev_dir, "hwmon")
                    if os.path.exists(hwmon_dir):
                        for hw in os.listdir(hwmon_dir):
                            temp_path = os.path.join(hwmon_dir, hw, "temp1_input")
                            if os.path.exists(temp_path):
                                with open(temp_path, "r") as f:
                                    gpu_status["gpu_temp"] = round(int(f.read().strip()) / 1000, 1)
                                break
                    break
    except Exception as e:
        logger.error(f"Error reading GPU status (Linux): {e}")
    return gpu_status


# ─── GPU: Windows (NVIDIA via nvidia-smi, AMD via Performance Counters) ──────

_GPU_COUNTER = r"\GPU Engine(*engtype_3D)\Utilization Percentage"
_MEM_COUNTER = r"\GPU Adapter Memory(*)\Dedicated Usage"


def _try_nvidia_smi() -> dict | None:
    """Пробует получить метрики GPU через nvidia-smi (только NVIDIA)."""
    import shutil
    try:
        nvidia_smi = r"C:\Windows\System32\nvidia-smi.exe"
        if not os.path.exists(nvidia_smi):
            nvidia_smi = shutil.which("nvidia-smi")
            if not nvidia_smi:
                return None

        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            return None

        parts = [p.strip() for p in result.stdout.strip().split(",")]
        if len(parts) >= 4:
            return {
                "gpu_percent": float(parts[0]),
                "gpu_temp": float(parts[1]),
                "vram_used_gb": round(float(parts[2]) / 1024, 2),
                "vram_total_gb": round(float(parts[3]) / 1024, 2),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    except Exception as e:
        logger.error(f"nvidia-smi error: {e}")
    return None


def _try_performance_counters() -> dict | None:
    """
    Читает GPU метрики через Windows Performance Counters + WMI.
    Работает для NVIDIA и AMD (Windows 10 1709+ / Windows 11).
    GPU % и VRAM used — из Performance Counters, VRAM total — из WMI.
    Температуру не даёт (для AMD на Windows нет простого способа).
    """
    gpu_pct = None
    vram_used = None
    vram_total = None

    # Шаг 1: GPU utilization + VRAM used из Performance Counters
    try:
        ps_script = (
            f"$gpu=(Get-Counter '{_GPU_COUNTER}').CounterSamples"
            f" | Measure-Object CookedValue -Sum;"
            f"$mem=(Get-Counter '{_MEM_COUNTER}').CounterSamples"
            f" | Measure-Object CookedValue -Sum;"
            f"Write-Output ('{{0}}|{{1}}' -f "
            f"[math]::Round($gpu.Sum,1),$mem.Sum)"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|")
            if len(parts) >= 2:
                gpu_pct = round(float(parts[0]), 1)
                vram_used = float(parts[1])
    except subprocess.TimeoutExpired:
        logger.warning("GPU Performance Counters timeout")
    except Exception as e:
        logger.error(f"GPU Performance Counters error: {e}")

    # Шаг 2: VRAM total из WMI (Win32_VideoController.AdapterRAM)
    try:
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "(Get-CimInstance Win32_VideoController"
                " | Select-Object -First 1).AdapterRAM"
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0 and result.stdout.strip():
            vram_total = float(result.stdout.strip())
    except Exception:
        pass

    if gpu_pct is not None:
        return {
            "gpu_percent": gpu_pct,
            "gpu_temp": None,
            "vram_used_gb": round(vram_used / (1024**3), 2) if vram_used else None,
            "vram_total_gb": round(vram_total / (1024**3), 2) if vram_total else None,
        }
    return None


def _get_gpu_status_windows() -> dict:
    """
    Читает GPU метрики на Windows.
    1) nvidia-smi  → NVIDIA (загрузка + температура + VRAM)
    2) Performance Counters + WMI → AMD (загрузка + VRAM, без температуры)
    """
    gpu_status: dict = {"gpu_percent": None, "gpu_temp": None, "vram_used_gb": None, "vram_total_gb": None}

    nvidia = _try_nvidia_smi()
    if nvidia:
        return nvidia

    perf = _try_performance_counters()
    if perf:
        return perf

    return gpu_status


# ─── Универсальный диспетчер GPU ─────────────────────────────────────────────

def _get_gpu_status() -> dict:
    """Выбирает метод чтения GPU в зависимости от ОС."""
    if settings.IS_WINDOWS:
        return _get_gpu_status_windows()
    return _get_gpu_status_linux()


# ─── Температура CPU ─────────────────────────────────────────────────────────

def _get_cpu_temperature() -> float | None:
    """Получает температуру CPU. На Windows psutil не поддерживает sensors_temperatures."""
    temp = None

    if settings.IS_WINDOWS:
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
                    "| Select-Object -First 1 -ExpandProperty CurrentTemperature"
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout.strip():
                raw = float(result.stdout.strip())
                temp = round((raw / 10.0) - 273.15, 1)
        except Exception:
            pass
    else:
        try:
            sensors = psutil.sensors_temperatures()
            if sensors:
                for chip_name in ("k10temp", "coretemp", "cpu_thermal", "acpitz"):
                    if chip_name in sensors and sensors[chip_name]:
                        temp = sensors[chip_name][0].current
                        break
                if temp is None:
                    first_chip = list(sensors.values())[0]
                    if first_chip:
                        temp = first_chip[0].current
        except Exception:
            pass

    return temp


# ─── Основной сбор метрик ────────────────────────────────────────────────────

def get_system_status() -> dict:
    """Собирает текущие метрики системы."""
    cpu = psutil.cpu_percent(interval=0)
    mem = psutil.virtual_memory()
    ram_used_gb = round(mem.used / (1024 ** 3), 1)
    ram_total_gb = round(mem.total / (1024 ** 3), 1)

    temp = _get_cpu_temperature()

    try:
        load_avg = os.getloadavg()
        load_str = f"{load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}"
    except (OSError, AttributeError):
        load_str = "N/A"

    disk_root = "C:\\" if settings.IS_WINDOWS else "/"
    disk = psutil.disk_usage(disk_root)
    disk_used_gb = round(disk.used / (1024 ** 3), 1)
    disk_total_gb = round(disk.total / (1024 ** 3), 1)

    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    gpu_stats = _get_gpu_status()

    os_label = (
        f"Windows 11 ({platform.release()})"
        if settings.IS_WINDOWS
        else f"{platform.system()} {platform.release()}"
    )

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
        "os": os_label,
        "timestamp": datetime.datetime.now(),
    }
    status.update(gpu_stats)

    _history.append({"time": status["timestamp"], "cpu": cpu, "ram": mem.percent})

    gpu_log = ""
    if gpu_stats.get("gpu_percent") is not None:
        gpu_log = f" GPU={gpu_stats['gpu_percent']}% GTemp={gpu_stats['gpu_temp']}° VRAM={gpu_stats['vram_used_gb']}G"

    logger.info(f"Metrics: CPU={cpu}% RAM={mem.percent}% Temp={temp}{gpu_log}")
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


async def get_system_status_async() -> dict:
    """Неблокирующая обёртка для get_system_status."""
    return await asyncio.to_thread(get_system_status)
