import os

def get_amd_gpu_status():
    gpu_status: dict = {
        "gpu_percent": None,
        "gpu_temp": None,
        "vram_used_gb": None,
        "vram_total_gb": None,
    }
    
    try:
        cards_dir = "/sys/class/drm"
        if not os.path.exists(cards_dir):
            return gpu_status
            
        for card in os.listdir(cards_dir):
            if card.startswith("card") and not "-" in card:
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
        print(e)
        
    return gpu_status

print(get_amd_gpu_status())
