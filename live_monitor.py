import joblib
import time
from pynput import keyboard, mouse
from collections import deque
from datetime import datetime
import numpy as np

# Load model and scaler
model = joblib.load("rf_model.joblib")
scaler = joblib.load("scaler.joblib")

# Initialize trackers
keystrokes = deque(maxlen=300)
press_times = {}
left_clicks = 0
right_clicks = 0
mouse_distance = 0
last_mouse_time = time.time()
last_mouse_x, last_mouse_y = None, None

# Mapping numeric prediction labels to strings
label_map = {1: "normal", 0: "abnormal"}

# Keystroke events
def on_press(key):
    try:
        key_char = key.char if hasattr(key, 'char') else str(key)
        keystrokes.append((key_char, time.time()))
        press_times[key_char] = time.time()
    except AttributeError:
        key_str = str(key)
        keystrokes.append((key_str, time.time()))
        press_times[key_str] = time.time()

def on_release(key):
    pass

# Mouse movement tracking
def on_move(x, y):
    global mouse_distance, last_mouse_x, last_mouse_y, last_mouse_time
    if last_mouse_x is not None and last_mouse_y is not None:
        dist = ((x - last_mouse_x) ** 2 + (y - last_mouse_y) ** 2) ** 0.5
        mouse_distance += dist
    last_mouse_x, last_mouse_y = x, y
    last_mouse_time = time.time()

# Mouse click tracking
def on_click(x, y, button, pressed):
    global left_clicks, right_clicks
    if pressed:
        if button.name == "left":
            left_clicks += 1
        elif button.name == "right":
            right_clicks += 1

# Start listeners
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
keyboard_listener.start()
mouse_listener.start()

print("✅ Live Monitor Running...")

# Feature extraction
def extract_features():
    now = time.time()
    keys = list(keystrokes)

    if not keys:
        return None

    total_keys = len(keys)

    # Calculate hold times properly
    hold_times = []
    for k, _ in keys:
        # press_times keys are strings
        if k in press_times:
            hold_times.append(now - press_times[k])
    avg_hold_time = np.mean(hold_times) * 1000 if hold_times else 0  # ms

    delays = [keys[i][1] - keys[i-1][1] for i in range(1, len(keys))]
    avg_delay = np.mean(delays) * 1000 if delays else 0  # ms

    backspaces = sum(1 for k, _ in keys if k in ('Key.backspace', 'Key.delete'))
    backspace_rate = backspaces / total_keys if total_keys else 0

    typing_speed_kpm = total_keys * 6  # keys per minute assuming 10 sec window
    typing_speed_cps = total_keys / 10  # keys per second in 10 sec window

    mouse_idle = now - last_mouse_time

    return [
        total_keys, avg_hold_time, avg_delay, backspace_rate,
        mouse_distance, left_clicks, right_clicks, mouse_idle,
        typing_speed_kpm, typing_speed_cps
    ]

# Test with a made-up "abnormal" case (optional, you can remove this after testing)
sample = [[10, 100, 50, 0.1, 200, 5, 3, 2, 60, 1]]
sample_scaled = scaler.transform(sample)
print("Sample prediction:", model.predict(sample_scaled))
print("Sample probabilities:", model.predict_proba(sample_scaled))

# Main loop
while True:
    time.sleep(10)  # collect data every 10 seconds
    features = extract_features()

    if not features:
        continue

    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]  # numeric label: 0 or 1
    probability = model.predict_proba(features_scaled).max()

    timestamp = datetime.now().strftime("%H:%M:%S")

    label = label_map.get(prediction, "unknown")

    if label == "abnormal":
        print(f"🚨 [{timestamp}] Abnormal behavior detected! (Confidence: {round(probability*100, 2)}%)")
        # TODO: Add popup or sound here
    else:
        print(f"✅ [{timestamp}] Normal activity (Confidence: {round(probability*100, 2)}%)")

    # Reset for next window
    keystrokes.clear()
    left_clicks = 0
    right_clicks = 0
    mouse_distance = 0
