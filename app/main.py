# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
# from fastapi.responses import Response
# import sqlite3
# import time
# import joblib
# import numpy as np
# from datetime import datetime

# MODEL       = None
# LE_ZONE     = None
# LE_TYPE     = None
# LE_SEASON   = None
# LE_LABEL    = None

# def load_model():
#     global MODEL, LE_ZONE, LE_TYPE, LE_SEASON, LE_LABEL
#     try:
#         MODEL     = joblib.load("model/delay_model.pkl")
#         LE_ZONE   = joblib.load("model/le_zone.pkl")
#         LE_TYPE   = joblib.load("model/le_type.pkl")
#         LE_SEASON = joblib.load("model/le_season.pkl")
#         LE_LABEL  = joblib.load("model/le_label.pkl")
#         print("ML model loaded successfully")
#     except Exception as e:
#         print(f"Model not found: {e}")

# load_model()

# app = FastAPI(title="RailWatch Gateway", description="Real-time Indian Railways monitoring system")

# DB_PATH = "railwatch.db"

# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS train_status (
#             id              INTEGER PRIMARY KEY AUTOINCREMENT,
#             train_id        TEXT,
#             train_name      TEXT,
#             zone            TEXT,
#             train_type      TEXT,
#             from_station    TEXT,
#             to_station      TEXT,
#             current_station TEXT,
#             scheduled_time  TEXT,
#             actual_time     TEXT,
#             delay_minutes   REAL,
#             delay_reason    TEXT,
#             status          TEXT,
#             prediction      TEXT,
#             timestamp       REAL
#         )
#     """)
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS alerts (
#             id          INTEGER PRIMARY KEY AUTOINCREMENT,
#             train_id    TEXT,
#             train_name  TEXT,
#             message     TEXT,
#             phone       TEXT,
#             sent        INTEGER DEFAULT 0,
#             timestamp   REAL
#         )
#     """)
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS subscribers (
#             id       INTEGER PRIMARY KEY AUTOINCREMENT,
#             train_id TEXT,
#             phone    TEXT,
#             name     TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# delay_gauge         = Gauge("train_delay_minutes",    "Current delay in minutes",        ["train_id", "zone"])
# zone_health_gauge   = Gauge("zone_health_score",      "Zone health score 0-100",         ["zone"])
# delayed_trains      = Gauge("trains_delayed_total",   "Total delayed trains right now",   ["zone"])
# alerts_sent_counter = Counter("alerts_sent_total",    "Total alerts sent")
# on_time_gauge       = Gauge("trains_on_time_total",   "Trains running on time",           ["zone"])

# ZONES = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bhopal"]
# latest_status = {}

# class TrainStatus(BaseModel):
#     train_id:        str
#     train_name:      str
#     zone:            str
#     train_type:      str
#     from_station:    str
#     to_station:      str
#     current_station: str
#     scheduled_time:  str
#     actual_time:     str
#     delay_minutes:   float
#     delay_reason:    str
#     status:          str

# class Subscriber(BaseModel):
#     train_id: str
#     phone:    str
#     name:     str

# def calc_zone_health(zone: str) -> float:
#     zone_trains = [v for v in latest_status.values() if v["zone"] == zone]
#     if not zone_trains:
#         return 100.0
#     minor = sum(1 for t in zone_trains if 0 < t["delay_minutes"] <= 15)
#     major = sum(1 for t in zone_trains if t["delay_minutes"] > 15)
#     score = 100 - (minor * 10) - (major * 25)
#     return max(0.0, score)

# @app.post("/trains/update")
# def update_train(data: TrainStatus):
#   prediction = "MODEL_NOT_READY"
# if MODEL is not None:
#     try:
#         now        = datetime.now()
#         month      = now.month
#         season     = ("Winter" if month in [12,1,2] else
#                       "Spring" if month in [3,4] else
#                       "Summer" if month in [5,6] else "Monsoon")
#         zone_enc   = LE_ZONE.transform([data.zone])[0]
#         type_enc   = LE_TYPE.transform([data.train_type])[0]
#         season_enc = LE_SEASON.transform([season])[0]
#         features   = np.array([[zone_enc, type_enc,
#                                  now.hour, now.weekday(), season_enc]])
#         pred       = MODEL.predict(features)[0]
#         prediction = LE_LABEL.inverse_transform([pred])[0]
#     except:
#         prediction = "PREDICTION_ERROR"

#     conn = sqlite3.connect(DB_PATH)
#     conn.execute(
#         """INSERT INTO train_status
#            (train_id, train_name, zone, train_type, from_station, to_station,
#             current_station, scheduled_time, actual_time, delay_minutes,
#             delay_reason, status, prediction, timestamp)
#            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
#         (data.train_id, data.train_name, data.zone, data.train_type,
#          data.from_station, data.to_station, data.current_station,
#          data.scheduled_time, data.actual_time, data.delay_minutes,
#          data.delay_reason, data.status, prediction, time.time())
#     )
#     if data.delay_minutes > 30:
#         subs = conn.execute(
#             "SELECT phone, name FROM subscribers WHERE train_id=?",
#             (data.train_id,)
#         ).fetchall()
#         for phone, name in subs:
#             msg = (f"RailWatch Alert: Train {data.train_id} {data.train_name} "
#                    f"is delayed by {int(data.delay_minutes)} mins at {data.current_station}. "
#                    f"Reason: {data.delay_reason}.")
#             conn.execute(
#                 "INSERT INTO alerts (train_id, train_name, message, phone, timestamp) VALUES (?,?,?,?,?)",
#                 (data.train_id, data.train_name, msg, phone, time.time())
#             )
#     conn.commit()
#     conn.close()

#     latest_status[data.train_id] = data.dict()
#     latest_status[data.train_id]["prediction"] = prediction
#     delay_gauge.labels(train_id=data.train_id, zone=data.zone).set(data.delay_minutes)

#     for zone in ZONES:
#         zone_trains = [v for v in latest_status.values() if v["zone"] == zone]
#         delayed_trains.labels(zone=zone).set(sum(1 for t in zone_trains if t["delay_minutes"] > 0))
#         on_time_gauge.labels(zone=zone).set(sum(1 for t in zone_trains if t["delay_minutes"] == 0))
#         zone_health_gauge.labels(zone=zone).set(calc_zone_health(zone))

#     return {"status": "ok", "prediction": prediction, "delay": data.delay_minutes}

# @app.get("/trains")
# def get_all_trains(zone: str = None):
#     trains = list(latest_status.values())
#     if zone:
#         trains = [t for t in trains if t["zone"] == zone]
#     trains.sort(key=lambda x: x["delay_minutes"], reverse=True)
#     return {"total": len(trains), "trains": trains, "zones": {z: calc_zone_health(z) for z in ZONES}}

# @app.get("/delays")
# def get_delays(min_delay: int = 0):
#     delayed = [t for t in latest_status.values() if t["delay_minutes"] >= min_delay]
#     delayed.sort(key=lambda x: x["delay_minutes"], reverse=True)
#     return {"total_delayed": len(delayed), "trains": delayed}

# @app.get("/zones")
# def get_zones():
#     return {zone: {"health_score": round(calc_zone_health(zone), 1),
#                    "trains": [t for t in latest_status.values() if t["zone"] == zone]}
#             for zone in ZONES}

# @app.get("/alerts")
# def get_alerts(limit: int = 20):
#     conn = sqlite3.connect(DB_PATH)
#     rows = conn.execute(
#         "SELECT train_id, train_name, message, phone, sent, timestamp FROM alerts "
#         "ORDER BY timestamp DESC LIMIT ?", (limit,)
#     ).fetchall()
#     conn.close()
#     return {"alerts": [{"train_id": r[0], "train_name": r[1], "message": r[2],
#                          "phone": r[3], "sent": r[4], "timestamp": r[5]} for r in rows]}

# @app.post("/subscribe")
# def subscribe(sub: Subscriber):
#     conn = sqlite3.connect(DB_PATH)
#     conn.execute("INSERT INTO subscribers (train_id, phone, name) VALUES (?,?,?)",
#                  (sub.train_id, sub.phone, sub.name))
#     conn.commit()
#     conn.close()
#     return {"status": "subscribed", "train_id": sub.train_id, "phone": sub.phone}

# @app.get("/health")
# def health():
#     return {"status": "healthy", "service": "railwatch-gateway", "trains_tracked": len(latest_status)}

# @app.get("/metrics")
# def metrics():
#     return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
# class PredictRequest(BaseModel):
#     zone:        str
#     train_type:  str
#     hour:        int
#     day_of_week: int
#     season:      str

# @app.post("/predict")
# def predict_delay(req: PredictRequest):
#     if MODEL is None:
#         return {"error": "Model not loaded"}
#     try:
#         zone_enc   = LE_ZONE.transform([req.zone])[0]
#         type_enc   = LE_TYPE.transform([req.train_type])[0]
#         season_enc = LE_SEASON.transform([req.season])[0]
#         features   = np.array([[zone_enc, type_enc,
#                                  req.hour, req.day_of_week, season_enc]])
#         pred       = MODEL.predict(features)[0]
#         proba      = MODEL.predict_proba(features)[0]
#         label      = LE_LABEL.inverse_transform([pred])[0]
#         confidence = round(float(max(proba)) * 100, 1)
#         return {
#             "prediction":  label,
#             "confidence":  confidence,
#             "zone":        req.zone,
#             "train_type":  req.train_type,
#             "hour":        req.hour
#         }
#     except Exception as e:
#         return {"error": str(e)}
from fastapi import FastAPI, Query
from pydantic import BaseModel
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import sqlite3
import time
import joblib
import numpy as np
from datetime import datetime

MODEL       = None
LE_ZONE     = None
LE_TYPE     = None
LE_SEASON   = None
LE_LABEL    = None

def load_model():
    global MODEL, LE_ZONE, LE_TYPE, LE_SEASON, LE_LABEL
    try:
        MODEL     = joblib.load("model/delay_model.pkl")
        LE_ZONE   = joblib.load("model/le_zone.pkl")
        LE_TYPE   = joblib.load("model/le_type.pkl")
        LE_SEASON = joblib.load("model/le_season.pkl")
        LE_LABEL  = joblib.load("model/le_label.pkl")
        print("ML model loaded successfully")
    except Exception as e:
        print(f"Model not found: {e}")

load_model()

app = FastAPI(title="RailWatch Gateway", description="Real-time Indian Railways monitoring system")

DB_PATH = "railwatch.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS train_status (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id        TEXT,
            train_name      TEXT,
            zone            TEXT,
            train_type      TEXT,
            from_station    TEXT,
            to_station      TEXT,
            current_station TEXT,
            scheduled_time  TEXT,
            actual_time     TEXT,
            delay_minutes   REAL,
            delay_reason    TEXT,
            status          TEXT,
            prediction      TEXT,
            timestamp       REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id    TEXT,
            train_name  TEXT,
            message     TEXT,
            phone       TEXT,
            sent        INTEGER DEFAULT 0,
            timestamp   REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id TEXT,
            phone    TEXT,
            name     TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

delay_gauge         = Gauge("train_delay_minutes",    "Current delay in minutes",        ["train_id", "zone"])
zone_health_gauge   = Gauge("zone_health_score",      "Zone health score 0-100",         ["zone"])
delayed_trains      = Gauge("trains_delayed_total",   "Total delayed trains right now",   ["zone"])
alerts_sent_counter = Counter("alerts_sent_total",    "Total alerts sent")
on_time_gauge       = Gauge("trains_on_time_total",   "Trains running on time",           ["zone"])

ZONES = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bhopal"]
latest_status = {}

class TrainStatus(BaseModel):
    train_id:        str
    train_name:      str
    zone:            str
    train_type:      str
    from_station:    str
    to_station:      str
    current_station: str
    scheduled_time:  str
    actual_time:     str
    delay_minutes:   float
    delay_reason:    str
    status:          str

class Subscriber(BaseModel):
    train_id: str
    phone:    str
    name:     str

def calc_zone_health(zone: str) -> float:
    zone_trains = [v for v in latest_status.values() if v["zone"] == zone]
    if not zone_trains:
        return 100.0
    minor = sum(1 for t in zone_trains if 0 < t["delay_minutes"] <= 15)
    major = sum(1 for t in zone_trains if t["delay_minutes"] > 15)
    score = 100 - (minor * 10) - (major * 25)
    return max(0.0, score)

@app.post("/trains/update")
def update_train(data: TrainStatus):
    # FIX 1: `prediction` declaration and the entire ML block were outside
    # the function body due to wrong indentation — moved inside.
    prediction = "MODEL_NOT_READY"
    if MODEL is not None:
        try:
            now        = datetime.now()
            month      = now.month
            season     = ("Winter" if month in [12,1,2] else
                          "Spring" if month in [3,4] else
                          "Summer" if month in [5,6] else "Monsoon")
            zone_enc   = LE_ZONE.transform([data.zone])[0]
            type_enc   = LE_TYPE.transform([data.train_type])[0]
            season_enc = LE_SEASON.transform([season])[0]
            features   = np.array([[zone_enc, type_enc,
                                     now.hour, now.weekday(), season_enc]])
            pred       = MODEL.predict(features)[0]
            prediction = LE_LABEL.inverse_transform([pred])[0]
        except:
            prediction = "PREDICTION_ERROR"

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO train_status
           (train_id, train_name, zone, train_type, from_station, to_station,
            current_station, scheduled_time, actual_time, delay_minutes,
            delay_reason, status, prediction, timestamp)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data.train_id, data.train_name, data.zone, data.train_type,
         data.from_station, data.to_station, data.current_station,
         data.scheduled_time, data.actual_time, data.delay_minutes,
         data.delay_reason, data.status, prediction, time.time())
    )
    if data.delay_minutes > 30:
        subs = conn.execute(
            "SELECT phone, name FROM subscribers WHERE train_id=?",
            (data.train_id,)
        ).fetchall()
        for phone, name in subs:
            msg = (f"RailWatch Alert: Train {data.train_id} {data.train_name} "
                   f"is delayed by {int(data.delay_minutes)} mins at {data.current_station}. "
                   f"Reason: {data.delay_reason}.")
            conn.execute(
                "INSERT INTO alerts (train_id, train_name, message, phone, timestamp) VALUES (?,?,?,?,?)",
                (data.train_id, data.train_name, msg, phone, time.time())
            )
            # FIX 2: counter was never incremented when an alert was inserted
            alerts_sent_counter.inc()
    conn.commit()
    conn.close()

    latest_status[data.train_id] = data.dict()
    latest_status[data.train_id]["prediction"] = prediction
    delay_gauge.labels(train_id=data.train_id, zone=data.zone).set(data.delay_minutes)

    for zone in ZONES:
        zone_trains = [v for v in latest_status.values() if v["zone"] == zone]
        delayed_trains.labels(zone=zone).set(sum(1 for t in zone_trains if t["delay_minutes"] > 0))
        on_time_gauge.labels(zone=zone).set(sum(1 for t in zone_trains if t["delay_minutes"] == 0))
        zone_health_gauge.labels(zone=zone).set(calc_zone_health(zone))

    return {"status": "ok", "prediction": prediction, "delay": data.delay_minutes}

