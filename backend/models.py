from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

# Association table for group members
group_members = Table(
    'group_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('groups.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    profile_picture_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    expenses_paid = relationship("Expense", back_populates="paid_by")
    groups = relationship("Group", secondary=group_members, back_populates="members")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    members = relationship("User", secondary=group_members, back_populates="groups")
    settlements = relationship("Settlement", back_populates="group", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    paid_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receipt_url = Column(String(255), nullable=True)
    
    # Relationships
    group = relationship("Group", back_populates="expenses")
    paid_by = relationship("User", foreign_keys=[paid_by_id])
    splits = relationship("ExpenseSplit", back_populates="expense")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    is_settled = Column(Boolean, default=False)
    
    # Relationships
    expense = relationship("Expense", back_populates="splits")

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    paid_by_id = Column(Integer, ForeignKey("users.id"))
    paid_to_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paid_by = relationship("User", foreign_keys=[paid_by_id])
    paid_to = relationship("User", foreign_keys=[paid_to_id])
    group = relationship("Group", back_populates="settlements")
