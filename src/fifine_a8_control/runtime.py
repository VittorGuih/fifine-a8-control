"""Background workers; HID input only, with optional local diagnostic logging."""
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import queue
import threading
import time
import hid
from .control import ControlClient
from .protocol import VID, PID, consumer_interfaces, is_button_report

events = queue.Queue()
commands = queue.Queue()
closing = threading.Event()
_logger = logging.getLogger("fifine_a8_control")
_logger.addHandler(logging.NullHandler())

def enable_debug():
    directory = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "FifineA8Control" / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(directory / "events.jsonl", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)

def log(event, **fields):
    _logger.info(json.dumps({"time": datetime.now().astimezone().isoformat(), "event": event, **fields}))

def backend():
    client = ControlClient()
    try:
        first = client.start()
        events.put(("ready", first))
        last_available = first.get("ok", False)
        last_check = time.monotonic()
        while not closing.is_set():
            try:
                command = commands.get(timeout=0.2)
            except queue.Empty:
                if time.monotonic() - last_check > 2:
                    status = client.request("status")
                    if status.get("ok", False) != last_available:
                        events.put(("availability", status))
                        last_available = status.get("ok", False)
                    last_check = time.monotonic()
                continue
            response = client.request(command)
            log("CONTROL", command=command, **response)
            events.put(("response", response))
    except Exception as exc:
        events.put(("error", str(exc)))
    finally:
        client.close()

def monitor():
    while not closing.is_set():
        device = None
        try:
            interfaces = consumer_interfaces(hid.enumerate(VID, PID))
            if len(interfaces) != 1:
                raise RuntimeError("Connect exactly one FIFINE A8 (3142:00a8).")
            device = hid.device()
            device.open_path(interfaces[0]["path"])
            device.set_nonblocking(1)
            events.put(("connected", None))
            while not closing.is_set():
                report = device.read(128)
                if report and is_button_report(report):
                    log("BUTTON_EVENT")
                    events.put(("button", datetime.now().strftime("%H:%M:%S")))
                closing.wait(0.01)
        except Exception as exc:
            events.put(("device_error", str(exc)))
            closing.wait(2)
        finally:
            if device is not None:
                device.close()
