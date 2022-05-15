import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import keyboards
import config, database

logger = logging.getLogger(__name__)


NAME, COMPANY, RETRY_NAME, CONFIRMATION = range(4)

'''
REGISTRATION ENTRY POINTS
'''
def start(update: Update, context: CallbackContext) -> int:
    
    chat = update.effective_chat
    
    # Check if user is already registered
    if (user_data := database.retrieve_user(update.message.from_user.id)):
        context.user_data.update(user_data)
        chat.send_message(
            text = f'Hi, *{context.user_data["rank_and_name"]} ({context.user_data["company"]})*.\n\n{config.BOT_COMMANDS}',
            parse_mode = ParseMode.MARKDOWN
        )
        return ConversationHandler.END # -1
    
    # Save telegram username
    context.user_data['username'] = update.message.from_user.username
    
    # Introduce bot and ask for user's rank and name
    chat.send_message(
        'Hi! I can help you book 5 SIR facilities, manage your existing bookings, and check facility availability.\n\n'
        "You'll need to create a user profile first. Please send me your rank and name."
    )
    
    return NAME


def profile(update: Update, context: CallbackContext) -> int:
    
    # Save telegram username
    context.user_data['username'] = update.message.from_user.username
    
    # Ask for user's rank and name
    update.effective_chat.send_message(
        'Ok, now updating your user profile. Send /cancel to stop.\n\n'
        'Please send me your rank and name.'
    )
    
    return NAME


"""
REGISTRATION CALLBACK FUNCTIONS
"""
def save_name(update: Update, context: CallbackContext) -> int:
    
    # Save user's rank and name
    context.user_data['rank_and_name'] = update.message.text.upper()
    
    # Ask for user's company
    update.effective_chat.send_message(
        text = 'Ok. Please select your company:',
        reply_markup = keyboards.companies,
    )
    
    return COMPANY


def save_coy(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    # Save user's company
    context.user_data['company'] = query.data
    
    # Check if user's rank and name + company are unique
    if database.retrieve_user_by_rank_name_company(
        context.user_data['rank_and_name'],
        context.user_data['company']
    ):
        update.effective_chat.send_message(
            text = 
                f"Sorry, there's already a user registered as *{context.user_data['rank_and_name']}* in *{context.user_data['company']}*. "
                'Please send me your rank and name again. Consider using your full name, or another variation of your name.',
            parse_mode = ParseMode.MARKDOWN
        )
        # CallbackQueries need to be answered, even if no user notification is needed
        query.answer()
        return RETRY_NAME
        
    # Ask user to confirm user profile
    update.effective_chat.send_message(
        text = f"Ok, I'll register you as *{context.user_data['rank_and_name']} ({context.user_data['company']})*. Is this correct?",
        reply_markup = keyboards.confirm_or_cancel,
        parse_mode = ParseMode.MARKDOWN
    )
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    return CONFIRMATION


def retry_name(update: Update, context: CallbackContext) -> int:
    
    # Save new rank and name
    context.user_data['rank_and_name'] = update.message.text
    
    # Check if user's rank and name + company are unique
    if database.retrieve_user_by_rank_name_company(
        context.user_data['rank_and_name'],
        context.user_data['company']
    ):
        update.effective_chat.send_message(
            text = 
                f"Sorry, there's also a user registered as *{context.user_data['rank_and_name']}* in *{context.user_data['company']}*. "
                'Please send me your rank and name again. Consider using another variation of your name.',
            parse_mode = ParseMode.MARKDOWN
        )
        # CallbackQueries need to be answered, even if no user notification is needed
        query.answer()
        return RETRY_NAME
    
    # Ask user to confirm user profile
    update.effective_chat.send_message(
        text = f"Ok, I'll register you as *{context.user_data['rank_and_name']} ({context.user_data['company']})*. Is this correct?",
        reply_markup = keyboards.confirm_or_cancel,
        parse_mode = ParseMode.MARKDOWN
    )
    
    return CONFIRMATION


def confirm(update: Update, context: CallbackContext) -> int: 
    
    query = update.callback_query
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Add new user profile to database
    database.add_user(query.from_user.id, context.user_data)
        
    # Confirm registration and introduce user to bot commands
    query.edit_message_text(
        text = 
            f'Profile created! Hi *{context.user_data["rank_and_name"]} ({context.user_data["company"]})*.\n\n{config.BOT_COMMANDS}',
        parse_mode = ParseMode.MARKDOWN
    )
    
    # Log new user registration
    logger.info(
        'User Registered - %s - %s - %s COMPANY', 
        query.from_user.id,
        context.user_data['rank_and_name'], 
        context.user_data['company']
    )
    
    return ConversationHandler.END # -1


def cancel(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Restart registration process
    query.edit_message_text(
        'User registration cancelled.\n\n'
        "You'll need to create a user profile to book facilities through me. Please send me your rank and name."
    )
    
    return NAME


'''
REGISTRATION HANDLER
'''
handler = ConversationHandler(
    entry_points = [
        CommandHandler('start', start),
        CommandHandler('profile', profile)
    ],
    states = {
        NAME: [MessageHandler(Filters.text, save_name)],
        COMPANY: [CallbackQueryHandler(save_coy)],
        RETRY_NAME: [MessageHandler(Filters.text, retry_name)],
        CONFIRMATION: [
            CallbackQueryHandler(callback = confirm, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
