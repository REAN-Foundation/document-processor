from datetime import datetime
from typing import List, Optional
from pydantic import UUID4, BaseModel, Field

class BaseResponseModel(BaseModel):
    Message : str 
    Data : dict[str,int]

