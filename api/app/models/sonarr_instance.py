from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class SonarrInstance(Base):
    __tablename__ = "sonarr_instances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String)
    api_key = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True))
    status = Column(String, default="unknown")  # online, offline, error
    error_message = Column(String, nullable=True)

    def __repr__(self):
        return f"<SonarrInstance(name='{self.name}', url='{self.url}')>" 