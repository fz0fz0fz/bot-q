import requests
import logging
from config import WASENDER_API_KEY, WASENDER_BASE_URL, ADMIN_PHONE

logger = logging.getLogger(__name__)

def send_message(to_number: str, message: str, timeout: int = 30) -> dict:
    url = f"{WASENDER_BASE_URL}/send-message"
    headers = {
        "Authorization": f"Bearer {WASENDER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": to_number,
        "text": message
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Message sent successfully to {to_number}")
        return {"success": True, "response": response.json()}
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
        return {"success": False, "error": str(e)}

def send_admin_notification(subject: str, user_id: str, details: str) -> dict:
    notification_message = f"نوع الرسالة: {subject}\nمن: {user_id}\nالبيانات: {details}"
    return send_message(ADMIN_PHONE, notification_message)