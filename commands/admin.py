from datetime import timedelta
import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import filters, actions, keyboards, calendar, database
import config

logger = logging.getLogger(__name__)


BOOKING_DETAILS, CONFIRMATION = range(2)

'''
ADMIN ENTRY POINT
'''
@actions.send_typing_action
def admin(update: Update, context: CallbackContext) -> int:
    
    admins = config.ADMIN_UID_LIST.splitlines()
    if str(update.message.from_user.id) in admins:
        update.effective_chat.send_message(
            text = 
                '*⚠ Conflict checking disabled*\n\n'
                'List booking details in this format:\n'
                '`FACILITY`\n'
                '`DDMMYY`\n'
                '`HHmm-HHmm`\n'
                '`Description`\n'
                '`RNK NAME`\n'
                '`COMPANY`',
            parse_mode = ParseMode.MARKDOWN
        )
        return BOOKING_DETAILS
    else:
        return ConversationHandler.END


'''
SAVE BOOKING DETAILS
'''
@actions.send_typing_action
def save_booking_details(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['admin_chat_data'] = {
        'facility': context.facility[0],
        'date': context.date[0],
        'datetime_date': context.datetime_date[0],
        'start_time': context.time_range[0],
        'end_time': context.time_range[1],
        'time_range_imput': context.time_range_input[0],
        'description': context.description[0]
    }
    context.chat_data['admin_user_data'] = {
        'rank_and_name': context.rank_and_name[0],
        'company': context.company[0]
    }
    
    # Check if given user is in database
    if (user_data := database.retrieve_user_by_rank_name_company(
        context.chat_data['admin_user_data']['rank_and_name'], 
        context.chat_data['admin_user_data']['company'])
    ):
        context.chat_data['admin_user_data']['id'] = user_data['id']
        context.chat_data['admin_user_data']['username'] = user_data['username']
        update.effective_chat.send_message(
            text = 
                "*⚠ Conflict checking disabled*\n\n"
                "Confirm this booking?\n"
                f"*Facility:* {context.chat_data['admin_chat_data']['facility']}\n"
                f"*Date:* {context.chat_data['admin_chat_data']['date']}\n"
                f"*Time:* {context.chat_data['admin_chat_data']['start_time']} - {context.chat_data['admin_chat_data']['end_time']}\n"
                f"*Description:* {context.chat_data['admin_chat_data']['description']}\n"
                f'*POC:* {context.chat_data["admin_user_data"]["rank_and_name"]} ({context.chat_data["admin_user_data"]["company"]})\n'
                f"*Username:* @{context.chat_data['admin_user_data']['username']}\n"
                f"*User ID:* {context.chat_data['admin_user_data']['id']}",
            parse_mode = ParseMode.MARKDOWN,
            reply_markup = keyboards.confirm_or_cancel
        )
        return CONFIRMATION
    
    # Warn that user does not exist
    else:
        update.effective_chat.send_message(
            text = 
                "*⚠ Conflict checking disabled*\n"
                "*⚠ User does not exist*\n\n"
                f"*{context.chat_data['admin_user_data']['rank_and_name']} ({context.chat_data['admin_user_data']['company']})* is not registered. Re-enter booking details or tap 'Continue with Booking'",
            parse_mode = ParseMode.MARKDOWN,
            reply_markup = keyboards.continue_with_booking
        )
        return BOOKING_DETAILS


def continue_with_unregistered_user(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['admin_user_data']['id'] = 'NULL'
    context.chat_data['admin_user_data']['username'] = 'NULL'
    update.callback_query.edit_message_text(
        text = 
            "*⚠ Conflict checking disabled*\n"
            "*⚠ User does not exist*\n\n"
            "Confirm this booking?\n"
            f"*Facility:* {context.chat_data['admin_chat_data']['facility']}\n"
            f"*Date:* {context.chat_data['admin_chat_data']['date']}\n"
            f"*Time:* {context.chat_data['admin_chat_data']['start_time']} - {context.chat_data['admin_chat_data']['end_time']}\n"
            f"*Description:* {context.chat_data['admin_chat_data']['description']}\n"
            f'*POC:* {context.chat_data["admin_user_data"]["rank_and_name"]} ({context.chat_data["admin_user_data"]["company"]})\n'
            f"*Username:* @NULL\n"
            f"*User ID:* NULL",
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
            user_id = context.chat_data['admin_user_data']['id'],
            user_data = context.chat_data['admin_user_data'],
            chat_data = context.chat_data['admin_chat_data'],
            update_channel = False
        )
    except Exception as error:
        update.effective_chat.send_message(
            text = 
                '*An exception occurred:*\n'
                f'{error}\n\n'
                'Try again?',
            parse_mode = ParseMode.MARKDOWN,
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
            "Booking confirmed. Tap to copy:\n\n"
            f"`**Facility:** {context.chat_data['admin_chat_data']['facility']}\n"
            f"**Date:** {context.chat_data['admin_chat_data']['date']}\n"
            f"**Time:** {context.chat_data['admin_chat_data']['start_time']} - {context.chat_data['admin_chat_data']['end_time']}\n"
            f"**Description:** {context.chat_data['admin_chat_data']['description']}\n"
            f'**POC:** {context.chat_data["admin_user_data"]["rank_and_name"]} ({context.chat_data["admin_user_data"]["company"]})\n`'
            f"*Username:* @{context.chat_data['admin_user_data']['username']}\n"
            f"*User ID:* {context.chat_data['admin_user_data']['id']}\n\n"
            f"⚠ Update log: {config.CHANNEL_ID}\n"
            "Book again: /admin\n\n"
            "Tap to copy next day template:\n"
            f"`{context.chat_data['admin_chat_data']['facility']}\n"
            f"{(context.chat_data['admin_chat_data']['datetime_date'] + timedelta(days=1)).strftime('%d%m%y')}\n"
            f"{context.chat_data['admin_chat_data']['time_range_input']}"
            f"{context.chat_data['admin_chat_data']['description']}"
            f"{context.chat_data['admin_user_data']['rank_and_name']}"
            f"{context.chat_data['admin_user_data']['company']}`",
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.show_in_calendar(event_url)
    )
    update.callback_query.answer()
    
    # Log new booking
    logger.info(
        'Admin Booking - %s - for %s - %s on %s, %s to %s',
        update.callback_query.from_user.id,
        context.chat_data['admin_user_data']['rank_and_name'],
        context.chat_data['admin_chat_data']['facility'],
        context.chat_data['admin_chat_data']['date'],
        context.chat_data['admin_chat_data']['start_time'],
        context.chat_data['admin_chat_data']['end_time']
    )
    
    return ConversationHandler.END # -1


def cancel(update: Update, context: CallbackContext) -> int:
    
    # Cancelling via inline keyboard
    if update.callback_query:
        update.callback_query.answer() 
        update.callback_query.edit_message_text('No booking was made.')
    
    # Cancelling via /cancel command
    else:
        update.effective_chat.send_message('No booking was made.')
    
    return ConversationHandler.END # -1


'''
ERROR CALLBACK
'''

def booking_details_error(update: Update, context: CallbackContext) -> int:
    
    update.effective_chat.send_message(
        text =
            "*⚠ Conflict checking disabled*\n"
            '*‼ Booking details invalid*\n\n'
            'Re-enter in this format:\n'
            '`FACILITY`\n'
            '`DDMMYY`\n'
            '`HHmm-HHmm`\n'
            '`Description`\n'
            '`RNK NAME`\n'
            '`COMPANY`',
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
            CallbackQueryHandler(continue_with_unregistered_user, pattern = 'continue'),
            MessageHandler(Filters.all & (~Filters.command), booking_details_error)
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
    allow_reentry = True
)