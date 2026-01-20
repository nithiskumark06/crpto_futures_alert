FROM python:3.12-slim

# Prevent Python buffering logs (important for Railway)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (optional but safe)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first (Docker cache optimization)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run bot
CMD ["python", "coindcx_bot.py"]
