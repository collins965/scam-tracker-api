from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import LocationEntry
from uuid import uuid4
from pydantic import BaseModel
from utils.auth import verify_api_key
from typing import List

router = APIRouter()

class LocationLog(BaseModel):
    phone_number: str
    latitude: float
    longitude: float
    ip_address: str

@router.post("/location", dependencies=[Depends(verify_api_key)])
def log_location(data: LocationLog, db: Session = Depends(get_db)):
    entry = LocationEntry(
        id=str(uuid4()),
        phone_number=data.phone_number,
        latitude=data.latitude,
        longitude=data.longitude,
        ip_address=data.ip_address
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "data": entry}

@router.get("/location/{phone_number}", dependencies=[Depends(verify_api_key)])
def get_location(phone_number: str, db: Session = Depends(get_db)):
    entries = db.query(LocationEntry).filter_by(phone_number=phone_number).all()
    if not entries:
        raise HTTPException(status_code=404, detail="No data found for this number")
    return {"status": "success", "locations": entries}
