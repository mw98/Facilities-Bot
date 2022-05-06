from datetime import datetime
import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import actions, keyboards, filters, calendar
import config, database

logger = logging.getLogger(__name__)


FACILITY, DATE, TIME_RANGE, DESCRIPTION, PATCH, CONFIRMATION = range(6)

'''
BOOKING ENTRY POINT
'''
@actions.send_typing_action
def book(update: Update, context: CallbackContext) -> int:
    
    chat = update.effective_chat
    
    # Check that user is registered and load user profile
    if (user_data := database.retrieve_user(update.message.from_user.id)):
        context.user_data.update(user_data)
    
    # Ask user to create a user profile & log error
    else:
        chat.send_message("Sorry, I can't find your user profile. Send /profile to create a new profile.")
        logger.debug('User Not Found - %s - %s', update.message.from_user.id, update.message.from_user.username)
        return ConversationHandler.END # -1
    
    # Ask user which facility to book
    chat.send_message(
        text = 'Which facility do you want to book?',
        reply_markup = keyboards.facilities
    )
    
    return FACILITY


'''
ERROR CALLBACK FUNCTIONS
'''
def date_error(update: Update, context: CallbackContext) -> int:
            
    # Ask user to send date again
    update.effective_chat.send_message(
        text = "Sorry, that is not a valid date. Please send me an upcoming date in the `DDMMYY` format.",
        parse_mode = ParseMode.MARKDOWN
    )
    
    # Log error
    logger.debug('Invalid Booking Date - %s - %s - "%s"', 
        update.message.from_user.id,
        context.user_data['rank_and_name'],
        update.message.text
    )
    
    return DATE


def time_range_error(update: Update, context: CallbackContext) -> int:
            
    # Ask user to send time range again
    update.effective_chat.send_message(
        text = 'Sorry, that is not a valid time range. Please send me an upcoming time range in the format `HHmm-HHmm`.',
        parse_mode = ParseMode.MARKDOWN
    )

    # Log error
    logger.debug('Invalid Booking Time Range - %s - %s - "%s"',
        update.message.from_user.id,
        context.user_data['rank_and_name'],
        update.message.text
    )
    
    return TIME_RANGE


