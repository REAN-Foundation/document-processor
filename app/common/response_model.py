from pydantic import UUID4, BaseModel, Field, parse_obj_as
from datetime import datetime
from enum import Enum
import json
from typing import TypeVar, Generic
from pydantic.generics import GenericModel
import uuid
from pygments import highlight, lexers, formatters

T = TypeVar("T")

class ResponseStatusTypes(str, Enum):
    Success = "Success"
    Failure = "Failure"
    Error = "Error"

class ResponseModel(GenericModel, Generic[T]):
    Status: ResponseStatusTypes = Field(description="Status of the response", default=ResponseStatusTypes.Success)
    Message: str
    Data: dict[str,int]| None = None
