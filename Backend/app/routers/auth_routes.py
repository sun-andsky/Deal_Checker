# router/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.crud import (
    get_user_by_email, get_user_by_username, get_user, get_all_users,
    create_user, update_user, delete_user, create_otp_for_user,
    verify_user_otp, authenticate_user
)
from app.utils import send_email
from app.auth import create_access_token, get_current_active_user
from app.schemas import UserCreate, UserUpdate, UserOut, LoginSchema, Token, OTPVerify

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------- Signup with OTP ----------
@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if email or username already exists
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = create_user(db, user_in)

    # Create OTP for user
    otp_entry = create_otp_for_user(db, user)  # expires in 10 mins by default

    # Send OTP email in background
    subject = "Your verification OTP"
    body = f"Hello {user.username},\n\nYour OTP is: {otp_entry.code}\nIt expires in 10 minutes."
    background_tasks.add_task(send_email, user.email, subject, body)

    return user


# ---------- Verify OTP ----------
@router.post("/verify-otp")
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    ok = verify_user_otp(db, payload.email, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"detail": "Email verified successfully"}


# ---------- Login ----------
@router.post("/login", response_model=Token)
def login(body: LoginSchema, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}


# ---------- User CRUD ----------
@router.get("/users", response_model=list[UserOut])
def read_users(db: Session = Depends(get_db)):
    return get_all_users(db)


@router.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user_data(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = update_user(db, user, payload.username, payload.password)
    return updated


@router.delete("/users/{user_id}")
def delete_user_data(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(db, user)
    return {"detail": "User deleted"}
