"""Test send — send a MIM message from command line.

Usage:
  python apps/winpeek-injector/send.py --to 2002 --from CC-yu2 --msg "task done"
"""

import json, argparse, time
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO = True
except ImportError:
    HAS_PAHO = False
    print("[error] pip install paho-mqtt")
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Send MIM message via MQTT")
    parser.add_argument("--to", required=True, type=int, help="Target agent uid")
    parser.add_argument("--from", dest="sender", default="cli", help="Sender name")
    parser.add_argument("--msg", required=True, help="Message body")
    parser.add_argument("--host", default="192.168.3.23")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    topic = f"comms/say/{getattr(args, 'to')}"
    payload = json.dumps({
        "from_uid": "0",
        "from": args.sender,
        "to_uid": str(getattr(args, 'to')),
        "body": args.msg,
        "ts": datetime.now().isoformat(),
    }, ensure_ascii=False)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(args.host, args.port, 60)
    client.publish(topic, payload, qos=1)
    client.disconnect()
    print(f"sent → uid={getattr(args, 'to')}: {args.msg}")


if __name__ == "__main__":
    main()
