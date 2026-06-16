FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies first (layer caching — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config.py .
COPY main.py .
COPY pdf_export.py .

# Create directories that will be volume-mounted or used at runtime
# (these exist so the app doesn't fail if a volume isn't mounted yet, e.g. first run)
RUN mkdir -p /app/chroma_store /app/data/uploads /app/logs /app/tmp_images

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
