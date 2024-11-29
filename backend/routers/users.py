from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import schemas
import models
from database import get_db
from auth import get_password_hash, get_current_active_user
from sqlalchemy import or_
from datetime import datetime
from utils.s3 import upload_file_to_s3, delete_file_from_s3
import logging

logger = logging.getLogger(__name__)

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

@router.post("/me/profile-picture", response_model=schemas.User)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Starting profile picture upload for user {current_user.id}")
        logger.info(f"File info - filename: {file.filename}, content_type: {file.content_type}")

        # Read file content
        content = await file.read()
        content_type = file.content_type

        # Delete old profile picture if exists
        if current_user.profile_picture_url:
            try:
                logger.info(f"Deleting old profile picture: {current_user.profile_picture_url}")
                delete_file_from_s3(current_user.profile_picture_url)
            except Exception as e:
                logger.warning(f"Failed to delete old profile picture: {str(e)}")

        # Upload to S3
        logger.info("Uploading new profile picture to S3...")
        profile_picture_url = upload_file_to_s3(content, content_type, folder="profile-pictures")
        logger.info(f"Upload successful. New URL: {profile_picture_url}")
        
        # Update user profile picture URL
        current_user.profile_picture_url = profile_picture_url
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        logger.info("Profile picture update completed successfully")
        return current_user
    except Exception as e:
        logger.error(f"Profile picture upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
