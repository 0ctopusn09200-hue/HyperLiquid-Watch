"""
Service layer for transaction operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from models import Transaction
from schemas import TransactionResponse


def get_transactions(
    db: Session,
    user_address: Optional[str] = None,
    coin: Optional[str] = None,
    side: Optional[str] = None,
    tx_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[TransactionResponse], int]:
    """Get transactions with pagination"""
    query = db.query(Transaction)
    
    if user_address:
        query = query.filter(Transaction.user_address == user_address)
    if coin:
        query = query.filter(Transaction.coin == coin)
    if side:
        query = query.filter(Transaction.side == side)
    if tx_type:
        query = query.filter(Transaction.tx_type == tx_type)
    if start_time:
        query = query.filter(Transaction.block_timestamp >= start_time)
    if end_time:
        query = query.filter(Transaction.block_timestamp <= end_time)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    transactions = query.order_by(desc(Transaction.block_timestamp)).offset(offset).limit(page_size).all()
    
    return [TransactionResponse.model_validate(tx) for tx in transactions], total


def get_transaction_by_hash(
    db: Session,
    tx_hash: str
) -> Optional[TransactionResponse]:
    """Get transaction by hash"""
    transaction = db.query(Transaction).filter(Transaction.tx_hash == tx_hash).first()
    
    if transaction:
        return TransactionResponse.model_validate(transaction)
    return None
