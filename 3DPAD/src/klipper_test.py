import time
import requests

MOONRAKER_URL = "http://127.0.0.1:7125"

CHECK_INTERVAL = 2  # сек


# =============================
# GET PRINT STATE
# =============================
def get_print_state():
    try:
        r = requests.get(
            f"{MOONRAKER_URL}/printer/objects/query?print_stats",
            timeout=3
        ).json()

        return r["result"]["status"]["print_stats"]["state"]

    except Exception as e:
        print("ERROR:", e)
        return "unknown"


# =============================
# SEND MESSAGE TO UI
# =============================
def send_message(msg):
    try:
        requests.post(
            f"{MOONRAKER_URL}/printer/gcode/script",
            json={"script": f'RESPOND MSG="{msg}"'},
            timeout=3
        )
    except:
        pass


# =============================
# WATCH LOOP
# =============================
print("👀 Watching printer state...")

prev_state = None

while True:

    state = get_print_state()

    if state != prev_state:
        print(f"State changed: {prev_state} → {state}")

        # 🔥 НАЧАЛО ПЕЧАТИ
        if state == "printing":
            print("🚀 PRINT START DETECTED")
            send_message("3DPAD: PRINT STARTED")

        # 🔚 КОНЕЦ ПЕЧАТИ
        if state in ["complete", "standby"]:
            print("🏁 PRINT FINISHED")
            send_message("3DPAD: PRINT FINISHED")

    prev_state = state

    time.sleep(CHECK_INTERVAL)