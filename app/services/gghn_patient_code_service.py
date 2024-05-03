
import json
import os

import requests
from app.common.cache import cache
from app.common.exceptions import HTTPError, NotFound
from app.common.utils import get_temp_filepath
###########################################################
class ExtractPatientCode:
    def __init__(self):
        summary_data=[]
        self.patient_code_count = 0
        self.appointment_details= []

        gghn_base_url = os.getenv("GGHN_BASE_URL")
        if gghn_base_url == None:
            raise Exception('GGHN_BASE_URL is not set')
        
        self.patient_code_url = str(gghn_base_url + "/api/PharmacyPickup")
        self.token = cache.get('gghn_access_token')
        print("gghn token----",self.token)

    #Get Paitient details using gghn api   
    def read_content(self, date):
        try:
            self.token = cache.get('gghn_access_token')
            suburl = str(f'/QueryPatientByNextAppointment?startdate={date}T00:00:00&endDate={date}T23:59:59')
            url=str(self.patient_code_url+suburl)
            print("Patient code url----",url)
       
            headers = {
            'Authorization': "Bearer " + self.token,
            # 'Content-Type': 'application/json'
            }
            try:
                response = requests.post(url,headers = headers)
                result = response.json()
            except HTTPError as e:
                print(f"HTTP Error {e.status_code}: {e.message}")

            print("result of post---",result)
            prefix="gghn_details_"
            file_name = self.create_data_file(result,date,prefix)
            appointment_file=self.extract_appointment(file_name,date)
            return (result)
        except HTTPError:
            raise NotFound(status_code=404, detail="Resource not found")

    #Create/update a detail file of api out put 
    def create_data_file(self,resp_data,enquiry_date,prefix):
        filename=str(prefix+enquiry_date+'.json')
        f_path=(os.getcwd()+"/temp/"+filename)
        if os.path.exists(f_path):
            print(f"The file {filename} already exists!")
            if(prefix=='gghn_details_'):
                self.update_content(filename,resp_data,enquiry_date,prefix)
            else:
                with open(f_path, 'w') as json_file:
                         json.dump(resp_data, json_file, indent=25)
                return(filename)
        else: 
            temp_folder = os.path.join(os.getcwd(), "temp")
            if not os.path.exists(temp_folder):
                os.mkdir(temp_folder)
            filepresent  = os.path.join(temp_folder, filename)
            with open(filepresent, 'w') as json_file:
                json.dump(resp_data, json_file, indent=25)
        return(filename)        
      
    #Create a file with only necessary details for appointment    
    def extract_appointment(self, file_name,date):

        filepath = get_temp_filepath(file_name)
        if not os.path.exists(filepath):
            raise Exception(file_name + " does not exist.")

        file=open(filepath,"r")
        file_content=file.read()
        appointment_data=json.loads(file_content)
        appointment_details= []
        for data in appointment_data:
            patient_code_details={
                "facilityname":data['facilityname'],
                "next_appointment_date":data['next_appointment_date'],
                "participant_code":data['participant_code'],
                "paitient_phone":""
            }
            appointment_details.append(patient_code_details)
            self.patient_code_count= self.patient_code_count+1
        print("patient_code_count",self.patient_code_count)
        # print("appointments-----",appointment_details)  
        prefix = "gghn_appointment_"  
        file_name = self.create_data_file(appointment_details,date,prefix)
      
    def update_content(self,filename,resp_data,enquiry_date,prefix):
        additional_data=[]
        try:
            filepath = get_temp_filepath(filename)
            with open(filepath, 'r') as file:
                file_data = json.load(file)
        except Exception as e:
            # Handle other exceptions
            print(f"An unexpected error occurred while reading file{filename}: {e}")
        # print("file data...",file_data)
        # print("resp_data...",resp_data)
        flag=0
        for rdata in resp_data:
            flag=0
            for fdata in file_data:
                if rdata['participant_code'] == fdata['participant_code']:
                    flag=1
                # print("value of flag",flag)  
            if flag==0:
                additional_paitient={
                                 "state": rdata['state'],
                                 "facilityname": rdata['facilityname'],
                                 "sex": rdata['sex'],
                                 "age":rdata['age'],
                                 "art_start_date": rdata['art_start_date'],
                                 "last_pickup_date": rdata['last_pickup_date'],
                                 "months_of_arv_refill": rdata['months_of_arv_refill'],
                                 "next_appointment_date":rdata['next_appointment_date'],
                                 "current_art_regimen": rdata['current_art_regimen'],
                                 "clinical_staging_at_last_visit": rdata['clinical_staging_at_last_visit'],
                                 "last_cd4_count": rdata['last_cd4_count'],
                                 "current_viral_load":rdata['current_viral_load'],
                                 "viral_load_status": rdata['viral_load_status'],
                                 "current_art_status": rdata['current_art_status'],
                                 "outcome_of_last_tb_screening":rdata['outcome_of_last_tb_screening'],
                                 "date_started_on_tb_treatment":rdata['date_started_on_tb_treatment'],
                                 "tb_treatment_type":rdata['tb_treatment_type'],
                                 "tb_treatment_completion_date": rdata['tb_treatment_completion_date'],
                                 "tb_treatment_outcome":rdata['tb_treatment_outcome'],
                                 "date_of_commencement_of_eac":rdata['date_of_commencement_of_eac'],
                                 "number_of_eac_sessions_completed": rdata['number_of_eac_sessions_completed'],
                                 "result_of_cervical_cancer_screening": rdata['result_of_cervical_cancer_screening'],
                                 "fingerprint_captured":rdata['fingerprint_captured'],
                                 "fingerprint_recaptured":rdata['fingerprint_recaptured'], 
                                 "participant_code":rdata['participant_code']
                                 }
                # print(type(additional_paitient))
                # print(type(additional_data))
                additional_data.append(additional_paitient)
           
        print("additional paitients are",additional_data)
        print(type(file_data))
        file_data.extend(additional_data)
        try:
            filepath = get_temp_filepath(filename)
            with open(filepath, 'w') as json_file:
                json.dump(file_data, json_file, indent=25)
            return(filename)
        except Exception as e:
        # Handle other exceptions
            print(f"An unexpected error occurred while writing into file{filename}: {e}")

       


            