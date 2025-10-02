import os
import time
import logging
...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Qurain Simple Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
Tool Call
Function Name:
Write
Arguments:
file_path:
/home/user/app.py
content:
import os
import time
import logging
from flask import Flask, request, jsonify
from config import ADMIN_PHONE, SERVICE_MESSAGES
from send_utils import send_message

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

# قاموس لتتبع حالة كل مستخدم
user_states = {}

@app.route("/", methods=["GET"])
def index():
    return {
        "status": "active",
        "service": "🚀 Qurain Bot - Simple Version",
        "timestamp": time.time(),
        "description": "Bot works with WhatsAuto for main menu"
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

        logger.info(f"Message from {user_id}: {message}")

        phone = user_id.split("@")[0] if "@" in user_id else user_id

        # التحقق من حالة المستخدم الحالية
        current_state = user_states.get(user_id, "initial")

        # إذا كانت رسالة رقم خدمة جديد
        if message in SERVICE_MESSAGES:
            # تحديث حالة المستخدم
            user_states[user_id] = f"waiting_for_{message}"
            
            response = SERVICE_MESSAGES[message]["request_message"]
            send_result = send_message(phone, response)
            if send_result.get("success"):
                logger.info(f"✅ Service request sent to {phone} for service {message}")
            else:
                logger.error(f"❌ Failed to send service request: {send_result}")
        
        # إذا كان المستخدم في انتظار بيانات خدمة معينة
        elif current_state.startswith("waiting_for_"):
            service_number = current_state.replace("waiting_for_", "")
            service_name = SERVICE_MESSAGES.get(service_number, {}).get("name", "خدمة غير معروفة")
            
            # إرسال البيانات للإدارة
            admin_message = f"📋 بيانات جديدة - {service_name}\n"
            admin_message += f"من العميل: {user_id}\n"
            admin_message += f"رقم الخدمة: {service_number}\n"
            admin_message += f"البيانات:\n{message}"
            
            send_result_admin = send_message(ADMIN_PHONE, admin_message)
            
            # إرسال تأكيد للعميل
            confirmation_msg = f"✅ تم استلام بياناتك لخدمة {service_name} وتم تحويلها للإدارة.\nسيتم إضافتها في أقرب وقت. شكرًا لك!"
            send_result_user = send_message(phone, confirmation_msg)
            
            # إعادة تعيين حالة المستخدم
            user_states[user_id] = "initial"
            
            if send_result_user.get("success"):
                logger.info(f"✅ Service data confirmation sent to {phone} for service {service_number}")
            else:
                logger.error(f"❌ Failed to send confirmation: {send_result_user}")
        
        # إذا لم تكن رسالة خدمة ولا ينتظر بيانات خدمة
        else:
            # تجاهل الرسالة أو إرسال رسالة توضيحية (اختياري)
            logger.info(f"🔕 Message ignored from {phone}: {message} (not a service request and user not waiting for data)")
            
            # يمكنك إرسال رسالة توضيحية للمستخدم (اختياريه)
            help_message = (
                "مرحباً بك! 👋\n"
                "للحصول على خدماتنا، يرجى إرسال أحد الأرقام التالية:\n\n"
                "40 - للأسر المنتجة 🌟\n"
                "50 - للسائقين 🚗\n"
                "60 - للعمال 👷\n"
                "70 - للتأجير 📦\n"
                "100 - للاقتراحات والملاحظات 💡"
            )
            send_message(phone, help_message)

        return jsonify({"status": "processed"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Qurain Simple Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
Response
Created file /home/user/app.py (5429 characters)