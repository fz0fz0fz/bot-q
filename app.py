import os
import time
import logging
from flask import Flask, request, jsonify
from config import ADMIN_PHONE, SERVICE_MESSAGES
from send_utils import send_message, send_admin_notification
from states import BotState, UserStateManager

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# إنشاء مدير الحالات
state_manager = UserStateManager()

@app.route("/", methods=["GET"])
def index():
    return {
        "status": "active",
        "service": "🚀 Qurain Bot - Enhanced Version",
        "timestamp": time.time(),
        "active_users": state_manager.get_active_users_count(),
        "description": "Bot works with WhatsAuto for main menu with state management"
    }

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data"}), 400

        if data.get("event") == "webhook.test":
            logger.info("📩 Webhook test received")
            return jsonify({"status": "test_ok"}), 200

        payload = data.get("data") or data
        messages = payload.get("messages")
        if not messages:
            return jsonify({"error": "No messages"}), 400

        key = messages.get("key", {})
        user_id = key.get("remoteJid")
        from_me = key.get("fromMe", False)

        if from_me:
            return jsonify({"status": "ignored"}), 200

        message_obj = messages.get("message", {})
        message = message_obj.get("conversation", "").strip()

        # تحويل الأرقام العربية إلى إنجليزية
        def convert_arabic_to_english_numbers(text):
            arabic_nums = "٠١٢٣٤٥٦٧٨٩"
            english_nums = "0123456789"
            trans = str.maketrans(arabic_nums, english_nums)
            return text.translate(trans)

        message = convert_arabic_to_english_numbers(message)

        if not user_id or not message:
            return jsonify({"error": "Invalid message data"}), 400

        logger.info(f"📨 Message from {user_id}: {message}")

        phone = user_id.split("@")[0] if "@" in user_id else user_id

        # الحصول على حالة المستخدم الحالية
        current_state = state_manager.get_user_state(user_id)

        # تنظيف الحالات المنتهية الصلاحية
        state_manager.cleanup_expired_states()

        # التحقق من الأرقام التي يجب تجاهلها (1-15 لواتس أوتو)
        if is_whatsauto_number(message):
            logger.info(f"🔕 Ignoring WhatsAuto number: {message} from {phone}")
            return jsonify({"status": "ignored_whatsauto"}), 200

        # منطق الحالات المعدل
        if current_state != BotState.INITIAL.value:
            # إذا أرسل أي رقم أثناء انتظار البيانات، نخرج من الحالة
            if message.isdigit():
                state_manager.reset_user_state(user_id)
                if message in SERVICE_MESSAGES:
                    # رقم خدمة: نبدأ معه مباشرة
                    handle_service_request(user_id, phone, message)
                else:
                    # رقم غير مدعوم: تجاهله أو أرسل رسالة مساعدة
                    handle_unknown_message(phone, message)
            else:
                # إذا لم يكن رقم، اعتبره بيانات خدمة
                handle_service_data(user_id, phone, message, current_state)
        else:
            # في حالة عادية (بدون انتظار بيانات خدمة)
            if message in SERVICE_MESSAGES:
                handle_service_request(user_id, phone, message)
            else:
                handle_unknown_message(phone, message)

        return jsonify({"status": "processed"}), 200

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def is_whatsauto_number(message: str) -> bool:
    """التحقق من أن الرسالة هي رقم من قائمة واتس أوتو (1-15)"""
    try:
        number = int(message)
        return 1 <= number <= 15
    except ValueError:
        return False

def handle_service_request(user_id: str, phone: str, service_number: str):
    """معالجة طلب خدمة جديد"""
    try:
        # تحديث حالة المستخدم
        state_manager.set_user_state(
            user_id, 
            BotState(f"waiting_for_{service_number}"), 
            service_number
        )

        # إرسال رسالة طلب البيانات
        response = SERVICE_MESSAGES[service_number]["request_message"]
        send_result = send_message(phone, response)

        if send_result.get("success"):
            logger.info(f"✅ Service request sent to {phone} for service {service_number}")
        else:
            logger.error(f"❌ Failed to send service request: {send_result}")
            # إعادة تعيين الحالة في حالة فشل الإرسال
            state_manager.reset_user_state(user_id)

    except Exception as e:
        logger.error(f"❌ Error handling service request: {e}")
        state_manager.reset_user_state(user_id)

def handle_service_data(user_id: str, phone: str, message: str, current_state: str):
    """معالجة بيانات الخدمة المرسلة من المستخدم"""
    try:
        service_number = state_manager.get_user_service_number(user_id)
        if not service_number or service_number not in SERVICE_MESSAGES:
            logger.error(f"❌ Invalid service number for user {user_id}")
            state_manager.reset_user_state(user_id)
            return

        service_info = SERVICE_MESSAGES[service_number]
        service_name = service_info["name"]

        # إرسال البيانات للإدارة
        send_result_admin = send_admin_notification(
            service_name, service_number, user_id, message
        )

        # إرسال تأكيد للعميل
        confirmation_msg = (
            f"✅ تم استلام بياناتك بنجاح!\n\n"
            f"🔹 الخدمة: {service_name}\n"
            f"🔹 تم تحويل البيانات للإدارة\n"
            f"🔹 سيتم إضافة البيانات في أقرب وقت\n\n"
            f"شكراً لك ! 🌹"
        )

        send_result_user = send_message(phone, confirmation_msg)

        # إعادة تعيين حالة المستخدم بعد إرسال البيانات بنجاح
        state_manager.reset_user_state(user_id)

        if send_result_user.get("success"):
            logger.info(f"✅ Service data processed successfully for {phone} - service {service_number}")
            logger.info(f"🔄 User state reset for {user_id} after successful data submission")
        else:
            logger.error(f"❌ Failed to send confirmation: {send_result_user}")

    except Exception as e:
        logger.error(f"❌ Error handling service data: {e}")
        state_manager.reset_user_state(user_id)

def handle_unknown_message(phone: str, message: str):
    """معالجة الرسائل غير المعروفة"""
    try:
        logger.info(f"🔕 Unknown message from {phone}: {message}")

        # رسالة المساعدة
        help_message = (
            "مرحباً بك في خدمات القرين! 👋\n\n"
            "للحصول على خدماتنا، يرجى إرسال أحد الأرقام التالية:\n\n"
            "🌟 40 - للأسر المنتجة\n"
            "🚗 50 - لخدمات السائقين\n"
            "👷 60 - لخدمات العمال\n"
            "💡 100 - للاقتراحات والملاحظات\n\n"
            "📱 يرجى إرسال الرقم فقط للبدء"
        )

        send_result = send_message(phone, help_message)

        if send_result.get("success"):
            logger.info(f"✅ Help message sent to {phone}")
        else:
            logger.error(f"❌ Failed to send help message: {send_result}")

    except Exception as e:
        logger.error(f"❌ Error handling unknown message: {e}")

@app.route("/stats", methods=["GET"])
def stats():
    """إحصائيات البوت"""
    return jsonify({
        "active_users": state_manager.get_active_users_count(),
        "timestamp": time.time(),
        "status": "active"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Qurain Enhanced Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)