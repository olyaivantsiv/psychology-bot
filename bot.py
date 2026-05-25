"""
Телеграм-бот для психологічної підтримки
Користувачі ставлять питання → психолог відповідає через бота
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────────
# НАЛАШТУВАННЯ — змінити тут!
# ─────────────────────────────────────────────
BOT_TOKEN = "ВАШ_ТОКЕН_ТУТ"          # токен від BotFather
PSYCHOLOGIST_ID = 123456789           # ваш Telegram ID (дивіться нижче як дізнатись)
# ─────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

WAITING_QUESTION = 1  # стан розмови


# ── /start ────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("💬 Поставити питання")]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Вітаємо!\n\n"
        "Це бот психологічної підтримки.\n"
        "Ви можете анонімно поставити питання — "
        "спеціаліст відповість якнайшвидше.\n\n"
        "Натисніть кнопку нижче, щоб почати 👇",
        reply_markup=markup
    )


# ── Кнопка «Поставити питання» ────────────────
async def ask_question_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Напишіть своє питання або опишіть ситуацію.\n\n"
        "Психолог отримає ваше повідомлення і відповість вам тут."
    )
    return WAITING_QUESTION


# ── Отримання питання від користувача ─────────
async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "без username"
    first_name = user.first_name or ""

    question_text = update.message.text

    # Надсилаємо психологу
    psychologist_msg = (
        f"🆕 Нове питання!\n\n"
        f"👤 Від: {first_name} ({username})\n"
        f"🆔 ID: {user_id}\n\n"
        f"❓ Питання:\n{question_text}\n\n"
        f"Щоб відповісти, використайте:\n"
        f"/reply {user_id} ВАША_ВІДПОВІДЬ"
    )

    try:
        await context.bot.send_message(
            chat_id=PSYCHOLOGIST_ID,
            text=psychologist_msg
        )
        # Підтверджуємо користувачу
        await update.message.reply_text(
            "✅ Ваше питання отримано!\n\n"
            "Психолог відповість вам найближчим часом. "
            "Зазвичай це займає до кількох годин.\n\n"
            "Якщо у вас є ще питання — просто напишіть."
        )
    except Exception as e:
        logging.error(f"Помилка надсилання психологу: {e}")
        await update.message.reply_text(
            "⚠️ Виникла технічна помилка. Спробуйте пізніше."
        )

    return ConversationHandler.END


# ── Команда /reply для психолога ──────────────
async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != PSYCHOLOGIST_ID:
        await update.message.reply_text("⛔ Ця команда лише для психолога.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Формат: /reply <ID_користувача> <текст відповіді>\n\n"
            "Приклад:\n/reply 123456789 Дякую за питання, ось моя відповідь..."
        )
        return

    try:
        target_id = int(context.args[0])
        answer_text = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ ID користувача має бути числом.")
        return

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"💬 Відповідь психолога:\n\n"
                f"{answer_text}\n\n"
                f"─────────────────\n"
                f"Якщо є ще питання — просто напишіть."
            )
        )
        await update.message.reply_text("✅ Відповідь надіслано!")
    except Exception as e:
        logging.error(f"Помилка надсилання відповіді: {e}")
        await update.message.reply_text(f"⚠️ Помилка: {e}")


# ── /myid — дізнатись свій ID ─────────────────
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Ваш Telegram ID: `{update.effective_user.id}`",
        parse_mode="Markdown"
    )


# ── /cancel ───────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Напишіть /start щоб почати знову.")
    return ConversationHandler.END


# ── Запуск бота ───────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler для прийому питань
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

    print("🤖 Бот запущено! Натисніть Ctrl+C для зупинки.")
    app.run_polling()


if __name__ == "__main__":
    main()
