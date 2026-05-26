import requests
import random
import time
import threading
from datetime import datetime, timedelta

GATEWAY_URL = "http://localhost:8000/trains/update"

# 20 trains across 5 zones
TRAINS = [
    # Delhi zone
    {"id": "12951", "name": "Rajdhani Express",     "zone": "Delhi",   "from": "Mumbai",    "to": "Delhi",     "type": "Superfast"},
    {"id": "12002", "name": "Bhopal Shatabdi",      "zone": "Delhi",   "from": "Bhopal",    "to": "Delhi",     "type": "Shatabdi"},
    {"id": "12627", "name": "Karnataka Express",    "zone": "Delhi",   "from": "Bangalore", "to": "Delhi",     "type": "Express"},
    {"id": "12301", "name": "Howrah Rajdhani",      "zone": "Delhi",   "from": "Howrah",    "to": "Delhi",     "type": "Superfast"},
    # Mumbai zone
    {"id": "12137", "name": "Punjab Mail",          "zone": "Mumbai",  "from": "Firozpur",  "to": "Mumbai",    "type": "Mail"},
    {"id": "11057", "name": "Amritsar Express",     "zone": "Mumbai",  "from": "Amritsar",  "to": "Mumbai",    "type": "Express"},
    {"id": "12263", "name": "Pune Duronto",         "zone": "Mumbai",  "from": "Hazrat",    "to": "Pune",      "type": "Duronto"},
    {"id": "12221", "name": "Rajkot Express",       "zone": "Mumbai",  "from": "Mumbai",    "to": "Rajkot",    "type": "Express"},
    # Chennai zone
    {"id": "12163", "name": "Chennai Express",      "zone": "Chennai", "from": "Mumbai",    "to": "Chennai",   "type": "Superfast"},
    {"id": "12695", "name": "Trivandrum Express",   "zone": "Chennai", "from": "Chennai",   "to": "Trivandrum","type": "Express"},
    {"id": "12657", "name": "Bangalore Mail",       "zone": "Chennai", "from": "Chennai",   "to": "Bangalore", "type": "Mail"},
    {"id": "12671", "name": "Nilagiri Express",     "zone": "Chennai", "from": "Chennai",   "to": "Coimbatore","type": "Express"},
    # Kolkata zone
    {"id": "12313", "name": "Sealdah Rajdhani",     "zone": "Kolkata", "from": "Sealdah",   "to": "Delhi",     "type": "Superfast"},
    {"id": "12381", "name": "Poorva Express",       "zone": "Kolkata", "from": "Howrah",    "to": "Delhi",     "type": "Express"},
    {"id": "13049", "name": "Amritsar Express",     "zone": "Kolkata", "from": "Howrah",    "to": "Amritsar",  "type": "Express"},
    {"id": "12345", "name": "Saraighat Express",    "zone": "Kolkata", "from": "Howrah",    "to": "Guwahati",  "type": "Express"},
    # Bhopal zone
    {"id": "12155", "name": "Bhopal Express",       "zone": "Bhopal",  "from": "Nizamuddin","to": "Bhopal",    "type": "Express"},
    {"id": "12533", "name": "Pushpak Express",      "zone": "Bhopal",  "from": "Lucknow",   "to": "Mumbai",    "type": "Express"},
    {"id": "11077", "name": "Jhelum Express",       "zone": "Bhopal",  "from": "Pune",      "to": "Jammu",     "type": "Express"},
    {"id": "12187", "name": "Jabalpur Express",     "zone": "Bhopal",  "from": "Jabalpur",  "to": "Delhi",     "type": "Express"},
]

STATIONS = {
    "Delhi":   ["New Delhi", "Mathura", "Agra Cantt", "Gwalior", "Jhansi", "Bhopal", "Nagpur"],
    "Mumbai":  ["Mumbai CST", "Thane", "Pune", "Solapur", "Gulbarga", "Wadi", "Raichur"],
    "Chennai": ["Chennai Central", "Katpadi", "Jolarpettai", "Salem", "Erode", "Coimbatore"],
    "Kolkata": ["Howrah", "Barddhaman", "Asansol", "Dhanbad", "Gaya", "Mughal Sarai"],
    "Bhopal":  ["Bhopal Jn", "Vidisha", "Sagar", "Damoh", "Katni", "Jabalpur"],
}

DELAY_REASONS = [
    "SIGNAL_FAILURE", "ENGINE_FAULT", "TRACK_MAINTENANCE",
    "WEATHER", "OVERCROWDING", "LATE_ARRIVAL", "LEVEL_CROSSING",
    "CREW_CHANGE", "TECHNICAL_ISSUE", "UNSCHEDULED_STOP"
]

def simulate_train(train: dict):
    """Runs forever for one train — sends status every 5 seconds."""
    tid       = train["id"]
    zone      = train["zone"]
    stations  = STATIONS[zone]
    delay     = random.randint(0, 15)   # start with small random delay
    station_idx = 0

    print(f"[{tid}] {train['name']} starting simulation")

    while True:
        # Current station cycles through the list
        current_station = stations[station_idx % len(stations)]

        # Delay drifts — can increase or occasionally recover slightly
        delay_change = random.choices(
            [-2, 0, 0, 2, 5, 15, 30],
            weights=[5, 40, 30, 15, 6, 3, 1]
        )[0]
        delay = max(0, delay + delay_change)

        # Reason only if delayed
        reason = random.choice(DELAY_REASONS) if delay > 5 else "ON_TIME"

        # Scheduled vs actual time
        scheduled = datetime.now().replace(second=0, microsecond=0)
        actual     = scheduled + timedelta(minutes=delay)

        # Status label
        if delay == 0:
            status = "ON_TIME"
        elif delay <= 15:
            status = "MINOR_DELAY"
        elif delay <= 60:
            status = "MAJOR_DELAY"
        else:
            status = "SEVERELY_DELAYED"

        payload = {
            "train_id":         tid,
            "train_name":       train["name"],
            "zone":             zone,
            "train_type":       train["type"],
            "from_station":     train["from"],
            "to_station":       train["to"],
            "current_station":  current_station,
            "scheduled_time":   scheduled.isoformat(),
            "actual_time":      actual.isoformat(),
            "delay_minutes":    delay,
            "delay_reason":     reason,
            "status":           status,
        }

        try:
            resp = requests.post(GATEWAY_URL, json=payload, timeout=3)
            result = resp.json()
            print(f"[{tid}] {train['name'][:20]:<20} | "
                  f"Station: {current_station:<20} | "
                  f"Delay: {delay:>3} min | Status: {status}")
        except requests.exceptions.ConnectionError:
            print(f"[{tid}] Gateway not reachable — retrying...")
        except Exception as e:
            print(f"[{tid}] Error: {e}")

        # Move to next station occasionally
        if random.random() < 0.1:
            station_idx += 1

        time.sleep(5)  # update every 5 seconds


def main():
    print("=" * 60)
    print("  RailWatch — Indian Railways Train Simulator")
    print(f"  Simulating {len(TRAINS)} trains across 5 zones")
    print(f"  Sending data to: {GATEWAY_URL}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    threads = []
    for train in TRAINS:
        t = threading.Thread(target=simulate_train, args=(train,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.1)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")

if __name__ == "__main__":
    main()
