from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
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
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    group = db.query(models.Group).filter(
        models.Group.id == group_id
    ).options(
        joinedload(models.Group.members)
    ).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if current user is a member
    if current_user.id not in [member.id for member in group.members]:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    return group

@router.post("/{group_id}/members/{user_id}")
def add_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in group.members:
        raise HTTPException(status_code=400, detail="User already in group")
    
    group.members.append(user)
    db.commit()
    return {"message": "Member added successfully"}

@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Get the group with creator information
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if current user is the creator
    if group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the group creator can delete it")
    
    # Delete all expenses and their splits in the group
    expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    for expense in expenses:
        # Delete splits for each expense
        db.query(models.ExpenseSplit).filter(models.ExpenseSplit.expense_id == expense.id).delete()
        # Delete the expense
        db.delete(expense)
    
    # Delete group memberships
    db.query(models.group_members).filter(models.group_members.c.group_id == group_id).delete()
    
    # Delete the group
    db.delete(group)
    db.commit()
    
    return {"message": "Group deleted successfully"}
