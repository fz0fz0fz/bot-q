import requests
import logging
from config import WASENDER_API_KEY, WASENDER_BASE_URL, ADMIN_PHONE

logger = logging.getLogger(__name__)

def send_message(to_number: str, message: str, timeout: int = 30) -> dict:
    """
    إرسال رسالة عبر WhatsApp API
    
    Args:
        to_number: رقم المستقبل
        message: نص الرسالة
        timeout: مهلة الانتظار
    
    Returns:
        dict: نتيجة الإرسال
    """
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
        logger.info(f"✅ Message sent successfully to {to_number}")
        return {"success": True, "response": response.json()}
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout sending message to {to_number}")
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Network error sending message to {to_number}: {e}")
        return {"success": False, "error": f"Network error: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ Unexpected error sending message to {to_number}: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def send_admin_notification(service_name: str, service_number: str, user_id: str, details: str) -> dict:
    """
    إرسال إشعار للإدارة عن بيانات جديدة
    
    Args:
        service_name: اسم الخدمة
        service_number: رقم الخدمة
        user_id: معرف المستخدم
        details: تفاصيل البيانات
    
    Returns:
        dict: نتيجة الإرسال
    """
    notification_message = (
        f"📋 بيانات جديدة - {service_name}\n"
        f"رقم الخدمة: {service_number}\n"
        f"من العميل: {user_id}\n"
        f"{'='*30}\n"
        f"البيانات:\n{details}\n"
        f"{'='*30}\n"
        f"⏰ الوقت: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return send_message(ADMIN_PHONE, notification_message)