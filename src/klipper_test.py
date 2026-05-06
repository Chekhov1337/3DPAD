import time
import requests
import threading

MOONRAKER_URL = "http://127.0.0.1:7125"
CHECK_INTERVAL = 2


# =============================
# API
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


def send_message(msg):
    try:
        requests.post(
            f"{MOONRAKER_URL}/printer/gcode/script",
            json={"script": f'RESPOND MSG="{msg}"'},
            timeout=3
        )
    except:
        pass


def pause_print():
    try:
        requests.post(
            f"{MOONRAKER_URL}/printer/print/pause",
            timeout=3
        )
        print("⏸ Print paused")
    except Exception as e:
        print("PAUSE ERROR:", e)


def resume_print():
    try:
        requests.post(
            f"{MOONRAKER_URL}/printer/print/resume",
            timeout=3
        )
        print("▶ Print resumed")
    except Exception as e:
        print("RESUME ERROR:", e)


# =============================
# TEST SEQUENCE
# =============================
def test_sequence():
    print("⏳ Waiting 30 sec before pause...")
    time.sleep(30)

    send_message("3DPAD: PAUSING PRINT")
    pause_print()

    print("⏳ Waiting 30 sec before resume...")
    time.sleep(30)

    send_message("3DPAD: RESUMING PRINT")
    resume_print()

    print("✅ Test finished")


# =============================
# WATCH LOOP
# =============================
print("👀 Watching printer state...")

prev_state = None
test_started = False

while True:

    state = get_print_state()

    if state != prev_state:
        print(f"State changed: {prev_state} → {state}")

        # 🚀 СТАРТ ПЕЧАТИ
        if state == "printing" and not test_started:
            print("🚀 PRINT START DETECTED")
            send_message("3DPAD: TEST STARTED")

            # запускаем тест в отдельном потоке
            threading.Thread(target=test_sequence, daemon=True).start()
            test_started = True

        # 🏁 СБРОС после завершения
        if state in ["complete", "standby"]:
            print("🏁 PRINT FINISHED")
            test_started = False

    prev_state = state

    time.sleep(CHECK_INTERVAL)
