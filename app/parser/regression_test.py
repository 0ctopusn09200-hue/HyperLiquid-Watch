"""
Regression Test for Parser Service
Validates that parse_trade() backward compatibility is maintained
"""
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Mock trade data (fixed test case)
MOCK_TRADE = {
    "coin": "BTC",
    "side": "B",
    "px": "45000.50",
    "sz": "1.5",
    "time": 1706443800000,  # 2024-01-28 10:30:00 UTC
    "hash": "0xabcdef1234567890",
    "tid": 12345,
    "users": ["0x1111111111111111111111111111111111111111", "0x2222222222222222222222222222222222222222"]
}

MOCK_RAW_DATA = {
    "channel": "trades",
    "data": [MOCK_TRADE]
}

# Expected OLD fields (must match exactly)
EXPECTED_OLD_FIELDS = {
    "coin": "BTC",
    "side": "LONG",  # B -> LONG mapping
    "size": "1.5",
    "price": "45000.50",
    "tx_type": "ORDER",
    "block_number": 0,
    "user_address": "UNKNOWN",  # trades don't have single user field
}

def test_parse_trade_backward_compatibility():
    """Test that parse_trade maintains backward compatibility"""
    print("\n" + "="*60)
    print("Regression Test: parse_trade Backward Compatibility")
    print("="*60)
    
    # Import main service
    try:
        from main import ParserService
    except ImportError:
        print("✗ Failed to import ParserService")
        return False
    
    # Create service instance
    service = ParserService()
    
    # Parse the mock trade
    result = service.parse_trade(MOCK_TRADE, MOCK_RAW_DATA)
    
    if not result:
        print("✗ parse_trade returned None")
        return False
    
    print("\n📋 Parsed Result:")
    print(json.dumps(result, indent=2, default=str))
    
    # Validate OLD fields (must match exactly)
    print("\n🔍 Validating OLD fields (backward compatibility):")
    all_passed = True
    
    for field, expected_value in EXPECTED_OLD_FIELDS.items():
        actual_value = result.get(field)
        
        # Convert Decimal to string for comparison
        if isinstance(actual_value, Decimal):
            actual_value = str(actual_value)
        
        if actual_value == expected_value:
            print(f"  ✓ {field}: {actual_value} == {expected_value}")
        else:
            print(f"  ✗ {field}: {actual_value} != {expected_value}")
            all_passed = False
    
    # Validate required fields exist
    print("\n🔍 Validating required fields exist:")
    required_fields = ["tx_hash", "block_timestamp", "fee", "raw_data"]
    
    for field in required_fields:
        if field in result:
            value = result[field]
            if field == "tx_hash":
                if value.startswith("0x") and len(value) == 66:
                    print(f"  ✓ {field}: {value[:10]}... (valid format)")
                else:
                    print(f"  ✗ {field}: invalid format")
                    all_passed = False
            elif field == "block_timestamp":
                # Validate ISO 8601 format
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                    print(f"  ✓ {field}: {value} (valid ISO 8601)")
                except:
                    print(f"  ✗ {field}: invalid timestamp format")
                    all_passed = False
            elif field == "fee":
                # Validate it's a decimal string
                try:
                    Decimal(value)
                    print(f"  ✓ {field}: {value} (valid decimal)")
                except:
                    print(f"  ✗ {field}: invalid decimal format")
                    all_passed = False
            else:
                print(f"  ✓ {field}: exists")
        else:
            print(f"  ✗ {field}: MISSING")
            all_passed = False
    
    # Check for NEW fields (should be present but optional)
    print("\n🔍 Checking NEW fields (should be added):")
    new_fields = ["order_side", "buyer_address", "seller_address", "trade_id", "trade_hash"]
    
    for field in new_fields:
        if field in result:
            print(f"  ✓ {field}: {result[field]}")
        else:
            print(f"  ℹ {field}: not present (optional)")
    
    # Validate field order (old fields should come first)
    print("\n🔍 Validating field order (old fields first):")
    keys = list(result.keys())
    old_field_names = list(EXPECTED_OLD_FIELDS.keys()) + ["tx_hash", "block_number", "block_timestamp", "user_address", "leverage", "margin", "fee", "tx_type", "raw_data"]
    
    # Find index of last old field
    last_old_field_idx = -1
    for i, key in enumerate(keys):
        if key in old_field_names:
            last_old_field_idx = i
    
    # Find index of first new field
    first_new_field_idx = len(keys)
    for i, key in enumerate(keys):
        if key in new_fields:
            first_new_field_idx = i
            break
    
    if first_new_field_idx > last_old_field_idx:
        print(f"  ✓ New fields appear after old fields")
    else:
        print(f"  ⚠ New fields may be interleaved with old fields")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ REGRESSION TEST PASSED")
        print("   All old fields match expected values")
        print("   Backward compatibility maintained")
    else:
        print("❌ REGRESSION TEST FAILED")
        print("   Some old fields do not match expected values")
        print("   Backward compatibility BROKEN")
    print("="*60 + "\n")
    
    return all_passed


