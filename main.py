import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# إعداد السجل
logging.basicConfig(level=logging.INFO)

# 1️⃣ تحميل قاعدة البيانات المحلية
def load_knowledge_base():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("⚠️ ملف data.json غير موجود. سيتم المتابعة بدون قاعدة معرفة.")
        return {}

knowledge_base = load_knowledge_base()

# 2️⃣ دالة التواصل مع Gemini
def gemini_ai(prompt: str) -> str:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # قم بتخزين المفتاح ضمن متغيرات البيئة
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate?key={GEMINI_API_KEY}"
    payload = {
        "prompt": {"text": prompt}
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            candidates = response.json().get("candidates", [])
            if candidates:
                return candidates[0].get("output", "لم يتم العثور على إجابة.")
            else:
                return "لم يتم العثور على إجابة."
        else:
            return f"⚠️ خطأ أثناء التواصل مع Gemini: {response.text}"
    except Exception as e:
        return f"⚠️ استثناء أثناء التواصل مع Gemini: {e}"

# 3️⃣ التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # 1️⃣ محاولة العثور على الإجابة من قاعدة البيانات
    for question, answer in knowledge_base.items():
        if question.lower() in user_text.lower():
            await update.message.reply_text(f"🤖 {answer}")
            return

    # 2️⃣ استخدام نموذج Gemini
    await update.message.reply_text("🧠 جاري التفكير...")
    reply = gemini_ai(user_text)
    await update.message.reply_text(reply)

# 4️⃣ تشغيل البوت
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN or not os.getenv("GEMINI_API_KEY"):
        print("❌ قم بتعيين متغيرات البيئة BOT_TOKEN و GEMINI_API_KEY قبل التشغيل.")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ بوت تيليجرام مع Gemini يعمل بنجاح.")
    app.run_polling()