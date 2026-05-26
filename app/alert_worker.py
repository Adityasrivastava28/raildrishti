import sqlite3
import time
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_WHATSAPP_FROM")
DB_PATH     = "railwatch.db"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp(to_number: str, message: str):
    try:
        msg = client.messages.create(
            from_=FROM_NUMBER,
            to=f"whatsapp:{to_number}",
            body=message
        )
        print(f"Alert sent to {to_number}: {msg.sid}")
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

def process_pending_alerts():
    conn  = sqlite3.connect(DB_PATH)
    rows  = conn.execute(
        "SELECT id, train_id, train_name, message, phone FROM alerts WHERE sent=0"
    ).fetchall()

    for row in rows:
        alert_id   = row[0]
        train_id   = row[1]
        train_name = row[2]
        message    = row[3]
        phone      = row[4]

        success = send_whatsapp(phone, message)
        if success:
            conn.execute("UPDATE alerts SET sent=1 WHERE id=?", (alert_id,))
            conn.commit()
            print(f"Alert for {train_id} sent successfully")

    conn.close()

def main():
    print("RailDrishti Alert Worker started")
    print("Checking for pending alerts every 30 seconds...")
    while True:
        try:
            process_pending_alerts()
        except Exception as e:
            print(f"Alert worker error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()