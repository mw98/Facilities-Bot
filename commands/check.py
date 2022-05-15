from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from utilities import actions, keyboards, calendar

SHOW_BOOKINGS = 0

'''
CHECK ENTRY POINT
'''
@actions.send_typing_action
def check(update: Update, context: CallbackContext) -> int:
    
    # Ask user to choose a facility to check
    update.effective_chat.send_message(
        text = "Which facility's availability would you like to check?",
        reply_markup = keyboards.facilities
    )
    
    return SHOW_BOOKINGS


'''
SEND UPCOMING BOOKINGS FOR CHOSEN FACILITY
'''
@actions.send_typing_action
def show_bookings(update: Update, context: CallbackContext) -> int:
    
    facility = update.callback_query.data
    bookings = calendar.find_upcoming_bookings_by_facility(facility)
    
    if not bookings['ongoing'] and not bookings['later_today'] and not bookings['after_today']:
        update.effective_chat.send_message(
            text = f"*{facility}* has no ongoing or upcoming bookings.\n\nUse /book to make a new booking.",
            parse_mode = ParseMode.MARKDOWN
        )
    
    else:
        message = f"Here's a list of upcoming *{facility}* bookings and their respective POCs:\n"
        
        if bookings['ongoing']:
            message += '\n*Ongoing*\n'
            for booking in bookings['upcoming']:
                booking_details = booking['extendedProperties']['shared']
                message += f"[{booking_details['start_time']}-{booking_details['end_time']}]({booking['htmlLink']}) {booking_details['name_and_company']}\n"
        
        if bookings['later_today']:
            message+= '\n*Later Today*\n'
            for booking in bookings['later_today']:
                booking_details = booking['extendedProperties']['shared']
                message += f"[{booking_details['start_time']}-{booking_details['end_time']}]({booking['htmlLink']}) {booking_details['name_and_company']}\n"
        
        date = None
        if bookings['after_today']:
            for booking in bookings['after_today']:
                booking_details = booking['extendedProperties']['shared']
                if booking_details['date'] != date:
                    message += f"\n*{datetime.strptime(booking_details['date'], '%Y-%m-%d').strftime('%d %b %Y')}*\n"
                message += f"[{booking_details['start_time']}-{booking_details['end_time']}]({booking['htmlLink']}) {booking_details['name_and_company']}\n"
        
        message += '\nUse /book to make a new booking.'
                
        update.effective_chat.send_message(
            text = message,
            parse_mode = ParseMode.MARKDOWN,
            reply_markup = keyboards.view_calendar
        )
                
    update.callback_query.answer()
    return ConversationHandler.END


'''
CHECK HANDLER
'''
handler = ConversationHandler(
    entry_points = [CommandHandler('check', check)],
    states = {SHOW_BOOKINGS: [CallbackQueryHandler(show_bookings)]},
    fallbacks = [MessageHandler(Filters.command, actions.silent_cancel)],
    allow_reentry = True
)