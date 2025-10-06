FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy config and source
COPY config/ /app/config/
COPY src/ /app/src/

# Set Python path
ENV PYTHONPATH=/app

# Run aggregator
CMD ["python", "-u", "src/main.py"]
