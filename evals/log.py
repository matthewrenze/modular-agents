import os
import datetime


class Log:
    def __init__(self, name):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d - %H-%M-%S")
        log_path  = os.path.join("../data/logs", f"{timestamp} - {name}.txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.file = open(log_path, "w")

    def write(self, *args, **kwargs):
        print(*args, **kwargs)
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        self.file.write(sep.join(str(a) for a in args) + end)
        self.file.flush()

    def close(self):
        self.file.close()
