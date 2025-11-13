# Claude Config Editor - Development Container
# This ensures identical execution environment between agent and developer

FROM python:3.11.7-slim-bookworm

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git=1:2.39.2-1.1 \
    sqlite3=3.40.1-2 \
    curl=7.88.1-10+deb12u8 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for development
RUN useradd -m -s /bin/bash developer && \
    mkdir -p /workspace && \
    chown -R developer:developer /workspace

# Set working directory
WORKDIR /workspace

# Copy requirements files
COPY --chown=developer:developer requirements.txt requirements-dev.txt ./

# Install Python dependencies with exact versions
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy project files
COPY --chown=developer:developer . .

# Install project in editable mode
RUN pip install -e .

# Switch to non-root user
USER developer

# Create data and logs directories
RUN mkdir -p /workspace/data /workspace/logs

# Expose API port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Default command - keep container running for interactive use
CMD ["tail", "-f", "/dev/null"]
