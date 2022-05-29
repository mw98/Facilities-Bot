from datetime import datetime
import logging, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

logger = logging.getLogger(__name__)

'''
ACCESS CALENDAR API
'''
# Authenticate service account
try:
    service_account_info = json.loads(config.SERVICE_ACCOUNT_INFO)
    credentials = service_account.Credentials.from_service_account_info(
        info = service_account_info,
        scopes = ['https://www.googleapis.com/auth/calendar.events']
    )
except FileNotFoundError as error:
    logger.debug(error)
    print('Service account key not found.')
    sys.exit()

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
    
    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime', # assumed by list_available_slots()
        singleEvents = True, # requirement for ordering by start time
        timeMin = f'{date}T00:00:00+08:00', # exclusive bound
        timeMax = f'{date}T23:59:59+08:00', # exclusive bound
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
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.time()
    
    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime',
        singleEvents = True,
        timeMin = f'{current_date}T00:00:00+08:00',
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
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.time()
    
    bookings = service.events().list(
        calendarId = config.CALENDAR_ID,
        orderBy = 'startTime',
        singleEvents = True,
        timeMin = f'{current_date}T00:00:00+08:00',
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
def list_conflicts(chat_data: dict) -> list:
    
    existing_bookings = find_bookings_for_facility_by_date(chat_data['facility'], chat_data['date'])
    
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
def add_booking(user_id: int, user_data: dict, chat_data: dict) -> str:
    
    new_booking = service.events().insert(
        calendarId = config.CALENDAR_ID, 
        body = {
            "summary": f"{chat_data['facility']} ({user_data['company']})",
            "description": 
                f"Activity: {chat_data['description']}\n"
                f"POC: {user_data['rank_and_name']} ({user_data['company']})",
            "start": {
                "dateTime": f"{chat_data['date']}T{chat_data['start_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
            "end": {
                "dateTime": f"{chat_data['date']}T{chat_data['end_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
            "colorId": config.EVENT_COLOUR_CODES[chat_data['facility']],
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
    
    return new_booking.get('htmlLink')


def patch_booking(user_id: int, user_data: dict, chat_data: dict) -> str:
    
    patched_booking = service.events().patch(
        calendarId = config.CALENDAR_ID,
        eventId = chat_data['event_id'],
        body = {
            "summary": f"{chat_data['facility']} ({user_data['company']})",
            "description": 
                f"Activity: {chat_data['description']}\n"
                f"POC: {user_data['rank_and_name']} ({user_data['company']})",
            "start": {
                "dateTime": f"{chat_data['date']}T{chat_data['start_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
            "end": {
                "dateTime": f"{chat_data['date']}T{chat_data['end_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
            "colorId": config.EVENT_COLOUR_CODES[chat_data['facility']],
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
    
    return patched_booking.get('htmlLink')
    

def delete_booking(event_id: str):
    
    return service.events().delete(
        calendarId = config.CALENDAR_ID, 
        eventId = event_id
    ).execute()
