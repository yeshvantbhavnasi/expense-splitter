from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

import database
import auth
import schemas
import models

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.post("", response_model=schemas.SettlementResponse)
def create_settlement(
    settlement: schemas.SettlementCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Verify users are in the group
    group = db.query(models.Group).filter(models.Group.id == settlement.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    member_ids = [member.id for member in group.members]
    if settlement.paid_by_id not in member_ids or settlement.paid_to_id not in member_ids:
        raise HTTPException(status_code=400, detail="Both users must be members of the group")
    
    # Create settlement record
    db_settlement = models.Settlement(
        paid_by_id=settlement.paid_by_id,
        paid_to_id=settlement.paid_to_id,
        amount=settlement.amount,
        group_id=settlement.group_id
    )
    db.add(db_settlement)
    db.commit()
    db.refresh(db_settlement)
    
    return {
        "settlement": db_settlement,
        "message": "Settlement recorded successfully"
    }

@router.get("/group/{group_id}/balances", response_model=schemas.GroupSettlementSummary)
def get_group_balances(
    group_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Get group and verify user is a member
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if current_user.id not in [member.id for member in group.members]:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Calculate balances
    balances: Dict[int, float] = {member.id: 0.0 for member in group.members}
    
    # Add expenses
    for expense in group.expenses:
        # Add amount paid by user
        balances[expense.paid_by_id] += expense.amount
        
        # Subtract splits from each user
        for split in expense.splits:
            balances[split.user_id] -= split.amount
    
    # Subtract settlements
    settlements = db.query(models.Settlement).filter(models.Settlement.group_id == group_id).all()
    for settlement in settlements:
        balances[settlement.paid_by_id] += settlement.amount
        balances[settlement.paid_to_id] -= settlement.amount
    
    # Convert balances to response format
    balance_response = []
    for member in group.members:
        balance_response.append({
            "user_id": member.id,
            "user_name": member.full_name,
            "profile_picture_url": member.profile_picture_url,
            "balance": round(balances[member.id], 2)
        })
    
    # Calculate suggested settlements
    suggested_settlements = []
    debtors = [(uid, bal) for uid, bal in balances.items() if bal < -0.01]
    creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0.01]
    
    debtors.sort(key=lambda x: x[1])  # Sort by amount owed (ascending)
    creditors.sort(key=lambda x: x[1], reverse=True)  # Sort by amount owed (descending)
    
    while debtors and creditors:
        debtor_id, debt = debtors[0]
        creditor_id, credit = creditors[0]
        
        # Get the smaller of the two amounts
        amount = min(abs(debt), credit)
        
        if amount >= 0.01:  # Only suggest settlements worth at least 1 cent
            debtor = next(m for m in group.members if m.id == debtor_id)
            creditor = next(m for m in group.members if m.id == creditor_id)
            
            suggested_settlements.append({
                "paid_by_id": debtor_id,
                "paid_by_name": debtor.full_name,
                "paid_to_id": creditor_id,
                "paid_to_name": creditor.full_name,
                "amount": round(amount, 2)
            })
            
            # Update remaining balances
            debtors[0] = (debtor_id, debt + amount)
            creditors[0] = (creditor_id, credit - amount)
            
            # Remove settled balances
            if abs(debtors[0][1]) < 0.01:
                debtors.pop(0)
            if abs(creditors[0][1]) < 0.01:
                creditors.pop(0)
    
    return {
        "balances": balance_response,
        "suggested_settlements": suggested_settlements
    }
