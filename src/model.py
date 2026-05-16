import time
import numpy as np
import tflite_runtime.interpreter as tflite


class TFLiteModel:
    def __init__(self, model_path, num_threads=2):
        self.interpreter = tflite.Interpreter(
            model_path=model_path,
            num_threads=num_threads
        )
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        print("Model loaded")

    def predict(self, image):
        image = image / 255.0
        image = np.expand_dims(image, axis=0).astype(np.float32)
        print(image.shape, image.min(), image.max())

        t0 = time.time()

        self.interpreter.set_tensor(self.input_details[0]['index'], image)
        self.interpreter.invoke()

        output = self.interpreter.get_tensor(self.output_details[0]['index'])

        latency = (time.time() - t0) * 1000

        return output[0][0], latency