def test_default_configuration():
    """Test that default configuration matches expected behavior"""
    print("\n" + "="*60)
    print("Configuration Test: Default Behavior")
    print("="*60)
    
    import os
    from dotenv import load_dotenv
    
    # Load environment (should use defaults)
    load_dotenv()
    
    # Check feature flags
    enable_liquidation = os.getenv("ENABLE_LIQUIDATION_FEED", "false").lower() == "true"
    enable_position = os.getenv("ENABLE_POSITION_FEED", "false").lower() == "true"
    enable_price = os.getenv("ENABLE_PRICE_FEED", "false").lower() == "true"
    
    print("\n🔍 Checking feature flags:")
    all_passed = True
    
    if not enable_liquidation:
        print("  ✓ ENABLE_LIQUIDATION_FEED: false (default)")
    else:
        print("  ✗ ENABLE_LIQUIDATION_FEED: true (should be false)")
        all_passed = False
    
    if not enable_position:
        print("  ✓ ENABLE_POSITION_FEED: false (default)")
    else:
        print("  ✗ ENABLE_POSITION_FEED: true (should be false)")
        all_passed = False
    
    if not enable_price:
        print("  ✓ ENABLE_PRICE_FEED: false (default)")
    else:
        print("  ✗ ENABLE_PRICE_FEED: true (should be false)")
        all_passed = False
    
    # Check default topic
    kafka_topic = os.getenv("KAFKA_TOPIC", "hyperliquid-raw-trades")
    print(f"\n🔍 Checking default topic:")
    if kafka_topic == "hyperliquid-raw-trades":
        print(f"  ✓ KAFKA_TOPIC: {kafka_topic} (default)")
    else:
        print(f"  ✗ KAFKA_TOPIC: {kafka_topic} (should be hyperliquid-raw-trades)")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ CONFIGURATION TEST PASSED")
        print("   All feature flags disabled by default")
        print("   Default topic unchanged")
    else:
        print("❌ CONFIGURATION TEST FAILED")
        print("   Some settings do not match defaults")
    print("="*60 + "\n")
    
    return all_passed


