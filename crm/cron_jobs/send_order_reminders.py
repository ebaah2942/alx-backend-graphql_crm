#!/usr/bin/env python3
import sys
import logging
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
log_file = "/tmp/order_reminders_log.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

def main():
    try:
        # GraphQL endpoint
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # Calculate last 7 days
        last_week = (datetime.now() - timedelta(days=7)).date().isoformat()

        # GraphQL query
        query = gql("""
        query GetPendingOrders($date: Date!) {
            orders(orderDateGte: $date) {
                id
                customer {
                    email
                }
            }
        }
        """)

        # Execute query
        params = {"date": last_week}
        result = client.execute(query, variable_values=params)

        # Process results
        for order in result.get("orders", []):
            order_id = order["id"]
            customer_email = order["customer"]["email"]
            logging.info(f"Reminder: Order ID {order_id}, Customer Email {customer_email}")

        print("Order reminders processed!")

    except Exception as e:
        logging.error(f"Error processing reminders: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
