from datetime import *
from ast import Dict
import json
import os
import requests
import urllib.parse
from app.common.utils import validate_mobile
from app.common.cache import cache
import pytz

###############################################################

PENDING_ARRIVAL = 'Pending arrival'

###############################################################

class Reminder:
    def __init__(self):

        reancare_base_url = os.getenv("REANCARE_BASE_URL")
        if reancare_base_url == None:
            raise Exception('REANCARE_BASE_URL is not set')

        self.patient_url = str(reancare_base_url + "/patients/")
        self.reminder_url = str(reancare_base_url + "/reminders/one-time")
        self.reminder_search_url = str(reancare_base_url + "/reminders/search")
        self.api_key = os.getenv("REANCARE_API_KEY")
        self.access_token = cache.get('access_token')

        self.new_patients_added_count = 0
        self.reminders_sent_count = 0
        self.pending_arrival_count = 0
        self.appointments_processed_count = 0
        self.appointments_skipped_count = 0

    def create_one_time_reminders(self, reminder_date, appointments):

        self.access_token = cache.get('access_token')

        for appointment in appointments:

            patient_mobile_number = appointment['PatientMobile']
            is_valid_mobile = validate_mobile(patient_mobile_number)
            if not is_valid_mobile:
                print('*Invalid phone-number - ', patient_mobile_number)
                self.appointments_skipped_count = self.appointments_skipped_count + 1
                continue

            self.appointments_processed_count = self.appointments_processed_count + 1

            user_id = self.find_patient_by_mobile(patient_mobile_number)
            user_model = self.get_update_patient_model(appointment)
            appointment_time = self.get_time_in_24hrs(appointment)
            first_time = appointment_time['FirstTime']
            second_time = appointment_time['SecondTime']
            first_name = user_model['FirstName']

            if appointment['Status'] != PENDING_ARRIVAL:
                continue

            self.pending_arrival_count = self.pending_arrival_count + 1

            # Create patient if does not exist
            if user_id == None:
                user_id = self.create_patient(patient_mobile_number)
                if user_id == None:
                    raise Exception('Unable to create patient')
                self.new_patients_added_count = self.new_patients_added_count  + 1
                self.update_patient(user_id, user_model)

            # First reminder set as soon as pdf upload
            print(patient_mobile_number) 
            first_reminder = self.time_of_first_reminder(patient_mobile_number)
            print(first_reminder)
            schedule_model = self.get_schedule_create_model(user_id, first_name, appointment,first_reminder, reminder_date)
            response = self.schedule_reminder(schedule_model)
            # print(response)

            # Send reminders
            is_reminder_set = self.search_reminder(user_id, reminder_date, first_time)
            if not is_reminder_set:
                schedule_model = self.get_schedule_create_model(user_id, first_name, appointment, first_time, reminder_date)
                self.schedule_reminder(schedule_model)
            is_reminder_set = self.search_reminder(user_id, reminder_date, second_time)
            if not is_reminder_set:
                schedule_model = self.get_schedule_create_model(user_id, first_name, appointment, second_time, reminder_date)
                self.schedule_reminder(schedule_model)

    def search_reminder(self, patient_user_id, reminder_date, reminder_time):
        url = self.reminder_search_url
        headers = self.get_headers()
        params = {
            'userId': patient_user_id,
            'whenDate': reminder_date,
            'whenTime': reminder_time
        }
        # +'?userId={}&whenDate={}&whenTime={}'.format(patient_user_id,reminder_date,reminder_time)
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        if response.status_code == 200 and not result['Message'] == 'No records found!':
            return True
        else:
            # print(result['Message'])
            return False

    def find_patient_by_mobile(self, mobile):
        self.url = self.patient_url
        headers = self.get_headers()
        formatted = urllib.parse.quote(mobile)
        url = self.url + "search?phone={}".format(formatted)
        response = requests.get(url, headers=headers)
        search_result = response.json()
        if search_result['Message'] == 'No records found!':
            return None
        else:
            return search_result['Data']['Patients']['Items'][0]['UserId']

    def create_patient(self, mobile):
        self.url = self.patient_url
        header = self.get_headers(create_user=True)
        body = json.dumps({'Phone': mobile})
        response = requests.post(self.url, headers = header, data = body)
        result = response.json()
        if not result['HttpCode'] == 201:
            print('Unable to create patient ', result['Message'])
            return None
        else:
            created_patient_info = response.json()
            user_id = created_patient_info['Data']['Patient']['UserId']
            return user_id

    def get_update_patient_model(self, patient):
        body = {}
        name = patient['PatientName'].split(' ')
        if len(name) == 2:
            body['FirstName'] = name[0]
            body['LastName'] = name[1]
        elif len(name) == 3:
            body['FirstName'] = name[0]
            body['MiddleName'] = name[1]
            body['LastName'] = name[2]
        elif len(name) == 4:
            body['FirstName'] = name[0]
            body['MiddleName'] = name[1] + ' ' + name[2]
            body['LastName'] = name[3]

        if patient['PatientMobile'].startswith('+1'):
            body['CurrentTimeZone'] = '-05:00'
            body['DefaultTimeZone'] = '-05:00'
        return body

    def update_patient(self, patient_user_id, update_patient_model):
        header = self.get_headers()
        response = requests.put(self.patient_url+patient_user_id, headers=header, data=json.dumps(update_patient_model))
        if response.status_code != 200:
            raise Exception('Unable to update patient')

    def get_schedule_create_model(self, patient_user_id, patient_name, patient, reminder_time, when_date):
        appointment_time = patient['AppointmentTime'].split(' ')
        hour, minute = appointment_time[0].split(':')
        rest = appointment_time[1]
        # appointment_time= '{}:{}:{}'.format(hour,minute,'00')
        raw_content = {
            "TemplateName": "appointment_msg",
            "Variables": {
                "en": [
                    {
                        "type": "text",
                        "text": "appointment"
                    },
                    {
                        "type": "text",
                        "text":  reminder_time
                    }
                ]
            },
            "ButtonIds": [
                "button_1",
                "button_2"
            ],
            # "ClientName": "GMU"
            "ClientName": "REAN_BOT",
            "AppointmentDate": patient['AppointmentTime']
        }

        return {
            'UserId': patient_user_id,
            # 'Name': 'Hey {}, you have an appointment schedule at {} with {}'.format(patient_name, patient['AppointmentTime'], patient['Provider']),
            'Name': 'appointment reminder',
            'WhenDate': when_date,
            'WhenTime': reminder_time,
            'NotificationType': 'WhatsApp',
            'RawContent':json.dumps(raw_content)
        }

    def schedule_reminder(self, schedule_create_model):
        header = self.get_headers()
        response = requests.post(self.reminder_url, headers=header, data=json.dumps(schedule_create_model))
        if response.status_code == 201:
            self.reminders_sent_count = self.reminders_sent_count + 1
        else:
            print('Unable to schedule reminder ', response.json())

    def get_time_in_24hrs(self, i):
        patient_ap_time = i['AppointmentTime']
        ap_time = patient_ap_time.split(' ')
        appointment_time = ap_time[0].split(':')
        rest = appointment_time[1]
        if ap_time[1] == "PM":
            new_app_time = int(appointment_time[0]) + int(12)
            newtime = str(new_app_time)
            if newtime.startswith('24'):
                newtime = '12'
                appointment = (str(newtime)+":"+rest+":00")
                # print("PM",appointment)
                return self.get_appointment_time(appointment)
            else:
                appointment = (str(newtime)+":"+rest+":00")
                # print("PM",appointment)
                return self.get_appointment_time(appointment)
        else:
            if appointment_time[0] == "12" or appointment_time[0] == "00":
                new_app_time = '00'
                appointment = (str(new_app_time)+":"+rest+":00")
                return self.get_appointment_time(appointment)
                # print("AM",appointment)
            else:
                appointment = str(appointment_time[0]+":"+rest+":00")
                # print("AM",appointment)
                return self.get_appointment_time(appointment)

    def get_appointment_time(self, time):
        appoint = str(time)
        time_str = appoint
        time_object = datetime.strptime(time_str, '%H:%M:%S').time()
        # print(type(time_object))
        # print(time_object)
        timestr = str(time_object)
        # print(type(timestr))
        t = timestr.split(':')
        hr = int(t[0])
        mn = int(t[1])
        sc = int(t[2])
        # second part
        time_1 = timedelta(hours=hr, minutes=mn, seconds=sc)
        time_2 = timedelta(hours=hr, minutes=mn, seconds=sc)
        delta = timedelta(minutes=10)
        return {'FirstTime': str(time_1 - delta), 'SecondTime': str(time_2 + delta)}
        # print(appoint)
        # print(time_1 - delta)
        # print(time_2 + delta)

    def get_headers(self, create_user = False):
        if create_user:
            return {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
        return {
            'Authorization': "Bearer " + self.access_token,
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def time_of_first_reminder(self, patient_mobile_number):
        temp = str(patient_mobile_number)
        if(temp.startswith('+1')):
            desired_timezone = 'America/Cancun' 
            utc_now = datetime.utcnow()
               # Convert UTC time to the desired time zone
            desired_timezone_obj = pytz.timezone(desired_timezone)
            current_time = utc_now.replace(tzinfo=pytz.utc).astimezone(desired_timezone_obj)
        if(temp.startswith('+91')):
            desired_timezone = 'Asia/Kolkata' 
            utc_now = datetime.utcnow()
               # Convert UTC time to the desired time zone
            desired_timezone_obj = pytz.timezone(desired_timezone)
            current_time = utc_now.replace(tzinfo=pytz.utc).astimezone(desired_timezone_obj)
       
        new_time = str(current_time + timedelta(minutes=20))
        date_element = new_time.split(' ')
        time_element = date_element[1].split('.')
        first_reminder_time = time_element[0]
        return first_reminder_time

    def summary(self):

        print('Appointments processed : ', self.appointments_processed_count)
        print('Appointments skipped   : ', self.appointments_skipped_count)
        print('Pending arrivals       : ', self.pending_arrival_count)
        print('Newly added patients   : ', self.new_patients_added_count)
        print('Reminders sent         : ', self.reminders_sent_count)

        result = {
            "Appointments processed": self.appointments_processed_count,
            "Appointments skipped"  : self.appointments_skipped_count,
            "Pending arrivals"      : self.pending_arrival_count,
            "Newly added patients"  : self.new_patients_added_count,
            "Reminders sent"        : self.reminders_sent_count,
        }
        return (result)

###############################################################
