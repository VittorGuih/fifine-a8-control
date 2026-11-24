"""Read-only device inspection. Prints no machine-specific IDs unless requested."""
import argparse
import json
from .control import ControlClient

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only FIFINE A8 availability check.")
    parser.add_argument("--json", action="store_true", help="Print status as JSON.")
    args = parser.parse_args(argv)
    client = ControlClient()
    try:
        result = client.start()
        if args.json:
            print(json.dumps(result))
        elif result.get("ok"):
            print("One FIFINE A8 (3142:00a8) capture endpoint found.")
            print("Windows cached mute: " + ("on" if result["muted"] else "off"))
            print("Input level: {:.1f}%".format(result["level"] * 100))
            print("No audio settings were changed. This is not a physical LED readout.")
        else:
            print(result.get("error", "The A8 was not found."))
        return 0 if result.get("ok") else 1
    except RuntimeError as exc:
        print(json.dumps({"ok":False,"error":str(exc)}) if args.json else str(exc))
        return 1
    finally:
        client.close()

if __name__ == "__main__":
    raise SystemExit(main())
