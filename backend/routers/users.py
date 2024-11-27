from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import schemas
import models
from database import get_db
from auth import get_password_hash, get_current_active_user
from sqlalchemy import or_
import os
from datetime import datetime
import shutil
from pathlib import Path

# Create upload directories if they don't exist
UPLOAD_DIR = Path("uploads")
PROFILE_PICTURES_DIR = UPLOAD_DIR / "profile_pictures"
PROFILE_PICTURES_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/search", response_model=List[schemas.User])
def search_users(
    q: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    users = db.query(models.User).filter(
        or_(
            models.User.email.ilike(f"%{q}%"),
            models.User.full_name.ilike(f"%{q}%")
        )
    ).all()
    return users

@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{current_user.id}_{datetime.now().timestamp()}.{file_extension}"
        file_path = PROFILE_PICTURES_DIR / filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate URL
        url = f"/static/profile_pictures/{filename}"
        
        # Update user profile
        current_user.profile_picture_url = url
        db.commit()
        
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
