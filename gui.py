import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, time, os
from datetime import datetime, timedelta
from collections import deque
import joblib
import numpy as np
import pandas as pd
import csv
import win32evtlog
from pynput import keyboard, mouse
import subprocess


# --- Load model and scaler ---
model = joblib.load("rf_model.joblib")
scaler = joblib.load("scaler.joblib")

# --- Global states ---
keystrokes = deque(maxlen=300)
press_times = {}
left_clicks = right_clicks = 0
mouse_distance = 0
last_mouse_time = time.time()
last_mouse_xy = (None, None)
label_map = {1: "NORMAL", 0: "ABNORMAL"}

# --- Key and Mouse Handlers ---
def on_key_press(key):
    global press_times, keystrokes
    try:
        c = key.char if hasattr(key, "char") else str(key)
    except:
        c = str(key)
    t = time.time()
    keystrokes.append((c, t))
    press_times[c] = t

def on_key_release(key):
    pass

def on_move(x, y):
    global mouse_distance, last_mouse_xy, last_mouse_time
    lx, ly = last_mouse_xy
    if lx is not None:
        mouse_distance += ((x - lx) ** 2 + (y - ly) ** 2) ** 0.5
    last_mouse_xy = (x, y)
    last_mouse_time = time.time()

def on_click(x, y, button, pressed):
    global left_clicks, right_clicks
    if pressed:
        if button.name == "left":
            left_clicks += 1
        else:
            right_clicks += 1

# --- Feature Extraction and Prediction ---
def extract_and_predict():
    global keystrokes, left_clicks, right_clicks, mouse_distance, last_mouse_time

    now = time.time()
    keys = list(keystrokes)
    if not keys:
        return None, None

    total = len(keys)
    holds = [(now - press_times[k]) * 1000 for k, _ in keys if k in press_times]
    avg_hold = np.mean(holds) if holds else 0
    delays = [(keys[i][1] - keys[i - 1][1]) * 1000 for i in range(1, len(keys))]
    avg_delay = np.mean(delays) if delays else 0
    backspaces = sum(k in ("Key.backspace", "Key.delete") for k, _ in keys)
    back_rate = backspaces / total
    speed_kpm = total * 6
    idle = now - last_mouse_time

    feat = pd.DataFrame([{
        "total_keys": total,
        "avg_hold_time_ms": avg_hold,
        "avg_delay_ms": avg_delay,
        "backspace_rate": back_rate,
        "mouse_move_distance": mouse_distance,
        "left_clicks": left_clicks,
        "right_clicks": right_clicks,
        "mouse_idle_time": idle,
        "typing_speed_kpm": speed_kpm,
        "typing_speed_cps": total / 10
    }])

    scaled = scaler.transform(feat)
    pred = model.predict(scaled)[0]
    prob = model.predict_proba(scaled).max()

    # Reset counters
    keystrokes.clear()
    left_clicks = right_clicks = 0
    mouse_distance = 0

    return label_map.get(pred, "UNKNOWN"), prob

