FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server and client
COPY server/ ./server/
COPY client/ ./client/

# Data directories will be provided by Docker volumes
# DO NOT copy data/ or media/ - volumes provide production data
RUN mkdir -p /app/data /app/media

EXPOSE 8082

# Run from server/ so bare imports resolve correctly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082", "--app-dir", "server"]
