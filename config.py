import os
from datetime import timezone, timedelta

# HEROKU
USER_DATABASE_URL = os.environ['DATABASE_URL']
HEROKU_APP_URL = os.environ['HEROKU_APP_URL']

# TELEGRAM BOT
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
WEBHOOK_PORT = os.environ.get('PORT', 8443)
ADMIN_UID_LIST = os.environ['ADMIN_UID_LIST']
TIMEZONE = timezone(timedelta(hours=8)) # UTC+8
BOT_COMMANDS = os.environ['BOT_COMMANDS']
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
