import os
import time
import logging
from flask import Flask, request, jsonify
from config import ADMIN_PHONE, SERVICE_MESSAGES
from send_utils import send_message

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

        if not user_id or not message:
            return jsonify({"error": "Invalid message data"}), 400

        logger.info(f"Message from {user_id}: {message}")

        # الرد حسب رقم الخدمة
        response = None
        if message in SERVICE_MESSAGES:
            response = SERVICE_MESSAGES[message]["request_message"]
        else:
            # أي رقم غير مدعوم يرد عليه WhatsAuto فقط ولا يرد البوت
            return jsonify({"status": "ignored"}), 200

        # إذا أرسل العميل التفاصيل بعد رقم الخدمة (مثلاً بعد ٦٠ يرسل كل البيانات دفعة واحدة)
        # نحدد ذلك بأن الرسالة ليست رقم خدمة، بل نص طويل (يتم تحويله للإدارة)
        # نتحقق هل الرسالة السابقة كانت رقم من الخدمة (يمكنك تحسين ذلك لاحقًا بحفظ آخر حالة للمستخدم في الذاكرة إذا أردت).
        # هنا سنفترض أن المستخدم يرسل الرقم ثم مباشرة التفاصيل في رسالة أخرى.

        # إذا كانت الرسالة نص طويل وليست رقم خدمة، نرسلها للإدارة
        if response is None and len(message) > 1:
            # أرسل للإدارة
            send_result = send_message(ADMIN_PHONE, f"رسالة جديدة من العميل ({user_id}):\n{message}")
            response = "✅ تم تحويل رسالتك للإدارة وسيتم إضافتها في أقرب وقت. شكرًا لك!"

        if response:
            phone = user_id.split("@")[0] if "@" in user_id else user_id
            send_result = send_message(phone, response)
            if send_result.get("success"):
                logger.info(f"✅ Response sent to {phone}")
            else:
                logger.error(f"❌ Failed to send response: {send_result}")

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