from telegram.ext import Updater, CommandHandler

def start(update, context):
    update.message.reply_text("سلام! به وان پیس رول بات خوش اومدید")

updater = Updater("TOKEN", use_context=True)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.start_polling()
updater.idle()
