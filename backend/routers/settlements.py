from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID

import database
import auth
import schemas
import models

router = APIRouter(prefix="/settlements", tags=["settlements"])

@router.post("", response_model=schemas.SettlementResponse)
def create_settlement(
    settlement: schemas.SettlementCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
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
    group_id: UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Get group and verify user is a member
    group = db.query(models.Group).filter(
        models.Group.id == group_id,
        models.Group.members.any(id=current_user.id)
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Calculate balances for each member
    balances = {}
    for member in group.members:
        balances[member.id] = {
            "user_id": member.id,
            "user_name": member.full_name,
            "profile_picture_url": member.profile_picture_url,
            "balance": 0.0
        }

    # Calculate expenses
    expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    for expense in expenses:
        # Add amount paid by user
        balances[expense.paid_by_id]["balance"] += expense.amount
        
        # Subtract splits from respective users
        for split in expense.splits:
            balances[split.user_id]["balance"] -= split.amount

    # Calculate settlements
    settlements = db.query(models.Settlement).filter(models.Settlement.group_id == group_id).all()
    for settlement in settlements:
        balances[settlement.paid_by_id]["balance"] += settlement.amount
        balances[settlement.paid_to_id]["balance"] -= settlement.amount

    # Convert balances dict to list
    balance_list = list(balances.values())

    # Calculate suggested settlements
    suggested_settlements = []
    debtors = [b for b in balance_list if b["balance"] < -0.01]  # Those who owe money
    creditors = [b for b in balance_list if b["balance"] > 0.01]  # Those who are owed money

    debtors.sort(key=lambda x: x["balance"])  # Sort by balance ascending (most negative first)
    creditors.sort(key=lambda x: x["balance"], reverse=True)  # Sort by balance descending (most positive first)

    for debtor in debtors:
        while debtor["balance"] < -0.01 and creditors:  # While debtor still owes money
            creditor = creditors[0]
            if creditor["balance"] < 0.01:  # If creditor has been fully paid
                creditors.pop(0)
                continue

            # Calculate settlement amount
            amount = min(-debtor["balance"], creditor["balance"])
            if amount > 0:
                suggested_settlements.append({
                    "from_user": {
                        "id": debtor["user_id"],
                        "name": debtor["user_name"]
                    },
                    "to_user": {
                        "id": creditor["user_id"],
                        "name": creditor["user_name"]
                    },
                    "amount": round(amount, 2)
                })

                # Update balances
                debtor["balance"] += amount
                creditor["balance"] -= amount

    return {
        "balances": balance_list,
        "suggested_settlements": suggested_settlements
    }
