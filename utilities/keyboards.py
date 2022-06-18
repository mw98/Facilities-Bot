from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import config

'''
MENUS
'''
companies = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('ALPHA', callback_data='ALPHA'),
        InlineKeyboardButton('BRAVO', callback_data='BRAVO'),
        InlineKeyboardButton('CHARLIE', callback_data='CHARLIE')
    ],
    [
        InlineKeyboardButton('MSC', callback_data='MSC'),
        InlineKeyboardButton('SP', callback_data='SP'),
        InlineKeyboardButton('HQ', callback_data='HQ')
    ],
])

facilities_list = [
    [
        InlineKeyboardButton('LT 1', callback_data = 'LT 1'),
        InlineKeyboardButton('LT 2', callback_data = 'LT 2'),
        InlineKeyboardButton('CONF ROOM', callback_data = 'CONF ROOM')
    ],
    [
        InlineKeyboardButton('RTS', callback_data = 'RTS'),
        InlineKeyboardButton('STINGRAY SQ', callback_data = 'STINGRAY SQ')
    ]
]

facilities = InlineKeyboardMarkup(facilities_list)

def facilities_minus(facility):
    
    facility = InlineKeyboardButton(facility, callback_data = facility)
    facilities_minus = []
    for row in facilities_list:
        row = [button for button in row if button != facility]
        facilities_minus.append(row)
    
    return InlineKeyboardMarkup(facilities_minus)

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
        InlineKeyboardButton('Yes', callback_data = 'yes'),
        InlineKeyboardButton('No', callback_data = 'no')
    ]
])

patch_confirm_or_cancel = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Confirm', callback_data = 'confirm patch'),
        InlineKeyboardButton('Cancel', callback_data = 'cancel patch')
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
def contact_poc(booking_conflicts: list, effective_username: str) -> InlineKeyboardMarkup:
    
    buttons = set()
    
    for conflict in booking_conflicts:
        if conflict['extendedProperties']['shared']['username'] != effective_username:
            if conflict['extendedProperties']['shared']['username'] != 'NULL':
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