
"""
إرسال الرسائل عبر WaSender API - نسخة مبسطة
"""
import json
import logging
import requests
from typing import Dict, Any, Optional

from config import WASENDER_API_KEY, WASENDER_BASE_URL

logger = logging.getLogger(__name__)

class WaSenderClient:
    """عميل إرسال رسائل واتساب مبسط"""
    
    def __init__(self):
        self.api_key = WASENDER_API_KEY
        self.base_url = WASENDER_BASE_URL
        self.send_endpoint = f"{self.base_url}/send-message"
    
    def send_message(self, to: str, text: str, timeout: int = 30) -> Dict[str, Any]:
        """
        إرسال رسالة واتساب
        """
        if not self.api_key:
            return {"success": False, "error": "API key not configured"}
        
        if not text or not text.strip():
            return {"success": False, "error": "Empty message"}
        
        # تنظيف النص
        text = text.strip()
        if len(text) > 4000:  # حد واتساب
            text = text[:3990] + "..."
        
        # إعداد الطلب
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": to,
            "text": text
        }
        
        try:
            logger.info(f"Sending message to {to}")
            logger.debug(f"Message: {text[:100]}...")
            
            response = requests.post(
                self.send_endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to {to}")
                try:
                    data = response.json()
                    return {"success": True, "data": data}
                except:
                    return {"success": True, "data": {"raw": response.text}}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ Failed to send message to {to}: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout}s"
            logger.error(f"❌ Send to {to} failed: {error_msg}")
            return {"success": False, "error": error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error to WaSender API"
            logger.error(f"❌ Send to {to} failed: {error_msg}")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ Send to {to} failed: {error_msg}")
            return {"success": False, "error": error_msg}

# إنشاء instance مشترك
wa_client = WaSenderClient()

def send_message(to: str, text: str, timeout: int = 30) -> Dict[str, Any]:
    """وظيفة الإرسال الرئيسية"""
    return wa_client.send_message(to, text, timeout)
