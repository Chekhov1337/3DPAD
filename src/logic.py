class DefectDetector:
    def __init__(self, threshold_count):
        self.threshold = threshold_count
        self.counter = 0

    def update(self, pred):
        if pred == 1:
            self.counter += 1
        else:
            self.counter = 0

        return self.counter >= self.threshold