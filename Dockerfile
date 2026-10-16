FROM python:3.11-slim

WORKDIR /app

# System libraries for OpenCV, and OpenMP for Paddle
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download the OCR models into the image, so a restart doesn't fetch them again.
RUN python -c "import ocr; ocr.load_all()"

EXPOSE 5123

CMD ["python", "app.py"]
