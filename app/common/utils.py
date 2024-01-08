import json
import os
import uuid
from pygments import highlight, lexers, formatters
from app.common.exceptions import UUIDValidationError

###############################################################################

def print_colorized_json(obj):
    jsonStr = json.dumps(obj.__dict__, default=str, indent=2)
    colored = highlight(jsonStr, lexers.JsonLexer(), formatters.TerminalFormatter())
    print(colored)

def validate_uuid4(uuid_str):
    try:
        val = uuid.UUID(uuid_str, version=4)
    except ValueError:
        raise UUIDValidationError("{uuid_str} is not valid UUID.")
    return uuid_str

def generate_uuid4():
    return str(uuid.uuid4())

def get_temp_filepath(file_name):
    temp_folder = os.path.join(os.getcwd(), "temp")
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)
    return os.path.join(temp_folder, file_name)

def validate_mobile(mobile):
        # if not bool(mobile.strip()) or not mobile.startswith('+1-'):
        if not bool(mobile.strip()):
            print('Invalid Mobile Number ', mobile)
            return False
        ten_digit = mobile.split('-')[1]
        if len(ten_digit) == 10 and ten_digit.isnumeric():
            return True