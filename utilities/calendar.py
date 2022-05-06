from datetime import datetime
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

logger = logging.getLogger(__name__)

'''
ACCESS CALENDAR API
'''
# Authenticate service account
credentials = service_account.Credentials.from_service_account_file(
    filename = config.SERVICE_ACCOUNT_FILE,
    scopes = config.SERVICE_ACCOUNT_SCOPES
)

# Create service object
try: 
    service = build('calendar', 'v3', credentials = credentials)
except HttpError as error: 
    service = None
    logger.exception(error)

'''
BACKBONE FUNCTIONS
'''
def list_bookings(facility: str, date: str) -> list:
    
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
        
        start_time = booking['start']['dateTime'][11:16]
        datetime_start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = booking['end']['dateTime'][11:16]
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


'''
DECONFLICT BOOKINGS
'''
def list_available_slots(chat_data: dict):
    
    # Get a list of bookings on the chosen date
    existing_bookings = list_bookings(chat_data['facility'], chat_data['date'])
    
    # If no bookings are found, the facility is fully available
    if not existing_bookings: return
    
    available_slots = []
    now = datetime.now(config.TIMEZONE)
    
    # If the chosen date is today
    if chat_data['datetime_date'] == now.date():
        
        # Check if there are ongoing or upcoming bookings
        if (ongoing_or_next := find_ongoing_or_next(existing_bookings, now.time())):
            
            # If there is an ongoing booking
            if ongoing_or_next['ongoing']:
                
                # Then the next slot starts when the ongoing booking ends
                slot_start_time = ongoing_or_next['end_time']
                start_iteration_idx = ongoing_or_next['idx'] + 1
            
            # Else if there is an upcoming booking
            else:
                
                # Then the first slot is between now and when the upcoming booking starts
                available_slots.append(('Now', ongoing_or_next['start_time']))
                
                # And the subsequent slot starts when the upcoming booking ends
                slot_start_time = ongoing_or_next['end_time']
                start_iteration_idx = ongoing_or_next['idx'] + 1
        
        # Else if there are no ongoing or upcoming bookings, the facility is fully available
        else: return
    
    # If the chosen date is after today
    else:
        
        first_booking = existing_bookings[0]
        start_time = first_booking['start']['dateTime'][11:16]
        datetime_start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = first_booking['end']['dateTime'][11:16]
        
        # If the first booking starts at midnight
        if datetime_start_time == datetime.time(0,0,0):
            
            # The first slot starts after the first booking ends
            slot_start_time = end_time
            start_interation_idx = 1
        
        # If the first booking starts after midnight
        else: 
            
            # The first slot is between 00:00 and when the first booking starts
            available_slots.append('00:00', start_time)
            
            # The next slot starts when the first booking ends
            slot_start_time = end_time
            start_iteration_idx = 1
    
    # Iteratively append subsequent slots
    for booking in existing_bookings[start_iteration_idx:]:
        available_slots.append((slot_start_time, booking['start']['dateTime'][11:16]))
        slot_start_time = booking['end']['dateTime'][11:16]
    
    # If the last booking ends before 23:59
    if slot_start_time != '23:59':
        
        # The last slot is between the end of the last booking and 23:59
        available_slots.append((slot_start_time, '23:59'))
    
    return available_slots


def list_conflicts(chat_data: dict) -> list:
    
    existing_bookings = list_bookings(chat_data['facility'], chat_data['date'])
    
    conflicts = []
    
    for booking in existing_bookings:
        
        start_time = booking['start']['dateTime'][11:16]
        end_time = booking['end']['dateTime'][11:16]
        datetime_start_time = datetime.strptime(start_time, '%H:%M').time()
        datetime_end_time = datetime.strptime(end_time, '%H:%M').time()        
        
        if (
            (chat_data['datetime_start_time'] > datetime_start_time and chat_data['datetime_start_time'] < datetime_end_time)
            or (chat_data['datetime_end_time'] > datetime_start_time and chat_data['datetime_end_time'] < datetime_end_time)
            or (chat_data['datetime_start_time'] <= datetime_start_time and chat_data['datetime_end_time'] >= datetime_end_time)
        ):
            description = booking['description'].splitlines()
            conflicts.append(
                {
                    'start_time': start_time,
                    'end_time': end_time,
                    'description': description[0][10:],
                    'POC': description[1][5:],
                    'htmlLink': booking['htmlLink'],
                    'username': booking['extendedProperties']['shared']['username'],
                    'user_id': booking['extendedProperties']['shared']['user_id'],
                    'event_id': booking['id']
                }
            )
        
    return conflicts


'''
MAKE OR CHANGE BOOKINGS
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
                   "user_id": str(user_id),
                   "username": user_data["username"]
                },
            },
        }
    ).execute()
    
    return new_booking.get('htmlLink')


def patch_booking(chat_data: dict) -> str:
    
    patched_booking = service.events().patch(
        calendarId = config.CALENDAR_ID,
        eventId = chat_data['event_id'],
        body = {
            "start": {
                "dateTime": f"{chat_data['date']}T{chat_data['start_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
            "end": {
                "dateTime": f"{chat_data['date']}T{chat_data['end_time']}:00+08:00",
                "timeZone": "Asia/Singapore",
            },
        }
    ).execute()
    
    return patched_booking.get('htmlLink')
    

def delete_booking(event_id: str) -> None:
    
    service.events().delete(
        calendarId = config.CALENDAR_ID, 
        eventId = event_id
    ).execute()
    
    return
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

