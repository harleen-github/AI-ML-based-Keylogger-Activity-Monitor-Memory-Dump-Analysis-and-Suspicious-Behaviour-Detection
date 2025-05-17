from pynput import keyboard, mouse
import time
import csv
from datetime import datetime
import threading
import math
import os
# Metrics (reset every minute)
total_keys = 0
backspace_count = 0
key_hold_times = []
inter_key_delays = []

# Mouse Metrics
mouse_move_distance = 0
left_click_count = 0
right_click_count = 0
mouse_idle_time = 0
last_mouse_move_time = time.time()

# Initialize mouse coordinates
last_mouse_x = None
last_mouse_y = None

# State tracking
last_key_release_time = None
key_press_times = {}

# CSV setup
output_file = "activity_metrics.csv"
header = ["timestamp", "total_keys", "avg_hold_time_ms", "avg_delay_ms", "backspace_rate", 
          "mouse_move_distance", "left_clicks", "right_clicks", "mouse_idle_time",
          "typing_speed_kpm", "typing_speed_cps"]


# Write header if file doesn't exist
# Write header if file is empty or doesn't exist
if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)


# Flag to stop the program
stop_flag = threading.Event()  # Using an Event to stop the threads

# Function to log metrics every minute
def log_metrics():
    global total_keys, backspace_count, key_hold_times, inter_key_delays
    global mouse_move_distance, left_click_count, right_click_count, mouse_idle_time

    while not stop_flag.is_set():  # Run until stop_flag is set to True
        time.sleep(60)  # Log every 60 seconds

        # Calculate metrics every minute
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        avg_hold = sum(key_hold_times) / len(key_hold_times) * 1000 if key_hold_times else 0
        avg_delay = sum(inter_key_delays) / len(inter_key_delays) * 1000 if inter_key_delays else 0
        backspace_rate = backspace_count / total_keys if total_keys else 0
        avg_mouse_idle = time.time() - last_mouse_move_time if last_mouse_move_time else 0
        typing_speed_kpm = total_keys
        typing_speed_cps = total_keys / 60

        # Write metrics to CSV file
        with open(output_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, total_keys, round(avg_hold, 2), round(avg_delay, 2), round(backspace_rate, 3),
                 mouse_move_distance, left_click_count, right_click_count, round(avg_mouse_idle, 2),
                 round(typing_speed_kpm, 2), round(typing_speed_cps, 2)])


        # Reset metrics for the next minute
        total_keys = 0
        backspace_count = 0
        key_hold_times = []
        inter_key_delays = []
        mouse_move_distance = 0
        left_click_count = 0
        right_click_count = 0
        mouse_idle_time = 0
        


# Function to handle key press events
def on_press(key):
    global total_keys, backspace_count, last_key_release_time, inter_key_delays

    now = time.time()
    total_keys += 1
    key_press_times[key] = now

    if last_key_release_time:
        inter_key_delays.append(now - last_key_release_time)

    if key == keyboard.Key.backspace:
        backspace_count += 1

# Function to handle key release events
def on_release(key):
    global key_hold_times, last_key_release_time

    now = time.time()
    press_time = key_press_times.pop(key, None)
    if press_time:
        hold_time = now - press_time
        key_hold_times.append(hold_time)

    last_key_release_time = now

    # Stop listener on ESC key press by setting the stop flag to True
    if key == keyboard.Key.esc:
        stop_flag.set()  # Set the flag to stop both threads
        return False  # This will stop the listener

# Function to track mouse movement
def on_move(x, y):
    global mouse_move_distance, last_mouse_x, last_mouse_y, last_mouse_move_time

    # Calculate distance moved using Euclidean distance formula
    if last_mouse_x is not None and last_mouse_y is not None:
        distance = math.sqrt((x - last_mouse_x) ** 2 + (y - last_mouse_y) ** 2)
        mouse_move_distance += distance

    # Update last position and time
    last_mouse_x, last_mouse_y = x, y
    last_mouse_move_time = time.time()

# Function to track mouse clicks
def on_click(x, y, button, pressed):
    global left_click_count, right_click_count

    if button == mouse.Button.left and pressed:
        left_click_count += 1
    elif button == mouse.Button.right and pressed:
        right_click_count += 1

# Start the logging thread to write metrics every minute
log_thread = threading.Thread(target=log_metrics, daemon=True)  # Daemon thread so it exits when the main program exits
log_thread.start()

# Start the key listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()  # Start the listener in its own thread

# Start the mouse listener
mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
mouse_listener.start()  # Start mouse listener in a separate thread

listener.join()  # Wait for listener to finish
mouse_listener.join()  # Wait for mouse listener to finish
log_thread.join()  # Ensure logging thread is also completed before exiting

print("Tracking stopped.")