# --- Failed Login Fetcher ---
def get_failed_logins():
    server, log_type = "localhost", "Security"
    cutoff = datetime.now() - timedelta(days=1)
    try:
        h = win32evtlog.OpenEventLog(server, log_type)
    except Exception as e:
        return f"Error opening event log: {e}"

    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    rows = []

    while True:
        batch = win32evtlog.ReadEventLog(h, flags, 0)
        if not batch:
            break
        for ev in batch:
            if ev.EventID == 4625 and ev.TimeGenerated >= cutoff:
                ts = ev.TimeGenerated.strftime("%Y-%m-%d %H:%M:%S")
                usr = ev.StringInserts[5] if ev.StringInserts and len(ev.StringInserts) > 5 else "Unknown"
                rows.append(f"{ts}\t{ev.SourceName}\t{usr}")
    win32evtlog.CloseEventLog(h)

    if not rows:
        return "No failed login attempts in the last 24 hrs."

    # Save CSV
    with open("failed_login_logs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "source", "username"])
        for line in rows:
            w.writerow(line.split("\t"))

    return "\n".join(rows)

# ================= GUI =================
root = tk.Tk()
root.title("AI Activity Monitor - Typing & Mouse Behaviour")
root.geometry("680x440")
root.configure(bg="#f0f4f7")

# Style
style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.map("TButton", background=[("active", "#d0eaff")])

status_lbl = tk.Label(root, text="Click a button to begin", font=("Segoe UI", 16, "bold"), bg="#f0f4f7")
status_lbl.pack(pady=25)

btn_frame = tk.Frame(root, bg="#f0f4f7")
btn_frame.pack(pady=10)

def start_tracker():
    keyboard.Listener(on_press=on_key_press, on_release=on_key_release).start()
    mouse.Listener(on_move=on_move, on_click=on_click).start()
    status_lbl.config(text="Tracker started—waiting 10 s for first reading…", fg="black")
    root.after(10000, periodic_check)

def periodic_check():
    label, prob = extract_and_predict()
    if label is None:
        status_lbl.config(text="No data yet—waiting another 10 s…", fg="gray")
    else:
        time_str = datetime.now().strftime('%H:%M:%S')
        color = "green" if label == "NORMAL" else "red"
        status_lbl.config(
            text=f"[{time_str}] Status: {label}",
            fg=color
        )
    root.after(10000, periodic_check)

# def show_failed():
#     def worker():
#         result = get_failed_logins()
#         root.after(0, lambda: pop_failed(result))
#     threading.Thread(target=worker, daemon=True).start()
def show_failed():
    def worker():
        attempts = get_failed_login_attempts()
        save_to_csv(attempts)
        text = "\n".join([f"{a['timestamp']}\t{a['source']}\t{a['username']}" for a in attempts]) or "No failed login attempts in the last 24 hrs."
        root.after(0, lambda: pop_failed(text))
    threading.Thread(target=worker, daemon=True).start()
def get_failed_login_attempts():
    server = 'localhost'
    log_type = 'Security'
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    cutoff_time = datetime.now() - timedelta(days=1)

    try:
        hand = win32evtlog.OpenEventLog(server, log_type)
    except Exception as e:
        return []

    events = []
    while True:
        events_list = win32evtlog.ReadEventLog(hand, flags, 0)
        if not events_list:
            break

        for event in events_list:
            if event.EventID == 4625:  # Failed logon
                event_time = event.TimeGenerated
                if event_time < cutoff_time:
                    continue

                timestamp = event_time.strftime("%Y-%m-%d %H:%M:%S")
                source = event.SourceName
                strings = event.StringInserts
                user = strings[5] if strings and len(strings) > 5 else "Unknown"

                events.append({
                    'timestamp': timestamp,
                    'source': source,
                    'username': user
                })

    win32evtlog.CloseEventLog(hand)
    return events


def save_to_csv(data, filename="failed_login_logs.csv"):
    if not data:
        return

    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'source', 'username']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for row in data:
            writer.writerow(row)

    if len(data) >= 3:
        try:
            subprocess.run(["python", "dump_trigger.py"], check=True)
        except Exception as e:
            print(f"Error triggering memory dump: {e}")


def pop_failed(text):
    win = tk.Toplevel(root)
    win.title("Failed Logins (last 24 hrs)")
    win.geometry("600x380")
    txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10))
    txt.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    txt.insert(tk.END, text)

# Buttons
ttk.Button(btn_frame, text="Keystrokes & Mouse Tracker", command=start_tracker, width=30).grid(row=0, column=0, padx=10, pady=10)
ttk.Button(btn_frame, text="Failed Logins (24 hrs)",     command=show_failed,   width=30).grid(row=0, column=1, padx=10, pady=10)
ttk.Button(btn_frame, text="Exit",                       command=root.quit,     width=15).grid(row=1, column=0, columnspan=2, pady=15)

root.mainloop()
