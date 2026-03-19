FROM python:3.11-slim

# No network access, read-only filesystem, minimal image
RUN pip install --no-cache-dir requests==2.31.0

# Create non-root user
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /sandbox

# Default command (overridden at runtime)
CMD ["python3", "/sandbox/target.py"]
