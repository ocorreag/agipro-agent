# CAUSA Agent - Cloud Streamlit Application
# For hybrid deployment with Local Helper
#
# Build: docker build -t causa-cloud -f cloud/Dockerfile .
# Run:   docker run -p 8501:8501 -e CAUSA_MODE=hybrid causa-cloud

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy cloud-specific requirements (lightweight, no PyTorch/CUDA)
COPY cloud/requirements-cloud.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./

# Set environment variables
ENV CAUSA_MODE=hybrid
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
