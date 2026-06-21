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
COPY ai-agent-fastapi/pyproject.toml ai-agent-fastapi/poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Pre-download ML Models (spaCy & SentenceTransformers) into the Docker Image
RUN python -m spacy download en_core_web_sm && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY ai-agent-fastapi/ .
COPY shared-proto/ /shared-proto/

# Generate gRPC Stubs dynamically during build
RUN ./scripts/generate_protos.sh

# Expose port (will be overridden by docker-compose)
EXPOSE 8007

# Run the FastAPI server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
