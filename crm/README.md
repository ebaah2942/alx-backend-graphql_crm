# CRM Reporting with Celery & GraphQL

### Setup
1. Install dependencies:
pip install -r requirements.txt

2. Start Redis:
redis-server


3. Run migrations:
python manage.py migrate


4. Start Celery worker:
celery -A crm worker -l info


5. Start Celery Beat:
celery -A crm beat -l info


6. Check reports:
cat /tmp/crm_report_log.txt