def test_liquidation_position_side_no_inference():
    """Test that parse_liquidation does NOT infer position_side from order_side"""
    print("\n" + "="*60)
    print("Liquidation Test: No Position Side Inference")
    print("="*60)
    
    # Mock liquidation fill (only has order_side, no explicit position fields)
    MOCK_LIQUIDATION_FILL = {
        "coin": "ETH",
        "side": "A",  # Ask (sell)
        "px": "2800.50",
        "sz": "10.0",
        "time": 1706443800000,
        "hash": "0xdeadbeef12345678",
        "tid": 54321,
        "fee": "0",
        "oid": 999,
        "crossed": True,
        "liquidation": {
            "liquidatedUser": "0x1234567890123456789012345678901234567890",
            "markPx": 2800.00,
            "method": "market"
        }
    }
    
    MOCK_USER = "0x9999999999999999999999999999999999999999"
    MOCK_RAW_DATA = {
        "channel": "userFills",
        "data": {
            "user": MOCK_USER,
            "fills": [MOCK_LIQUIDATION_FILL]
        }
    }
    
    try:
        from main import ParserService
    except ImportError:
        print("✗ Failed to import ParserService")
        return False
    
    # Create service instance
    service = ParserService()
    
    # Parse the liquidation
    result = service.parse_liquidation(MOCK_LIQUIDATION_FILL, MOCK_USER, MOCK_RAW_DATA)
    
    if not result:
        print("✗ parse_liquidation returned None")
        return False
    
    print("\n📋 Parsed Liquidation Result (key fields):")
    print(f"  tx_type: {result.get('tx_type')}")
    print(f"  order_side: {result.get('order_side')}")
    print(f"  position_side: {result.get('position_side')}")
    print(f"  position_side_inferred: {result.get('position_side_inferred')}")
    print(f"  side_semantics: {result.get('side_semantics')}")
    
    print("\n🔍 Validating NO inference from order_side:")
    all_passed = True
    
    # Check that position_side is UNKNOWN (not inferred from order_side)
    expected_position_side = "UNKNOWN"
    actual_position_side = result.get("position_side")
    if actual_position_side == expected_position_side:
        print(f"  ✓ position_side: {actual_position_side} == {expected_position_side}")
    else:
        print(f"  ✗ position_side: {actual_position_side} != {expected_position_side}")
        print(f"    ERROR: Should NOT infer from order_side!")
        all_passed = False
    
    # Check that position_side_inferred is False
    expected_inferred = False
    actual_inferred = result.get("position_side_inferred")
    if actual_inferred == expected_inferred:
        print(f"  ✓ position_side_inferred: {actual_inferred} == {expected_inferred}")
    else:
        print(f"  ✗ position_side_inferred: {actual_inferred} != {expected_inferred}")
        all_passed = False
    
    # Verify order_side is still populated correctly
    expected_order_side = "SELL"  # side="A" -> SELL
    actual_order_side = result.get("order_side")
    if actual_order_side == expected_order_side:
        print(f"  ✓ order_side: {actual_order_side} == {expected_order_side} (preserved)")
    else:
        print(f"  ✗ order_side: {actual_order_side} != {expected_order_side}")
        all_passed = False
    
    # Verify side_semantics is present
    if result.get("side_semantics") == "BACKWARD_COMPAT_AMBIGUOUS":
        print(f"  ✓ side_semantics: BACKWARD_COMPAT_AMBIGUOUS (preserved)")
    else:
        print(f"  ✗ side_semantics: missing or incorrect")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ LIQUIDATION TEST PASSED")
        print("   No inference from order_side")
        print("   position_side remains UNKNOWN without explicit fields")
    else:
        print("❌ LIQUIDATION TEST FAILED")
        print("   Incorrect position_side inference behavior")
    print("="*60 + "\n")
    
    return all_passed


