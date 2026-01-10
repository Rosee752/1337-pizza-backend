import uuid
from pydantic import BaseModel, ConfigDict
from app.database.models import SpicinessType

class SauceBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class SauceCreateSchema(SauceBaseSchema):
    name:str
    price:float
    spiciness:SpicinessType
    stock:int
    description:str

class SauceSchema(SauceCreateSchema):
    id:uuid.UUID

class SauceListItemSchema(SauceBaseSchema):
    id: uuid.UUID
    name: str
    price: float
    description: str
    spiciness: SpicinessType
    stock: int

