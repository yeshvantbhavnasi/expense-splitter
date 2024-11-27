from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID
import schemas
import models
from database import get_db
from auth import get_current_active_user

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_group = models.Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Add the creator as a member after the group is created
    db_group.members.append(current_user)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/", response_model=List[schemas.Group])
def read_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    groups = db.query(models.Group).filter(
        models.Group.members.any(id=current_user.id)
    ).offset(skip).limit(limit).all()
    return groups

@router.get("/{group_id}", response_model=schemas.Group)
def read_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).options(
        joinedload(models.Group.members)
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/{group_id}/members/{user_id}")
def add_member(
    group_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    group.members.append(user)
    db.commit()
    return {"message": "Member added successfully"}

@router.delete("/{group_id}")
def delete_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if the current user is the creator (first member)
    if group.members[0].id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the group creator can delete the group"
        )
    
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}
