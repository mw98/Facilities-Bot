from datetime import datetime
import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import actions, keyboards, filters, calendar
import config

logger = logging.getLogger(__name__)


BOOKING, ACTION, CHANGE, CHECK_FACILITY, CHECK_DATE, CHECK_TIME_RANGE, SAVE_DESCRIPTION, CONFIRM_CHANGE, CONFIRM_DELETE = range(9)

'''
CHANGE ENTRY POINT
'''
@actions.send_typing_action
@actions.load_user_profile
def change(update: Update, context: CallbackContext) -> int:
        
    # Retrieve user's bookings
    try: 
        bookings = calendar.find_upcoming_bookings_by_user(update.message.from_user.id)
    except Exception as error:
        update.effective_chat.send_message('⚠ Sorry, I could not connect to Google Calendar. Send /change to try again.')
    
    bookings = bookings['ongoing'] + bookings['later_today'] + bookings['after_today']
    
    if bookings:
    
        # Ask user to choose booking to change
        update.effective_chat.send_message(
            text = "Ok, here are your bookings. Choose one to change or delete. Send /cancel to stop.",
            reply_markup = keyboards.user_bookings(bookings),
        )
        return BOOKING
    
    else:
        update.effective_chat.send_message("You have no ongoing or upcoming bookings")
        return ConversationHandler.END # -1


