import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_jwt_token, get_current_admin

router = APIRouter()

RECAPTCHA_SECRET_KEY = "6LdZNVgrAAAAAJu2X-b9hFXSJpc5Xw06FYnCmgx4"

def verify_recaptcha(token: str) -> bool:
    """Verify reCAPTCHA token with Google."""
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": token
    }
    resp = requests.post(url, data=payload)
    result = resp.json()
    # You can also check score and action for v3
    return result.get("success", False) and result.get("score", 0) >= 0.5 and result.get("action") == "submit"

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Expect recaptcha_token in the user object or extend schema accordingly
    recaptcha_token = getattr(user, 'recaptcha_token', None)
    if not recaptcha_token or not verify_recaptcha(recaptcha_token):
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA")

    if not any(term in user.reason.lower() for term in ["investigation", "fraud", "scam", "cyber", "law", "p.i."]):
        raise HTTPException(status_code=403, detail="Reason not valid enough")

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    hashed = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed, reason=user.reason)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Registration request submitted. Await admin approval."}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_approved:
        raise HTTPException(status_code=403, detail="Awaiting admin approval")

    token = create_jwt_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/approve-user/{user_id}")
def approve(user_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.commit()
    return {"message": "User approved"}
