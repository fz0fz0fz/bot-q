
"""
بوت واتساب القرين المبسط - يعمل مع WhatsAuto
فقط معالجة أرقام محددة وإرسال للإدمن
"""
import os
import time
import logging
from flask import Flask, request, jsonify

from config import ADMIN_PHONE, WASENDER_API_KEY
from bot_handler import BotHandler
from send_utils import send_message

# إعداد نظام السجلات
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
bot_handler = BotHandler()

@app.route("/", methods=["GET"])
def index():
    """صفحة الحالة الرئيسية"""
    return {
        "status": "active",
        "service": "🚀 Qurain Bot - Simple Version",
        "timestamp": time.time(),
        "description": "Bot works with WhatsAuto for main menu"
    }

@app.route("/webhook", methods=["POST"])
def webhook():
    """معالج الرسائل الرئيسي"""
    try:
        # استخراج البيانات
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data"}), 400

        # اختبار الويب هوك
        if data.get("event") == "webhook.test":
            logger.info("📩 Webhook test received")
            return jsonify({"status": "test_ok"}), 200

        # استخراج بيانات الرسالة
        payload = data.get("data") or data
        messages = payload.get("messages")
        
        if not messages:
            return jsonify({"error": "No messages"}), 400

        key = messages.get("key", {})
        user_id = key.get("remoteJid")
        from_me = key.get("fromMe", False)

        # تجاهل الرسائل من البوت نفسه
        if from_me:
            return jsonify({"status": "ignored"}), 200

        message_obj = messages.get("message", {})
        message = message_obj.get("conversation", "").strip()

        if not user_id or not message:
            return jsonify({"error": "Invalid message data"}), 400

        logger.info(f"Message from {user_id}: {message}")

        # معالجة الرسالة
        response = bot_handler.process_message(user_id, message)

        # إرسال الرد إذا كان موجوداً
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
