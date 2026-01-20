# Dockerfile for Parser Service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY producer.py .
COPY hl_ws_client.py .

# Environment variables (can be overridden)
ENV HL_COIN=BTC
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV KAFKA_TOPIC=hyperliquid-raw-trades
ENV DRY_RUN=0

# Run the parser
CMD ["python", "-u", "main.py"]
