from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
from utilities import shared
import config

'''
HELP CALLBACK FUNCTION
'''
def show_help(update: Update, context: CallbackContext) -> None:
    
    # Construct help message
    commands = shared.construct_commands_list()
        
    # Send help message
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = 
            f'{shared.construct_commands_list()}\n\n'
            f'For technical assistance, please [contact](tg://user?id={config.ADMIN_USERS[0]}) S3 branch.',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return

'''
HELP HANDLER
'''
handler = CommandHandler('help', show_help)