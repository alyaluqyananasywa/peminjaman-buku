FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Konfigurasi database dikirim saat container dijalankan (variabel DB_*), tidak ditulis di image
ENV PORT=80
EXPOSE 80

CMD ["python", "app.py"]
