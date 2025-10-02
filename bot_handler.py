import requests
import logging
import re
from config import (
    WASENDER_API_KEY, 
    WASENDER_BASE_URL, 
    ADMIN_PHONE
)


class BotHandler:
    def process_message(self, user_id, message):
        # يقبل أي رقم ويرد عليه برسالة عادية
        return f"تم استقبال رسالتك: {message}"

logger = logging.getLogger(__name__)

def send_message(to_number: str, message: str) -> dict:
    url = f"{WASENDER_BASE_URL}/message/send"
    headers = {
        "Content-Type": "application/json",
        "apikey": WASENDER_API_KEY
    }
    payload = {
        "number": to_number,
        "message": message
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Message sent successfully to {to_number}")
        return {"success": True, "response": response.json()}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message to {to_number}: {e}")
        return {"success": False, "error": str(e)}

def send_admin_notification(subject: str, user_id: str, details: str) -> dict:
    notification_message = f"نوع الرسالة: {subject}\nمن: {user_id}\nالبيانات: {details}"
    return send_message(ADMIN_PHONE, notification_message)

def is_valid_phone_number(phone_number: str) -> bool:
    # تعبير عادي للتحقق من أرقام الجوال السعودية (05xxxxxxxx) أو الدولية (+9665xxxxxxxx)
    # يمكن تعديل هذا التعبير ليتناسب مع متطلبات أكثر دقة
    pattern = r"^(05|\+9665)\d{8}$"
    return bool(re.match(pattern, phone_number))