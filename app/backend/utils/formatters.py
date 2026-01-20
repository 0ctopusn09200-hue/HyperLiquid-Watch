"""
Utility functions for formatting data to match frontend expectations
"""
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal


def format_relative_time(timestamp: datetime) -> str:
    """Format timestamp to relative time string (e.g., '2 min ago')"""
    now = datetime.utcnow()
    if timestamp.tzinfo:
        now = now.replace(tzinfo=timestamp.tzinfo)
    
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        seconds = int(diff.total_seconds())
        return f"{seconds} sec ago" if seconds > 1 else "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} min ago" if minutes > 1 else "1 min ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hr ago" if hours > 1 else "1 hr ago"
    elif diff.days < 30:
        days = diff.days
        return f"{days} days ago" if days > 1 else "1 day ago"
    else:
        return timestamp.strftime("%Y-%m-%d")


def truncate_address(address: str, start: int = 6, end: int = 4) -> str:
    """Truncate wallet address (e.g., '0x742d35...f0bEb')"""
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"


def format_token_amount(amount: Decimal, token: str, decimals: int = 8) -> str:
    """Format token amount (e.g., '28.40572 BTC')"""
    # Round to reasonable precision
    amount_float = float(amount)
    if amount_float >= 1:
        formatted = f"{amount_float:.5f}".rstrip('0').rstrip('.')
    else:
        formatted = f"{amount_float:.8f}".rstrip('0').rstrip('.')
    return f"{formatted} {token}"


def format_currency(value: Decimal, unit: str = "USD") -> str:
    """Format currency value (e.g., '$717M', '$1.2K')"""
    value_float = float(value)
    
    if value_float >= 1_000_000_000:
        return f"${value_float / 1_000_000_000:.2f}B"
    elif value_float >= 1_000_000:
        return f"${value_float / 1_000_000:.0f}M"
    elif value_float >= 1_000:
        return f"${value_float / 1_000:.1f}K"
    else:
        return f"${value_float:.2f}"


def parse_position_side(side: str) -> tuple:
    """
    Parse position side and type from activity_type or side field
    Returns: (side: "Long"|"Short", type: "Open"|"Close")
    """
    side_upper = side.upper()
    
    # Map common patterns
    if "LONG" in side_upper or side_upper == "L":
        pos_side = "Long"
    elif "SHORT" in side_upper or side_upper == "S":
        pos_side = "Short"
    else:
        pos_side = None
    
    # For type, check tx_type or activity_type
    # This is a simplified mapping, may need adjustment based on actual data
    pos_type = None  # Will be determined from transaction context
    
    return pos_side, pos_type
