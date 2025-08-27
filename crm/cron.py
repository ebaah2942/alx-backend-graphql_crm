import datetime
import requests
from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client



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



def update_low_stock():
    url = "http://127.0.0.1:8000/graphql/"  # your GraphQL endpoint
    query = """
    mutation {
        updateLowStockProducts {
            message
            updatedProducts {
                id
                name
                stock
            }
        }
    }
    """

    response = requests.post(url, json={'query': query})
    data = response.json()

    log_file = "/tmp/low_stock_updates_log.txt"
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {data}\n")            
    