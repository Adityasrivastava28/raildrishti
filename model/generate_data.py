import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

ZONES        = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bhopal"]
TRAIN_TYPES  = ["Superfast", "Express", "Mail", "Shatabdi", "Duronto"]
SEASONS      = ["Summer", "Monsoon", "Winter", "Spring"]
REASONS      = ["SIGNAL_FAILURE","ENGINE_FAULT","TRACK_MAINTENANCE",
                 "WEATHER","OVERCROWDING","LATE_ARRIVAL","ON_TIME"]

# Zone base delay — Delhi and Kolkata historically worse
ZONE_BASE = {"Delhi":18,"Mumbai":12,"Chennai":10,"Kolkata":20,"Bhopal":15}

# Train type base delay — Mail trains slower, Shatabdi fastest
TYPE_BASE = {"Superfast":10,"Express":15,"Mail":20,"Shatabdi":5,"Duronto":8}

records = []

for _ in range(10000):
    zone       = random.choice(ZONES)
    train_type = random.choice(TRAIN_TYPES)
    hour       = random.randint(0, 23)
    day_of_week= random.randint(0, 6)   # 0=Monday, 6=Sunday
    season     = random.choice(SEASONS)

    # Base delay from zone and type
    base = ZONE_BASE[zone] + TYPE_BASE[train_type]

    # Peak hours add delay (morning 7-10, evening 17-20)
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        base += random.randint(5, 20)

    # Weekend adds delay
    if day_of_week >= 5:
        base += random.randint(5, 15)

    # Monsoon and winter add delay
    if season == "Monsoon":
        base += random.randint(10, 30)
    elif season == "Winter":
        base += random.randint(5, 20)

    # Add randomness
    delay = max(0, base + random.randint(-15, 25))

    # Label
    if delay == 0:
        label = "ON_TIME"
    elif delay <= 15:
        label = "MINOR_DELAY"
    elif delay <= 60:
        label = "MAJOR_DELAY"
    else:
        label = "SEVERELY_DELAYED"

    records.append({
        "zone":          zone,
        "train_type":    train_type,
        "hour":          hour,
        "day_of_week":   day_of_week,
        "season":        season,
        "delay_minutes": delay,
        "label":         label
    })

df = pd.DataFrame(records)

os.makedirs("data", exist_ok=True)
df.to_csv("data/train_history.csv", index=False)

print(f"Generated {len(df)} records")
print(f"\nLabel distribution:")
print(df["label"].value_counts())
print(f"\nSample data:")
print(df.head(10))