FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for grpc/psycopg
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==1.8.3

# Copy poetry config
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Generate gRPC Stubs dynamically during build
RUN ./scripts/generate_protos.sh

# Expose port (will be overridden by docker-compose)
EXPOSE 8007

# Run the FastAPI server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
