# ================================
# 🐳 Telegram Hosting Bot — Docker
# ================================

FROM python:3.11-slim

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies pehle copy karo (cache ke liye)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Project files copy karo
COPY . .

# Port expose karo
EXPOSE 8080

# Bot run karo
CMD ["python", "main.py"]
