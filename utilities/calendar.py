from datetime import datetime
import logging, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utilities import shared
import config

logger = logging.getLogger(__name__)

'''
ACCESS CALENDAR API
'''
# Authenticate service account
credentials = service_account.Credentials.from_service_account_info(
    info = config.SERVICE_ACCOUNT_INFO,
    scopes = ['https://www.googleapis.com/auth/calendar.events']
)

# Create service object
try:
    service = build('calendar', 'v3', credentials = credentials)
except HttpError as error:
    service = None
    logger.exception(error)

'''
LIST BOOKINGS
'''
def find_bookings_for_facility_by_date(facility: str, date: str) -> list:
    
    utc_offset = datetime.now(config.TIMEZONE).isoformat()[26:]
    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime', # assumed by list_available_slots()
        singleEvents = True, # requirement for ordering by start time
        timeMin = f'{date}T00:00:00{utc_offset}', # exclusive bound
        timeMax = f'{date}T23:59:59{utc_offset}', # exclusive bound
        sharedExtendedProperty = f'facility={facility}',
    ).execute()

    return bookings['items']


def find_ongoing_or_next(bookings_today: list, current_time: datetime.time):

    for idx, booking in enumerate(bookings_today):

        start_time = booking['extendedProperties']['shared']['start_time']
        datetime_start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = booking['extendedProperties']['shared']['end_time']
        datetime_end_time = datetime.strptime(end_time, '%H:%M').time()

        # If a booking is currently happening
        if datetime_start_time < current_time and datetime_end_time > current_time:

            # Output the start and end times so they don't have to be found again
            return {
                'idx': idx,
                'ongoing': True,
                'start_time': start_time,
                'end_time': end_time,
                'datetime_start_time': datetime_start_time,
                'datetime_end_time': datetime_end_time
            }

        # If a booking is upcoming
        elif datetime_start_time > current_time:

            # Output the start and end times so they don't have to be found again
            return {
                'idx': idx,
                'ongoing': False,
                'start_time': start_time,
                'end_time': end_time,
                'datetime_start_time': datetime_start_time,
                'datetime_end_time': datetime_end_time
            }

    # If no ongoing or upcoming bookings found, return None
    return


def find_upcoming_bookings_by_user(user_id: int) -> list:

    now = datetime.now(config.TIMEZONE)
    utc_offset = now.isoformat()[26:]
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.time()

    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime',
        singleEvents = True,
        timeMin = f'{current_date}T00:00:00{utc_offset}',
        sharedExtendedProperty = f'user_id={user_id}',
    ).execute()['items']

    result = {'ongoing': [], 'later_today': [], 'after_today': []}

    remainder_idx = None

    for idx, booking in enumerate(bookings):
        booking_details = booking['extendedProperties']['shared']
        if booking_details['date'] == current_date:

            start_time = datetime.strptime(booking_details['start_time'], '%H:%M').time()
            end_time = datetime.strptime(booking_details['end_time'], '%H:%M').time()

            if start_time <= current_time and end_time >= current_time:
                result['ongoing'].append(booking)

            elif start_time > current_time:
                result['later_today'].append(booking)

        else: # Since bookings are arranged by start time, all subsequent items are after today
            result['after_today'].append(booking)
            remainder_idx = idx + 1
            break

    if remainder_idx:
        result['after_today'] += bookings[remainder_idx:]

    return result


def find_upcoming_bookings_by_facility(facility: str) -> list:

    now = datetime.now(config.TIMEZONE)
    utc_offset = now.isoformat()[26:]
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.time()

    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime',
        singleEvents = True,
        timeMin = f'{current_date}T00:00:00{utc_offset}',
        sharedExtendedProperty = f'facility={facility}'
    ).execute()['items']

    result = {'ongoing': [], 'later_today': [], 'after_today': []}
    remainder_idx = None

    for idx, booking in enumerate(bookings):
        booking_details = booking['extendedProperties']['shared']
        if booking_details['date'] == current_date:

            start_time = datetime.strptime(booking_details['start_time'], '%H:%M').time()
            end_time = datetime.strptime(booking_details['end_time'], '%H:%M').time()

            if start_time <= current_time and end_time >= current_time:
                result['ongoing'].append(booking)

            elif start_time > current_time:
                result['later_today'].append(booking)

        else: # Since bookings are arranged by start time, all subsequent items are after today
            result['after_today'].append(booking)
            remainder_idx = idx + 1
            break

    if remainder_idx:
        result['after_today'] += bookings[remainder_idx:]

    return result


'''
DECONFLICT BOOKINGS
'''
def list_conflicts(chat_data: dict, facility = None) -> list:

    target_facility = facility or chat_data['facility'] # optionally specify facility, supports alt facility functionality
    existing_bookings = find_bookings_for_facility_by_date(target_facility, chat_data['date'])

    conflicts = []
    for booking in existing_bookings:

        datetime_start_time = datetime.strptime(booking['extendedProperties']['shared']['start_time'], '%H:%M').time()
        datetime_end_time = datetime.strptime(booking['extendedProperties']['shared']['end_time'], '%H:%M').time()

        if (
            (chat_data['datetime_start_time'] > datetime_start_time and chat_data['datetime_start_time'] < datetime_end_time)
            or (chat_data['datetime_end_time'] > datetime_start_time and chat_data['datetime_end_time'] < datetime_end_time)
            or (chat_data['datetime_start_time'] <= datetime_start_time and chat_data['datetime_end_time'] >= datetime_end_time)
        ):
            conflicts.append(booking)

    return conflicts


