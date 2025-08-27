import datetime
import requests

def log_crm_heartbeat():
    """Log a heartbeat message and optionally query GraphQL hello field."""
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    # Append to heartbeat log
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(log_message)

    # Optionally verify GraphQL hello field
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"}
        )
        if response.ok:
            result = response.json()
            hello_msg = result.get("data", {}).get("hello", "No response")
            with open("/tmp/crm_heartbeat_log.txt", "a") as f:
                f.write(f"GraphQL hello: {hello_msg}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"GraphQL check failed: {e}\n")
    