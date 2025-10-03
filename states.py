from enum import Enum
from typing import Dict, Optional
import time

class BotState(Enum):
    """حالات البوت المختلفة"""
    INITIAL = "initial"
    WAITING_FOR_40 = "waiting_for_40"  # انتظار بيانات الأسر المنتجة
    WAITING_FOR_50 = "waiting_for_50"  # انتظار بيانات السائقين
    WAITING_FOR_60 = "waiting_for_60"  # انتظار بيانات العمال
    WAITING_FOR_100 = "waiting_for_100"  # انتظار الاقتراحات والملاحظات

class UserStateManager:
    """مدير حالات المستخدمين"""

    def __init__(self):
        self.user_states: Dict[str, Dict] = {}

    def set_user_state(self, user_id: str, state: BotState, service_number: str = None):
        """تعيين حالة المستخدم"""
        self.user_states[user_id] = {
            "state": state.value,
            "service_number": service_number,
            "timestamp": time.time()
        }

    def get_user_state(self, user_id: str) -> str:
        """الحصول على حالة المستخدم"""
        user_data = self.user_states.get(user_id)
        if not user_data:
            return BotState.INITIAL.value
        return user_data["state"]

    def get_user_service_number(self, user_id: str) -> Optional[str]:
        """الحصول على رقم الخدمة للمستخدم"""
        user_data = self.user_states.get(user_id)
        return user_data.get("service_number") if user_data else None

    def reset_user_state(self, user_id: str):
        """إعادة تعيين حالة المستخدم"""
        if user_id in self.user_states:
            del self.user_states[user_id]

    def cleanup_expired_states(self):
        """تنظيف الحالات المنتهية الصلاحية (اختياري إذا أردت حذف الحالات القديمة يدوياً)"""
        pass  # لم يعد هناك حاجة لتنظيف بناءً على الوقت

    def get_active_users_count(self) -> int:
        """الحصول على عدد المستخدمين النشطين"""
        return len(self.user_states)