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
        self.state_timeout = 1800  # 30 دقيقة timeout

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

        # التحقق من انتهاء صلاحية الحالة
        if time.time() - user_data["timestamp"] > self.state_timeout:
            self.reset_user_state(user_id)
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
        """تنظيف الحالات المنتهية الصلاحية"""
        current_time = time.time()
        expired_users = []

        for user_id, user_data in self.user_states.items():
            if current_time - user_data["timestamp"] > self.state_timeout:
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.user_states[user_id]

    def get_active_users_count(self) -> int:
        """الحصول على عدد المستخدمين النشطين"""
        self.cleanup_expired_states()
        return len(self.user_states)