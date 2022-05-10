from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler

import config

'''
HELP CALLBACK FUNCTION
'''
def show_help(update: Update, context: CallbackContext) -> None:
    
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = f"{config.BOT_COMMANDS}\n\nIf you experience technical issues, please contact S3 branch.",
        parse_mode = ParseMode.MARKDOWN
    )
    
    return

'''
HELP HANDLER
'''
handler = CommandHandler('help', show_help)
