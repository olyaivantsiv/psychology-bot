import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PSYCHOLOGIST_ID = int(os.environ.get("PSYCHOLOGIST_ID"))

WAITING_QUESTION = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("💬 Поставити питання")]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Вітаємо!\n\n"
        "Це бот психологічної підтримки.\n"
        "Ви можете анонімно поставити питання — "
        "спеціаліст відповість якнайшвидше.\n\n"
        "Натисніть кнопку нижче 👇",
        reply_markup=markup
    )


async def ask_question_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Напишіть своє питання або опишіть ситуацію.\n\n"
        "Психолог отримає повідомлення і відповість вам тут."
    )
    return WAITING_QUESTION


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "без username"
    first_name = user.first_name or ""
    question_text = update.message.text

    psychologist_msg = (
        f"🆕 Нове питання!\n\n"
        f"👤 Від: {first_name} ({username})\n"
        f"🆔 ID: {user_id}\n\n"
        f"❓ Питання:\n{question_text}\n\n"
        f"Щоб відповісти:\n"
        f"/reply {user_id} ВАША ВІДПОВІДЬ"
    )

    try:
        await context.bot.send_message(
            chat_id=PSYCHOLOGIST_ID,
            text=psychologist_msg
        )
        await update.message.reply_text(
            "✅ Питання отримано!\n\n"
            "Психолог відповість вам найближчим часом.\n\n"
            "Якщо є ще питання — натисніть кнопку знову 👇"
        )
    except Exception as e:
        logging.error(f"Помилка: {e}")
        await update.message.reply_text("⚠️ Технічна помилка. Спробуйте пізніше.")

    return ConversationHandler.END


async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != PSYCHOLOGIST_ID:
        await update.message.reply_text("⛔ Ця команда лише для психолога.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Формат: /reply <ID> <текст>\n\n"
            "Приклад:\n/reply 123456789 Дякую за питання..."
        )
        return

    try:
        target_id = int(context.args[0])
        answer_text = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ ID має бути числом.")
        return

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"💬 Відповідь психолога:\n\n"
                f"{answer_text}\n\n"
                f"─────────────────\n"
                f"Є ще питання? Натисніть кнопку 👇"
            )
        )
        await update.message.reply_text("✅ Відповідь надіслано!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Помилка: {e}")


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Ваш Telegram ID: {update.effective_user.id}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Напишіть /start щоб почати знову.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💬 Поставити питання$"), ask_question_prompt)
        ],
        states={
            WAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", my_id))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(conv_handler)

    print("🤖 Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
