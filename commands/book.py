from datetime import datetime
import logging
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from utilities import keyboards, filters, calendar
import config, database

logger = logging.getLogger(__name__)


FACILITY, DATE, TIME_RANGE, DESCRIPTION, CONFIRMATION = range(5)

'''
BOOKING ENTRY POINT
'''
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
BOOKING CALLBACK FUNCTIONS
'''
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


def save_date(update: Update, context: CallbackContext) -> int:
        
    # If user taps 'Today' inline keyboard button
    if (query := update.callback_query):
        
        # CallbackQueries need to be answered, even if no user notification is needed
        query.answer()
        
        # Get today's date and save in gcal api event date format
        context.chat_data['datetime_date'] = datetime.now(config.TIMEZONE).date()
        context.chat_data['date'] = context.chat_data['datetime_date'].strftime('%Y-%m-%d')
        
        today = True
    
    # If user sends a date
    else: 
        
        # Save user entered booking date (retrieved from filters.date)
        context.chat_data['date'] = context.booking_date[0]
        context.chat_data['datetime_date'] = context.booking_date[1]
        
        today = False
    
    # Check what time periods are available on the chosen date    
    if (available_slots := calendar.list_available_slots(context.chat_data)):
        
        # Contextualise bot response
        message = f'*{context.chat_data["facility"]}* is available at these times '
        if today: message += 'today:\n\n'
        else: message += f'on {context.chat_data["date"]}:\n\n'
        
        # Iteratively append each period of availability
        for slot in available_slots:
            message += f'{slot[0]} - {slot[1]}\n'
    
    else:
        
        # Contextualise bot response
        message = f'*{context.chat_data["facility"]}* is fully available '
        if today: message += 'for the rest of today.\n'
        else: message += f'on {context.chat_data["date"]}.\n'
    
    # Ask user for a time range
    update.effective_chat.send_message(
        text = f'{message}\nSend me a time range for your booking. Please use this format: `HHmm-HHmm` (e.g. 0930-1300).',
        parse_mode = ParseMode.MARKDOWN
    )
    
    return TIME_RANGE


def save_time_range(update: Update, context: CallbackContext) -> int:
        
    chat = update.effective_chat
    
    # Save time range of booking
    context.chat_data['start_time'] = context.start_time[0]
    context.chat_data['datetime_start_time'] = context.start_time[1]
    context.chat_data['end_time'] = context.end_time[0]
    context.chat_data['datetime_end_time'] = context.end_time[1]
    
    # Check for conflicting bookings
    if (conflicts := calendar.list_conflicts(context.chat_data)):
        
        # Contextualise bot response
        if len(conflicts) > 1:
            message_start = 'The time range you sent me conflicts with these bookings:\n\n'
            message_end = 'Please send me another time range, or contact the POCs to deconflict.'
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


def confirm(update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    
    # CallbackQueries need to be answered, even if no user notification is needed
    query.answer()
    
    # Book facility on Google Calendar
    try: 
        event_url = calendar.add_booking(query.from_user.id, context.user_data, context.chat_data)
    except Exception as error:
        update.effective_chat.send_message(
            text = 'Sorry, I could not connect to Google Calendar. Try again?',
            reply_markup = keyboards.confirm_or_cancel
        )
        logger.exception(
            'GCal Request Failure - %s - %s - %s',
            query.from_user.id,
            context.user_data['rank_and_name'],
            error
        )
        return CONFIRMATION
    
    # Inform user booking is confirmed
    query.edit_message_text(
        text =
            'Booking confirmed! 🎉\n\n'
            f'*Facility:* {context.chat_data["facility"]}\n'
            f'*Date:* {context.chat_data["date"]}\n'
            f'*Time:* {context.chat_data["start_time"]} - {context.chat_data["end_time"]}\n'
            f'*Description:* {context.chat_data["description"]}\n\n'
            'Send /book to make another booking.',
        parse_mode = ParseMode.MARKDOWN,
        reply_markup = keyboards.show_in_calendar(event_url)
    )
    
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
        query.edit_message_text('Booking cancelled. Send /book to make a new booking.')
    
    # Cancelling via /cancel command
    else:
        update.effective_chat.send_message('Booking cancelled. Send /book to make a new booking.')
    
    return ConversationHandler.END # -1

'''
ERROR CALLBACK FUNCTIONS
'''
def date_error(update: Update, context: CallbackContext) -> int:
            
    # Ask user to send date again
    update.effective_chat.send_message(
        text = 'Sorry, that is not a valid date. Please send me an upcoming date in the `DDMMYY` format.',
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
        CONFIRMATION: [
            CallbackQueryHandler(callback = confirm, pattern = 'confirm'),
            CallbackQueryHandler(callback = cancel, pattern = 'cancel')
        ]
    },
    fallbacks = [CommandHandler('cancel', cancel)]
)
