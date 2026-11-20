FROM python:3.11-slim

WORKDIR /app

ARG ENABLE_OCR=1

# System libs (OpenCV / EasyOCR when enabled)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# App dependencies first (stable layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# OCR stack (optional). Kept in a separate layer so app-only changes stay cacheable.
COPY requirements-ocr.txt .
RUN if [ "$ENABLE_OCR" = "1" ]; then \
      pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
      pip install --no-cache-dir -r requirements-ocr.txt && \
      python -c "import easyocr; easyocr.Reader(['en','fr'], gpu=False); print('EasyOCR models precached')" ; \
    else \
      echo "ENABLE_OCR=0 — skipping torch/easyocr" ; \
    fi

ENV ENABLE_OCR=${ENABLE_OCR}

COPY ./app /app/app
COPY ./static /app/static
COPY run_local.py /app/run_local.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