'''
BOOKING CALLBACK FUNCTIONS
'''
@actions.send_typing_action
def save_facility(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    # Save user's facility selection
    context.chat_data['facility'] = query.data
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Ask user for date of booking
    update.effective_chat.send_message(
        text = 
            f'Ok, now booking *{context.chat_data["facility"]}* for you. Use /cancel to stop.\n\n'
            "Send me a date for this booking or select 'Today'. Please use the `DDMMYY` format.",
        reply_markup = keyboards.today,
        parse_mode = ParseMode.MARKDOWN
    )
    
    return DATE


@actions.send_typing_action
def save_date(update: Update, context: CallbackContext) -> int:
    
    now = datetime.now(config.TIMEZONE)
    current_date = now.date()
    
    # If user taps 'Today' inline keyboard button
    if (query := update.callback_query):
                        
        # CallbackQueries need to be answered, even if no user notification is needed
        query.answer()
        
        # Save today's date in gcal api event date format
        context.chat_data['datetime_date'] = current_date
        context.chat_data['date'] = context.chat_data['datetime_date'].strftime('%Y-%m-%d')
            
    # If user sends a date
    else: 
        # Save user entered booking date (retrieved from filters.date)
        context.chat_data['date'] = context.booking_date[0]
        context.chat_data['datetime_date'] = context.booking_date[1]
        
    '''
        message_date = f'on {context.chat_data["date"]}' # Contextualise bot response
    
    # Check if/when the facility is in use on the chosen date
    upcoming_bookings = calendar.list_bookings(context.chat_data['facility'], context.chat_data['date'])
    
    # If the chosen date is today
    if context.chat_data['datetime_date'] == current_date:
        
        # If upcoming_bookings is not empty after removing bookings that have ended
        if (ongoing_or_next := calendar.find_ongoing_or_next(upcoming_bookings, now.time())):
            upcoming_bookings = upcoming_bookings[ongoing_or_next['idx']:]
            message_date = 'today' # Contextualise bot response
        
        # No upcoming bookings left
        else:
            upcoming_bookings = None
            message_date = 'for the rest of today' # Contextualise bot response
    
    # If there are upcoming bookings
    if upcoming_bookings:
        
        # Contextualise bot response
        if len(upcoming_bookings) > 1: message_quantity = 'at these times'
        else: message_quantity = 'during this period'
        message = f'*{context.chat_data["facility"]}* will be in use {message_quantity} {message_date}:\n\n'
        
    # Append each upcoming booking
        for booking in upcoming_bookings:
            start_time = booking["start"]["dateTime"][11:16]
            end_time = booking["end"]["dateTime"][11:16]
            description = booking['description'].splitlines()[0][10:]
            url = booking['htmlLink']
            message += f'[{start_time}-{end_time}]({url}) {description}\n'
        
    # No upcoming bookings
    else:
        # Contextualise bot response
        message = f'*{context.chat_data["facility"]}* is fully available {message_date}.\n'
    '''
     
    # Ask user for a time range
    update.effective_chat.send_message(
        text = 'Send me a time range for your booking. Please use this format:\n\n`HHmm-HHmm` (e.g. 0930-1300).',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return TIME_RANGE


@actions.send_typing_action
def save_time_range(update: Update, context: CallbackContext) -> int:
        
    # Check that time range is not in the past, since this can't be done in the filter
    now = datetime.now(config.TIMEZONE)
    current_time = now.time()
    current_date = now.date()
    datetime_end_time = context.end_time[1]
    if (context.chat_data['datetime_date'] == current_date 
        and datetime_end_time < current_time
    ):
        # Loop user back to previous step if it is
        return time_range_error(update, context)
    
    chat = update.effective_chat
    
    # Save time range of booking
    context.chat_data['start_time'] = context.start_time[0]
    context.chat_data['datetime_start_time'] = context.start_time[1]
    context.chat_data['end_time'] = context.end_time[0]
    context.chat_data['datetime_end_time'] = datetime_end_time
    
    # Check for conflicting bookings
    if (conflicts := calendar.list_conflicts(context.chat_data)):
        
        # Contextualise bot response
        if len(conflicts) > 1:
            message_start = 'The time range you sent me conflicts with these bookings:\n\n'
            message_end = 'Please send me another time range, or contact the POCs to deconflict.'
        
        else: 
            
            conflict = conflicts[0]
            
            # If conflict is with user's previous booking
            if int(conflict['user_id']) == update.message.from_user.id:
                
                event_summary = (
                    f'*Facility:* {context.chat_data["facility"]}\n'
                    f'*Time:* {conflict["start_time"]} - {conflict["end_time"]}\n'
                    f'*Date:* {context.chat_data["date"]}\n'
                    f'*Description:* {conflict["description"]}\n'
                    f'[Event Link]({conflict["htmlLink"]})'
                )
                
                # Check that the new booking isn't identical with the previous one
                if (conflict['start_time'] == context.chat_data['start_time']
                    and conflict['end_time'] == context.chat_data['end_time']
                ): 
                    chat.send_message(
                        text = 
                            "You've already made this booking:\n\n"
                            f'{event_summary}\n\n'
                            'Send /book to make another booking.',
                        parse_mode = ParseMode.MARKDOWN
                    )
                    return ConversationHandler.END
                
                # Save the previous booking details
                context.chat_data['old_start_time'] = conflict['start_time']
                context.chat_data['old_end_time'] = conflict['end_time']
                context.chat_data['event_id'] = conflict['event_id']
                context.chat_data['description'] = conflict['description']
                
                # Offer to update previous booking
                chat.send_message(
                    text = 
                        'The time range you sent conflicts with a previous booking you made:\n\n'
                        f'{event_summary}\n\n'
                        "Select 'Update' to shift your previous booking to the new time range, or send me another time range.",
                    reply_markup = keyboards.update_button,
                    parse_mode = ParseMode.MARKDOWN
                )
                return PATCH
            
            else: 
                message_start = 'The time range you sent me conflicts with this booking:\n\n'
                message_end = 'Please send me another time range, or contact the POC to deconflict.'
        
        for conflict in conflicts:
            message_start += (
                f'*Time:* {conflict["start_time"]} - {conflict["end_time"]}\n'
                f'*Description:* {conflict["description"]}\n'
                f'*POC:* {conflict["POC"]}\n'
                f'[Event Link]({conflict["htmlLink"]})\n\n'
            )
        
        chat.send_message(
            text = f'{message_start}{message_end}',
            reply_markup = keyboards.contact_poc(conflicts),
            parse_mode = ParseMode.MARKDOWN
        )
        
        return TIME_RANGE
    
    # Ask for a brief description of the booking
    chat.send_message('Lastly, send me a brief description of the booking.')
    
    return DESCRIPTION


def save_description(update: Update, context: CallbackContext) -> int:
        
    # Save booking description
    context.chat_data['description'] = update.message.text
    
    # Ask user to confirm booking request
    update.effective_chat.send_message(
        text =
            "Ok. Here's a summary of your booking request.\n\n"
            f'*Facility:* {context.chat_data["facility"]}\n'
            f'*Date:* {context.chat_data["date"]}\n'
            f'*Time:* {context.chat_data["start_time"]} - {context.chat_data["end_time"]}\n'
            f'*Description:* {context.chat_data["description"]}\n\n'
            'Do you want to confirm this booking?',
        reply_markup = keyboards.confirm_or_cancel,
        parse_mode = ParseMode.MARKDOWN
    )
    
    return CONFIRMATION


def patch_booking(update: Update, context: CallbackContext) -> int:
    
    update.effective_chat.send_message(
        text = 
            "Ok. Here's what your updated booking will look like.\n\n"
            f'<b>Facility:</b> {context.chat_data["facility"]}\n'
            f'<b>Date:</b> {context.chat_data["date"]}\n'
            f'<b>Time:</b> <s>{context.chat_data["old_start_time"]} {context.chat_data["old_end_time"]}</s> {context.chat_data["start_time"]} - {context.chat_data["end_time"]}\n'
            f'<b>Description:</b> {context.chat_data["description"]}\n\n'
            'Do you want to proceed?',
        reply_markup = keyboards.patch_confirm_or_cancel,
        parse_mode = ParseMode.HTML
    )
    
    return CONFIRMATION


def confirm(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    if query.data == 'confirm':
        
        # Book facility on Google Calendar
        try: 
            event_url = calendar.add_booking(query.from_user.id, context.user_data, context.chat_data)
        except Exception as error:
            update.effective_chat.send_message(
                text = 'Sorry, I could not connect to Google Calendar. Try again?',
                reply_markup = keyboards.confirm_or_cancel
            )
            logger.exception(
                'GCal Insert Request Failure - %s - %s - %s',
                query.from_user.id,
                context.user_data['rank_and_name'],
                error
            )
            return CONFIRMATION

        # Contextualise response
        message_adjective = 'confirmed'
    
    elif query.data == 'confirm patch':
        
        # Patch facility booking on Google Calendar
        try:
            event_url = calendar.patch_booking(context.chat_data)
        except Exception as error:
            update.effective_chat.send_message(
                text = 'Sorry, I could not connect to Google Calendar. Try again?',
                reply_markup = keyboards.patch_confirm_or_cancel
            )
            logger.exception(
                'GCal Patch Request Failure - %s - %s - %s',
                query.from_user.id,
                context.user_data['rank_and_name'],
                error
            )
            return CONFIRMATION

        # Contextualise response
        message_adjective = 'updated'
    
    # Inform user booking is confirmed
    query.edit_message_text(
        text =
            f'Booking {message_adjective}! 🎉\n\n'
            f'*Facility:* {context.chat_data["facility"]}\n'
            f'*Date:* {context.chat_data["date"]}\n'
            f'*Time:* {context.chat_data["start_time"]} - {context.chat_data["end_time"]}\n'
            f'*Description:* {context.chat_data["description"]}\n\n'
            'Send /book to make another booking.',
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.show_in_calendar(event_url)
    )
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Log new booking
    logger.info(
        'New Booking - %s - %s - %s on %s, %s to %s',
        query.from_user.id,
        context.user_data['rank_and_name'],
        context.chat_data['facility'],
        context.chat_data['date'],
        context.chat_data['start_time'],
        context.chat_data['end_time']
    )
    
    return ConversationHandler.END # -1


def cancel(update: Update, context: CallbackContext) -> int:
    
    # Cancelling via inline keyboard
    if (query := update.callback_query): 
        
        # CallbackQueries need to be answered, even if no user notification is needed
        query.answer()
        
        if query.data == 'cancel':
            query.edit_message_text('Booking cancelled. Send /book to make a new booking.')
        
        elif query.data == 'cancel patch':
            query.edit_message_text('Ok, no changes were made. Send /book to make a new booking, or /change to manage your existing bookings.')
    
    # Cancelling via /cancel command
    else:
        update.effective_chat.send_message('Booking cancelled. Send /book to make a new booking.')
    
    return ConversationHandler.END # -1
    

'''
BOOKING HANDLER
'''
handler = ConversationHandler(
    entry_points = [CommandHandler('book', book)],
    states = {
        FACILITY: [CallbackQueryHandler(save_facility)],
        DATE: [
            CallbackQueryHandler(callback = save_date, pattern = 'today'),
            MessageHandler(filters.date, save_date),
            MessageHandler(Filters.all & (~Filters.command), date_error)
        ],
        TIME_RANGE: [
            MessageHandler(filters.time_range, save_time_range),
            MessageHandler(Filters.all & (~Filters.command), time_range_error)
        ],
        DESCRIPTION: [MessageHandler(Filters.text & (~Filters.command), save_description)],
        PATCH: [
            CallbackQueryHandler(callback = patch_booking, pattern = 'update'),
            MessageHandler(filters.time_range, save_time_range)
        ],
        CONFIRMATION: [
            CallbackQueryHandler(callback = confirm, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
