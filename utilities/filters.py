from datetime import datetime
import logging
from telegram import Message
from telegram.ext import MessageFilter
import config

logger = logging.getLogger(__name__)

'''
DATE FILTER
Ensures that date matches DDMMYY format and is not in the past.
'''
class DateFilter(MessageFilter):
    
    name = 'filters.date'
    data_filter = True
    
    def filter(self, message: Message):
        
        try:
            input_date = datetime.strptime(message.text, '%d%m%y').date()
        except Exception as e:
            logger.debug(e)
            return False
        
        current_date = datetime.now(config.TIMEZONE).date()
        if input_date < current_date:
            return False
        else:
            return {'booking_date': [input_date.strftime('%Y-%m-%d'), input_date]}

date = DateFilter()

'''
TIME RANGE FILTER
Ensures that time range matches HHmm-HHmm format, is a valid range.
DOES NOT ensure that time range is not in the past, because booking
date can't be passed to this filter. That is done in the callback function.
'''
class TimeRangeFilter(MessageFilter):
    
    name = 'filters.time_range'
    data_filter = True
    
    def filter(self, message: Message):
        
        try: 
            start_time = datetime.strptime(message.text[:4], '%H%M').time()
            end_time = datetime.strptime(message.text[-4:], '%H%M').time()
        except Exception as e:
            logger.debug(e)
            return False
                
        if start_time >= end_time:
            return False
        
        else:
            return {
                'start_time': [start_time.strftime('%H:%M'), start_time],
                'end_time': [end_time.strftime('%H:%M'), end_time]
            }

time_range = TimeRangeFilter()

'''
ADMIN BOOKING FILTERS
Ensures that booking and user details submitted in admin mode fit required format
'''
class AdminBookingDetailsFilter(MessageFilter):
    
    name = 'filters.admin_booking_details'
    data_filter = True
    
    def filter(self, message: Message):
        booking_details = message.text.splitlines()
        
        # Test facility input
        try:
            facility = booking_details[0]
        except IndexError as e:
            logger.debug(e)
            return False
        if facility not in config.FACILITIES_LIST:
            return False
        
        # Test date input
        try:
            date = datetime.strptime(booking_details[1], '%d%m%y').strftime('%Y-%m-%d')
        except Exception as e:
            logger.debug(e)
            return False
        
        # Test time input
        try:
            time_range = booking_details[2]
            start_time = datetime.strptime(time_range[:4], '%H%M').strftime('%H:%M')
            end_time = datetime.strptime(time_range[-4:], '%H%M').strftime('%H:%M')
        except Exception as e:
            logger.debug(e)
            return False
        
        # Test description
        try:
            description = booking_details[3]
        except IndexError as e:
            logger.debug(e)
            return False
        
        return {
            'facility': [facility],
            'date': [date],
            'time_range': [start_time, end_time],
            'description': [description]
        }

admin_booking_details = AdminBookingDetailsFilter()


class AdminUserDetailsFilter(MessageFilter):
    
    name = 'filters.admin_user_details'
    data_filter = True
    
    def filter(self, message: Message):
        admin_details = message.text.splitlines()        
        
        # Test rank/name input
        try: 
            rank_and_name = admin_details[0].upper()
        except IndexError as e:
            logger.debug(e)
            return False
        
        # Test company input
        try:
            company = admin_details[1].upper()
        except IndexError as e:
            logger.debug(e)
            return False
        
        return {
            'rank_and_name': [rank_and_name],
            'company': [company]
        }

admin_user_details = AdminUserDetailsFilter()
            
        
        




