def test_default_topic_naming():
    """Test that default topic names follow aligned naming convention"""
    print("\n" + "="*60)
    print("Topic Naming Test: Aligned Convention")
    print("="*60)
    
    import os
    from dotenv import load_dotenv
    
    # Load environment (should use defaults from env.example)
    load_dotenv()
    
    # Check topic naming convention
    topic_liquidations = os.getenv("KAFKA_TOPIC_LIQUIDATIONS", "hyperliquid-raw-liquidation")
    topic_positions = os.getenv("KAFKA_TOPIC_POSITIONS", "hyperliquid-raw-positions")
    topic_prices = os.getenv("KAFKA_TOPIC_PRICES", "hyperliquid-raw-price")
    
    print("\n🔍 Checking topic naming convention:")
    all_passed = True
    
    # Check liquidation (singular)
    if topic_liquidations == "hyperliquid-raw-liquidation":
        print(f"  ✓ KAFKA_TOPIC_LIQUIDATIONS: {topic_liquidations} (singular)")
    else:
        print(f"  ✗ KAFKA_TOPIC_LIQUIDATIONS: {topic_liquidations} (should be hyperliquid-raw-liquidation)")
        all_passed = False
    
    # Check positions (plural - kept for consistency)
    if topic_positions == "hyperliquid-raw-positions":
        print(f"  ✓ KAFKA_TOPIC_POSITIONS: {topic_positions} (plural - kept)")
    else:
        print(f"  ✗ KAFKA_TOPIC_POSITIONS: {topic_positions} (should be hyperliquid-raw-positions)")
        all_passed = False
    
    # Check prices (singular)
    if topic_prices == "hyperliquid-raw-price":
        print(f"  ✓ KAFKA_TOPIC_PRICES: {topic_prices} (singular)")
    else:
        print(f"  ✗ KAFKA_TOPIC_PRICES: {topic_prices} (should be hyperliquid-raw-price)")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ TOPIC NAMING TEST PASSED")
        print("   All topic names follow aligned convention")
    else:
        print("❌ TOPIC NAMING TEST FAILED")
        print("   Some topic names do not match convention")
    print("="*60 + "\n")
    
    return all_passed


def test_default_subscriptions():
    """Test that _build_subscriptions() returns only trades in default config"""
    print("\n" + "="*60)
    print("Subscription Test: Default Subscriptions")
    print("="*60)
    
    try:
        from main import ParserService
    except ImportError:
        print("✗ Failed to import ParserService")
        return False
    
    # Create service instance (will use default env)
    service = ParserService()
    
    # Get subscriptions
    subscriptions = service._build_subscriptions()
    
    print(f"\n🔍 Checking _build_subscriptions() output:")
    print(f"  Subscription count: {len(subscriptions)}")
    
    all_passed = True
    
    # Check length
    if len(subscriptions) == 1:
        print(f"  ✓ Length: {len(subscriptions)} == 1 (only trades)")
    else:
        print(f"  ✗ Length: {len(subscriptions)} != 1 (expected only trades)")
        print(f"    Subscriptions: {subscriptions}")
        all_passed = False
    
    # Check type
    if len(subscriptions) > 0:
        first_sub = subscriptions[0]
        if first_sub.get("type") == "trades":
            print(f"  ✓ Type: trades")
            if first_sub.get("coin") == service.coin:
                print(f"  ✓ Coin: {first_sub.get('coin')} (matches config)")
            else:
                print(f"  ✗ Coin: {first_sub.get('coin')} != {service.coin}")
                all_passed = False
        else:
            print(f"  ✗ Type: {first_sub.get('type')} != trades")
            all_passed = False
    
    # Check no other subscriptions
    if len(subscriptions) > 1:
        print(f"\n  ⚠ Unexpected additional subscriptions:")
        for i, sub in enumerate(subscriptions[1:], 1):
            print(f"    [{i}] {sub}")
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ SUBSCRIPTION TEST PASSED")
        print("   Default config returns only trades subscription")
    else:
        print("❌ SUBSCRIPTION TEST FAILED")
        print("   Default subscriptions do not match expected")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Parser Service Regression Test Suite")
    print("#"*60)
    
    # Run tests
    test1_passed = test_default_configuration()
    test2_passed = test_default_topic_naming()
    test3_passed = test_default_subscriptions()
    test4_passed = test_parse_trade_backward_compatibility()
    test5_passed = test_liquidation_position_side_no_inference()
    
    # Summary
    print("\n" + "#"*60)
    print("# Test Summary")
    print("#"*60)
    print(f"  Default Configuration: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Topic Naming Convention: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"  Default Subscriptions: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    print(f"  Backward Compatibility: {'✅ PASS' if test4_passed else '❌ FAIL'}")
    print(f"  Liquidation No Inference: {'✅ PASS' if test5_passed else '❌ FAIL'}")
    print("#"*60 + "\n")
    
    # Exit with appropriate code
    if test1_passed and test2_passed and test3_passed and test4_passed and test5_passed:
        print("🎉 All regression tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some regression tests failed!")
        sys.exit(1)
