import os
import json
import shutil
import requests
from app.common.utils import validate_mobile

class AdminNotification:
    def __init__(self):
        whatsapp_url = os.getenv("NOTIFICATION_URL") 
        whatsapp_id =  os.getenv("WHATSAPP_PHONE_ID")
        whatsapp_token = os.getenv("WHATSAPP_TOKEN")
        self.notification_base_url = str(whatsapp_url+whatsapp_id+"/messages")
        if self.notification_base_url == None:
            raise Exception('notification_base_url is not set')
        
        self.notification_token = "Bearer " + whatsapp_token

    def admin_notify(self,reminder_date,summary):
        print('Sending message to admins')
        file_name = 'GMU_admin.json'
        current_path = os.getcwd()
        folder_path = os.path.join(current_path, "../", "temp")
        exists = os.path.exists(folder_path)
        if exists:
            file_path = os.path.join(folder_path,file_name)
            print(file_path)
            file=open(file_path,"r")
            file_content=file.read()
            file_data=json.loads(file_content)
            for line in file_data:
                admin_phone = (line['Phone'])
                is_valid_mobile = validate_mobile(admin_phone)
                if not is_valid_mobile:
                    print('*Invalid phone-number - ', admin_phone)
                phone_nos=self.reform(admin_phone)
                print(phone_nos)
                self.send_whatapp_to_GMU_admin(phone_nos,reminder_date,summary)  

    def send_whatapp_to_GMU_admin(self,phone_nos,reminder_date,summary):
        total_patient = summary['Appointments processed']
        # reminder_set = round(int(summary['Reminders sent'])/2)
        reminder_set = round(int(summary['Reminders sent']))
        reminders = str(reminder_set)
        header = self.get_notification_headers()
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_nos,
            "type": "template",
                "template": {
                "name": "hospital_appointment_message",
                "language": {
                    "code": "en"
                },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                    {
                        "type": "text",
                        "text": reminder_date
                    },
                    {
                        "type": "text",
                        "text": total_patient
                    },
                    {
                        "type": "text",
                        "text": reminders
                    }
                ]
            }
        ]
    }
}
        response = requests.post(self.notification_base_url, headers=header, data=json.dumps(body))
        if response:
            print(response)
        else:
            print('Unable  ', response.json())

    def get_notification_headers(self): 
        return {    
            'Authorization':self.notification_token,
            'Content-Type': 'application/json'
            }
        
    def reform(self,phone):
        temp = phone.replace("+", "")
        temp = temp.replace("-","")
        temp = temp.replace("(","")
        temp = temp.replace(")","")
        return temp
    