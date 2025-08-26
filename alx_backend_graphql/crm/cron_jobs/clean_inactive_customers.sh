#!/bin/bash
# Script to delete inactive customers (no orders in the last year)
# Logs results to /tmp/customer_cleanup_log.txt

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Run Django shell command to delete customers
DELETED_COUNT=$(python manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

cutoff = timezone.now() - timedelta(days=365)
qs = Customer.objects.filter(orders__isnull=True, created_at__lt=cutoff)
count = qs.count()
qs.delete()
print(count)
")

# Append log
echo \"[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers\" >> /tmp/customer_cleanup_log.txt
