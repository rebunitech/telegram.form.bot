import json


class Setup:
    def __init__(self, file):
        configs = json.load(open(file, "r"))
        for attr, value in configs.items():
            setattr(self, attr, value)
