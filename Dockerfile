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

# Download the OCR models into the image, so a restart doesn't fetch them again, then run the
# tests here: the OCR backend behaves differently on this platform than on a Mac.
RUN python -c "import ocr; ocr.load_all()" \
    && pip install --no-cache-dir pytest \
    && OPENAI_API_KEY=test python -m pytest -q -p no:cacheprovider \
    && pip uninstall -y pytest

EXPOSE 5123

CMD ["python", "app.py"]
