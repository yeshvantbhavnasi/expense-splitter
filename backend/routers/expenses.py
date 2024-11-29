from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from uuid import UUID
import schemas
import models
from database import get_db
from auth import get_current_active_user
from datetime import datetime
from utils.s3 import upload_file_to_s3, delete_file_from_s3

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

@router.get("/balances", response_model=schemas.GroupSettlementSummary)
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
    balances_dict = {str(member.id): 0.0 for member in group.members}
    
    # Calculate expenses
    expenses = (
        db.query(models.Expense)
        .filter(models.Expense.group_id == group_id)
        .all()
    )
    
    for expense in expenses:
        # Add the full amount to the person who paid
        balances_dict[str(expense.paid_by_id)] += float(expense.amount)
        
        # Get all splits for this expense
        splits = db.query(models.ExpenseSplit).filter(
            models.ExpenseSplit.expense_id == expense.id
        ).all()
        
        # Subtract each person's split amount
        for split in splits:
            balances_dict[str(split.user_id)] -= float(split.amount)
    
    # Calculate settlements
    settlements = (
        db.query(models.Settlement)
        .filter(models.Settlement.group_id == group_id)
        .all()
    )
    
    for settlement in settlements:
        # When someone pays a settlement, their balance increases (they've paid what they owed)
        balances_dict[str(settlement.paid_by_id)] += float(settlement.amount)
        # The person receiving the settlement has their balance decrease (they've been paid what they were owed)
        balances_dict[str(settlement.paid_to_id)] -= float(settlement.amount)
    
    # Round balances to 2 decimal places to avoid floating point issues
    balances_dict = {k: round(v, 2) for k, v in balances_dict.items()}
    
    # Convert balances dict to list of GroupBalances objects
    balances = []
    for member in group.members:
        member_id = str(member.id)
        balances.append({
            "user_id": member.id,
            "user_name": member.full_name,
            "profile_picture_url": member.profile_picture_url,
            "balance": balances_dict[member_id]
        })
    
    # Calculate suggested settlements
    suggested_settlements = []
    debtors = [(str(b["user_id"]), b["balance"], b["user_name"]) 
               for b in balances if b["balance"] < 0]
    creditors = [(str(b["user_id"]), b["balance"], b["user_name"]) 
                 for b in balances if b["balance"] > 0]
    
    # Sort by absolute amount to settle larger debts first
    debtors.sort(key=lambda x: abs(x[1]), reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)
    
    while debtors and creditors:
        debtor_id, debt, debtor_name = debtors[0]
        creditor_id, credit, creditor_name = creditors[0]
        
        # Calculate settlement amount
        amount = min(abs(debt), credit)
        
        if amount > 0.01:  # Only suggest settlements above 1 cent
            suggested_settlements.append({
                "paid_by_id": debtor_id,
                "paid_by_name": debtor_name,
                "paid_to_id": creditor_id,
                "paid_to_name": creditor_name,
                "amount": round(amount, 2)
            })
        
        # Update remaining balances
        new_debt = debt + amount
        new_credit = credit - amount
        
        if abs(new_debt) < 0.01:  # Debt fully settled
            debtors.pop(0)
        else:
            debtors[0] = (debtor_id, new_debt, debtor_name)
            
        if new_credit < 0.01:  # Credit fully used
            creditors.pop(0)
        else:
            creditors[0] = (creditor_id, new_credit, creditor_name)
    
    return {
        "balances": balances,
        "suggested_settlements": suggested_settlements
    }

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
    member_ids = {str(member.id) for member in group.members}
    for split in expense.splits:
        if str(split.user_id) not in member_ids:
            raise HTTPException(
                status_code=400,
                detail=f"User {split.user_id} is not a member of the group"
            )
    
    # Validate split amounts sum up to total expense amount
    total_split = sum(float(split.amount) for split in expense.splits)
    if abs(total_split - float(expense.amount)) > 0.01:
        raise HTTPException(
            status_code=400,
            detail="Split amounts must equal the total expense amount"
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
            amount=float(split.amount)  # Ensure amount is stored as float
        )
        db.add(db_split)
    
    try:
        db.commit()
        db.refresh(db_expense)
        return db_expense
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

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

@router.post("/{expense_id}/receipt", response_model=schemas.Expense)
async def upload_receipt(
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
    
    try:
        # Read file content
        content = await file.read()

        # Delete old receipt if exists
        if expense.receipt_url:
            try:
                delete_file_from_s3(expense.receipt_url)
            except:
                pass  # Ignore if old file doesn't exist

        # Upload to S3
        receipt_url = upload_file_to_s3(content, file.content_type, folder="receipts")
        
        # Update expense with receipt URL
        expense.receipt_url = receipt_url
        expense.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(expense)
        
        return expense
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{expense_id}")
async def delete_expense(
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
    
    # Delete receipt from S3 if exists
    if expense.receipt_url:
        try:
            delete_file_from_s3(expense.receipt_url)
        except:
            pass  # Ignore if file doesn't exist
    
    # Delete expense (cascade will handle splits)
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}
