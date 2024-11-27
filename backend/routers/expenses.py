from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
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
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    expenses = db.query(models.Expense).filter(
        models.Expense.group_id == group_id
    ).offset(skip).limit(limit).all()
    return expenses

@router.get("/balances", response_model=Dict[int, float])
def get_balances(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Calculate balances
    balances = {}
    for member in group.members:
        # Initialize balance for each member
        balances[member.id] = 0.0
    
    # Calculate amounts paid
    expenses = db.query(models.Expense).filter(
        models.Expense.group_id == group_id
    ).all()
    
    for expense in expenses:
        # Add amount to payer's balance
        balances[expense.paid_by_id] += float(expense.amount)
        
        # Subtract split amounts from each member's balance
        for split in expense.splits:
            balances[split.user_id] -= float(split.amount)
    
    return balances

@router.post("/", response_model=schemas.Expense)
def create_expense(
    group_id: int,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Check if specified paid_by user is in the group
    paid_by_user = db.query(models.User).filter(models.User.id == expense.paid_by_id).first()
    if not paid_by_user or paid_by_user not in group.members:
        raise HTTPException(status_code=400, detail="Specified payer is not in the group")
    
    # Create expense
    db_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        group_id=group_id,
        paid_by_id=expense.paid_by_id
    )
    db.add(db_expense)
    db.flush()

    # Create splits
    for split in expense.splits:
        db_split = models.ExpenseSplit(
            expense_id=db_expense.id,
            user_id=split.user_id,
            amount=split.amount
        )
        db.add(db_split)
    
    # Handle receipt upload if provided
    if hasattr(expense, 'receipt') and expense.receipt:
        # Generate unique filename
        file_extension = expense.receipt.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        upload_path = RECEIPTS_DIR / unique_filename
        
        # Save the file
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(expense.receipt.file, buffer)
    
    db.commit()
    return db_expense

# Then, define routes with expense_id parameter
@router.get("/{expense_id}", response_model=schemas.Expense)
def get_expense_details(
    group_id: int, 
    expense_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    # Fetch the expense with all related information
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Optional: Add additional authorization check if needed
    if expense.group_id != group_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")
    
    return expense

@router.post("/{expense_id}/receipt")
async def upload_receipt(
    group_id: int,
    expense_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if expense exists and user has access
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.group_id != group_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this expense")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    upload_path = RECEIPTS_DIR / unique_filename
    
    try:
        # Save the file
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update expense with receipt URL
        receipt_url = f"/static/receipts/{unique_filename}"
        expense.receipt_url = receipt_url
        db.commit()
        
        return {"receipt_url": receipt_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

@router.delete("/{expense_id}")
def delete_expense(
    group_id: int,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify group exists and user is a member
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Get the expense
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, 
        models.Expense.group_id == group_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Check if the current user is the one who created the expense
    if expense.paid_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the expense creator can delete it")
    
    # Delete associated splits first
    db.query(models.ExpenseSplit).filter(models.ExpenseSplit.expense_id == expense_id).delete()
    
    # Delete the expense
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}
