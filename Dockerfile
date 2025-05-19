# Use a Python base image
FROM python:3.11-slim AS python-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Set working directory
WORKDIR $PYSETUP_PATH

# Copy only dependencies first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev

# Development stage
FROM python-base AS development

# Install development dependencies
RUN poetry install

# Copy application code
COPY . .

# Final stage
FROM python-base AS production

# Copy application code
COPY . .

# Copy installed packages from the development stage
COPY --from=development $PYSETUP_PATH $PYSETUP_PATH

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Set ownership and permissions
RUN chown -R app:app $PYSETUP_PATH

# Switch to non-root user
USER app

# Create necessary directories with correct permissions
RUN mkdir -p /tmp/app/logs && chown -R app:app /tmp/app

# Set the entry point script
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
ENTRYPOINT ["/docker-entrypoint.sh"]