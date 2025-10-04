from sqlalchemy.orm import Session
from app.models import User, OTP
from app.schemas import UserCreate
from app.utils import get_password_hash, generate_numeric_otp
from datetime import datetime, timedelta
from typing import Optional

# ---------------- Users ----------------
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(User).all()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: User, new_username: Optional[str] = None, new_password: Optional[str] = None) -> User:
    if new_username:
        user.username = new_username
    if new_password:
        user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()


# ---------------- OTP ----------------
def create_otp_for_user(db: Session, user: User, expire_minutes: int = 10) -> OTP:
    """
    Creates a new OTP for the given user.
    expire_minutes must be an integer (default: 10).
    """
    code = generate_numeric_otp()  # this is the OTP sent to user
    expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
    db_otp = OTP(user_id=user.id, code=code, expires_at=expires_at)
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp

def verify_user_otp(db: Session, email: str, code: str) -> bool:
    """
    Verifies if the OTP code for the user's email is valid and not expired.
    """
    user = get_user_by_email(db, email)
    if not user:
        return False

    otp_entry = db.query(OTP).filter(OTP.user_id == user.id, OTP.code == code).first()
    if not otp_entry:
        return False
    if otp_entry.expires_at < datetime.utcnow():
        return False
    return True

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user by email and password. Returns User if valid.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None

    from app.auth import verify_password
    if not verify_password(password, user.hashed_password):
        return None

    return user
