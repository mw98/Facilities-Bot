import os
from zoneinfo import ZoneInfo
import ujson

# HEROKU
HEROKU_APP_URL = os.environ['HEROKU_APP_URL']
DATABASE_URL = os.environ['DATABASE_URL']

# TELEGRAM
BOT_TOKEN = os.environ['BOT_TOKEN']
WEBHOOK_PORT = os.getenv('PORT') or 8443
ADMIN_USERS = set(ujson.loads(os.getenv('ADMIN_USERS') or '[]'))
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
CHANNEL_MUTED = (os.getenv('CHANNEL_MUTED') == 'True')
COMMANDS_BOOKING = [
    ("book", "Make a new booking"), 
    ("change", "Change or cancel a booking"), 
    ("check", "Check facility availability"), 
    ("mybookings", "List your upcoming bookings")
]
COMMANDS_SETTING = [
    ("profile", "Update your user profile"), 
    ("help", "Show this list of commands")
]
COMMANDS_ADMIN = [
    ("admin", "Make new bookings as any user")
]

# GOOGLE CALENDAR
CALENDAR_ID = os.environ['CALENDAR_ID']
CALENDAR_URL = os.getenv('CALENDAR_URL')
SERVICE_ACCOUNT_INFO = ujson.loads(os.environ['SERVICE_ACCOUNT_INFO'])

# BOOKING PARAMETERS
COMPANIES = ujson.loads(os.environ['COMPANIES'])
FACILITIES = ujson.loads(os.environ['FACILITIES'])
ALT_FACILITIES = ujson.loads(os.getenv('ALT_FACILITIES') or '{}')
IANA_TIMEZONE_NAME = os.getenv('IANA_TIMEZONE_NAME') or 'Asia/Singapore'
TIMEZONE = ZoneInfo(IANA_TIMEZONE)