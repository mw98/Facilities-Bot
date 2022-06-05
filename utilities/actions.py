from functools import wraps
from telegram import ChatAction, ParseMode
from telegram.ext import ConversationHandler
from utilities import calendar
import database

'''
DECORATORS
'''
# Decorate callback function to send typing action while processing
def send_typing_action(func):

    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        kwargs['update'] = update
        kwargs['context'] = context
        return func(**kwargs)

    return wrapper


#Decorate callback function to load user profile before proceeding
#Prompts user to create profile if it does not exist
def load_user_profile(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        
        update = kwargs['update']
        context = kwargs['context']
        
        if (user_data := database.retrieve_user(update.message.from_user.id)):
            context.user_data.update(user_data)
        else:
            update.effective_chat.send_message("⚠ Sorry, I can't find your user profile. Send /profile to create a new profile.")
            logger.debug('User Not Found - %s - %s', update.message.from_user.id, update.message.from_user.username)
            return ConversationHandler.END # -1
        
        return func(update, context)
    
    return wrapper


'''
SHARED CALLBACK FUNCTIONS
'''             
def send_date_error(update, context, logger) -> None:
            
    # Ask user to send date again
    update.effective_chat.send_message(
        text = "⚠ Sorry, that is not a valid date. Please send me an upcoming date in the `DDMMYY` format.",
        parse_mode = ParseMode.MARKDOWN
    )
    
    # Log error
    logger.debug('Invalid Booking Date - %s - %s - "%s"', 
        update.message.from_user.id,
        context.user_data['rank_and_name'],
        update.message.text
    )
    
    return


def send_time_range_error(update, context, logger) -> None:
            
    # Ask user to send time range again
    update.effective_chat.send_message(
        text = '⚠ Sorry, that is not a valid time range. Please send me an upcoming time range in the format `HHmm-HHmm`.',
        parse_mode = ParseMode.MARKDOWN
    )

    # Log error
    logger.debug('Invalid Booking Time Range - %s - %s - "%s"',
        update.message.from_user.id,
        context.user_data['rank_and_name'],
        update.message.text
    )
    
    return


def silent_cancel(update, context) -> int:
    return ConversationHandler.END
