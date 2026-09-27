import threading

import psutil


class SystemMonitor:
    """Polls CPU/RAM once per interval on a daemon thread and reports via callback."""

    def __init__(self, interval=1.0):
        self.interval = interval
        self.cpu_usage = 0.0
        self.ram_usage = 0.0
        self._stop = threading.Event()
        self._thread = None

    def sample(self):
        self.cpu_usage = psutil.cpu_percent()
        self.ram_usage = psutil.virtual_memory().percent
        return self.cpu_usage, self.ram_usage

    def start_monitoring(self, update_callback):
        def loop():
            while not self._stop.is_set():
                update_callback(*self.sample())
                self._stop.wait(self.interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._stop.set()
