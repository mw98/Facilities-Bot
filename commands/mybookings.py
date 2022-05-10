from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
from utilities import calendar, actions

'''
MYBOOKINGS CALLBACK FUNCTION
'''
@actions.send_typing_action
def show_upcoming_user_bookings(update: Update, context: CallbackContext) -> None:
    
    bookings = calendar.find_upcoming_bookings_by_user(update.message.from_user.id)
    
    message = "Ok, here are your bookings:\n"
    
    if bookings['ongoing']:
        message += "\n*Ongoing*\n"
        for booking in bookings['ongoing']:
            message += (
                f"{booking['start']['dateTime'][11:16]}-{booking['end']['dateTime'][11:16]} {booking['extendedProperties']['shared']['facility']} ([Link]({booking['htmlLink']}))\n"
            )
    
    if bookings['later_today']:
        message += "\n*Later Today*\n"
        for booking in bookings['later_today']:
            message += (
                f"{booking['start']['dateTime'][11:16]}-{booking['end']['dateTime'][11:16]} {booking['extendedProperties']['shared']['facility']} ([Link]({booking['htmlLink']}))\n"
            )
    
    if bookings['after_today']:
        date = None
        for booking in bookings['after_today']:
            booking_date = booking['start']['dateTime'][:10]
            if booking_date != date:
                date = booking_date
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d').strftime('%d %b %Y')
                message += f"\n*{booking_date}*\n"
            message += (
                f"{booking['start']['dateTime'][11:16]}-{booking['end']['dateTime'][11:16]} {booking['extendedProperties']['shared']['facility']} ([Link]({booking['htmlLink']}))\n"
            )
    
    else:
        message = "You don't have any ongoing or upcoming bookings"
    
    update.effective_chat.send_message(
        text = message,
        parse_mode = ParseMode.MARKDOWN
    )
    
    return


'''
MYBOOKINGS HANDLER
'''
handler = CommandHandler('mybookings', show_upcoming_user_bookings)