FROM python:3.11-slim

# Install system dependencies including FFmpeg and Node.js for YouTube JS solver
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && (which node || ln -s /usr/bin/nodejs /usr/bin/node)

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/clips storage/thumbnails storage/temp storage/processed

ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
