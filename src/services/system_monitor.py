import psutil
import threading
import time

class SystemMonitor:
    def __init__(self):
        self.cpu_usage = 0
        self.ram_usage = 0
        self._stop_monitoring = False

    def start_monitoring(self, update_callback):
        def monitor():
            while not self._stop_monitoring:
                self.cpu_usage = psutil.cpu_percent()
                self.ram_usage = psutil.virtual_memory().percent
                
                # Call update callback with current stats
                update_callback(self.cpu_usage, self.ram_usage)
                
                time.sleep(1)

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self._stop_monitoring = True
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()