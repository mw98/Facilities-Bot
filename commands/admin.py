import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import filters, actions, keyboards, calendar
import config, database

logger = logging.getLogger(__name__)


BOOKING_DETAILS, USER_DETAILS, CONFIRMATION = range(3)

'''
ADMIN ENTRY POINT
'''
@actions.send_typing_action
def admin(update: Update, context: CallbackContext) -> int:
    
    if update.message.from_user.id in config.ADMIN_UID_LIST:
        
        update.effective_chat.send_message(
            text = 
                '⚠ *Running Admin Mode*\nFacilitiesBot will not check for conflicts before making bookings. Use /cancel to exit.\n\n'
                'Send a list of booking details in this order and format:\n\n'
                '`LT 1/LT 2/CONF ROOM/RTS/STINGRAY SQ`\n'
                '`DDMMYY` (e.g. 150722)\n'
                '`HHmm-HHmm` (e.g. 0900-1300)\n'
                '`Description`',
            parse_mode = ParseMode.MARKDOWN
        )
        
        return BOOKING_DETAILS
    
    else:
        return ConversationHandler.END


'''
SAVE BOOKING & USER DETAILS
'''
@actions.send_typing_action
def save_booking_details(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['admin_booking_details'] = {
        'facility': context.facility[0],
        'date': context.date[0],
        'start_time': context.time_range[0],
        'end_time': context.time_range[1],
        'description': context.description[0]
    }
    
    update.effective_chat.send_message(
        text = 
            'Send a list of user details in this order and format:\n\n'
            '`RNK NAME` (e.g. PTE FacilitiesBot)\n'
            '`ALPHA/BRAVO/CHARLIE/SP/MSC/HQ`',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return USER_DETAILS

@actions.send_typing_action
def save_user_details(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['admin_user_details'] = {
        'rank_and_name': context.rank_and_name[0],
        'company': context.company[0]
    }
    
    if (user_data := database.retrieve_user_by_rank_name_company(
        context.chat_data['admin_user_details']['rank_and_name'], 
        context.chat_data['admin_user_details']['company'])
    ):
        context.chat_data['admin_user_details']['id'] = user_data['id']
        context.chat_data['admin_user_details']['username'] = user_data['username']
        update.effective_chat.send_message(
            text = 
                "Here's what the new booking will look like:\n\n"
                f"*Facility:* {context.chat_data['admin_booking_details']['facility']}\n"
                f"*Date:* {context.chat_data['admin_booking_details']['date']}\n"
                f"*Time:* {context.chat_data['admin_booking_details']['start_time']} - {context.chat_data['admin_booking_details']['end_time']}\n"
                f"*Description:* {context.chat_data['admin_booking_details']['description']}\n\n"
                f'*POC:* {context.chat_data["admin_user_details"]["rank_and_name"]} ({context.chat_data["admin_user_details"]["company"]})\n'
                f"*Username:* [@{context.chat_data['admin_user_details']['username']}](https://t.me/{context.chat_data['admin_user_details']['username']})\n"
                f"*User ID:* {context.chat_data['admin_user_details']['id']}\n\n"
                "Confirm this booking?",
            parse_mode = ParseMode.MARKDOWN,
            reply_markup = keyboards.confirm_or_cancel
        )
        return CONFIRMATION
    
    else:
        update.effective_chat.send_message(
            text = "No users match this description. Re-enter user data or select 'Continue with Booking'.",
            reply_markup = keyboards.continue_with_booking
        )
        return USER_DETAILS


def save_unregistered_user_details(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['admin_user_details']['id'] = 'NULL'
    context.chat_data['admin_user_details']['username'] = 'NULL'
    
    update.callback_query.edit_message_text(
        text = 
            "Here's what the new booking will look like:\n\n"
            f"*Facility:* {context.chat_data['admin_booking_details']['facility']}\n"
            f"*Date:* {context.chat_data['admin_booking_details']['date']}\n"
            f"*Time:* {context.chat_data['admin_booking_details']['start_time']} - {context.chat_data['admin_booking_details']['end_time']}\n"
            f"*Description:* {context.chat_data['admin_booking_details']['description']}\n\n"
            f'*POC:* {context.chat_data["admin_user_details"]["rank_and_name"]} ({context.chat_data["admin_user_details"]["company"]})\n'
            f"*Username:* [@{context.chat_data['admin_user_details']['username']}](https://t.me/{context.chat_data['admin_user_details']['username']})\n"
            f"*User ID:* {context.chat_data['admin_user_details']['id']}\n\n"
            "Confirm this booking?",
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.confirm_or_cancel
    )
    return CONFIRMATION


'''
CONFIRMATION / CANCELLATION
'''
def confirm(update: Update, context: CallbackContext) -> int:
    
    try:
        event_url = calendar.add_booking(
            user_id = context.chat_data['admin_user_details']['id'],
            user_data = context.chat_data['admin_user_details'],
            chat_data = context.chat_data['admin_booking_details']
        )
    except Exception as error:
        update.effective_chat.send_message(
            text = '⚠ Sorry, I could not connect to Google Calendar. Try again?',
            reply_markup = keyboards.confirm_or_cancel
        )
        logger.exception(
            'GCal Insert Request Failure - %s - %s - %s',
            query.from_user.id,
            context.user_data['rank_and_name'],
            error
        )
        return CONFIRMATION
    
    update.callback_query.edit_message_text(
        text =
            'Booking confirmed:\n\n'
            f"*Facility:* {context.chat_data['admin_booking_details']['facility']}\n"
            f"*Date:* {context.chat_data['admin_booking_details']['date']}\n"
            f"*Time:* {context.chat_data['admin_booking_details']['start_time']} - {context.chat_data['admin_booking_details']['end_time']}\n"
            f"*Description:* {context.chat_data['admin_booking_details']['description']}\n\n"
            f'*POC:* {context.chat_data["admin_user_details"]["rank_and_name"]} ({context.chat_data["admin_user_details"]["company"]})\n'
            f"*Username:* [@{context.chat_data['admin_user_details']['username']}](https://t.me/{context.chat_data['admin_user_details']['username']})\n"
            f"*User ID:* {context.chat_data['admin_user_details']['id']}\n\n"
            '⚠ *Please verify the booking on Google Calendar.* FacilitiesBot does not check for conflicts in admin mode.',
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.show_in_calendar(event_url)
    )
    
    update.callback_query.answer()
    
    # Log new booking
    logger.info(
        'Admin Booking - %s - for %s - %s on %s, %s to %s',
        update.callback_query.from_user.id,
        context.chat_data['admin_user_details']['rank_and_name'],
        context.chat_data['admin_booking_details']['facility'],
        context.chat_data['admin_booking_details']['date'],
        context.chat_data['admin_booking_details']['start_time'],
        context.chat_data['admin_booking_details']['end_time']
    )
    
    return ConversationHandler.END # -1


def cancel(update: Update, context: CallbackContext) -> int:
    
    # Cancelling via inline keyboard
    if update.callback_query: 
        update.callback_query.edit_message_text('No booking was made.')
        # CallbackQueries need to be answered, even if no user notification is needed
        update.callback_query.answer()
    
    # Cancelling via /cancel command
    else:
        update.effective_chat.send_message('No booking was made.')
    
    return ConversationHandler.END # -1


'''
ERROR CALLBACKS
'''
def user_details_error(update: Update, context: CallbackContext) -> int:
    
    update.effective_chat.send_message(
        text = 
            "Sorry, the list of user details you sent is invalid. Please reenter in this order and format:\n\n"
            '`RNK NAME` (e.g. PTE FacilitiesBot)\n'
            '`ALPHA/BRAVO/CHARLIE/SP/MSC/HQ`',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return USER_DETAILS


def booking_details_error(update: Update, context: CallbackContext) -> int:
    
    update.effective_chat.send_message(
        text =
            "Sorry, the list of booking details you sent is invalid. Please reenter in this order and format:\n\n"
            '`LT 1/LT 2/CONF ROOM/RTS/STINGRAY SQ`\n'
            '`DDMMYY` (e.g. 091222)\n'
            '`HHmm-HHmm` (e.g. 0900-1300)\n'
            '`Description`',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return BOOKING_DETAILS


'''
ADMIN HANDLER
'''
handler = ConversationHandler(
    entry_points = [CommandHandler('admin', admin)],
    states = {
        BOOKING_DETAILS: [
            MessageHandler(filters.admin_booking_details, save_booking_details),
            MessageHandler(Filters.all & (~Filters.command), booking_details_error)
        ],
        USER_DETAILS: [
            MessageHandler(filters.admin_user_details, save_user_details),
            CallbackQueryHandler(save_unregistered_user_details, pattern = 'continue'),
            MessageHandler(Filters.all & (~Filters.command), user_details_error)
        ],
        CONFIRMATION: [
            CallbackQueryHandler(callback = confirm, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ],
    },
    fallbacks = [
        CommandHandler('cancel', cancel),
        MessageHandler(Filters.command, actions.silent_cancel)
    ],
    allow_reentry = True,
    name = 'admin',
    persistent = True
)