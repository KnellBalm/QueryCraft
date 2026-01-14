# backend/services/notification_service.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.common.logging import get_logger

logger = get_logger(__name__)

def send_email(subject: str, body: str, to_email: str = None):
    """이메일 발송 유틸리티"""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not smtp_user or not smtp_password:
        logger.warning("SMTP 설정이 누락되어 이메일을 발송할 수 없습니다.")
        return False

    target_email = to_email or smtp_user
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = target_email
        msg['Subject'] = f"[QueryCraft] {subject}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"이메일 발송 성공: {subject} to {target_email}")
        return True
    except Exception as e:
        logger.error(f"이메일 발송 실패: {e}")
        return False
