"""
Initialize database schema
Run this script to create all tables in the database
"""
from database import engine, Base
from models import (
    Transaction, Liquidation, LongShortRatio, 
    LiquidationMap, Position, WhaleWatch, WhaleActivity
)

def init_database():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
