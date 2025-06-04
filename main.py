import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Если локально, загрузим .env
# В Railway и других хостингах этот блок просто проигнорируется, 
# поскольку .env там не существует и python-dotenv безопасно промолчит.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Читать из переменных окружения
TG_BOT_TOKEN       = os.getenv("TG_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL")

# Проверим, что токены заданы
if not TG_BOT_TOKEN or not OPENROUTER_API_KEY:
    raise RuntimeError("Не найдены TG_BOT_TOKEN или OPENROUTER_API_KEY в окружении.")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Настроим логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка команды /start
    """
    await update.message.reply_text(
        "Здарова работяги!"
        "Чтобы задать вопрос, используй:\n/askgpt <твой вопрос>"
    )

async def askgpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка команды /askgpt
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("❗️ Укажи текст после /askgpt.")
        return

    user_query = " ".join(context.args)

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Ты — полезный ассистент."},
            {"role": "user",   "content": user_query},
        ],
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        gpt_answer = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenRouter: {e}")
        await update.message.reply_text("❗️ Не удалось получить ответ от модели.")
        return

    text_to_send = f"@{user.username or user.first_name}, ответ:\n\n{gpt_answer}"
    await context.bot.send_message(chat_id=chat_id, text=text_to_send)

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка неизвестных команд
    """
    await update.message.reply_text("Извини, я не понимаю эту команду.")

def main():
    """
    Точка входа
    """
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("askgpt", askgpt_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_handler))

    print("Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
