"""Windows audio control transport. Only explicit mute/unmute requests write audio settings."""
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading

SERVER = Path(__file__).parent / "native" / "audio-server.ps1"

class ControlClient:
    def __init__(self):
        self.process = None
        self._replies = queue.Queue()

    def start(self):
        if sys.platform != "win32":
            raise RuntimeError("Fifine A8 Control currently supports Windows only.")
        powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        self.process = subprocess.Popen(
            [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
        )
        def read():
            try:
                for line in self.process.stdout:
                    self._replies.put(json.loads(line))
            except Exception as exc:
                self._replies.put({"ok": False, "error": str(exc)})
            finally:
                self._replies.put(None)
        threading.Thread(target=read, daemon=True).start()
        # Drain native errors so a full stderr pipe cannot block the helper.
        threading.Thread(target=lambda: self.process.stderr.read(), daemon=True).start()
        return self._reply()

    def _reply(self):
        try:
            reply = self._replies.get(timeout=12)
        except queue.Empty:
            raise RuntimeError("The Windows audio helper timed out. Close and reopen the app.") from None
        if reply is None:
            raise RuntimeError("The Windows audio helper stopped. Close and reopen the app.")
        return reply

    def request(self, command):
        if command not in {"mute", "unmute", "status"}:
            raise ValueError("Unsupported audio command")
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("The Windows audio helper is not running.")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        return self._reply()

    def close(self):
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
                self.process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                self.process.terminate()
                self.process.wait(timeout=2)
