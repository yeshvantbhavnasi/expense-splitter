from sqlalchemy import Boolean, Column, ForeignKey, String, Float, DateTime, Text, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base

# Association table for group members
group_members = Table(
    'group_members',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE')),
    Column('group_id', UUID(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE')),
    extend_existing=True
)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    profile_picture_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses_paid = relationship("Expense", foreign_keys="[Expense.paid_by_id]", back_populates="paid_by")
    expense_splits = relationship("ExpenseSplit", back_populates="user")
    groups = relationship("Group", secondary=group_members, back_populates="members")
    settlements_paid = relationship("Settlement", foreign_keys="[Settlement.paid_by_id]", back_populates="paid_by")
    settlements_received = relationship("Settlement", foreign_keys="[Settlement.paid_to_id]", back_populates="paid_to")

class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")
    members = relationship("User", secondary=group_members, back_populates="groups")
    settlements = relationship("Settlement", back_populates="group", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    receipt_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    paid_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'))
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete='CASCADE'))

    # Relationships
    paid_by = relationship("User", foreign_keys=[paid_by_id], back_populates="expenses_paid")
    group = relationship("Group", back_populates="expenses")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    is_settled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id", ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'))

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="expense_splits")

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    paid_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'))
    paid_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'))
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete='CASCADE'))

    # Relationships
    paid_by = relationship("User", foreign_keys=[paid_by_id], back_populates="settlements_paid")
    paid_to = relationship("User", foreign_keys=[paid_to_id], back_populates="settlements_received")
    group = relationship("Group", back_populates="settlements")
