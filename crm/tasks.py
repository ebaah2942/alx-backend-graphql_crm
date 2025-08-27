from celery import shared_task
from django.utils import timezone
from graphene_django.settings import graphene_settings
from graphene import Schema

@shared_task
def generate_crm_report():
    schema: Schema = graphene_settings.SCHEMA

    query = '''
    query {
        totalCustomers
        totalOrders
        totalRevenue
    }
    '''
    result = schema.execute(query)

    if result.errors:
        log_msg = f"{timezone.now()} - Error: {result.errors}"
    else:
        data = result.data
        customers = data["totalCustomers"]
        orders = data["totalOrders"]
        revenue = data["totalRevenue"]

        log_msg = (
            f"{timezone.now().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Report: {customers} customers, {orders} orders, {revenue} revenue"
        )

    with open("/tmp/crm_report_log.txt", "a") as f:
        f.write(log_msg + "\n")

    return log_msg
