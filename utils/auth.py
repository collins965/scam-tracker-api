import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from database import get_db
from models import User

# Load environment variables from .env inside 'env/' folder
load_dotenv(dotenv_path="env/.env")

# === API KEY VERIFICATION SECTION ===

VALID_API_KEYS = [os.getenv("API_SECRET_KEY")]

def verify_api_key(x_api_key: str = Header(...)):
    """
    Verify the provided X-API-KEY header matches a valid API key.
    """
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")


# === JWT + PASSWORD AUTH SECTION ===

SECRET_KEY = os.getenv("API_SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    """
    Hash the given plain password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain password to a hashed one.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict) -> str:
    """
    Generate a JWT token with provided payload.
    """
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Decode the token, fetch the user, and ensure they are an approved admin.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token payload invalid")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized as admin")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
