"""
Database models - SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class CardStatus(str, enum.Enum):
    NORMAL = "Normal"
    FROZEN = "Frozen"
    LOST = "Reported Lost"


class TransactionType(str, enum.Enum):
    TRANSFER_IN = "Transfer In"
    TRANSFER_OUT = "Transfer Out"
    PURCHASE = "Purchase"
    REDEEM = "Redeem"
    SUBSCRIPTION = "Subscription"
    REFUND = "Refund"


class AuditLog(Base):
    """Audit log table"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), default="current_user")
    operation = Column(String(100))
    tool_name = Column(String(100))
    params = Column(Text)
    risk_level = Column(String(20))
    mfa_status = Column(String(20))
    result = Column(String(20))
    intent = Column(Text)
    decision_chain = Column(Text)
    error_message = Column(Text, nullable=True)


class Account(Base):
    """Account table"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(200))
    name = Column(String(100))
    phone = Column(String(20))
    balance = Column(Float, default=0.0)
    daily_transfer_total = Column(Float, default=0.0)
    last_transfer_date = Column(String(20))
    risk_score = Column(Float, default=0.0)
    is_locked = Column(Boolean, default=False)
    lock_reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class BankCard(Base):
    """Bank card table"""
    __tablename__ = "bank_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    card_number = Column(String(20), unique=True)
    card_name = Column(String(100))
    card_type = Column(String(20))
    balance_or_limit = Column(Float, default=0.0)
    status = Column(String(20), default=CardStatus.NORMAL.value)
    cvv = Column(String(4), default="123")


class Transaction(Base):
    """Transaction table"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    transaction_type = Column(String(20))
    amount = Column(Float)
    counterparty = Column(String(100))
    counterparty_bank = Column(String(100), nullable=True)
    memo = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True)
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.now)


class Product(Base):
    """Product table"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    tag = Column(String(50))
    description = Column(Text)
    annual_rate = Column(String(20))
    risk_level = Column(Integer)
    min_amount = Column(Float, default=1000.0)
    category = Column(String(50))


class Portfolio(Base):
    """Portfolio table"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    amount = Column(Float)
    purchase_date = Column(DateTime, default=datetime.now)
    current_value = Column(Float)
    profit_loss = Column(Float)


class Subscription(Base):
    """Subscription table"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    name = Column(String(100))
    logo = Column(String(10))
    cycle = Column(String(20))
    amount = Column(Float)
    next_date = Column(String(20))
    is_active = Column(Boolean, default=True)


class AutoRule(Base):
    """Auto rule table"""
    __tablename__ = "auto_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    trigger = Column(String(200))
    action = Column(Text)
    amount = Column(Float, nullable=True)
    days_before = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class Contact(Base):
    """Contact table"""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("accounts.user_id"))
    name = Column(String(100))
    phone = Column(String(20), nullable=True)
    bank = Column(String(100), nullable=True)
    card_number = Column(String(30), nullable=True)
    memo = Column(String(200), nullable=True)
