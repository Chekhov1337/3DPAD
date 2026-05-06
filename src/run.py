import time
import configparser
import threading

import requests

from model import TFLiteModel
from camera import Camera
from system import get_stats
from logic import DefectDetector


# =============================
# CONFIG
# =============================
config = configparser.ConfigParser()
config.read("config/vision.cfg")

MOONRAKER_URL = config["moonraker"]["url"]

POLL_INTERVAL = config.getint("vision", "poll_interval_sec")
ANALYSIS_INTERVAL = config.getint("vision", "analysis_interval_sec")
WARMUP_TIME = config.getint("vision", "warmup_time_sec")

CAM_URL = config["camera"]["snapshot_url"]

MODEL_PATH = config["model"]["path"]
THRESHOLD = config.getfloat("model", "threshold")
THREADS = config.getint("model", "num_threads")

W = config.getint("preprocess", "width")
H = config.getint("preprocess", "height")

DEFECT_N = config.getint("logic", "defect_threshold")
MODE = config["logic"]["mode"]


# =============================
# INIT
# =============================
model = TFLiteModel(MODEL_PATH, THREADS)
camera = Camera(CAM_URL, W, H)
detector = DefectDetector(DEFECT_N)


# =============================
# MOONRAKER HELPERS
# =============================
def get_state():
    try:
        r = requests.get(
            f"{MOONRAKER_URL}/printer/objects/query?print_stats",
            timeout=3
        ).json()

        return r["result"]["status"]["print_stats"]["state"]
    except:
        return "unknown"


def send(msg):
    try:
        requests.post(
            f"{MOONRAKER_URL}/printer/gcode/script",
            json={"script": f'RESPOND MSG="{msg}"'},
            timeout=3
        )
    except:
        pass


def pause():
    requests.post(f"{MOONRAKER_URL}/printer/print/pause", timeout=3)


# =============================
# ANALYSIS LOOP
# =============================
def analysis_loop(stop_event):
    print("🧠 Analysis started")

    detector.counter = 0

    while not stop_event.is_set():

        frame = camera.get_frame()
        prob, t = model.predict(frame)

        pred = 1 if prob > THRESHOLD else 0
        triggered = detector.update(pred)

        ram, cpu, temp = get_stats()
        cpu_str = " | ".join([f"{c:.0f}%" for c in cpu])

        print(
            f"[AI] prob={prob:.3f} "
            f"pred={pred} "
            f"t={t:.1f}ms "
            f"CPU=[{cpu_str}] "
            f"TEMP={temp:.1f}°C"
        )

        if triggered:
            print("🚨 DEFECT DETECTED")
            send("3DPAD: DEFECT DETECTED")

            if MODE == "pause":
                pause()

            detector.counter = 0

        time.sleep(ANALYSIS_INTERVAL)

    print("🛑 Analysis stopped")


# =============================
# MAIN STATE MACHINE
# =============================
print("🚀 3DPAD started")

state_prev = None
analysis_thread = None
stop_event = None

warmup_started = False
warmup_start_time = None


while True:

    state = get_state()

    # =========================
    # PRINT START
    # =========================
    if state == "printing" and state_prev != "printing":

        print("🚀 PRINT START DETECTED")
        send("3DPAD: PRINT STARTED")

        warmup_started = True
        warmup_start_time = time.time()

        stop_event = threading.Event()

    # =========================
    # WARMUP PHASE
    # =========================
    if warmup_started:

        elapsed = time.time() - warmup_start_time

        if elapsed >= WARMUP_TIME:
            warmup_started = False

            print("🔥 Warmup finished → starting AI loop")

            analysis_thread = threading.Thread(
                target=analysis_loop,
                args=(stop_event,),
                daemon=True
            )
            analysis_thread.start()

    # =========================
    # PRINT FINISHED
    # =========================
    if state in ["complete", "standby"] and state_prev == "printing":

        print("🏁 PRINT FINISHED")
        send("3DPAD: PRINT FINISHED")

        if stop_event:
            stop_event.set()

        warmup_started = False

    state_prev = state
    time.sleep(POLL_INTERVAL)
