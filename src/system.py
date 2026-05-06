import psutil
import os

process = psutil.Process(os.getpid())


def get_stats():
    ram = process.memory_info().rss / 1024 / 1024
    cpu = psutil.cpu_percent(interval=None, percpu=True)

    try:
        temp = psutil.sensors_temperatures()
        cpu_temp = list(temp.values())[0][0].current
    except:
        cpu_temp = -1

    return ram, cpu, cpu_temp