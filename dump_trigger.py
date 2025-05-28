import os
import psutil
import datetime
import subprocess
import time;
# Path to your procdump.exe
PROCDUMP_PATH = r"C:\tools\procdump\procdump64.exe"

# Directory to save dumps
DUMP_DIR = "dumps"
os.makedirs(DUMP_DIR, exist_ok=True)
SKIP_PROCESSES=[]
# List of processes we want to skip

SKIP_PROCESSES = [
    'Idle', 'System', 'System Idle Process', 'MemCompression',
    'Registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
    'winlogon.exe', 'services.exe', 'lsass.exe', 'svchost.exe',
    'fontdrvhost.exe', 'dwm.exe'
]


def find_suspicious_process(cpu_threshold=2.0, mem_threshold_mb=100, max_runtime_sec=300):
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            name = proc.info['name']
            pid = proc.info['pid']
            cpu = proc.info['cpu_percent']
            mem = proc.info['memory_info'].rss / (1024 * 1024)  # MB
            runtime = time.time() - proc.info['create_time']

           
            if not name or name.lower() in [p.lower() for p in SKIP_PROCESSES]:
                continue

            # ✅ Match on metrics
            if cpu > cpu_threshold or mem > mem_threshold_mb or runtime < max_runtime_sec:
                print(f"[INFO] Selected process: {name} (PID: {pid}) CPU: {cpu:.2f}%, MEM: {mem:.2f}MB, Runtime: {runtime:.1f}s")
                return pid, name

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    print("[INFO] No valid process found to dump.")
    return None, None

import string
import random

def analyze_dump_file(dump_path, mem_usage=0, cpu_usage=0, runtime=0):
    analysis_filename = os.path.splitext(os.path.basename(dump_path))[0] + "_analysis.txt"
    analysis_path = os.path.join(DUMP_DIR, analysis_filename)

    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write(f"[ANALYSIS] Analyzing dump file: {dump_path}\n")

        size = os.path.getsize(dump_path) / (1024 * 1024)
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(dump_path)).strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[ANALYSIS] Size: {size:.2f} MB\n")
        f.write(f"[ANALYSIS] Last Modified: {mtime}\n")

        # Optional: show first bytes
        with open(dump_path, 'rb') as df:
            first_bytes = df.read(256)
            hex_output = ' '.join(f"{b:02x}" for b in first_bytes)
            f.write(f"[ANALYSIS] First 256 bytes (hex):\n{hex_output}\n")
            # ASCII translation for printable characters
            ascii_output = ''.join(chr(b) if 32 <= b < 127 else '.' for b in first_bytes)
            f.write(f"\n[ANALYSIS] ASCII representation:\n{ascii_output}\n")


        f.write("\n[BEHAVIORAL INSIGHTS]\n")
        if mem_usage > 150:
            f.write("🧠 High memory usage detected — could indicate memory abuse or large data load.\n")
        if cpu_usage < 1 and mem_usage > 100:
            f.write("🕵️ Low CPU with high memory — potential sign of code injection or idle persistence.\n")
        if runtime > 3600:
            f.write("⏳ Long-running process — may be part of persistent background activity.\n")
        if size > 5:
            f.write("📦 Dump file is large — could contain complex or multi-threaded execution.\n")

        f.write("\n[NOTE] These results are inferred heuristics, not deep malware signatures.\n")

    print(f"[✔] Simulated behavior-based analysis saved to: {analysis_path}")



def dump_process(pid, name, reason="auto_triggered"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = name if name else f"pid{pid}"
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)
    dump_file = os.path.join(DUMP_DIR, f"{safe_name}_{timestamp}_{reason}.dmp")

    cmd = [PROCDUMP_PATH, "-ma", str(pid), dump_file]
    print(f"[INFO] Dumping PID {pid} ({name}) to {dump_file}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check if dump file exists and is not empty
    if os.path.exists(dump_file) and os.path.getsize(dump_file) > 0:
        print("✅ Memory dump created successfully.")
        analyze_dump_file(dump_file)  # call analysis function
    else:
        print(f"ProcDump failed or dump file missing. Return code: {result.returncode}")
        print(f"[STDERR]:\n{result.stderr}")


# Main execution block
if __name__ == "__main__":
    print("[DEBUG] Entered __main__ block")
    pid, name = find_suspicious_process()
    if pid:
        dump_process(pid, name)
    else:
        print("[INFO] No valid process found to dump.")
