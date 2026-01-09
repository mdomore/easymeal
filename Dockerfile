FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for EasyOCR (OpenCV, etc.)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only first (much smaller than CUDA version)
# This prevents EasyOCR from pulling in CUDA/NVIDIA packages
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY ./static /app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

