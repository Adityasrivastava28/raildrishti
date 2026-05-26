import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="RailWatch", page_icon="🚂", layout="wide")

GATEWAY_URL = "http://localhost:8000"

def get_trains(zone=None):
    try:
        url = f"{GATEWAY_URL}/trains"
        if zone and zone != "All Zones":
            url += f"?zone={zone}"
        return requests.get(url, timeout=3).json()
    except:
        return {"trains": [], "zones": {}}

def get_alerts():
    try:
        return requests.get(f"{GATEWAY_URL}/alerts?limit=15", timeout=3).json().get("alerts", [])
    except:
        return []

def status_icon(status):
    return {"ON_TIME":"🟢","MINOR_DELAY":"🟡","MAJOR_DELAY":"🔴","SEVERELY_DELAYED":"🆘"}.get(status,"⚪")

def zone_color(score):
    if score >= 75: return "🟢"
    if score >= 50: return "🟡"
    return "🔴"

st.title("🚂 RailWatch — Indian Railways Live Monitor")
st.caption("Real-time delay tracking across 5 zones · 20 trains · refreshes every 5 seconds")

zones    = ["All Zones","Delhi","Mumbai","Chennai","Kolkata","Bhopal"]
selected = st.selectbox("Filter by zone", zones)

data    = get_trains(selected if selected != "All Zones" else None)
trains  = data.get("trains", [])
z_scores= data.get("zones", {})
alerts  = get_alerts()

st.markdown("---")
st.subheader("Zone Health")
cols = st.columns(5)
for i, zone in enumerate(["Delhi","Mumbai","Chennai","Kolkata","Bhopal"]):
    score = z_scores.get(zone, 100)
    with cols[i]:
        st.metric(f"{zone_color(score)} {zone}", f"{score:.0f}/100",
                  delta="Healthy" if score>=75 else "Degraded" if score>=50 else "Critical",
                  delta_color="normal" if score>=75 else "inverse")

st.markdown("---")
total     = len(trains)
on_time   = sum(1 for t in trains if t["status"]=="ON_TIME")
minor     = sum(1 for t in trains if t["status"]=="MINOR_DELAY")
major     = sum(1 for t in trains if t["status"]=="MAJOR_DELAY")
severe    = sum(1 for t in trains if t["status"]=="SEVERELY_DELAYED")
avg_delay = sum(t["delay_minutes"] for t in trains)/total if total else 0
max_delay = max((t["delay_minutes"] for t in trains), default=0)
worst     = next((t["train_name"] for t in trains if t["delay_minutes"]==max_delay),"None")

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.metric("Total Trains", total)
with c2: st.metric("🟢 On Time", on_time)
with c3: st.metric("🟡 Minor Delay", minor)
with c4: st.metric("🔴 Major Delay", major)
with c5: st.metric("🆘 Severe", severe)

st.markdown("---")
c6,c7,c8 = st.columns(3)
with c6: st.metric("Avg Delay", f"{avg_delay:.1f} min")
with c7: st.metric("Max Delay", f"{max_delay:.0f} min")
with c8: st.metric("Most Delayed", worst[:25] if worst else "None")

st.markdown("---")
st.subheader("Live Train Status")

if not trains:
    st.warning("No train data yet — make sure gateway and simulator are running.")
else:
    for t in trains:
        icon  = status_icon(t["status"])
        delay = t["delay_minutes"]
        with st.expander(
            f"{icon}  {t['train_id']} — {t['train_name']}  |  Delay: {delay:.0f} min  |  Zone: {t['zone']}  |  {t['status']}",
            expanded=delay>30
        ):
            col1,col2,col3,col4 = st.columns(4)
            with col1:
                st.metric("Current Station", t["current_station"])
                st.metric("Route", f"{t['from_station']} → {t['to_station']}")
            with col2:
                st.metric("Delay", f"{delay:.0f} minutes",
                          delta="CRITICAL" if delay>60 else "HIGH" if delay>30 else "OK",
                          delta_color="inverse" if delay>15 else "normal")
                st.metric("Train Type", t["train_type"])
            with col3:
                st.metric("Reason", t["delay_reason"])
                st.metric("Zone", t["zone"])
            with col4:
                st.metric("Prediction", t.get("prediction","UNKNOWN"))
                st.metric("Scheduled", t["scheduled_time"][11:16] if len(t["scheduled_time"])>11 else "—")

st.markdown("---")
st.subheader("🚨 Alert Feed — Trains delayed 30+ minutes")
if not alerts:
    st.success("No major delays — all trains running normally.")
else:
    for alert in alerts:
        ts = datetime.fromtimestamp(alert["timestamp"]).strftime("%H:%M:%S")
        st.error(f"🚨 [{ts}] {alert['train_id']} — {alert['message']}")

st.markdown("---")
st.subheader("📱 Subscribe to WhatsApp Alerts")
st.caption("Get a WhatsApp message when your train is delayed by 30+ minutes")
with st.form("subscribe_form"):
    col1,col2,col3 = st.columns(3)
    with col1: train_id = st.text_input("Train Number", placeholder="12951")
    with col2: phone    = st.text_input("WhatsApp Number", placeholder="+919876543210")
    with col3: name     = st.text_input("Your Name", placeholder="Rahul")
    submitted = st.form_submit_button("Subscribe")
    if submitted and train_id and phone and name:
        try:
            r = requests.post(f"{GATEWAY_URL}/subscribe",
                              json={"train_id":train_id,"phone":phone,"name":name})
            st.success(f"Subscribed! You will get WhatsApp alerts for train {train_id}")
        except:
            st.error("Could not subscribe — check gateway is running")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}  ·  Refreshing every 5 seconds")
time.sleep(5)
st.rerun()
