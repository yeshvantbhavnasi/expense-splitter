from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Group schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_at: datetime
    members: List[User]

    class Config:
        from_attributes = True

# Expense schemas
class ExpenseSplitBase(BaseModel):
    user_id: int
    amount: float

class ExpenseSplitCreate(ExpenseSplitBase):
    pass

class ExpenseSplit(ExpenseSplitBase):
    id: int
    expense_id: int
    is_settled: bool

    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    amount: float
    description: str
    group_id: int

class ExpenseCreate(ExpenseBase):
    paid_by_id: int
    splits: List[ExpenseSplitCreate]

class Expense(ExpenseBase):
    id: int
    date: datetime
    paid_by_id: int
    group_id: int
    receipt_url: Optional[str] = None
    splits: List[ExpenseSplit]

    class Config:
        from_attributes = True

# Settlement schemas
class SettlementCreate(BaseModel):
    paid_by_id: int
    paid_to_id: int
    amount: float
    group_id: int

class Settlement(SettlementCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SettlementResponse(BaseModel):
    settlement: Settlement
    message: str

# Balance schemas
class GroupBalances(BaseModel):
    user_id: int
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
