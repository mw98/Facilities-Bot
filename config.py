import os
from datetime import timezone, timedelta

# DATABASE
# Outside Heroku runtime, set environment variable before running bot with:
# export DATABASE_URL=$(heroku config:get DATABASE_URL -a facilities-bot)
USER_DATABASE_URL = os.environ['DATABASE_URL']

# TELEGRAM BOT
BOT_TOKEN = os.environ['BOT_TOKEN']
WEBHOOK_PORT = os.environ.get('PORT', 5000)
ADMIN_UID_LIST = os.environ['ADMIN_UID_LIST']
TIMEZONE = timezone(timedelta(hours=8)) # UTC+8
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
FACILITIES_LIST = [
    'LT 1', 
    'LT 2', 
    'CONF ROOM', 
    'RTS', 
    'STINGRAY SQ'
]

# GOOGLE CALENDAR API
SERVICE_ACCOUNT_INFO = os.environ['SERVICE_ACCOUNT_INFO']
CALENDAR_ID = os.environ['CALENDAR_ID']
CALENDAR_URL = os.environ['CALENDAR_URL']
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