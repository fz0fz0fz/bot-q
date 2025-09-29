"""
import os
import time
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
import logging

from config import Config
from bot_manager import BotManager
from rate_limiter import RateLimiter
from utils import validate_webhook_data, extract_message_data
from send_utils import send_message

# إعداد نظام السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_manager = BotManager()
rate_limiter = RateLimiter()

# Cache للرسائل المرسلة مؤخراً لمنع التكرار
recent_messages = {}

@app.route("/", methods=["GET"])
def index():
    """صفحة الحالة الرئيسية"""
    return {
        "status": "active",
        "service": "🚀 Qurain Delivery Bot v2.0",
        "timestamp": time.time(),
        "features": [
            "معالجة أخطاء محسنة",
            "حماية من التكرار",
            "إدارة منظمة للخدمات",
            "قاعدة بيانات محسنة"
        ]
    }

@app.route("/health", methods=["GET"])
def health_check():
    """فحص حالة البوت"""
    try:
        # فحص قاعدة البيانات
        db_status = bot_manager.check_database_health()
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """معالج الرسائل الرئيسي مع حماية شاملة"""
    try:
        # استخراج البيانات مع التحقق
        data = request.get_json(force=True)
        if not data:
            logger.warning("Empty webhook data received")
            return jsonify({"error": "No data"}), 400

        # التحقق من صحة البيانات
        validation_result = validate_webhook_data(data)
        if not validation_result["valid"]:
            logger.warning(f"Invalid webhook data: {validation_result['error']}")
            return jsonify({"error": validation_result["error"]}), 400

        # اختبار الويب هوك
        if data.get("event") == "webhook.test":
            logger.info("📩 Webhook test received")
            return jsonify({"status": "test_ok"}), 200

        # استخراج بيانات الرسالة
        message_data = extract_message_data(data)
        if not message_data:
            logger.warning("Could not extract message data")
            return jsonify({"error": "Invalid message format"}), 400

        user_id = message_data["user_id"]
        message = message_data["message"]
        from_me = message_data["from_me"]

        # تجاهل الرسائل من البوت نفسه
        if from_me:
            logger.debug("🔄 Message from bot ignored")
            return jsonify({"status": "ignored"}), 200

        # فحص معدل الإرسال لمنع التكرار
        if not rate_limiter.is_allowed(user_id):
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return jsonify({"status": "rate_limited"}), 429

        # فحص الرسائل المكررة
        message_hash = hash(f"{user_id}:{message}:{int(time.time()/10)}")
        if message_hash in recent_messages:
            logger.debug(f"Duplicate message ignored for user: {user_id}")
            return jsonify({"status": "duplicate_ignored"}), 200
        
        recent_messages[message_hash] = time.time()
        # تنظيف الرسائل القديمة (أكثر من 5 دقائق)
        cleanup_old_messages()

        # معالجة الرسالة
        response = bot_manager.process_message(
            user_id=user_id,
            message=message,
            additional_data=message_data
        )

        # إرسال الرد إذا كان موجوداً
        if response:
            phone = user_id.split("@")[0] if "@" in user_id else user_id
            send_result = send_message(phone, response)
            
            if send_result.get("success"):
                logger.info(f"✅ Message sent successfully to {phone}")
            else:
                logger.error(f"❌ Failed to send message to {phone}: {send_result}")

        return jsonify({"status": "processed"}), 200

    except BadRequest as e:
        logger.error(f"Bad request: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

def cleanup_old_messages():
    """تنظيف الرسائل المخزنة مؤقتاً"""
    current_time = time.time()
    old_keys = [
        key for key, timestamp in recent_messages.items()
        if current_time - timestamp > 300  # 5 دقائق
    ]
    for key in old_keys:
        recent_messages.pop(key, None)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # إنشاء الجداول عند بدء التشغيل
    try:
        bot_manager.initialize_database()
        logger.info("🚀 Bot started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # تشغيل التطبيق
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
