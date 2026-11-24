"""Observed FIFINE A8 HID input; this is an action notification, not LED state."""
VID = 0x3142
PID = 0x00A8
CONSUMER_PAGE = 0x0C
CONSUMER_USAGE = 0x01
# Captured on the tested A8 firmware. Do not accept ordinary consumer mute keys.
BUTTON_REPORT = bytes.fromhex("01 80 00 00 00 ff 00 ff 42 31 a8 00 40 00 20 21")

def is_button_report(report):
    """Preserve identical reports: each can represent a separate physical press."""
    return bytes(report) == BUTTON_REPORT

def consumer_interfaces(devices):
    """Select only the A8 consumer collection, never another microphone."""
    return [d for d in devices if d.get("vendor_id") == VID and d.get("product_id") == PID
            and d.get("usage_page") == CONSUMER_PAGE and d.get("usage") == CONSUMER_USAGE]
