import logging
from functools import wraps
from telegram import Bot, ChatAction, ParseMode
from telegram.ext import ConversationHandler
from utilities import calendar, database
import config

logger = logging.getLogger(__name__)

'''
DECORATORS
'''
# Decorate callback function to send typing action while processing
def send_typing_action(func):

    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        kwargs['update'] = update
        kwargs['context'] = context
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
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
            update.effective_chat.send_message("⚠ Sorry, I can't find your user profile. Send /start to create a new profile.")
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


def construct_commands_list() -> str:
    
    commands = "Interact with me using these commands:\n\n*Manage Facility Bookings*"
    for command in config.COMMANDS_BOOKING:
        commands += f"\n/{command[0]} - {command[1]}"
    commands += "\n\n*Bot Settings*"
    for command in config.COMMANDS_SETTING:
        commands += f"\n/{command[0]} - {command[1]}"
    
    return commands


'''
ADDITIONAL API REQUESTS
'''
def update_facilities_channel(text: str) -> None:
    
    if config.CHANNEL_USERNAME:
        try:
            Bot(config.BOT_TOKEN).send_message(
                chat_id = f'@{config.CHANNEL_USERNAME}',
                text = text,
                parse_mode = ParseMode.HTML,
                disable_web_page_preview = True,
                disable_notification = config.CHANNEL_MUTED
            )
        except Exception as error:
            logger.exception('Channel Update Failure - %s', error)
    return