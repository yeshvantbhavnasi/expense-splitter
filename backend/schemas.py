from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    is_active: bool
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Group schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    members: List[User]

    class Config:
        from_attributes = True

# Expense schemas
class ExpenseSplitBase(BaseModel):
    user_id: UUID
    amount: float

class ExpenseSplitCreate(ExpenseSplitBase):
    pass

class ExpenseSplit(ExpenseSplitBase):
    id: UUID
    expense_id: UUID
    is_settled: bool

    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    amount: float
    description: str
    group_id: UUID

class ExpenseCreate(ExpenseBase):
    paid_by_id: UUID
    splits: List[ExpenseSplitCreate]

class Expense(ExpenseBase):
    id: UUID
    date: datetime
    paid_by_id: UUID
    group_id: UUID
    receipt_url: Optional[str] = None
    splits: List[ExpenseSplit]

    class Config:
        from_attributes = True

# Settlement schemas
class SettlementCreate(BaseModel):
    paid_by_id: UUID
    paid_to_id: UUID
    amount: float
    group_id: UUID

class Settlement(BaseModel):
    id: UUID
    paid_by_id: UUID
    paid_to_id: UUID
    amount: float
    group_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SettlementResponse(BaseModel):
    settlement: Settlement
    message: str

# Balance schemas
class GroupBalances(BaseModel):
    user_id: UUID
    user_name: str
    profile_picture_url: Optional[str] = None
    balance: float

    class Config:
        from_attributes = True

class GroupSettlementSummary(BaseModel):
    balances: List[GroupBalances]
    suggested_settlements: List[Dict[str, Any]]

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
