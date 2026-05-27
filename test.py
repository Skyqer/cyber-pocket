import subprocess

def test_vram():
    ps_script = "(Get-Counter -ListSet 'GPU Adapter Memory').Counter"
    result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    print("GPU Counters:", result.stdout)

def test_wmi_vram():
    ps_script = "(Get-CimInstance Win32_VideoController).AdapterRAM"
    result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    print("WMI VRAM:", result.stdout)

def test_cpu_temp():
    # Attempt to read CPU temp using various methods
    ps_script = "Get-WmiObject msacpi_thermalzonetemperature -namespace 'root/wmi' | Select CurrentTemperature"
    result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    print("Thermal Zone Temp:", result.stdout)
    print("Thermal Zone Error:", result.stderr)

test_vram()
test_wmi_vram()
test_cpu_temp()
