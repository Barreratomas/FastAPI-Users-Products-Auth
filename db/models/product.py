from pydantic import BaseModel,Field, model_validator
from typing import Optional

class Product(BaseModel):
    id: Optional[str]=None
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    
    
    
class Product_update(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1)  
    description: Optional[str] = Field(None, min_length=1)  
    price: Optional[float] = Field(None, gt=0)  

    @model_validator(mode="before")
    def check_empy_fields(cls,values):
        for field, value in values.items():
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"El campo '{field}' no puede estar vacío.")
        return values