from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import Base

class TrackLog(Base):
    __tablename__ = "track_logs"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    ip_address = Column(String)
    device_info = Column(String)
    location = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    reason = Column(String)
    is_approved = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
