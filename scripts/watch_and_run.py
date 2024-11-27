import os
import signal
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ScriptReloader(FileSystemEventHandler):
    def __init__(self, script_path, watch_path):
        self.script_path = script_path
        self.watch_path = watch_path
        self.process = None
        self.start_script()

    def start_script(self):
        if self.process:
            try:
                pgid = os.getpgid(self.process.pid)
                os.killpg(pgid, signal.SIGTERM)
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

            time.sleep(2)

        self.process = subprocess.Popen(
            [sys.executable, self.script_path], preexec_fn=os.setsid
        )

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"\nRestarting {self.script_path}...")
            self.start_script()


def main():
    if len(sys.argv) != 3:
        print("Usage: watch_and_run.py <script_path> <watch_path>")
        sys.exit(1)

    script_path = sys.argv[1]
    watch_path = sys.argv[2]

    event_handler = ScriptReloader(script_path, watch_path)
    observer = Observer()
    observer.schedule(event_handler, path=watch_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            pgid = os.getpgid(event_handler.process.pid)
            os.killpg(pgid, signal.SIGTERM)
    observer.join()


if __name__ == "__main__":
    main()
