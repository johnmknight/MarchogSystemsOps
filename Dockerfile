FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server and client
COPY server/ ./server/
COPY client/ ./client/
COPY data/ ./data/
COPY media/ ./media/

# Data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8082

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8082"]