'''
LOAD EXISTING BOOKING
'''
def load_booking(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Save event id to change or delete it later
    context.chat_data['event_id'] = query.data
    
    booking = calendar.service.events().get(
        calendarId = config.CALENDAR_ID,
        eventId = context.chat_data['event_id']
    ).execute()
    
    # Load booking details
    context.chat_data['facility'] = booking['extendedProperties']['shared']['facility']
    context.chat_data['date'] = booking['extendedProperties']['shared']['date']
    context.chat_data['start_time'] = booking['extendedProperties']['shared']['start_time']
    context.chat_data['end_time'] = booking['extendedProperties']['shared']['end_time']
    context.chat_data['datetime_start_time'] = datetime.strptime(context.chat_data['start_time'], '%H:%M').time()
    context.chat_data['datetime_end_time'] = datetime.strptime(context.chat_data['end_time'], '%H:%M').time()
    context.chat_data['description'] = booking['extendedProperties']['shared']['description']
    
    # Ask user change or delete the booking
    update.callback_query.edit_message_text(
        text = 
            "Here's the booking you selected.\n\n"
            f"*Facility:* {context.chat_data['facility']}\n"
            f"*Date:* {context.chat_data['date']}\n"
            f"*Time:* {context.chat_data['start_time']} - {context.chat_data['end_time']}\n"
            f"*Description:* {context.chat_data['description']}\n\n"
            "Do you want to change or delete this booking?",
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.change_or_delete
    )
    
    return ACTION


def show_edit_menu(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    # Create chat_data dict entries for original booking details
    context.chat_data['old_facility'] = ''
    context.chat_data['old_date'] = ''
    context.chat_data['old_start_time'] = ''
    context.chat_data['old_end_time'] = ''
    context.chat_data['old_description'] = ''
    
    query.edit_message_text(
        text = 
            "Here's the booking you selected.\n\n"
            f"*Facility:* {context.chat_data['facility']}\n"
            f"*Date:* {context.chat_data['date']}\n"
            f"*Time:* {context.chat_data['start_time']} - {context.chat_data['end_time']}\n"
            f"*Description:* {context.chat_data['description']}\n\n"
            "What do you want to change?",
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.edit_menu
    )
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    return CHANGE


def show_delete_prompt(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    query.edit_message_text(
        text = 
            "Here's the booking you selected.\n\n"
            f"*Facility:* {context.chat_data['facility']}\n"
            f"*Date:* {context.chat_data['date']}\n"
            f"*Time:* {context.chat_data['start_time']} - {context.chat_data['end_time']}\n"
            f"*Description:* {context.chat_data['description']}\n\n"
            "‼ Are you sure you want to delete it? This cannot be undone.",
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.confirm_or_cancel
    )
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    return CONFIRM_DELETE

'''
CONFIRMATION & CONFLICT PROMPTS
'''
def send_conflicts_message(update: Update, context: CallbackContext, user_id: int, conflicts: dict, conflict_prompt: str, reply_markup = None):
    
    chat = update.effective_chat
    
    # Contextualise bot response for multiple conflicts
    if len(conflicts) > 1:
        
        message = f"{context.chat_data['facility']} is unavailable at {context.chat_data['start_time']}-{context.chat_data['end_time']} on {context.chat_data['date']} due to conflicts with these bookings:\n\n"
        for conflict in conflicts:
            conflict_details = conflict['extendedProperties']['shared']
            message += (
                f"*Time:* {conflict_details['start_time']} - {conflict_details['end_time']}\n"
                f"*Description:* {conflict_details['description']}\n"
                f"*POC:* {conflict_details['name_and_company']}\n"
                f"[Event Link]({conflict['htmlLink']})\n\n"
            )
        message += f'{conflict_prompt}, or contact the POCs to deconflict.'
    
    elif len(conflicts) == 1:
        
        conflict = conflicts[0]
        conflict_details = conflict['extendedProperties']['shared']
        
        # If conflict is with user's previous booking
        if int(conflict_details['user_id']) == user_id:
            
            # Check if the new booking is identical with the previous one
            if (conflict_details['start_time'] == context.chat_data['start_time']
                and conflict_details['end_time'] == context.chat_data['end_time']
            ):
                # If it is, inform the user and end the conversation
                chat.send_message(
                    text =
                        "You've already made this booking:\n\n"
                        f"*Facility:* {context.chat_data['facility']}\n"
                        f"*Date:* {context.chat_data['date']}\n"
                        f"*Time:* {conflict_details['start_time']} - {conflict_details['end_time']}\n"
                        f"*Description:* {conflict_details['description']}\n"
                        f"[Event Link]({conflict['htmlLink']})\n\n"
                        "Send /change to edit another booking.",
                    parse_mode = ParseMode.MARKDOWN
                )
                return ConversationHandler.END
            
            # Ask user if they want to change the other booking instead
            message = (
                f"{context.chat_data['facility']} is unavailable at {context.chat_data['start_time']}-{context.chat_data['end_time']} on {context.chat_data['date']} due to a conflict with your previous booking:\n\n"
                f"*Time:* {conflict_details['start_time']} - {conflict_details['end_time']}\n"
                f"*Description:* {conflict_details['description']}\n"
                f"[Event Link]({conflict['htmlLink']})\n\n"
                f"{conflict_prompt}, or use /change to edit your previous booking instead."
            )
        
        # Contextualise bot response for singular conflict
        else:
            message = (
                f"{context.chat_data['facility']} is unavailable at {context.chat_data['start_time']}-{context.chat_data['end_time']} on {context.chat_data['date']} due to a conflict with this booking:\n\n"
                f"*Time:* {conflict_details['start_time']} - {conflict_details['end_time']}\n"
                f"*Description:* {conflict_details['description']}\n"
                f"[Event Link]({conflict['htmlLink']})\n\n"
                f"{conflict_prompt}, or contact the POC to deconflict."
            )
    
    return chat.send_message(
        text = message,
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = reply_markup
    )


def send_confirmation_query(update: Update, context: CallbackContext):
    
    return update.effective_chat.send_message(
        text = 
            "Ok, here's what your updated booking will look like:\n\n"
            f"<b>Facility:</b> {context.chat_data['old_facility']}{context.chat_data['facility']}\n"
            f"<b>Date:</b> {context.chat_data['old_date']}{context.chat_data['date']}\n"
            f"<b>Time:</b> {context.chat_data['old_start_time']}{context.chat_data['old_end_time']}{context.chat_data['start_time']} - {context.chat_data['end_time']}\n"
            f"<b>Description:</b> {context.chat_data['old_description']}{context.chat_data['description']}\n\n"
            "Do you want to proceed?",
        parse_mode = ParseMode.HTML,
        reply_markup = keyboards.confirm_or_cancel
    )


'''
CHANGE FACILITY
'''
@actions.send_typing_action
def change_facility(update: Update, context: CallbackContext) -> int:
    
    # CallbackQueries need to be answered, even if no user notification is needed
    update.callback_query.answer()
    
    update.effective_chat.send_message(
        text = "Choose a new facility:",
        reply_markup = keyboards.facilities_minus(context.chat_data['facility'])
    )
        
    return CHECK_FACILITY


@actions.send_typing_action
def check_facility(update: Update, context: CallbackContext) -> int:
    update.callback_query.answer()
    context.chat_data['old_facility'] = context.chat_data['facility']
    context.chat_data['facility'] = update.callback_query.data
        
    if (conflicts := calendar.list_conflicts(context.chat_data)):
        send_conflicts_message(
            update = update,
            context = context,
            user_id = update.callback_query.from_user.id,
            conflicts = conflicts,
            conflict_prompt = 'Please select another facility',
            reply_markup = keyboards.facilities_minus(context.chat_data['old_facility'])
        )
        context.chat_data['facility'] = context.chat_data['old_facility']
        return CHECK_FACILITY
    
    else:
        context.chat_data['old_facility'] = f"<s>{context.chat_data['old_facility']}</s> "
        send_confirmation_query(update, context)
        return CONFIRM_CHANGE


'''
CHANGE DATE
'''
@actions.send_typing_action
def change_date(update: Update, context: CallbackContext) -> int:
    
    # CallbackQueries need to be answered, even if no user notification is needed
    update.callback_query.answer()
    
    update.effective_chat.send_message(
        text = "Send me a new date for your booking. Please use the `DDMMYY` format.",
        parse_mode = ParseMode.MARKDOWN
    )
    
    return CHECK_DATE


@actions.send_typing_action
def date_error(update: Update, context: CallbackContext) -> int:
    actions.send_date_error(update, context, logger)
    return CHECK_DATE


@actions.send_typing_action
def check_date(update: Update, context: CallbackContext) -> int:
        
    context.chat_data['old_date'] = context.chat_data['date']
    context.chat_data['date'] = context.booking_date[0]
    
    if context.chat_data['old_date'] == context.chat_data['date']:
        update.effective_chat.send_message(
            text = "Your booking is already on that date. Send me a new date in the `DDMMYY` format or use /cancel to stop.",
            parse_mode = ParseMode.MARKDOWN
        )
        return CHECK_DATE
    
    if (conflicts := calendar.list_conflicts(context.chat_data)):
        send_conflicts_message(
            update = update,
            context = context,
            user_id = update.message.from_user.id,
            conflicts = conflicts,
            conflict_prompt = 'Send me another date in the `DDMMYY` format',
            reply_markup = keyboards.contact_poc(conflicts, update.message.from_user.username)
        )
        context.chat_data['date'] = context.chat_data['old_date']
        return CHECK_DATE
    
    else:
        context.chat_data['old_date'] = f"<s>{context.chat_data['old_date']}</s> "
        send_confirmation_query(update, context)
        return CONFIRM_CHANGE


'''
CHANGE TIME RANGE
'''
@actions.send_typing_action
def change_time_range(update: Update, context: CallbackContext) -> int:
    
    # CallbackQueries need to be answered, even if no user notification is needed
    update.callback_query.answer()
    
    update.effective_chat.send_message(
        text = "Send me a new time range for your booking. Please use this format: `HHmm-HHmm` (e.g. 0930-1300)",
        parse_mode = ParseMode.MARKDOWN
    )
    
    return CHECK_TIME_RANGE


@actions.send_typing_action
def time_range_error(update: Update, context: CallbackContext) -> int:
    actions.send_time_range_error(update, context, logger)    
    return CHECK_TIME_RANGE


@actions.send_typing_action
def check_time_range(update: Update, context: CallbackContext) -> int:
        
    context.chat_data['old_start_time'] = context.chat_data['start_time']
    context.chat_data['old_end_time'] = context.chat_data['end_time']
    context.chat_data['old_datetime_start_time'] = context.chat_data['datetime_start_time']
    context.chat_data['old_datetime_end_time'] = context.chat_data['datetime_end_time']
    context.chat_data['start_time'] = context.start_time[0]
    context.chat_data['end_time'] = context.end_time[0]
    context.chat_data['datetime_start_time'] = context.start_time[1]
    context.chat_data['datetime_end_time'] = context.end_time[1]
    
    if (context.chat_data['old_start_time'] == context.chat_data['start_time']
        and context.chat_data['old_end_time'] == context.chat_data['end_time']
    ):
        update.effective_chat.send_message(
            text = f"Your booking is already at {context.chat_data['start_time']}-{context.chat_data['end_time']}. Send me a new time range in the `HHmm-HHmm` format or use /cancel to stop.",
            parse_mode = ParseMode.MARKDOWN
        )
        return CHECK_TIME_RANGE
    
    
    conflicts = calendar.list_conflicts(context.chat_data)
    if (conflicts
        and not (len(conflicts) == 1 and conflicts[0]['id'] == context.chat_data['event_id'])
    ):
        send_conflicts_message(
            update = update,
            context = context,
            user_id = update.message.from_user.id,
            conflicts = conflicts,
            conflict_prompt = 'Send me another time range in the `HHmm-HHmm` format',
            reply_markup = keyboards.contact_poc(conflicts, update.message.from_user.username)
        )
        context.chat_data['start_time'] = context.chat_data['old_start_time']
        context.chat_data['end_time'] = context.chat_data['old_end_time']
        context.chat_data['datetime_start_time'] = context.chat_data['old_datetime_start_time']
        context.chat_data['datetime_end_time'] = context.chat_data['old_datetime_end_time']
        return CHECK_TIME_RANGE
    
    else:
        context.chat_data['old_start_time'] = f"<s>{context.chat_data['old_start_time']} "
        context.chat_data['old_end_time'] = f"{context.chat_data['old_end_time']}</s> "
        send_confirmation_query(update, context)
        return CONFIRM_CHANGE


'''
CHANGE DESCRIPTION
'''
@actions.send_typing_action
def change_description(update: Update, context: CallbackContext) -> int:
    
    # CallbackQueries need to be answered, even if no user notification is needed
    update.callback_query.answer()
    update.effective_chat.send_message("Send me a new description for your booking.")
    return SAVE_DESCRIPTION

def save_description(update: Update, context: CallbackContext) -> int:
    
    context.chat_data['old_description'] = f"<s>{context.chat_data['description']}</s> "
    context.chat_data['description'] = update.message.text
    send_confirmation_query(update, context)
    return CONFIRM_CHANGE


'''
CHANGED / DELETED / CANCELLED
'''
def confirm_change(update: Update, context: CallbackContext) -> int:
    
    try:
        event_url = calendar.patch_booking(
            user_id = update.callback_query.from_user.id,
            user_data = context.user_data,
            chat_data = context.chat_data
        )
    except Exception as error:
        update.effective_chat.send_message(
            text = '⚠ Sorry, I could not connect to Google Calendar. Try again?',
            reply_markup = keyboards.confirm_or_cancel
        )
        update.callback_query.answer()
        logger.exception(
            'GCal Patch Request Failure - %s - %s - %s',
            update.callback_query.from_user.id,
            context.user_data['rank_and_name'],
            error
        )
        return CONFIRM_CHANGE
    
    # Inform user booking has been changed
    update.callback_query.edit_message_text(
        text = 
            f'Booking updated! 🎉\n\n'
            f'*Facility:* {context.chat_data["facility"]}\n'
            f'*Date:* {context.chat_data["date"]}\n'
            f'*Time:* {context.chat_data["start_time"]} - {context.chat_data["end_time"]}\n'
            f'*Description:* {context.chat_data["description"]}\n\n'
            'Send /change to edit another booking.',
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.show_in_calendar(event_url)
    )
    update.callback_query.answer()
    
    # Log new booking
    logger.info(
        'New Booking - %s - %s - %s on %s, %s to %s',
        update.callback_query.from_user.id,
        context.user_data['rank_and_name'],
        context.chat_data['facility'],
        context.chat_data['date'],
        context.chat_data['start_time'],
        context.chat_data['end_time']
    )
    
    return ConversationHandler.END # -1


def confirm_delete(update: Update, context: CallbackContext) -> int:
    
    try:
        calendar.delete_booking(context.chat_data, context.user_data)
    except Exception as error:
        update.effective_chat.send_message(
            text = '⚠ Sorry, I could not connect to Google Calendar. Try again?',
            reply_markup = keyboards.confirm_or_cancel
        )
        update.callback_query.answer()
        logger.exception(
            'GCal Delete Request Failure - %s - %s - %s',
            update.callback_query.from_user.id,
            context.user_data['rank_and_name'],
            error
        )
        return CONFIRM_DELETE
    
    # Inform user booking has been deleted
    update.callback_query.edit_message_text("Booking deleted. Send /change to edit another booking.")
    update.callback_query.answer()
    
    # Log new booking
    logger.info(
        'Booking Deleted - %s - %s - %s on %s, %s to %s',
        update.callback_query.from_user.id,
        context.user_data['rank_and_name'],
        context.chat_data['facility'],
        context.chat_data['date'],
        context.chat_data['start_time'],
        context.chat_data['end_time']
    )
    
    return ConversationHandler.END # -1


def cancel(update: Update, context: CallbackContext) -> int:

    # Cancelling via inline keyboard
    if update.callback_query:
        update.callback_query.edit_message_text('Ok, no changes were made. Send /change to manage a different booking.')
         # CallbackQueries need to be answered, even if no user notification is needed
        update.callback_query.answer()
    
    # Cancelling via /cancel command
    else:
        update.effective_chat.send_message('Ok, no changes were made. Send /change to manage a different booking.')
    
    return ConversationHandler.END # -1


'''
CHANGE HANDLER
'''
handler = ConversationHandler(
    entry_points = [CommandHandler('change', change)],
    states = {
        BOOKING: [CallbackQueryHandler(load_booking)],
        ACTION: [
            CallbackQueryHandler(callback = show_edit_menu, pattern = 'change'),
            CallbackQueryHandler(callback = show_delete_prompt, pattern = 'delete')
        ],
        CHANGE: [
            CallbackQueryHandler(callback = change_facility, pattern = 'facility'),
            CallbackQueryHandler(callback = change_date, pattern = 'date'),
            CallbackQueryHandler(callback = change_time_range, pattern = 'time_range'),
            CallbackQueryHandler(callback = change_description, pattern = 'description'),
        ],
        CHECK_FACILITY: [CallbackQueryHandler(check_facility)],
        CHECK_DATE: [
            MessageHandler(filters.date, check_date),
            MessageHandler(Filters.all & (~Filters.command), date_error)
        ],
        CHECK_TIME_RANGE: [
            MessageHandler(filters.time_range, check_time_range),
            MessageHandler(Filters.all & (~Filters.command), time_range_error)
        ],
        SAVE_DESCRIPTION: [MessageHandler(Filters.text & (~Filters.command), save_description)],
        CONFIRM_CHANGE: [
            CallbackQueryHandler(callback = confirm_change, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ],
        CONFIRM_DELETE: [
            CallbackQueryHandler(callback = confirm_delete, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ]
    },
    fallbacks = [
        CommandHandler('cancel', cancel),
        MessageHandler(Filters.command, actions.silent_cancel)
    ],
    allow_reentry = True
)