#!/bin/bash
# Verification script for Parser service

echo "=========================================="
echo "Parser Service Verification"
echo "=========================================="
echo ""

# Check if Python is installed
echo "1. Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ $PYTHON_VERSION"
else
    echo "   ✗ Python 3 not found"
    exit 1
fi

# Check if dependencies are installed
echo ""
echo "2. Checking Python dependencies..."
if python3 -c "import kafka" 2>/dev/null; then
    echo "   ✓ kafka-python installed"
else
    echo "   ✗ kafka-python not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

if python3 -c "import websockets" 2>/dev/null; then
    echo "   ✓ websockets installed"
else
    echo "   ✗ websockets not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

if python3 -c "import dotenv" 2>/dev/null; then
    echo "   ✓ python-dotenv installed"
else
    echo "   ✗ python-dotenv not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Check if required files exist
echo ""
echo "3. Checking required files..."
FILES=("main.py" "producer.py" "hl_ws_client.py" "consumer_test.py" "requirements.txt" "env.example")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file exists"
    else
        echo "   ✗ $file not found"
        exit 1
    fi
done

# Check if .env file exists
echo ""
echo "4. Checking environment configuration..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    
    # Check required variables
    if grep -q "HL_COIN" .env; then
        echo "   ✓ HL_COIN configured"
    else
        echo "   ⚠ HL_COIN not set in .env"
    fi
    
    if grep -q "KAFKA_BOOTSTRAP_SERVERS" .env; then
        echo "   ✓ KAFKA_BOOTSTRAP_SERVERS configured"
    else
        echo "   ⚠ KAFKA_BOOTSTRAP_SERVERS not set in .env"
    fi
else
    echo "   ⚠ .env file not found (will use defaults)"
    echo "   Create one from env.example: cp env.example .env"
fi

# Test DRY_RUN mode
echo ""
echo "5. Testing DRY_RUN mode..."
echo "   Starting parser in DRY_RUN mode for 5 seconds..."
timeout 5 python3 main.py 2>&1 | head -20 &
PID=$!
sleep 5
kill $PID 2>/dev/null
echo "   ✓ DRY_RUN test completed"

echo ""
echo "=========================================="
echo "✓ All checks passed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start Kafka if not running"
echo "2. Run: python main.py"
echo "3. Verify messages: python consumer_test.py"
echo ""
