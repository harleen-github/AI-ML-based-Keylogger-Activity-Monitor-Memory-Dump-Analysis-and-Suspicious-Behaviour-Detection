import csv
import os
import win32evtlog
from datetime import datetime, timedelta

def get_failed_login_attempts():
    print("Attempting to read Security logs for the past 24 hours...")
    server = 'localhost'
    log_type = 'Security'
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    # Only consider events from the past 24 hours
    cutoff_time = datetime.now() - timedelta(days=1)

    try:
        hand = win32evtlog.OpenEventLog(server, log_type)
    except Exception as e:
        print(f"Error opening event log: {e}")
        return []

    total = win32evtlog.GetNumberOfEventLogRecords(hand)
    print(f"Total records in Security log: {total}")

    events = []
    while True:
        events_list = win32evtlog.ReadEventLog(hand, flags, 0)
        if not events_list:
            break

        for event in events_list:
            if event.EventID == 4625:  # Failed logon
                event_time = event.TimeGenerated
                if event_time < cutoff_time:
                    continue  # Ignore old events

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

    if not events:
        print("No failed login attempts found in the last 24 hours.")
        print("👉 If you expected entries, try running this script as Administrator.")
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

    print(f"{len(data)} failed login attempts written to {filename}")

if __name__ == "__main__":
    attempts = get_failed_login_attempts()
    save_to_csv(attempts)
