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

        # هل هي رسالة رقم خدمة؟
        if message in SERVICE_MESSAGES:
            response = SERVICE_MESSAGES[message]["request_message"]
            send_result = send_message(phone, response)
            if send_result.get("success"):
                logger.info(f"✅ Response sent to {phone}")
            else:
                logger.error(f"❌ Failed to send response: {send_result}")
        else:
            # رسالة تفاصيل: أرسلها للإدارة وارسل للعميل تأكيد
            send_result_admin = send_message(ADMIN_PHONE, f"رسالة جديدة من العميل ({user_id}):\n{message}")
            confirmation_msg = "✅ تم تحويل رسالتك للإدارة وسيتم إضافتها في أقرب وقت. شكرًا لك!"
            send_result_user = send_message(phone, confirmation_msg)
            if send_result_user.get("success"):
                logger.info(f"✅ Confirmation sent to {phone}")
            else:
                logger.error(f"❌ Failed to send confirmation: {send_result_user}")

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