'''
MAKE/CHANGE/DELETE BOOKINGS
'''
def generate_event_colorid(company: str) -> int:
    ColorId = config.COMPANIES.index(company) + 1
    if ColorId > 11: 
        ColorId = ColorId - 11
    return ColorId


def add_booking(user_id: int, user_data: dict, chat_data: dict, update_channel = True) -> str:
    
    utc_offset = datetime.now(config.TIMEZONE).isoformat()[26:]
    new_booking = service.events().insert(
        calendarId = config.CALENDAR_ID,
        body = {
            "summary": f"{chat_data['facility']} ({user_data['company']})",
            "description":
                f"Activity: {chat_data['description']}\n"
                f"POC: {user_data['rank_and_name']} ({user_data['company']})",
            "start": {
                "dateTime": f"{chat_data['date']}T{chat_data['start_time']}:00{utc_offset}",
                "timeZone": config.IANA_TIMEZONE_NAME,
            },
            "end": {
                "dateTime": f"{chat_data['date']}T{chat_data['end_time']}:00{utc_offset}",
                "timeZone": config.IANA_TIMEZONE_NAME,
            },
            "colorId": generate_event_colorid(user_data['company']),
            "extendedProperties": {
                "shared": {
                   "facility": chat_data["facility"],
                   "date": chat_data["date"],
                   "start_time": chat_data["start_time"],
                   "end_time": chat_data["end_time"],
                   "description": chat_data["description"],
                   "name_and_company": f"{user_data['rank_and_name']} ({user_data['company']})",
                   "user_id": str(user_id),
                   "username": user_data["username"]
                },
            },
        }
    ).execute()

    if update_channel:
        if user_data['username'] != 'NULL':
            chat_link = f"https://t.me/{user_data['username']}"
        else:
            chat_link = f"tg://user?id={user_id}"
        shared.update_facilities_channel(
            f'<b><a href="{new_booking["htmlLink"]}">New Booking</a></b>\n'
            f"<b>Facility</b>: {chat_data['facility']}\n"
            f"<b>Date</b>: {chat_data['date']}\n"
            f"<b>Time</b>: {chat_data['start_time']} - {chat_data['end_time']}\n"
            f"<b>Description</b>: {chat_data['description']}\n"
            f"<b>POC</b>: <a href='{chat_link}'>{user_data['rank_and_name']} ({user_data['company']})</a>"
        )

    return new_booking['htmlLink']


def patch_booking(user_id: int, user_data: dict, chat_data: dict) -> str:
    
    now = datetime.now(config.TIMEZONE)
    utc_offset = now.isoformat()[26:]
    patch_timestamp = now.strftime('%Y-%m-%d %H:%M:%S (UTC%z)')
    patched_booking = service.events().patch(
        calendarId = config.CALENDAR_ID,
        eventId = chat_data['event_id'],
        body = {
            "summary": f"{chat_data['facility']} ({user_data['company']})",
            "description":
                f"Activity: {chat_data['description']}\n"
                f"POC: {user_data['rank_and_name']} ({user_data['company']})\n\n"
                f"Edited on {patch_timestamp}",
            "start": {
                "dateTime": f"{chat_data['date']}T{chat_data['start_time']}:00{utc_offset}",
                "timeZone": config.IANA_TIMEZONE_NAME,
            },
            "end": {
                "dateTime": f"{chat_data['date']}T{chat_data['end_time']}:00{utc_offset}",
                "timeZone": config.IANA_TIMEZONE_NAME,
            },
            "colorId": generate_event_colorid(user_data['company']),
            "extendedProperties": {
                "shared": {
                   "facility": chat_data["facility"],
                   "date": chat_data["date"],
                   "start_time": chat_data["start_time"],
                   "end_time": chat_data["end_time"],
                   "description": chat_data["description"],
                   "name_and_company": f"{user_data['rank_and_name']} ({user_data['company']})",
                   "user_id": str(user_id),
                   "username": user_data["username"]
                },
            },
        }
    ).execute()

    if user_data['username'] != 'NULL':
        chat_link = f"https://t.me/{user_data['username']}"
    else:
        chat_link = f"tg://user?id={user_id}"
    shared.update_facilities_channel(
        f'<b><a href="{patched_booking["htmlLink"]}">Booking Updated</a></b>\n'
        f"<b>Facility</b>: {chat_data['old_facility']}{chat_data['facility']}\n"
        f"<b>Date</b>: {chat_data['old_date']}{chat_data['date']}\n"
        f"<b>Time</b>: {chat_data['old_start_time']}{chat_data['old_end_time']}{chat_data['start_time']} - {chat_data['end_time']}\n"
        f"<b>Description</b>: {chat_data['old_description']}{chat_data['description']}\n"
        f"<b>POC</b>: <a href='{chat_link}'>{user_data['rank_and_name']} ({user_data['company']})</a>"
    )

    return patched_booking['htmlLink']


def delete_booking(user_id: int, user_data: dict, chat_data: dict) -> None:

    service.events().delete(
        calendarId = config.CALENDAR_ID,
        eventId = chat_data['event_id']
    ).execute()

    if user_data['username'] != 'NULL':
        chat_link = f"https://t.me/{user_data['username']}"
    else:
        chat_link = f"tg://user?id={user_id}"
    shared.update_facilities_channel(
        "<b>Booking Cancelled</b>\n"
        f"<b>Facility</b>: {chat_data['facility']}\n"
        f"<b>Date</b>: {chat_data['date']}\n"
        f"<b>Time</b>: {chat_data['start_time']} - {chat_data['end_time']}\n"
        f"<b>Description</b>: {chat_data['description']}\n"
        f"<b>POC</b>: <a href='{chat_link}'>{user_data['rank_and_name']} ({user_data['company']})</a>"
    )

    return
