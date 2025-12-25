FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

# Install the absolute latest CPU torch and transformers
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers

COPY requirements.txt .
# Ensure requirements.txt doesn't overwrite torch or transformers
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]