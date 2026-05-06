import time
import configparser
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

CAM_URL = config["camera"]["snapshot_url"]
INTERVAL = config.getint("vision", "interval_sec")

MODEL_PATH = config["model"]["path"]
THRESHOLD = config.getfloat("model", "threshold")
NUM_THREADS = config.getint("model", "num_threads")

W = config.getint("preprocess", "width")
H = config.getint("preprocess", "height")

DEFECT_N = config.getint("logic", "defect_threshold")
MODE = config["logic"]["mode"]

MOONRAKER = config.getboolean("moonraker", "enabled")
PAUSE_URL = config["moonraker"]["pause_url"]


# =============================
# INIT
# =============================
print("Starting 3DPAD...")

model = TFLiteModel(MODEL_PATH, NUM_THREADS)
camera = Camera(CAM_URL, W, H)
detector = DefectDetector(DEFECT_N)


# =============================
# ACTION
# =============================
def pause_print():
    if not MOONRAKER:
        return

    try:
        requests.post(PAUSE_URL, timeout=2)
        print("Print paused")
    except:
        print("Failed to pause print")


# =============================
# MAIN LOOP
# =============================
print("\nRunning...\n")

total_time = 0
total = 0

while True:

    frame = camera.get_frame()
    prob, latency = model.predict(frame)

    pred = 1 if prob > THRESHOLD else 0

    triggered = detector.update(pred)

    ram, cpu, temp = get_stats()
    cpu_str = " | ".join([f"{c:.1f}%" for c in cpu])

    print(
        f"prob={prob:.3f} "
        f"pred={pred} "
        f"defect={detector.counter}/{DEFECT_N} "
        f"t={latency:.1f}ms "
        f"RAM={ram:.1f}MB "
        f"CPU=[{cpu_str}] "
        f"TEMP={temp:.1f}°C"
    )

    total += 1
    total_time += latency

    # ACTION
    if triggered:
        print("DEFECT DETECTED")

        if MODE == "pause":
            pause_print()

        detector.counter = 0

    time.sleep(INTERVAL)