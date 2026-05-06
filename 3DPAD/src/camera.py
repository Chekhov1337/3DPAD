import requests
import numpy as np
from PIL import Image
from io import BytesIO


class Camera:
    def __init__(self, url, width, height):
        self.url = url
        self.width = width
        self.height = height

    def get_frame(self):
        r = requests.get(self.url, timeout=3)
        img = Image.open(BytesIO(r.content)).convert("RGB")

        img = img.resize((self.width, self.height))

        return np.array(img, dtype=np.float32)