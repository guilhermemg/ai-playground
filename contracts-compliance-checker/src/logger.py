import json
from datetime import datetime, timezone

def log_event(event: dict, path: str = "logs.json"):
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")
