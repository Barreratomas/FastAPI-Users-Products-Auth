from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional


class User(BaseModel):
    id: Optional[str] = None
    username: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    admin: bool = Field(default=False)
    disabled: bool = Field(default=False)
    password: Optional[str] = Field(None, min_length=2)
    
class User_update(BaseModel):
    username: Optional[str] = Field(None, min_length=1)
    full_name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    admin: Optional[bool] = None
    disabled: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=2)


    @model_validator(mode="before")
    def check_empty_fields(cls, values):
        for field, value in values.items():
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"El campo '{field}' no puede estar vacío.")
        return values