from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
import config

'''
HELP CALLBACK FUNCTION
'''
def show_help(update: Update, context: CallbackContext) -> None:
    
    # Construct help message
    message = "Interact with me using these commands:\n\n*Manage Facility Bookings*\n"
    for command in config.COMMANDS_BOOKING:
        message += f"/{command[0]} - {command[1]}\n"
    message += "\n*Bot Settings*\n"
    for command in config.COMMANDS_SETTING:
        message += f"/{command[0]} - {command[1]}\n"
    message += f"\nFor technical assistance, please [contact](tg://user?id={config.ADMIN_UID_LIST[0]}) S3 branch."
    
    # Send help message
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = message,
        parse_mode = ParseMode.MARKDOWN
    )
    
    return

'''
HELP HANDLER
'''
handler = CommandHandler('help', show_help)