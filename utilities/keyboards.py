from itertools import zip_longest
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import config

'''
MENUS
'''
edit_menu = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Date', callback_data = 'date'),
        InlineKeyboardButton('Time Range', callback_data = 'time_range'),
    ],
    [
        InlineKeyboardButton('Facility', callback_data = 'facility'),
        InlineKeyboardButton('Description', callback_data = 'description')
    ],
])

'''
BINARY SELECTORS
'''
confirm_or_cancel = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Confirm', callback_data = 'confirm'),
        InlineKeyboardButton('Cancel', callback_data = 'cancel')
    ]
])

yes_or_no = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Yes', callback_data = 'confirm'),
        InlineKeyboardButton('No', callback_data = 'cancel')
    ]
])

confirm_or_cancel_update = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Confirm', callback_data = 'update'),
        InlineKeyboardButton('Cancel', callback_data = 'cancel update')
    ]
])

change_or_delete = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Change', callback_data = 'change'),
        InlineKeyboardButton('Delete', callback_data = 'delete')
    ]
])

today_tomorrow = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Today', callback_data = 'today'), 
        InlineKeyboardButton('Tomorrow', callback_data = 'tomorrow')
    ]
])

'''
SINGLE OPTION SELECTORS
'''
continue_with_booking = InlineKeyboardMarkup([[InlineKeyboardButton('Continue with Booking', callback_data = 'continue')]])

move_previous = InlineKeyboardMarkup([[InlineKeyboardButton('Move Previous Booking', callback_data = 'patch')]])

def show_in_calendar(event_url: str) -> InlineKeyboardMarkup:
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Show in Google Calendar', url=event_url)]
    ])

view_calendar = InlineKeyboardMarkup([[InlineKeyboardButton('Open Bookings Calendar', url=config.CALENDAR_URL)]])

'''
GENERATED OPTIONS SELECTORS
'''
def generate_menu(options: list, row_size: int = 2) -> InlineKeyboardMarkup:
    # Adapted from grouper recipe in Python itertools docs
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    args = [iter(options)] * row_size
    menu = [list(row) for row in zip_longest(*args)]
    menu[-1] = [option for option in matrix[-1] if option is not None]
    for idx, row in enumerate(menu):
        menu[idx] = [InlineKeyboardButton(option, callback_data = option) for option in row]
    return InlineKeyboardMarkup(menu)

companies = generate_menu(config.COMPANIES)

facilities = generate_menu(config.FACILITIES)

def facilities_minus(facility: str) -> InlineKeyboardMarkup:
    facilities = [f for f in config.FACILITIES if not facility]
    return generate_menu(facilities)


def contact_poc(booking_conflicts: list, effective_username: str) -> InlineKeyboardMarkup:
    
    buttons = set()
    
    for conflict in booking_conflicts:
        if (conflict['extendedProperties']['shared']['username'] != effective_username
            and conflict['extendedProperties']['shared']['user_id'] != 'NULL' # admin bookings for unregistered users don't carry user ids
        ):
            if conflict['extendedProperties']['shared']['username'] != 'NULL': # some telegram users don't have usernames
                url = f'https://t.me/{conflict["extendedProperties"]["shared"]["username"]}'
            else:
                url = f'tg://user?id={conflict["extendedProperties"]["shared"]["user_id"]}'
            buttons.add(InlineKeyboardButton(f'Message {conflict["extendedProperties"]["shared"]["name_and_company"]}', url=url))
    
    buttons = list(buttons)
    buttons = [[button] for button in buttons]
    return InlineKeyboardMarkup(buttons)


def user_bookings(bookings):
    
    buttons = []
    
    for booking in bookings:
        booking_details = booking['extendedProperties']['shared']
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{booking_details['date']}, {booking_details['start_time']}-{booking_details['end_time']} {booking_details['facility']}",
                    callback_data = f"{booking['id']}"
                )
            ]
        )
    
    return InlineKeyboardMarkup(buttons)