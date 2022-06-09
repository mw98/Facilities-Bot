import os
from datetime import timezone, timedelta

# HEROKU
HEROKU_APP_URL = os.environ['HEROKU_APP_URL']
DATABASE_URL = os.environ['DATABASE_URL']

# TELEGRAM
ADMIN_UID_LIST = os.getenv('ADMIN_UID_LIST', [])
BOT_TOKEN = os.environ['BOT_TOKEN']
BOT_COMMANDS = os.getenv('BOT_COMMANDS', '')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_MUTED = (os.getenv('CHANNEL_MUTED', False) == 'True')
WEBHOOK_PORT = os.getenv('PORT', 8443)

# GOOGLE CALENDAR
CALENDAR_ID = os.environ['CALENDAR_ID']
CALENDAR_URL = os.getenv('CALENDAR_URL')
EVENT_COLOUR_CODES = {'LT 1': '1', 'LT 2': '7', 'CONF ROOM': '2', 'RTS': '5', 'STINGRAY SQ': '6'}
SERVICE_ACCOUNT_INFO = os.environ['SERVICE_ACCOUNT_INFO']

# SHARED VARIABLES
COMPANIES_LIST = ['ALPHA', 'BRAVO', 'CHARLIE', 'SP', 'MSC', 'HQ']
FACILITIES_LIST = ['LT 1', 'LT 2', 'CONF ROOM', 'RTS', 'STINGRAY SQ']
TIMEZONE = timezone(timedelta(hours=8)) # UTC+8