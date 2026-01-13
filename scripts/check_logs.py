from backend.services.db_logger import get_logs
import json
from datetime import datetime

logs = get_logs(limit=50)
for log in logs:
    # Convert datetime to string for printing
    if isinstance(log.get('created_at'), datetime):
        log['created_at'] = log['created_at'].isoformat()
    print(json.dumps(log, ensure_ascii=False))