@app.get("/trains")
def get_all_trains(zone: str = None):
    trains = list(latest_status.values())
    if zone:
        trains = [t for t in trains if t["zone"] == zone]
    trains.sort(key=lambda x: x["delay_minutes"], reverse=True)
    return {"total": len(trains), "trains": trains, "zones": {z: calc_zone_health(z) for z in ZONES}}

@app.get("/delays")
def get_delays(min_delay: int = 0):
    delayed = [t for t in latest_status.values() if t["delay_minutes"] >= min_delay]
    delayed.sort(key=lambda x: x["delay_minutes"], reverse=True)
    return {"total_delayed": len(delayed), "trains": delayed}

@app.get("/zones")
def get_zones():
    return {zone: {"health_score": round(calc_zone_health(zone), 1),
                   "trains": [t for t in latest_status.values() if t["zone"] == zone]}
            for zone in ZONES}

@app.get("/alerts")
def get_alerts(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT train_id, train_name, message, phone, sent, timestamp FROM alerts "
        "ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"alerts": [{"train_id": r[0], "train_name": r[1], "message": r[2],
                         "phone": r[3], "sent": r[4], "timestamp": r[5]} for r in rows]}

@app.post("/subscribe")
def subscribe(sub: Subscriber):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO subscribers (train_id, phone, name) VALUES (?,?,?)",
                 (sub.train_id, sub.phone, sub.name))
    conn.commit()
    conn.close()
    return {"status": "subscribed", "train_id": sub.train_id, "phone": sub.phone}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "railwatch-gateway", "trains_tracked": len(latest_status)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class PredictRequest(BaseModel):
    zone:        str
    train_type:  str
    hour:        int
    day_of_week: int
    season:      str

@app.post("/predict")
def predict_delay(req: PredictRequest):
    if MODEL is None:
        return {"error": "Model not loaded"}
    try:
        zone_enc   = LE_ZONE.transform([req.zone])[0]
        type_enc   = LE_TYPE.transform([req.train_type])[0]
        season_enc = LE_SEASON.transform([req.season])[0]
        features   = np.array([[zone_enc, type_enc,
                                 req.hour, req.day_of_week, season_enc]])
        pred       = MODEL.predict(features)[0]
        proba      = MODEL.predict_proba(features)[0]
        label      = LE_LABEL.inverse_transform([pred])[0]
        confidence = round(float(max(proba)) * 100, 1)
        return {
            "prediction":  label,
            "confidence":  confidence,
            "zone":        req.zone,
            "train_type":  req.train_type,
            "hour":        req.hour
        }
    except Exception as e:
        return {"error": str(e)}