from backend.services.db_logger import get_logs
import json
from datetime import datetime

logs = get_logs(level='error', limit=50)
for log in logs:
    if isinstance(log.get('created_at'), datetime):
        log['created_at'] = log['created_at'].isoformat()
    print(json.dumps(log, ensure_ascii=False))
