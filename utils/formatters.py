def format_status(data: dict) -> str:
    """Форматирует метрики системы для Telegram."""
    temp_str = f"{data['temperature']:.1f}°C" if data["temperature"] else "N/A"

    return (
        f"🖥 <b>Система:</b> {data['os']}\n"
        f"⏱ <b>Uptime:</b> {data['uptime']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>CPU:</b> {data['cpu_percent']}%\n"
        f"💾 <b>RAM:</b> {data['ram_used_gb']}/{data['ram_total_gb']} GB ({data['ram_percent']}%)\n"
        f"🌡 <b>Temp:</b> {temp_str}\n"
        f"🎮 <b>GPU:</b> {data.get('gpu_percent', 'N/A')}% (Temp: {data.get('gpu_temp', 'N/A')}°C)\n"
        f"📹 <b>VRAM:</b> {data.get('vram_used_gb', 'N/A')}/{data.get('vram_total_gb', 'N/A')} GB\n"
        f"📊 <b>Load Avg:</b> {data['load_avg']}\n"
        f"💿 <b>Disk:</b> {data['disk_used_gb']}/{data['disk_total_gb']} GB ({data['disk_percent']}%)\n"
    )


def format_processes(procs: list[dict]) -> str:
    """Форматирует список процессов для Telegram."""
    if not procs:
        return "Нет данных о процессах."

    lines = ["<b>🔝 Top процессы:</b>\n"]
    for i, p in enumerate(procs, 1):
        lines.append(
            f"<code>{i}. {p['name']:<25} CPU: {p['cpu']:>5.1f}%  RAM: {p['mem']:>4.1f}%</code>"
        )
    return "\n".join(lines)

def format_speedtest(results: dict) -> str:
    """Форматирует данные speedtest для Telegram."""
    download_mbps = results["download"] / 1_000_000
    upload_mbps = results["upload"] / 1_000_000
    ping = results["ping"]
    server = f"{results['server']['sponsor']} ({results['server']['name']})"
    client_ip = results["client"]["ip"]
    
    return (
        f"🌐 <b>Отчёт Speedtest:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⬇️ <b>Download:</b> {download_mbps:.2f} Mbps\n"
        f"⬆️ <b>Upload:</b> {upload_mbps:.2f} Mbps\n"
        f"🏓 <b>Ping:</b> {ping:.2f} ms\n"
        f"🎯 <b>Server:</b> {server}\n"
        f"📡 <b>IP клиент:</b> {client_ip}"
    )
