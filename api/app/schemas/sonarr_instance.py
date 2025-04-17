# Standard library imports
from datetime import datetime
from typing import Optional

# Third-party imports
from pydantic import BaseModel, HttpUrl

class SonarrInstanceBase(BaseModel):
    name: str
    url: HttpUrl
    api_key: str

class SonarrInstanceCreate(SonarrInstanceBase):
    pass

class SonarrInstanceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None

class SonarrInstanceInDB(SonarrInstanceBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_checked: Optional[datetime]
    status: str
    error_message: Optional[str]

    class Config:
        orm_mode = True

class SonarrInstanceResponse(SonarrInstanceInDB):
    pass 