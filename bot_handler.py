
"""
معالج البوت الرئيسي - يتعامل مع الأرقام المحددة فقط
"""
import logging
from typing import Optional
from datetime import datetime

from config import SUPPORTED_NUMBERS, MESSAGES, ADMIN_PHONE
from send_utils import send_message

logger = logging.getLogger(__name__)

class BotHandler:
    """معالج البوت المبسط"""
    
    def __init__(self):
        # تخزين حالات المستخدمين مؤقتاً في الذاكرة
        self.user_states = {}
        self.user_data = {}
    
    def process_message(self, user_id: str, message: str) -> Optional[str]:
        """
        معالجة الرسالة الواردة
        """
        try:
            message = message.strip()
            
            # التحقق من الأرقام المدعومة
            if message in SUPPORTED_NUMBERS:
                return self._start_registration(user_id, message)
            
            # معالجة خطوات التسجيل
            if user_id in self.user_states:
                return self._handle_registration_step(user_id, message)
            
            # رقم غير مدعوم
            logger.info(f"Unsupported number {message} from {user_id}")
            return None  # لا نرد على الأرقام غير المدعومة
            
        except Exception as e:
            logger.error(f"Error processing message from {user_id}: {e}")
            return MESSAGES["error"]
    
    def _start_registration(self, user_id: str, number: str) -> str:
        """بدء عملية التسجيل"""
        try:
            service = SUPPORTED_NUMBERS[number]
            
            # حفظ حالة المستخدم
            self.user_states[user_id] = {
                "service_number": number,
                "service_name": service["name"],
                "current_step": 0,
                "total_steps": len(service["steps"]),
                "fields": service["fields"]
            }
            
            # إنشاء مخزن البيانات
            self.user_data[user_id] = {}
            
            logger.info(f"Started {service['name']} registration for {user_id}")
            
            # إرجاع أول سؤال
            return service["steps"][0]
            
        except Exception as e:
            logger.error(f"Error starting registration: {e}")
            return MESSAGES["error"]
    
    def _handle_registration_step(self, user_id: str, message: str) -> str:
        """معالجة خطوة في عملية التسجيل"""
        try:
            state = self.user_states[user_id]
            service_number = state["service_number"]
            current_step = state["current_step"]
            service = SUPPORTED_NUMBERS[service_number]
            
            # حفظ الإجابة الحالية
            field_name = state["fields"][current_step]
            self.user_data[user_id][field_name] = message
            
            # الانتقال للخطوة التالية
            next_step = current_step + 1
            
            # التحقق من انتهاء الخطوات
            if next_step >= state["total_steps"]:
                # إنهاء التسجيل وإرسال البيانات للإدمن
                return self._complete_registration(user_id)
            else:
                # الانتقال للخطوة التالية
                self.user_states[user_id]["current_step"] = next_step
                return service["steps"][next_step]
                
        except Exception as e:
            logger.error(f"Error handling registration step: {e}")
            return MESSAGES["error"]
    
    def _complete_registration(self, user_id: str) -> str:
        """إكمال التسجيل وإرسال البيانات للإدمن"""
        try:
            state = self.user_states[user_id]
            data = self.user_data[user_id]
            service_name = state["service_name"]
            
            # تحضير الرسالة للإدمن
            admin_message = self._prepare_admin_message(user_id, service_name, data)
            
            # إرسال للإدمن
            send_result = send_message(ADMIN_PHONE, admin_message)
            
            if send_result.get("success"):
                logger.info(f"✅ Data sent to admin for {service_name} from {user_id}")
                response_message = MESSAGES["suggestion_sent"] if state["service_number"] == "100" else MESSAGES["data_sent"]
            else:
                logger.error(f"❌ Failed to send data to admin: {send_result}")
                response_message = MESSAGES["error"]
            
            # تنظيف حالة المستخدم
            self._clear_user_state(user_id)
            
            return response_message
            
        except Exception as e:
            logger.error(f"Error completing registration: {e}")
            return MESSAGES["error"]
    
    def _prepare_admin_message(self, user_id: str, service_name: str, data: dict) -> str:
        """تحضير رسالة الإدمن"""
        try:
            # استخراج رقم الهاتف من user_id
            phone = user_id.split("@")[0] if "@" in user_id else user_id
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📋 *{service_name} جديد*\n\n"
            message += f"👤 *رقم المرسل:* {phone}\n"
            message += f"⏰ *الوقت:* {timestamp}\n\n"
            message += "*📝 البيانات:*\n"
            
            for field, value in data.items():
                if value.strip():  # تجاهل الحقول الفارغة
                    message += f"• *{field}:* {value}\n"
            
            message += "\n" + "="*30
            
            return message
            
        except Exception as e:
            logger.error(f"Error preparing admin message: {e}")
            return f"خطأ في تحضير الرسالة من {user_id}"
    
    def _clear_user_state(self, user_id: str):
        """مسح حالة المستخدم"""
        try:
            self.user_states.pop(user_id, None)
            self.user_data.pop(user_id, None)
            logger.debug(f"Cleared state for {user_id}")
        except Exception as e:
            logger.error(f"Error clearing user state: {e}")
    
    def get_active_users_count(self) -> int:
        """عدد المستخدمين النشطين حالياً"""
        return len(self.user_states)
    
    def clear_all_states(self) -> int:
        """مسح جميع الحالات - للصيانة"""
        count = len(self.user_states)
        self.user_states.clear()
        self.user_data.clear()
        logger.info(f"Cleared all states: {count} users")
        return count
