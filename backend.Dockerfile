# Base image
FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache --no-install-project

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
