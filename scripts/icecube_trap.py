import os
import json
import time
from datetime import datetime, timezone
from gcn_kafka import Consumer

# Pull credentials securely from GitHub Actions environment
CLIENT_ID = os.environ.get("GCN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GCN_CLIENT_SECRET")
CSV_FILE = "data/neutrino_events/icecube_strikes.csv"

def run_trap(timeout_seconds=240):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Arming LUFT Neutrino Trap (Python)...")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("CRITICAL: NASA GCN credentials not found in environment.")
        return

    consumer = Consumer(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    
    # Subscribe to the exact topic you found for Gold/Bronze alerts
    consumer.subscribe(['gcn.notices.icecube.gold_bronze_track_alerts'])

    # Ensure the directory exists
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE)

    start_time = time.time()
    
    try:
        # Listen for 4 minutes, then exit cleanly
        while time.time() - start_time < timeout_seconds:
            for message in consumer.consume(timeout=1.0):
                if message.error():
                    print(f"Stream Error: {message.error()}")
                    continue

                print("\n==================================================")
                print(f"KINETIC STRIKE DETECTED ON CHANNEL: {message.topic()}")
                print("==================================================")
                
                raw_data = message.value()
                
                try:
                    # Parse the JSON payload to extract cleanly
                    payload = json.loads(raw_data.decode('utf-8'))
                    strike_time = datetime.now(timezone.utc).isoformat()
                    
                    # Log the raw event to the CSV
                    with open(CSV_FILE, 'a') as f:
                        if not file_exists:
                            f.write("timestamp,topic,raw_payload\n")
                            file_exists = True
                        
                        # We save the raw JSON string in the CSV so you can parse RA/Dec later
                        clean_payload = json.dumps(payload).replace('"', '""')
                        f.write(f"{strike_time},{message.topic()},\"{clean_payload}\"\n")
                        
                    print(f"SUCCESS: Subatomic strike logged to {CSV_FILE}")
                    
                except Exception as e:
                    print(f"Failed to parse payload: {e}")
                    print(raw_data)

    except KeyboardInterrupt:
        print("Trap disarmed locally.")
    finally:
        consumer.close()
        print("4-minute window complete. Connection safely closed to preserve compute budget.")

if __name__ == "__main__":
    run_trap()
