import logging
import os
import json
import sys
from datetime import datetime

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """GCP Cloud Run 호환 JSON 포맷터"""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    env = os.getenv("ENV", "development")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if env == "production":
        # 상용 환경: stdout에 JSON 형식으로 출력 (GCP가 파싱)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(console_handler)
    else:
        # 개발 환경: 보기 편한 텍스트 형식
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        file_handler = logging.FileHandler(f"{LOG_DIR}/query_craft.log")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

# 앱 시작 시 호출
setup_logging()

def get_logger(name: str):
    return logging.getLogger(name)
