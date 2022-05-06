from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Company Selector
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


# Facilities Selector
facilities = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('LT 1', callback_data = 'LT 1'),
        InlineKeyboardButton('LT 2', callback_data = 'LT 2'),
        InlineKeyboardButton('CONF ROOM', callback_data = 'CONF ROOM')
    ],
    [
        InlineKeyboardButton('RTS', callback_data = 'RTS'),
        InlineKeyboardButton('STINGRAY SQ', callback_data = 'STINGRAY SQ')
    ]
])


# Confirm / Cancel
confirm_or_cancel = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Confirm', callback_data = 'confirm'),
        InlineKeyboardButton('Cancel', callback_data = 'cancel')
    ]
])


# Confirm / Cancel for Patch Booking
patch_confirm_or_cancel = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Confirm', callback_data = 'confirm patch'),
        InlineKeyboardButton('Cancel', callback_data = 'cancel patch')
    ]
])


# Today Shortcut
today = InlineKeyboardMarkup([
    [InlineKeyboardButton('Today', callback_data = 'today')]
])


# Show in Google Calendar
def show_in_calendar(event_url: str) -> InlineKeyboardMarkup:
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Show in Google Calendar', url=event_url)]
    ])


# Contact POC
def contact_poc(booking_conflicts: list, effective_username: str) -> InlineKeyboardMarkup:
    
    buttons = set()
    
    for conflict in booking_conflicts:
        if conflict['username'] != effective_username:
            buttons.add(InlineKeyboardButton(f'Message {conflict["POC"]}', url=f'https://t.me/{conflict["username"]}'))
    
    buttons = list(buttons)
    buttons = [[button] for button in buttons]
    return InlineKeyboardMarkup(buttons)

# Move Previous Booking
move_previous = InlineKeyboardMarkup([
    [InlineKeyboardButton('Move Previous Booking', callback_data = 'patch')]
])
        
    










