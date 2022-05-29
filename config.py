from datetime import timezone, timedelta

# TELEGRAM BOT
TIMEZONE = timezone(timedelta(hours=8)) # UTC+8
BOT_TOKEN_FILE = 'keys/bot_token.txt'
BOT_COMMANDS = (
    'Interact with me using these commands:\n\n'
    '*Manage Facility Bookings*\n'
    '/book - Book facilities in 5 SIR\n'
    '/change - Change or cancel a booking\n'
    '/check - Check facility availability\n'
    '/mybookings - List your upcoming bookings\n\n'
    '*Bot Settings*\n'
    '/profile - Update your user profile\n'
    '/help - Show this list of commands'
)
ADMIN_UID_LIST = 'data/admins.txt'
FACILITIES_LIST = [
    'LT 1', 
    'LT 2', 
    'CONF ROOM', 
    'RTS', 
    'STINGRAY SQ'
]

# GOOGLE CALENDAR API
SERVICE_ACCOUNT_SCOPES = ['https://www.googleapis.com/auth/calendar.events']
SERVICE_ACCOUNT_FILE = 'keys/service_account.json'
CALENDAR_ID = 'mui51q6orvum7s22r2civ3hmps@group.calendar.google.com'
CALENDAR_URL = 'https://calendar.google.com/calendar/embed?src=begpgae3aecell7h163qoek9l0%40group.calendar.google.com&ctz=Asia%2FSingapore'
EVENT_COLOUR_CODES = {
    'LT 1': '1',
    'LT 2': '7',
    'CONF ROOM': '2',
    'RTS': '5',
    'STINGRAY SQ': '6'
}
'''
GOOGLE CALENDAR API 
EVENT COLOR IDs:

ID | Name      | Hex Code
==========================
1  | Lavender  | #7886cb
2  | Sage      | #33b679
3  | Grape     | #8e24aa
4  | Flamingo  | #e67c73
5  | Banana    | #f6c026
6  | Tangerine | #f5511d
7  | Peacock   | #039be5
8  | Graphite  | #616161
9  | Blueberry | #3f51b5
10 | Basil     | #0b8043
11 | Tomato    | #d60000
'''