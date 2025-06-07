from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, TrackLog
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend requests (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API key verification dependency
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# Helper function: Get location from IP using ipinfo.io API
def get_location_from_ip(ip: str) -> str:
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}")
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country", "")
            loc = data.get("loc", "")  # latitude,longitude
            location_str = ", ".join(filter(None, [city, region, country]))
            if loc:
                location_str += f" (Coordinates: {loc})"
            return location_str or "Unknown Location"
        else:
            return "Unknown Location"
    except Exception as e:
        print(f"Error fetching location: {e}")
        return "Unknown Location"

@app.post("/track")
async def track_scammer(
    request: Request,
    db: Session = Depends(get_db),
    api=Depends(verify_api_key)
):
    body = await request.json()
    phone_number = body.get("phone_number", "unknown")
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")

    location = get_location_from_ip(ip)

    log = TrackLog(
        phone_number=phone_number,
        ip_address=ip,
        device_info=user_agent,
        location=location
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Tracking log saved", "id": log.id, "location": location}

@app.get("/logs")
def get_logs(db: Session = Depends(get_db), api=Depends(verify_api_key)):
    logs = db.query(TrackLog).order_by(TrackLog.timestamp.desc()).all()
    return logs

from fastapi import FastAPI
from routes import auth

app = FastAPI()

app.include_router(auth.router)
