from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from uuid import UUID
import schemas
import models
from database import get_db
from auth import get_current_active_user
from datetime import datetime
from pathlib import Path
import shutil
import uuid
import os

# Create upload directories if they don't exist
UPLOAD_DIR = Path("uploads")
RECEIPTS_DIR = UPLOAD_DIR / "receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/groups/{group_id}/expenses",
    tags=["expenses"]
)

# First, define routes without expense_id parameter
@router.get("/", response_model=List[schemas.Expense])
def read_expenses(
    group_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    expenses = db.query(models.Expense).filter(
        models.Expense.group_id == group_id
    ).offset(skip).limit(limit).all()
    return expenses

@router.get("/balances", response_model=Dict[str, float])
def get_balances(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Initialize balances for all members
    balances = {str(member.id): 0.0 for member in group.members}
    
    # Calculate expenses
    expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    for expense in expenses:
        # Add amount paid by user
        balances[str(expense.paid_by_id)] += expense.amount
        # Subtract splits from respective users
        for split in expense.splits:
            balances[str(split.user_id)] -= split.amount
    
    return balances

@router.post("/", response_model=schemas.Expense)
def create_expense(
    group_id: UUID,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify all users in splits are group members
    member_ids = {member.id for member in group.members}
    for split in expense.splits:
        if split.user_id not in member_ids:
            raise HTTPException(
                status_code=400,
                detail=f"User {split.user_id} is not a member of the group"
            )
    
    # Create expense
    db_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        paid_by_id=expense.paid_by_id,
        group_id=group_id,
        date=datetime.utcnow()
    )
    db.add(db_expense)
    db.flush()  # Get the expense ID without committing
    
    # Create splits
    for split in expense.splits:
        db_split = models.ExpenseSplit(
            expense_id=db_expense.id,
            user_id=split.user_id,
            amount=split.amount
        )
        db.add(db_split)
    
    db.commit()
    db.refresh(db_expense)
    return db_expense

# Then, define routes with expense_id parameter
@router.get("/{expense_id}", response_model=schemas.Expense)
def get_expense_details(
    group_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.group_id == group_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user is a member of the group
    if current_user.id not in [member.id for member in expense.group.members]:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    return expense

@router.post("/{expense_id}/receipt")
def upload_receipt(
    group_id: UUID,
    expense_id: UUID,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify expense exists and user has access
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.group_id == group_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user is a member of the group
    if current_user.id not in [member.id for member in expense.group.members]:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Create unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = RECEIPTS_DIR / filename
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update expense with receipt URL
    expense.receipt_url = f"/uploads/receipts/{filename}"
    db.commit()
    
    return {"filename": filename}

@router.delete("/{expense_id}")
def delete_expense(
    group_id: UUID,
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify expense exists and user has access
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.group_id == group_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user is either the one who paid or a group admin
    if expense.paid_by_id != current_user.id and current_user.id != expense.group.members[0].id:
        raise HTTPException(
            status_code=403,
            detail="Only the expense creator or group admin can delete expenses"
        )
    
    # Delete receipt file if it exists
    if expense.receipt_url:
        receipt_path = UPLOAD_DIR / expense.receipt_url.lstrip("/uploads/")
        if receipt_path.exists():
            receipt_path.unlink()
    
    # Delete expense (cascade will handle splits)
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}
